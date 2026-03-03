"""Caso de uso: actualizar configuración del sistema."""

from datetime import time

from api.models.system_config_models import SystemConfigResponse, UpdateSystemConfigRequest
from domain.repositories import ISystemConfigRepository
from domain.value_objects.identifiers import UserId


class UpdateSystemConfigUseCase:
    def __init__(self, config_repository: ISystemConfigRepository) -> None:
        self._repo = config_repository

    async def execute(self, request: UpdateSystemConfigRequest, user_id: UserId) -> SystemConfigResponse:
        config = await self._repo.get(user_id)

        start_h, start_m = map(int, request.feeding_start_time.split(":"))
        end_h, end_m = map(int, request.feeding_end_time.split(":"))

        config.update(
            feeding_start_time=time(start_h, start_m),
            feeding_end_time=time(end_h, end_m),
            timezone_id=request.timezone_id,
            selector_positioning_time_seconds=request.selector_positioning_time_seconds,
        )

        config._user_id = user_id
        await self._repo.save(config)

        return SystemConfigResponse(
            feeding_start_time=config.feeding_start_time.strftime("%H:%M"),
            feeding_end_time=config.feeding_end_time.strftime("%H:%M"),
            timezone_id=config.timezone_id,
            selector_positioning_time_seconds=config.selector_positioning_time_seconds,
        )
