"""Repositorio para operaciones de Doser."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.aggregates.feeding_line.doser import Doser
from infrastructure.persistence.models.doser_calibration_model import DoserCalibrationModel
from infrastructure.persistence.models.doser_model import DoserModel
from infrastructure.persistence.models.doser_silo_model import DoserSiloModel


@dataclass
class DoserWithContext:
    """Doser con información de contexto de su línea."""

    doser: Doser
    line_id: UUID
    line_name: str
    line_status: str


class DoserRepository:
    """Repositorio para acceso directo a dosers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, doser_id: UUID) -> Optional[Doser]:
        """Busca un doser por su ID."""
        stmt = (
            select(DoserModel)
            .options(selectinload(DoserModel.silos))
            .where(DoserModel.id == doser_id)
        )
        result = await self.session.execute(stmt)
        doser_model = result.scalar_one_or_none()
        return doser_model.to_domain() if doser_model else None

    async def find_by_id_with_context(self, doser_id: UUID) -> Optional[DoserWithContext]:
        """Busca un doser por su ID y devuelve también información de la línea."""
        stmt = (
            select(DoserModel)
            .options(
                selectinload(DoserModel.feeding_line),
                selectinload(DoserModel.silos),
            )
            .where(DoserModel.id == doser_id)
        )
        result = await self.session.execute(stmt)
        doser_model = result.scalar_one_or_none()

        if not doser_model:
            return None

        return DoserWithContext(
            doser=doser_model.to_domain(),
            line_id=doser_model.line_id,
            line_name=doser_model.feeding_line.name,
            line_status=doser_model.feeding_line.status,
        )

    async def update(self, doser_id: UUID, doser: Doser) -> None:
        """Actualiza un doser existente."""
        stmt = select(DoserModel).where(DoserModel.id == doser_id)
        result = await self.session.execute(stmt)
        doser_model = result.scalar_one_or_none()

        if not doser_model:
            raise ValueError(f"Doser {doser_id} no encontrado")

        # Actualizar campos
        doser_model.name = str(doser.name)
        doser_model.silo_id = None
        doser_model.doser_type = doser.doser_type.value
        doser_model.dosing_rate_value = doser.current_rate.value
        doser_model.dosing_rate_unit = doser.current_rate.unit
        doser_model.min_rate_value = doser.dosing_range.min_rate
        doser_model.max_rate_value = doser.dosing_range.max_rate
        doser_model.rate_unit = doser.dosing_range.unit
        doser_model.is_on = doser.is_on
        doser_model.speed_percentage = doser.speed_percentage
        doser_model.calibrated_grams_per_second = doser.calibrated_grams_per_second
        doser_model.pulse_on_time = doser.pulse_on_time
        doser_model.pulse_off_time = doser.pulse_off_time
        doser_model.pulse_speed = doser.pulse_speed

        await self.session.execute(
            delete(DoserSiloModel).where(DoserSiloModel.doser_id == doser_id)
        )
        for silo_id in doser.assigned_silo_ids:
            self.session.add(DoserSiloModel(doser_id=doser_id, silo_id=silo_id.value))

        await self.session.flush()

    async def update_calibration(
        self,
        doser_id: UUID,
        calibration: DoserCalibrationModel,
    ) -> DoserCalibrationModel:
        """Guarda una calibración y actualiza el valor actual del doser."""
        stmt = select(DoserModel).where(DoserModel.id == doser_id)
        result = await self.session.execute(stmt)
        doser_model = result.scalar_one_or_none()

        if not doser_model:
            raise ValueError(f"Doser {doser_id} no encontrado")

        doser_model.calibrated_grams_per_second = calibration.grams_per_second

        self.session.add(calibration)
        await self.session.flush()
        await self.session.refresh(calibration)
        return calibration

    async def list_calibration_history(self, doser_id: UUID) -> List[DoserCalibrationModel]:
        """Lista historial de calibraciones, más reciente primero."""
        stmt = (
            select(DoserCalibrationModel)
            .where(DoserCalibrationModel.doser_id == doser_id)
            .order_by(desc(DoserCalibrationModel.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
