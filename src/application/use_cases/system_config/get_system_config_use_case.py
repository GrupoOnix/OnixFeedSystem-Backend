"""Caso de uso: obtener configuración del sistema."""

from api.models.system_config_models import SystemConfigResponse
from domain.repositories import ISystemConfigRepository


class GetSystemConfigUseCase:

    def __init__(self, config_repository: ISystemConfigRepository) -> None:
        self._repo = config_repository

    async def execute(self) -> SystemConfigResponse:
        config = await self._repo.get()
        return SystemConfigResponse(
            feeding_start_time=config.feeding_start_time.strftime("%H:%M"),
            feeding_end_time=config.feeding_end_time.strftime("%H:%M"),
            timezone_id=config.timezone_id,
        )
