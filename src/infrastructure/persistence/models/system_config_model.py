from datetime import time

from sqlmodel import Field, SQLModel

from domain.aggregates.system_config import SystemConfig


class SystemConfigModel(SQLModel, table=True):
    """
    Registro singleton que almacena la configuración operativa global.
    Siempre existe un único registro con id=1.
    """

    __tablename__ = "system_config"

    id: int = Field(default=1, primary_key=True)
    feeding_start_time: time = Field(nullable=False)
    feeding_end_time: time = Field(nullable=False)
    timezone_id: str = Field(max_length=64, nullable=False)
    selector_positioning_time_seconds: int = Field(default=10, nullable=False)
    doser_calibration_tolerance_percentage: float = Field(default=5.0, nullable=False)
    doser_calibration_max_pulses: int = Field(default=10, nullable=False)
    doser_calibration_max_attempt_seconds: int = Field(default=20, nullable=False)
    temperature_warning_threshold: float = Field(default=70.0, nullable=False)
    temperature_critical_threshold: float = Field(default=85.0, nullable=False)
    pressure_warning_threshold: float = Field(default=1.3, nullable=False)
    pressure_critical_threshold: float = Field(default=1.5, nullable=False)
    flow_warning_threshold: float = Field(default=18.0, nullable=False)
    flow_critical_threshold: float = Field(default=22.0, nullable=False)
    dosing_rate_unit: str = Field(default="kg/min", max_length=10, nullable=False)

    @staticmethod
    def from_domain(config: SystemConfig) -> "SystemConfigModel":
        return SystemConfigModel(
            id=config.id,
            feeding_start_time=config.feeding_start_time,
            feeding_end_time=config.feeding_end_time,
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

    def to_domain(self) -> SystemConfig:
        return SystemConfig(
            feeding_start_time=self.feeding_start_time,
            feeding_end_time=self.feeding_end_time,
            timezone_id=self.timezone_id,
            selector_positioning_time_seconds=self.selector_positioning_time_seconds,
            doser_calibration_tolerance_percentage=self.doser_calibration_tolerance_percentage,
            doser_calibration_max_pulses=self.doser_calibration_max_pulses,
            doser_calibration_max_attempt_seconds=self.doser_calibration_max_attempt_seconds,
            temperature_warning_threshold=self.temperature_warning_threshold,
            temperature_critical_threshold=self.temperature_critical_threshold,
            pressure_warning_threshold=self.pressure_warning_threshold,
            pressure_critical_threshold=self.pressure_critical_threshold,
            flow_warning_threshold=self.flow_warning_threshold,
            flow_critical_threshold=self.flow_critical_threshold,
            dosing_rate_unit=self.dosing_rate_unit,
        )
