from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.feeding_line_dtos import (
    BlowerDTO,
    DoserDTO,
    FeedingLineDTO,
    SelectorDTO,
    SensorDTO,
)
from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import LineId
from infrastructure.persistence.models import CageModel


class GetFeedingLineUseCase:
    """Caso de uso para obtener una línea de alimentación específica."""

    def __init__(
        self, feeding_line_repository: IFeedingLineRepository, session: AsyncSession
    ):
        self._feeding_line_repository = feeding_line_repository
        self._session = session

    async def execute(self, line_id: str) -> FeedingLineDTO:
        """
        Ejecuta el caso de uso para obtener una línea de alimentación.

        Args:
            line_id: ID de la línea a obtener

        Returns:
            FeedingLineDTO con los detalles de la línea

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
        """
        # Obtener línea
        feeding_line = await self._feeding_line_repository.find_by_id(LineId(line_id))

        if not feeding_line:
            raise FeedingLineNotFoundException(
                f"Línea de alimentación con ID {line_id} no encontrada"
            )

        # Obtener conteo de jaulas para esta línea
        cage_count = await self._get_cage_count_by_line(line_id)

        # Convertir a DTO
        return self._to_dto(feeding_line, cage_count)

    async def _get_cage_count_by_line(self, line_id: str) -> int:
        """Obtiene el conteo de jaulas para una línea específica."""
        stmt = select(func.count(CageModel.id)).where(
            CageModel.line_id == LineId(line_id).value
        )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    def _to_dto(self, line, total_cages: int) -> FeedingLineDTO:
        """Convierte un agregado FeedingLine a FeedingLineDTO."""
        # Convertir blower
        blower_dto = BlowerDTO(
            id=str(line.blower.id),
            name=str(line.blower.name),
            non_feeding_power=line.blower.non_feeding_power.value,
            current_power=line.blower.current_power.value,
            blow_before_feeding_time=line.blower.blow_before_feeding_time.value,
            blow_after_feeding_time=line.blower.blow_after_feeding_time.value,
        )

        # Convertir dosers
        doser_dtos = [
            DoserDTO(
                id=str(doser.id),
                name=str(doser.name),
                doser_type=doser.doser_type.value,
                current_rate=doser.current_rate.value,
                dosing_range_min=doser.dosing_range.min_rate,
                dosing_range_max=doser.dosing_range.max_rate,
                speed_percentage=doser.speed_percentage,
                silo_id=str(doser.assigned_silo_id),
                silo_name=None,  # Se puede agregar join si es necesario
            )
            for doser in line.dosers
        ]

        # Convertir selector
        selector_dto = SelectorDTO(
            id=str(line.selector.id),
            name=str(line.selector.name),
            capacity=line.selector.capacity.value,
            fast_speed=line.selector.speed_profile.fast_speed.value,
            slow_speed=line.selector.speed_profile.slow_speed.value,
            current_slot=line.selector.current_slot,
        )

        # Convertir sensors
        sensor_dtos = [
            SensorDTO(
                id=str(sensor.id),
                name=str(sensor.name),
                sensor_type=sensor.sensor_type.value,
            )
            for sensor in line._sensors
        ]

        return FeedingLineDTO(
            id=str(line.id),
            name=str(line.name),
            created_at=line._created_at,
            blower=blower_dto,
            dosers=doser_dtos,
            selector=selector_dto,
            sensors=sensor_dtos,
            total_cages=total_cages,
        )
