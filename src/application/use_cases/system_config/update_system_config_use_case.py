"""Caso de uso: actualizar configuración del sistema."""

from datetime import time

from api.models.system_config_models import SystemConfigResponse, UpdateSystemConfigRequest
from domain.repositories import ISystemConfigRepository


class UpdateSystemConfigUseCase:

    def __init__(self, config_repository: ISystemConfigRepository) -> None:
        self._repo = config_repository

    async def execute(self, request: UpdateSystemConfigRequest) -> SystemConfigResponse:
        config = await self._repo.get()

        start_h, start_m = map(int, request.feeding_start_time.split(":"))
        end_h, end_m = map(int, request.feeding_end_time.split(":"))

        config.update(
            feeding_start_time=time(start_h, start_m),
            feeding_end_time=time(end_h, end_m),
            timezone_id=request.timezone_id,
        )

        await self._repo.save(config)

        return SystemConfigResponse(
            feeding_start_time=config.feeding_start_time.strftime("%H:%M"),
            feeding_end_time=config.feeding_end_time.strftime("%H:%M"),
            timezone_id=config.timezone_id,
        )
