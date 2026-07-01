from typing import Optional
from uuid import UUID

from application.dtos.silo_dtos import SiloInventoryBatchDTO
from application.dtos.silo_inventory_dtos import (
    CreateSiloBatchRequest,
    ListSiloBatchesResponse,
    MoveSiloBatchRequest,
    TransferSiloStockRequest,
    TransferSiloStockResponse,
    UpdateSiloBatchRequest,
    WithdrawSiloBatchRequest,
)
from application.mappers.silo_inventory_mapper import to_batch_dto
from domain.entities.silo_inventory import SiloInventoryBatchStatus
from infrastructure.persistence.repositories.silo_inventory_repository import (
    SiloInventoryRepository,
)


class CreateSiloBatchUseCase:
    def __init__(self, inventory_repository: SiloInventoryRepository):
        self._repository = inventory_repository

    async def execute(self, silo_id: str, request: CreateSiloBatchRequest) -> SiloInventoryBatchDTO:
        batch = await self._repository.create_batch(
            UUID(silo_id),
            UUID(request.food_id),
            request.quantity_kg,
            request.operator_id,
            before_batch_id=UUID(request.before_batch_id) if request.before_batch_id else None,
            after_batch_id=UUID(request.after_batch_id) if request.after_batch_id else None,
            reason=request.reason,
        )
        return to_batch_dto(batch)


class UpdateSiloBatchUseCase:
    def __init__(self, inventory_repository: SiloInventoryRepository):
        self._repository = inventory_repository

    async def execute(
        self, silo_id: str, batch_id: str, request: UpdateSiloBatchRequest
    ) -> SiloInventoryBatchDTO:
        batch = await self._repository.update_batch(
            UUID(silo_id),
            UUID(batch_id),
            request.operator_id,
            food_id=UUID(request.food_id) if request.food_id else None,
            remaining_quantity_kg=request.remaining_quantity_kg,
            reason=request.reason,
        )
        return to_batch_dto(batch)


class MoveSiloBatchUseCase:
    def __init__(self, inventory_repository: SiloInventoryRepository):
        self._repository = inventory_repository

    async def execute(
        self, silo_id: str, batch_id: str, request: MoveSiloBatchRequest
    ) -> SiloInventoryBatchDTO:
        batch = await self._repository.move_batch(
            UUID(silo_id),
            UUID(batch_id),
            request.operator_id,
            before_batch_id=UUID(request.before_batch_id) if request.before_batch_id else None,
            after_batch_id=UUID(request.after_batch_id) if request.after_batch_id else None,
            reason=request.reason,
        )
        return to_batch_dto(batch)


class WithdrawSiloBatchUseCase:
    def __init__(self, inventory_repository: SiloInventoryRepository):
        self._repository = inventory_repository

    async def execute(
        self, silo_id: str, batch_id: str, request: WithdrawSiloBatchRequest
    ) -> SiloInventoryBatchDTO:
        batch = await self._repository.withdraw_batch(
            UUID(silo_id),
            UUID(batch_id),
            request.operator_id,
            reason=request.reason,
        )
        return to_batch_dto(batch)


class TransferSiloStockUseCase:
    def __init__(self, inventory_repository: SiloInventoryRepository):
        self._repository = inventory_repository

    async def execute(
        self,
        source_silo_id: str,
        request: TransferSiloStockRequest,
    ) -> TransferSiloStockResponse:
        transferred_batches = await self._repository.transfer_stock(
            UUID(source_silo_id),
            UUID(request.destination_silo_id),
            request.quantity_kg,
            request.operator_id,
            reason=request.reason,
        )
        return TransferSiloStockResponse(
            source_silo_id=source_silo_id,
            destination_silo_id=request.destination_silo_id,
            quantity_kg=request.quantity_kg,
            transferred_batches=[to_batch_dto(batch) for batch in transferred_batches],
        )


class ListSiloBatchesUseCase:
    def __init__(self, inventory_repository: SiloInventoryRepository):
        self._repository = inventory_repository

    async def execute(
        self,
        silo_id: str,
        status: Optional[str],
        offset: int,
        limit: int,
    ) -> ListSiloBatchesResponse:
        statuses = [SiloInventoryBatchStatus(status)] if status else None
        batches = await self._repository.list_batches(
            UUID(silo_id),
            statuses=statuses,
            offset=offset,
            limit=limit,
        )
        return ListSiloBatchesResponse(
            batches=[to_batch_dto(batch) for batch in batches],
            offset=offset,
            limit=limit,
        )
