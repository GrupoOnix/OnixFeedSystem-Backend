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
            selector_positioning_time_seconds=config.selector_positioning_time_seconds,
            doser_calibration_tolerance_percentage=config.doser_calibration_tolerance_percentage,
            doser_calibration_max_pulses=config.doser_calibration_max_pulses,
            doser_calibration_max_attempt_seconds=config.doser_calibration_max_attempt_seconds,
            temperature_warning_threshold=config.temperature_warning_threshold,
            temperature_critical_threshold=config.temperature_critical_threshold,
            pressure_warning_threshold=config.pressure_warning_threshold,
            pressure_critical_threshold=config.pressure_critical_threshold,
            flow_warning_threshold=config.flow_warning_threshold,
            flow_critical_threshold=config.flow_critical_threshold,
            dosing_rate_unit=config.dosing_rate_unit,
        )
