from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.feeding_line_dtos import (
    BlowerDTO,
    DoserDTO,
    FeedingLineDTO,
    ListFeedingLinesResponse,
    SelectorDTO,
    SensorDTO,
)
from domain.repositories import IFeedingLineRepository
from infrastructure.persistence.models import CageModel


class ListFeedingLinesUseCase:
    """Caso de uso para listar todas las líneas de alimentación."""

    def __init__(
        self, feeding_line_repository: IFeedingLineRepository, session: AsyncSession
    ):
        self._feeding_line_repository = feeding_line_repository
        self._session = session

    async def execute(self) -> ListFeedingLinesResponse:
        """
        Ejecuta el caso de uso para listar todas las líneas de alimentación.

        Returns:
            ListFeedingLinesResponse con la lista de líneas y sus componentes
        """
        # Obtener todas las líneas
        feeding_lines = await self._feeding_line_repository.get_all()

        # Obtener conteos de jaulas por línea
        cage_counts = await self._get_cage_counts_by_line()

        # Convertir a DTOs
        line_dtos = [
            self._to_dto(line, cage_counts.get(str(line.id.value), 0))
            for line in feeding_lines
        ]

        return ListFeedingLinesResponse(feeding_lines=line_dtos)

    async def _get_cage_counts_by_line(self) -> dict[str, int]:
        """Obtiene el conteo de jaulas por línea."""
        stmt = (
            select(CageModel.line_id, func.count(CageModel.id))
            .where(CageModel.line_id.is_not(None))
            .group_by(CageModel.line_id)
        )

        result = await self._session.execute(stmt)
        return {str(line_id): count for line_id, count in result.all()}

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
