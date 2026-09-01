from datetime import datetime, time
from zoneinfo import ZoneInfo


class SystemConfig:
    _SINGLETON_ID: int = 1

    _DEFAULT_SELECTOR_POSITIONING_TIME: int = 10
    _DEFAULT_CALIBRATION_TOLERANCE: float = 5.0
    _DEFAULT_CALIBRATION_MAX_PULSES: int = 10
    _DEFAULT_CALIBRATION_MAX_SECONDS: int = 20
    _DEFAULT_TEMPERATURE_WARNING_THRESHOLD: float = 70.0
    _DEFAULT_TEMPERATURE_CRITICAL_THRESHOLD: float = 85.0
    _DEFAULT_PRESSURE_WARNING_THRESHOLD: float = 1.3
    _DEFAULT_PRESSURE_CRITICAL_THRESHOLD: float = 1.5
    _DEFAULT_FLOW_WARNING_THRESHOLD: float = 18.0
    _DEFAULT_FLOW_CRITICAL_THRESHOLD: float = 22.0
    _DEFAULT_DOSING_RATE_UNIT: str = "kg/min"

    def __init__(
        self,
        feeding_start_time: time,
        feeding_end_time: time,
        timezone_id: str,
        selector_positioning_time_seconds: int | None = None,
        doser_calibration_tolerance_percentage: float | None = None,
        doser_calibration_max_pulses: int | None = None,
        doser_calibration_max_attempt_seconds: int | None = None,
        temperature_warning_threshold: float | None = None,
        temperature_critical_threshold: float | None = None,
        pressure_warning_threshold: float | None = None,
        pressure_critical_threshold: float | None = None,
        flow_warning_threshold: float | None = None,
        flow_critical_threshold: float | None = None,
        dosing_rate_unit: str | None = None,
    ) -> None:
        self._id = self._SINGLETON_ID
        self._feeding_start_time = feeding_start_time
        self._feeding_end_time = feeding_end_time
        self._timezone_id = timezone_id
        self._selector_positioning_time_seconds = (
            selector_positioning_time_seconds
            if selector_positioning_time_seconds is not None
            else self._DEFAULT_SELECTOR_POSITIONING_TIME
        )
        self._doser_calibration_tolerance_percentage = (
            doser_calibration_tolerance_percentage or self._DEFAULT_CALIBRATION_TOLERANCE
        )
        self._doser_calibration_max_pulses = doser_calibration_max_pulses or self._DEFAULT_CALIBRATION_MAX_PULSES
        self._doser_calibration_max_attempt_seconds = (
            doser_calibration_max_attempt_seconds or self._DEFAULT_CALIBRATION_MAX_SECONDS
        )
        self._temperature_warning_threshold = (
            temperature_warning_threshold
            if temperature_warning_threshold is not None
            else self._DEFAULT_TEMPERATURE_WARNING_THRESHOLD
        )
        self._temperature_critical_threshold = (
            temperature_critical_threshold
            if temperature_critical_threshold is not None
            else self._DEFAULT_TEMPERATURE_CRITICAL_THRESHOLD
        )
        self._pressure_warning_threshold = (
            pressure_warning_threshold
            if pressure_warning_threshold is not None
            else self._DEFAULT_PRESSURE_WARNING_THRESHOLD
        )
        self._pressure_critical_threshold = (
            pressure_critical_threshold
            if pressure_critical_threshold is not None
            else self._DEFAULT_PRESSURE_CRITICAL_THRESHOLD
        )
        self._flow_warning_threshold = (
            flow_warning_threshold if flow_warning_threshold is not None else self._DEFAULT_FLOW_WARNING_THRESHOLD
        )
        self._flow_critical_threshold = (
            flow_critical_threshold if flow_critical_threshold is not None else self._DEFAULT_FLOW_CRITICAL_THRESHOLD
        )
        self._dosing_rate_unit = dosing_rate_unit or self._DEFAULT_DOSING_RATE_UNIT

    @property
    def id(self) -> int:
        return self._id

    @property
    def feeding_start_time(self) -> time:
        return self._feeding_start_time

    @property
    def feeding_end_time(self) -> time:
        return self._feeding_end_time

    @property
    def timezone_id(self) -> str:
        return self._timezone_id

    @property
    def selector_positioning_time_seconds(self) -> int:
        return self._selector_positioning_time_seconds

    @property
    def doser_calibration_tolerance_percentage(self) -> float:
        return self._doser_calibration_tolerance_percentage

    @property
    def doser_calibration_max_pulses(self) -> int:
        return self._doser_calibration_max_pulses

    @property
    def doser_calibration_max_attempt_seconds(self) -> int:
        return self._doser_calibration_max_attempt_seconds

    @property
    def temperature_warning_threshold(self) -> float:
        return self._temperature_warning_threshold

    @property
    def temperature_critical_threshold(self) -> float:
        return self._temperature_critical_threshold

    @property
    def pressure_warning_threshold(self) -> float:
        return self._pressure_warning_threshold

    @property
    def pressure_critical_threshold(self) -> float:
        return self._pressure_critical_threshold

    @property
    def flow_warning_threshold(self) -> float:
        return self._flow_warning_threshold

    @property
    def flow_critical_threshold(self) -> float:
        return self._flow_critical_threshold

    @property
    def dosing_rate_unit(self) -> str:
        return self._dosing_rate_unit

    def seconds_remaining_in_window(self, now_utc: datetime) -> float:
        """
        Calcula los segundos que quedan dentro del horario operativo
        a partir de un instante UTC dado.

        Si now_utc está fuera del horario operativo (antes del inicio o
        después del fin), retorna 0.0.

        Args:
            now_utc: Instante actual en UTC (timezone-aware).

        Returns:
            Segundos restantes hasta feeding_end_time en la zona local.
        """
        tz = ZoneInfo(self._timezone_id)
        now_local = now_utc.astimezone(tz)
        today = now_local.date()

        window_end = datetime.combine(today, self._feeding_end_time, tzinfo=tz)
        window_start = datetime.combine(today, self._feeding_start_time, tzinfo=tz)

        if now_local < window_start or now_local >= window_end:
            return 0.0

        return (window_end - now_local).total_seconds()

    def is_within_window(self, now_utc: datetime) -> bool:
        """Retorna True si now_utc cae dentro del horario operativo."""
        return self.seconds_remaining_in_window(now_utc) > 0.0

    def update(
        self,
        feeding_start_time: time,
        feeding_end_time: time,
        timezone_id: str,
        selector_positioning_time_seconds: int | None = None,
        doser_calibration_tolerance_percentage: float | None = None,
        doser_calibration_max_pulses: int | None = None,
        doser_calibration_max_attempt_seconds: int | None = None,
        temperature_warning_threshold: float | None = None,
        temperature_critical_threshold: float | None = None,
        pressure_warning_threshold: float | None = None,
        pressure_critical_threshold: float | None = None,
        flow_warning_threshold: float | None = None,
        flow_critical_threshold: float | None = None,
        dosing_rate_unit: str | None = None,
    ) -> None:
        if feeding_end_time <= feeding_start_time:
            raise ValueError("feeding_end_time debe ser posterior a feeding_start_time")
        if selector_positioning_time_seconds is not None:
            if not (1 <= selector_positioning_time_seconds <= 60):
                raise ValueError("selector_positioning_time_seconds debe estar entre 1 y 60")
            self._selector_positioning_time_seconds = selector_positioning_time_seconds
        self._feeding_start_time = feeding_start_time
        self._feeding_end_time = feeding_end_time
        self._timezone_id = timezone_id
        if doser_calibration_tolerance_percentage is not None:
            self._doser_calibration_tolerance_percentage = doser_calibration_tolerance_percentage
        if doser_calibration_max_pulses is not None:
            self._doser_calibration_max_pulses = doser_calibration_max_pulses
        if doser_calibration_max_attempt_seconds is not None:
            self._doser_calibration_max_attempt_seconds = doser_calibration_max_attempt_seconds
        threshold_updates = (
            ("temperature", temperature_warning_threshold, temperature_critical_threshold),
            ("pressure", pressure_warning_threshold, pressure_critical_threshold),
            ("flow", flow_warning_threshold, flow_critical_threshold),
        )
        for name, warning, critical in threshold_updates:
            current_warning = getattr(self, f"_{name}_warning_threshold")
            current_critical = getattr(self, f"_{name}_critical_threshold")
            new_warning = warning if warning is not None else current_warning
            new_critical = critical if critical is not None else current_critical
            if new_critical <= new_warning:
                labels = {"temperature": "temperatura", "pressure": "presión", "flow": "flujo"}
                raise ValueError(f"El umbral crítico de {labels[name]} debe ser mayor que el de advertencia")
            setattr(self, f"_{name}_warning_threshold", new_warning)
            setattr(self, f"_{name}_critical_threshold", new_critical)
        if dosing_rate_unit is not None:
            if dosing_rate_unit not in {"kg/min", "g/s"}:
                raise ValueError("dosing_rate_unit no es una unidad válida")
            self._dosing_rate_unit = dosing_rate_unit

    @classmethod
    def create_default(cls) -> "SystemConfig":
        """Crea una configuración por defecto: 06:00–18:00 America/Santiago."""
        return cls(
            feeding_start_time=time(6, 0),
            feeding_end_time=time(18, 0),
            timezone_id="America/Santiago",
            selector_positioning_time_seconds=cls._DEFAULT_SELECTOR_POSITIONING_TIME,
        )
