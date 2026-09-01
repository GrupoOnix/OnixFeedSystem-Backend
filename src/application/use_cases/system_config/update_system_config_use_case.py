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
            selector_positioning_time_seconds=request.selector_positioning_time_seconds,
            doser_calibration_tolerance_percentage=request.doser_calibration_tolerance_percentage,
            doser_calibration_max_pulses=request.doser_calibration_max_pulses,
            doser_calibration_max_attempt_seconds=request.doser_calibration_max_attempt_seconds,
            temperature_warning_threshold=request.temperature_warning_threshold,
            temperature_critical_threshold=request.temperature_critical_threshold,
            pressure_warning_threshold=request.pressure_warning_threshold,
            pressure_critical_threshold=request.pressure_critical_threshold,
            flow_warning_threshold=request.flow_warning_threshold,
            flow_critical_threshold=request.flow_critical_threshold,
            dosing_rate_unit=request.dosing_rate_unit,
        )

        await self._repo.save(config)

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
