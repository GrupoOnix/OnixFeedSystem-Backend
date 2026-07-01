from datetime import datetime, timezone
from typing import Any, Optional, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.entities.silo_inventory import (
    SiloInventoryBatch,
    SiloInventoryBatchStatus,
    SiloInventoryMovementType,
    SiloStockReservationStatus,
    SiloStockSummary,
)
from infrastructure.persistence.models.food_model import FoodModel
from infrastructure.persistence.models.silo_inventory_model import (
    FeedingBatchConsumptionModel,
    SiloInventoryBatchModel,
    SiloInventoryMovementModel,
    SiloStockReservationModel,
)
from infrastructure.persistence.models.silo_model import SiloModel


class SiloInventoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_mg(quantity_kg: float) -> int:
        if quantity_kg < 0:
            raise ValueError("La cantidad no puede ser negativa")
        return round(quantity_kg * 1_000_000)

    async def get_summary(self, silo_id: UUID) -> SiloStockSummary:
        total_result = await self.session.execute(
            select(func.coalesce(func.sum(col(SiloInventoryBatchModel.remaining_quantity_mg)), 0)).where(
                col(SiloInventoryBatchModel.silo_id) == silo_id,
                col(SiloInventoryBatchModel.status) != SiloInventoryBatchStatus.ARCHIVED.value,
            )
        )
        reserved_result = await self.session.execute(
            select(
                func.coalesce(
                    func.sum(
                        col(SiloStockReservationModel.reserved_quantity_mg)
                        - col(SiloStockReservationModel.consumed_quantity_mg)
                    ),
                    0,
                )
            ).where(
                col(SiloStockReservationModel.silo_id) == silo_id,
                col(SiloStockReservationModel.status) == SiloStockReservationStatus.ACTIVE.value,
            )
        )
        return SiloStockSummary(
            total_stock_mg=int(total_result.scalar_one()),
            reserved_stock_mg=int(reserved_result.scalar_one()),
        )

    async def list_batches(
        self,
        silo_id: UUID,
        statuses: Optional[list[SiloInventoryBatchStatus]] = None,
        *,
        offset: int = 0,
        limit: int = 100,
        lock: bool = False,
    ) -> list[SiloInventoryBatch]:
        reserved_subquery = (
            select(
                col(SiloStockReservationModel.batch_id).label("batch_id"),
                func.coalesce(
                    func.sum(
                        col(SiloStockReservationModel.reserved_quantity_mg)
                        - col(SiloStockReservationModel.consumed_quantity_mg)
                    ),
                    0,
                ).label("reserved_mg"),
            )
            .where(col(SiloStockReservationModel.status) == SiloStockReservationStatus.ACTIVE.value)
            .group_by(col(SiloStockReservationModel.batch_id))
            .subquery()
        )
        query = (
            select(
                SiloInventoryBatchModel,
                col(FoodModel.name),
                col(FoodModel.code),
                col(FoodModel.provider),
                func.coalesce(reserved_subquery.c.reserved_mg, 0).label("reserved_mg"),
            )
            .outerjoin(FoodModel, col(FoodModel.id) == col(SiloInventoryBatchModel.food_id))
            .outerjoin(reserved_subquery, reserved_subquery.c.batch_id == col(SiloInventoryBatchModel.id))
            .where(col(SiloInventoryBatchModel.silo_id) == silo_id)
            .order_by(col(SiloInventoryBatchModel.position), col(SiloInventoryBatchModel.received_at))
            .offset(offset)
            .limit(limit)
        )
        if statuses:
            query = query.where(col(SiloInventoryBatchModel.status).in_([status.value for status in statuses]))
        if lock:
            query = query.with_for_update(of=SiloInventoryBatchModel)
        result = await self.session.execute(query)
        return [
            self._to_domain(row.SiloInventoryBatchModel, int(row.reserved_mg), row.name, row.code, row.provider)
            for row in result.all()
        ]

    async def create_batch(
        self,
        silo_id: UUID,
        food_id: UUID,
        quantity_kg: float,
        operator_id: str,
        *,
        before_batch_id: Optional[UUID] = None,
        after_batch_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> SiloInventoryBatch:
        if before_batch_id and after_batch_id:
            raise ValueError("Debe indicar before_batch_id o after_batch_id, no ambos")
        quantity_mg = self._to_mg(quantity_kg)
        if quantity_mg <= 0:
            raise ValueError("La cantidad debe ser mayor a cero")
        silo = await self._lock_silo(silo_id)
        await self._require_active_food(food_id)
        summary = await self.get_summary(silo_id)
        if summary.total_stock_mg + quantity_mg > silo.capacity_mg:
            raise ValueError("La carga supera la capacidad disponible del silo")
        batches = await self._active_models(silo_id, lock=True)
        insert_index = self._resolve_insert_index(batches, before_batch_id, after_batch_id)
        for index, batch in enumerate(batches):
            batch.position = index + (2 if index >= insert_index else 1)
        now = datetime.now(timezone.utc)
        model = SiloInventoryBatchModel(
            silo_id=silo_id,
            food_id=food_id,
            remaining_quantity_mg=quantity_mg,
            position=insert_index + 1,
            status=SiloInventoryBatchStatus.ACTIVE.value,
            received_at=now,
            created_by_operator_id=operator_id,
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        self._add_movement(
            model,
            SiloInventoryMovementType.INITIAL_LOAD,
            operator_id,
            reason=reason,
            previous_quantity_mg=0,
            new_quantity_mg=quantity_mg,
            new_food_id=food_id,
            new_position=model.position,
        )
        await self.session.flush()
        return await self.get_batch(silo_id, model.id)

    async def get_batch(self, silo_id: UUID, batch_id: UUID, *, lock: bool = False) -> SiloInventoryBatch:
        batches = await self.list_batches(silo_id, offset=0, limit=10000, lock=lock)
        batch = next((item for item in batches if item.id == batch_id), None)
        if not batch:
            raise ValueError("Partida no encontrada en el silo")
        return batch

    async def update_batch(
        self,
        silo_id: UUID,
        batch_id: UUID,
        operator_id: str,
        *,
        food_id: Optional[UUID] = None,
        remaining_quantity_kg: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> SiloInventoryBatch:
        silo = await self._lock_silo(silo_id)
        model = await self._batch_model(silo_id, batch_id, lock=True)
        reserved = await self._reserved_for_batch(batch_id)
        now = datetime.now(timezone.utc)
        if food_id is not None and food_id != model.food_id:
            if reserved > 0:
                raise ValueError("No se puede cambiar el alimento de una partida con reservas activas")
            await self._require_active_food(food_id)
            previous_food_id = model.food_id
            model.food_id = food_id
            self._add_movement(
                model,
                SiloInventoryMovementType.FOOD_CHANGED,
                operator_id,
                reason=reason,
                previous_quantity_mg=model.remaining_quantity_mg,
                new_quantity_mg=model.remaining_quantity_mg,
                previous_food_id=previous_food_id,
                new_food_id=food_id,
            )
        if remaining_quantity_kg is not None:
            new_quantity_mg = self._to_mg(remaining_quantity_kg)
            if new_quantity_mg < reserved:
                raise ValueError("La cantidad no puede ser menor al stock reservado")
            summary = await self.get_summary(silo_id)
            if summary.total_stock_mg - model.remaining_quantity_mg + new_quantity_mg > silo.capacity_mg:
                raise ValueError("El ajuste supera la capacidad del silo")
            previous_quantity_mg = model.remaining_quantity_mg
            model.remaining_quantity_mg = new_quantity_mg
            model.status = (
                SiloInventoryBatchStatus.DEPLETED.value
                if new_quantity_mg == 0
                else SiloInventoryBatchStatus.ACTIVE.value
            )
            self._add_movement(
                model,
                SiloInventoryMovementType.ADJUSTMENT,
                operator_id,
                reason=reason,
                previous_quantity_mg=previous_quantity_mg,
                new_quantity_mg=new_quantity_mg,
            )
        model.updated_at = now
        await self._normalize_positions(silo_id)
        await self.session.flush()
        return await self.get_batch(silo_id, batch_id)

    async def move_batch(
        self,
        silo_id: UUID,
        batch_id: UUID,
        operator_id: str,
        *,
        before_batch_id: Optional[UUID] = None,
        after_batch_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> SiloInventoryBatch:
        if before_batch_id and after_batch_id:
            raise ValueError("Debe indicar before_batch_id o after_batch_id, no ambos")
        await self._lock_silo(silo_id)
        batches = await self._active_models(silo_id, lock=True)
        target = next((batch for batch in batches if batch.id == batch_id), None)
        if not target:
            raise ValueError("Solo se pueden mover partidas activas")
        previous_position = target.position
        batches.remove(target)
        insert_index = self._resolve_insert_index(batches, before_batch_id, after_batch_id)
        batches.insert(insert_index, target)
        for index, batch in enumerate(batches, start=1):
            batch.position = index
            batch.updated_at = datetime.now(timezone.utc)
        self._add_movement(
            target,
            SiloInventoryMovementType.REORDERED,
            operator_id,
            reason=reason,
            previous_quantity_mg=target.remaining_quantity_mg,
            new_quantity_mg=target.remaining_quantity_mg,
            previous_position=previous_position,
            new_position=target.position,
        )
        await self.session.flush()
        return await self.get_batch(silo_id, batch_id)

    async def withdraw_batch(
        self,
        silo_id: UUID,
        batch_id: UUID,
        operator_id: str,
        reason: Optional[str] = None,
    ) -> SiloInventoryBatch:
        await self._lock_silo(silo_id)
        model = await self._batch_model(silo_id, batch_id, lock=True)
        if await self._reserved_for_batch(batch_id) > 0:
            raise ValueError("No se puede retirar una partida con reservas activas")
        previous = model.remaining_quantity_mg
        model.remaining_quantity_mg = 0
        model.status = SiloInventoryBatchStatus.ARCHIVED.value
        model.updated_at = datetime.now(timezone.utc)
        self._add_movement(
            model,
            SiloInventoryMovementType.WITHDRAWAL,
            operator_id,
            reason=reason,
            previous_quantity_mg=previous,
            new_quantity_mg=0,
        )
        await self._normalize_positions(silo_id)
        await self.session.flush()
        return await self.get_batch(silo_id, batch_id)

    async def transfer_stock(
        self,
        source_silo_id: UUID,
        destination_silo_id: UUID,
        quantity_kg: float,
        operator_id: str,
        *,
        reason: Optional[str] = None,
    ) -> list[SiloInventoryBatch]:
        if source_silo_id == destination_silo_id:
            raise ValueError("El silo de origen y destino deben ser distintos")
        quantity_mg = self._to_mg(quantity_kg)
        if quantity_mg <= 0:
            raise ValueError("La cantidad a trasvasijar debe ser mayor a cero")

        silos = await self._lock_silos(source_silo_id, destination_silo_id)
        destination_silo = silos[destination_silo_id]
        destination_summary = await self.get_summary(destination_silo_id)
        if destination_summary.total_stock_mg + quantity_mg > destination_silo.capacity_mg:
            raise ValueError("El trasvasije supera la capacidad disponible del silo destino")

        source_batches = await self._active_models(source_silo_id, lock=True)
        source_available: list[tuple[SiloInventoryBatchModel, int]] = []
        for batch in source_batches:
            reserved_mg = await self._reserved_for_batch(batch.id)
            source_available.append(
                (batch, max(batch.remaining_quantity_mg - reserved_mg, 0))
            )
        if sum(available_mg for _, available_mg in source_available) < quantity_mg:
            raise ValueError("Stock disponible insuficiente en el silo de origen")

        destination_batches = await self._active_models(
            destination_silo_id, lock=True
        )
        next_position = len(destination_batches) + 1
        pending_mg = quantity_mg
        now = datetime.now(timezone.utc)
        transferred_ids: list[UUID] = []

        for source_batch, available_mg in source_available:
            transferred_mg = min(pending_mg, available_mg)
            if transferred_mg <= 0:
                continue

            previous_source_mg = source_batch.remaining_quantity_mg
            source_batch.remaining_quantity_mg -= transferred_mg
            if source_batch.remaining_quantity_mg == 0:
                source_batch.status = SiloInventoryBatchStatus.DEPLETED.value
            source_batch.updated_at = now
            self._add_movement(
                source_batch,
                SiloInventoryMovementType.TRANSFER_OUT,
                operator_id,
                reason=reason,
                previous_quantity_mg=previous_source_mg,
                new_quantity_mg=source_batch.remaining_quantity_mg,
                previous_food_id=source_batch.food_id,
                new_food_id=source_batch.food_id,
                previous_position=source_batch.position,
                new_position=source_batch.position,
            )

            destination_batch = SiloInventoryBatchModel(
                silo_id=destination_silo_id,
                food_id=source_batch.food_id,
                remaining_quantity_mg=transferred_mg,
                position=next_position,
                status=SiloInventoryBatchStatus.ACTIVE.value,
                received_at=source_batch.received_at,
                created_by_operator_id=operator_id,
                created_at=now,
                updated_at=now,
            )
            self.session.add(destination_batch)
            await self.session.flush()
            self._add_movement(
                destination_batch,
                SiloInventoryMovementType.TRANSFER_IN,
                operator_id,
                reason=reason,
                previous_quantity_mg=0,
                new_quantity_mg=transferred_mg,
                new_food_id=destination_batch.food_id,
                new_position=destination_batch.position,
            )
            transferred_ids.append(destination_batch.id)
            next_position += 1
            pending_mg -= transferred_mg
            if pending_mg == 0:
                break

        await self._normalize_positions(source_silo_id)
        await self.session.flush()
        return [
            await self.get_batch(destination_silo_id, batch_id)
            for batch_id in transferred_ids
        ]

    async def reserve(self, session_id: str, silo_id: UUID, quantity_kg: float) -> None:
        quantity_mg = self._to_mg(quantity_kg)
        if quantity_mg <= 0:
            raise ValueError("La reserva debe ser mayor a cero")
        await self._lock_silo(silo_id)
        active = await self._active_models(silo_id, lock=True, identified_only=True)
        available: list[tuple[SiloInventoryBatchModel, int]] = []
        for batch in active:
            reserved = await self._reserved_for_batch(batch.id)
            available.append((batch, max(batch.remaining_quantity_mg - reserved, 0)))
        if sum(value for _, value in available) < quantity_mg:
            raise ValueError("Stock disponible insuficiente en el silo")
        pending = quantity_mg
        now = datetime.now(timezone.utc)
        for batch, available_mg in available:
            allocation = min(pending, available_mg)
            if allocation <= 0:
                continue
            self.session.add(
                SiloStockReservationModel(
                    feeding_session_id=session_id,
                    silo_id=silo_id,
                    batch_id=batch.id,
                    reserved_quantity_mg=allocation,
                    consumed_quantity_mg=0,
                    status=SiloStockReservationStatus.ACTIVE.value,
                    created_at=now,
                    updated_at=now,
                )
            )
            pending -= allocation
            if pending == 0:
                break
        await self.session.flush()

    async def resize_reservation(self, session_id: str, desired_total_kg: float) -> None:
        desired_mg = self._to_mg(desired_total_kg)
        reservations = await self._session_reservations(session_id, lock=True)
        if not reservations:
            raise ValueError("La sesión no tiene reservas de inventario")
        consumed = sum(item.consumed_quantity_mg for item in reservations)
        if desired_mg < consumed:
            raise ValueError("La reserva no puede ser menor a lo ya consumido")
        current = sum(item.reserved_quantity_mg for item in reservations)
        if desired_mg == current:
            return
        if desired_mg > current:
            await self._extend_reservation(session_id, reservations[0].silo_id, desired_mg - current)
            return
        to_release = current - desired_mg
        for reservation in reversed(reservations):
            releasable = reservation.reserved_quantity_mg - reservation.consumed_quantity_mg
            released = min(to_release, releasable)
            reservation.reserved_quantity_mg -= released
            reservation.updated_at = datetime.now(timezone.utc)
            if reservation.reserved_quantity_mg == reservation.consumed_quantity_mg:
                reservation.status = SiloStockReservationStatus.CONSUMED.value
            to_release -= released
            if to_release == 0:
                break
        await self.session.flush()

    async def consume(
        self,
        session_id: str,
        cage_feeding_id: str,
        quantity_kg: float,
        operator_id: str,
    ) -> None:
        quantity_mg = self._to_mg(quantity_kg)
        if quantity_mg <= 0:
            return
        reservations = await self._session_reservations(session_id, lock=True)
        if not reservations:
            raise ValueError("No existen reservas activas para la sesión")
        silo_id = reservations[0].silo_id
        await self._lock_silo(silo_id)
        pending = quantity_mg
        for reservation in reservations:
            reserved_remaining = reservation.reserved_quantity_mg - reservation.consumed_quantity_mg
            consumed = min(pending, reserved_remaining)
            if consumed > 0:
                await self._consume_batch(
                    reservation,
                    cage_feeding_id,
                    consumed,
                    operator_id,
                )
                pending -= consumed
            if pending == 0:
                break
        if pending > 0:
            pending = await self._consume_unreserved_overflow(
                session_id, cage_feeding_id, silo_id, pending, operator_id
            )
        if pending > 0:
            raise ValueError("La cantidad dispensada excede el stock conciliable del silo")
        await self._normalize_positions(silo_id)
        await self.session.flush()

    async def release(self, session_id: str) -> None:
        reservations = await self._session_reservations(session_id, lock=True)
        now = datetime.now(timezone.utc)
        for reservation in reservations:
            reservation.status = (
                SiloStockReservationStatus.CONSUMED.value
                if reservation.consumed_quantity_mg >= reservation.reserved_quantity_mg
                else SiloStockReservationStatus.RELEASED.value
            )
            reservation.updated_at = now
        await self.session.flush()

    async def food_is_referenced(self, food_id: UUID) -> bool:
        for model, field in (
            (SiloInventoryBatchModel, SiloInventoryBatchModel.food_id),
            (FeedingBatchConsumptionModel, FeedingBatchConsumptionModel.food_id),
        ):
            column = cast(Any, field)
            result = await self.session.execute(select(func.count()).select_from(model).where(column == food_id))
            if result.scalar_one() > 0:
                return True
        movement_result = await self.session.execute(
            select(func.count())
            .select_from(SiloInventoryMovementModel)
            .where(
                (col(SiloInventoryMovementModel.previous_food_id) == food_id)
                | (col(SiloInventoryMovementModel.new_food_id) == food_id)
            )
        )
        return movement_result.scalar_one() > 0

    async def list_session_consumptions(self, session_id: str) -> list[dict]:
        result = await self.session.execute(
            select(
                FeedingBatchConsumptionModel,
                col(FoodModel.name),
                col(FoodModel.code),
                col(FoodModel.provider),
            )
            .join(FoodModel, col(FoodModel.id) == col(FeedingBatchConsumptionModel.food_id))
            .where(col(FeedingBatchConsumptionModel.feeding_session_id) == session_id)
            .order_by(col(FeedingBatchConsumptionModel.created_at))
        )
        return [
            {
                "id": str(row.FeedingBatchConsumptionModel.id),
                "cage_feeding_id": row.FeedingBatchConsumptionModel.cage_feeding_id,
                "silo_id": str(row.FeedingBatchConsumptionModel.silo_id),
                "batch_id": str(row.FeedingBatchConsumptionModel.batch_id),
                "food_id": str(row.FeedingBatchConsumptionModel.food_id),
                "food_name": row.name,
                "food_code": row.code,
                "food_provider": row.provider,
                "quantity_kg": row.FeedingBatchConsumptionModel.quantity_mg / 1_000_000,
                "operator_id": row.FeedingBatchConsumptionModel.operator_id,
                "created_at": row.FeedingBatchConsumptionModel.created_at,
            }
            for row in result.all()
        ]

    async def _consume_batch(
        self,
        reservation: SiloStockReservationModel,
        cage_feeding_id: str,
        quantity_mg: int,
        operator_id: str,
    ) -> None:
        batch = await self._batch_model(reservation.silo_id, reservation.batch_id, lock=True)
        if not batch.food_id:
            raise ValueError("No se puede consumir una partida sin alimento identificado")
        previous = batch.remaining_quantity_mg
        if quantity_mg > previous:
            raise ValueError("La partida no tiene saldo suficiente")
        batch.remaining_quantity_mg -= quantity_mg
        if batch.remaining_quantity_mg == 0:
            batch.status = SiloInventoryBatchStatus.DEPLETED.value
        batch.updated_at = datetime.now(timezone.utc)
        reservation.consumed_quantity_mg += quantity_mg
        if reservation.consumed_quantity_mg >= reservation.reserved_quantity_mg:
            reservation.status = SiloStockReservationStatus.CONSUMED.value
        reservation.updated_at = datetime.now(timezone.utc)
        self.session.add(
            FeedingBatchConsumptionModel(
                feeding_session_id=reservation.feeding_session_id,
                cage_feeding_id=cage_feeding_id,
                silo_id=reservation.silo_id,
                batch_id=batch.id,
                food_id=batch.food_id,
                quantity_mg=quantity_mg,
                operator_id=operator_id,
            )
        )
        self._add_movement(
            batch,
            SiloInventoryMovementType.CONSUMPTION,
            operator_id,
            previous_quantity_mg=previous,
            new_quantity_mg=batch.remaining_quantity_mg,
            feeding_session_id=reservation.feeding_session_id,
            cage_feeding_id=cage_feeding_id,
        )

    async def _consume_unreserved_overflow(
        self,
        session_id: str,
        cage_feeding_id: str,
        silo_id: UUID,
        pending: int,
        operator_id: str,
    ) -> int:
        batches = await self._active_models(silo_id, lock=True, identified_only=True)
        for batch in batches:
            reserved = await self._reserved_for_batch(batch.id)
            available = max(batch.remaining_quantity_mg - reserved, 0)
            allocation = min(pending, available)
            if allocation <= 0:
                continue
            reservation = SiloStockReservationModel(
                feeding_session_id=session_id,
                silo_id=silo_id,
                batch_id=batch.id,
                reserved_quantity_mg=allocation,
                consumed_quantity_mg=0,
                status=SiloStockReservationStatus.ACTIVE.value,
            )
            self.session.add(reservation)
            await self.session.flush()
            await self._consume_batch(reservation, cage_feeding_id, allocation, operator_id)
            pending -= allocation
            if pending == 0:
                break
        return pending

    async def _extend_reservation(self, session_id: str, silo_id: UUID, extra_mg: int) -> None:
        await self._lock_silo(silo_id)
        batches = await self._active_models(silo_id, lock=True, identified_only=True)
        pending = extra_mg
        now = datetime.now(timezone.utc)
        for batch in batches:
            available = max(batch.remaining_quantity_mg - await self._reserved_for_batch(batch.id), 0)
            allocation = min(pending, available)
            if allocation <= 0:
                continue
            self.session.add(
                SiloStockReservationModel(
                    feeding_session_id=session_id,
                    silo_id=silo_id,
                    batch_id=batch.id,
                    reserved_quantity_mg=allocation,
                    consumed_quantity_mg=0,
                    status=SiloStockReservationStatus.ACTIVE.value,
                    created_at=now,
                    updated_at=now,
                )
            )
            pending -= allocation
            if pending == 0:
                break
        if pending > 0:
            raise ValueError("Stock disponible insuficiente para ampliar la reserva")
        await self.session.flush()

    async def _session_reservations(
        self, session_id: str, *, lock: bool = False
    ) -> list[SiloStockReservationModel]:
        query = (
            select(SiloStockReservationModel)
            .join(
                SiloInventoryBatchModel,
                col(SiloInventoryBatchModel.id) == col(SiloStockReservationModel.batch_id),
            )
            .where(
                col(SiloStockReservationModel.feeding_session_id) == session_id,
                col(SiloStockReservationModel.status) == SiloStockReservationStatus.ACTIVE.value,
            )
            .order_by(col(SiloInventoryBatchModel.position), col(SiloStockReservationModel.created_at))
        )
        if lock:
            query = query.with_for_update(of=SiloStockReservationModel)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _lock_silo(self, silo_id: UUID) -> SiloModel:
        result = await self.session.execute(
            select(SiloModel).where(col(SiloModel.id) == silo_id).with_for_update()
        )
        silo = result.scalar_one_or_none()
        if not silo:
            raise ValueError("Silo no encontrado")
        return silo

    async def _lock_silos(self, *silo_ids: UUID) -> dict[UUID, SiloModel]:
        ordered_ids = sorted(set(silo_ids), key=str)
        result = await self.session.execute(
            select(SiloModel)
            .where(col(SiloModel.id).in_(ordered_ids))
            .order_by(col(SiloModel.id))
            .with_for_update()
        )
        silos = {silo.id: silo for silo in result.scalars().all()}
        if len(silos) != len(ordered_ids):
            raise ValueError("Silo de origen o destino no encontrado")
        return silos

    async def _require_active_food(self, food_id: UUID) -> FoodModel:
        food = await self.session.get(FoodModel, food_id)
        if not food:
            raise ValueError("Alimento no encontrado")
        if not food.active:
            raise ValueError("No se puede asignar un alimento inactivo")
        return food

    async def _batch_model(
        self, silo_id: UUID, batch_id: UUID, *, lock: bool = False
    ) -> SiloInventoryBatchModel:
        query = select(SiloInventoryBatchModel).where(
            col(SiloInventoryBatchModel.id) == batch_id,
            col(SiloInventoryBatchModel.silo_id) == silo_id,
        )
        if lock:
            query = query.with_for_update()
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError("Partida no encontrada en el silo")
        return model

    async def _active_models(
        self, silo_id: UUID, *, lock: bool = False, identified_only: bool = False
    ) -> list[SiloInventoryBatchModel]:
        query = (
            select(SiloInventoryBatchModel)
            .where(
                col(SiloInventoryBatchModel.silo_id) == silo_id,
                col(SiloInventoryBatchModel.status) == SiloInventoryBatchStatus.ACTIVE.value,
                col(SiloInventoryBatchModel.remaining_quantity_mg) > 0,
            )
            .order_by(col(SiloInventoryBatchModel.position), col(SiloInventoryBatchModel.received_at))
        )
        if identified_only:
            query = query.where(col(SiloInventoryBatchModel.food_id).is_not(None))
        if lock:
            query = query.with_for_update()
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _reserved_for_batch(self, batch_id: UUID) -> int:
        result = await self.session.execute(
            select(
                func.coalesce(
                    func.sum(
                        col(SiloStockReservationModel.reserved_quantity_mg)
                        - col(SiloStockReservationModel.consumed_quantity_mg)
                    ),
                    0,
                )
            ).where(
                col(SiloStockReservationModel.batch_id) == batch_id,
                col(SiloStockReservationModel.status) == SiloStockReservationStatus.ACTIVE.value,
            )
        )
        return int(result.scalar_one())

    async def _normalize_positions(self, silo_id: UUID) -> None:
        active = await self._active_models(silo_id, lock=True)
        for position, batch in enumerate(active, start=1):
            batch.position = position

    @staticmethod
    def _resolve_insert_index(
        batches: list[SiloInventoryBatchModel],
        before_batch_id: Optional[UUID],
        after_batch_id: Optional[UUID],
    ) -> int:
        if before_batch_id:
            for index, batch in enumerate(batches):
                if batch.id == before_batch_id:
                    return index
            raise ValueError("La partida indicada en before_batch_id no pertenece a la cola activa")
        if after_batch_id:
            for index, batch in enumerate(batches):
                if batch.id == after_batch_id:
                    return index + 1
            raise ValueError("La partida indicada en after_batch_id no pertenece a la cola activa")
        return len(batches)

    def _add_movement(
        self,
        batch: SiloInventoryBatchModel,
        movement_type: SiloInventoryMovementType,
        operator_id: str,
        *,
        reason: Optional[str] = None,
        previous_quantity_mg: int,
        new_quantity_mg: int,
        previous_food_id: Optional[UUID] = None,
        new_food_id: Optional[UUID] = None,
        previous_position: Optional[int] = None,
        new_position: Optional[int] = None,
        feeding_session_id: Optional[str] = None,
        cage_feeding_id: Optional[str] = None,
    ) -> None:
        self.session.add(
            SiloInventoryMovementModel(
                silo_id=batch.silo_id,
                batch_id=batch.id,
                movement_type=movement_type.value,
                operator_id=operator_id,
                reason=reason,
                quantity_delta_mg=new_quantity_mg - previous_quantity_mg,
                previous_quantity_mg=previous_quantity_mg,
                new_quantity_mg=new_quantity_mg,
                previous_food_id=previous_food_id,
                new_food_id=new_food_id,
                previous_position=previous_position,
                new_position=new_position,
                feeding_session_id=feeding_session_id,
                cage_feeding_id=cage_feeding_id,
            )
        )

    @staticmethod
    def _to_domain(
        model: SiloInventoryBatchModel,
        reserved_mg: int,
        food_name: Optional[str],
        food_code: Optional[str],
        food_provider: Optional[str],
    ) -> SiloInventoryBatch:
        return SiloInventoryBatch(
            id=model.id,
            silo_id=model.silo_id,
            food_id=model.food_id,
            remaining_quantity_mg=model.remaining_quantity_mg,
            reserved_quantity_mg=reserved_mg,
            position=model.position,
            status=SiloInventoryBatchStatus(model.status),
            received_at=model.received_at,
            created_by_operator_id=model.created_by_operator_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            food_name=food_name,
            food_code=food_code,
            food_provider=food_provider,
        )
