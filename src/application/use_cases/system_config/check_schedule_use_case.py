
from datetime import datetime, timezone

from api.models.system_config_models import ScheduleCheckRequest, ScheduleCheckResponse
from domain.repositories import ICageRepository, IFeedingLineRepository, ISystemConfigRepository
from domain.services.feeding_time_calculator import calculate_visit_duration
from domain.services.operating_schedule_service import OperatingScheduleService
from domain.value_objects import CageId, LineId


class CheckScheduleUseCase:

    def __init__(
        self,
        config_repository: ISystemConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
    ) -> None:
        self._config_repo = config_repository
        self._line_repo = line_repository
        self._cage_repo = cage_repository

    async def execute(self, request: ScheduleCheckRequest) -> ScheduleCheckResponse:
        line = await self._line_repo.find_by_id(LineId.from_string(request.line_id))
        if not line:
            raise ValueError(f"Línea con ID {request.line_id} no encontrada")

        if not line.blower:
            raise ValueError(f"La línea {request.line_id} no tiene blower configurado")

        cage = await self._cage_repo.find_by_id(CageId.from_string(request.cage_id))
        if not cage:
            raise ValueError(f"Jaula con ID {request.cage_id} no encontrada")

        if cage.config.transport_time_seconds is None:
            raise ValueError(
                f"La jaula {cage.name.value} no tiene tiempo de transporte configurado"
            )

        estimated_seconds = calculate_visit_duration(
            quantity_kg=request.quantity_kg,
            rate_kg_per_min=request.rate_kg_per_min,
            transport_time_seconds=cage.config.transport_time_seconds,
            blower=line.blower,
        )

        config = await self._config_repo.get()
        now_utc = datetime.now(timezone.utc)
        remaining_seconds = config.seconds_remaining_in_window(now_utc)
        fits = OperatingScheduleService(config).fits_in_window(estimated_seconds, now_utc)

        return ScheduleCheckResponse(
            fits=fits,
            estimated_seconds=estimated_seconds,
            estimated_minutes=round(estimated_seconds / 60, 2),
            remaining_seconds=remaining_seconds,
            remaining_minutes=round(remaining_seconds / 60, 2),
        )
