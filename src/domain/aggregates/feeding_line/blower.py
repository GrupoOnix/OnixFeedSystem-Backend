from datetime import datetime

from domain.interfaces import IBlower
from domain.value_objects import (
    BlowDurationInSeconds,
    BlowerId,
    BlowerName,
    BlowerPowerPercentage,
)


class Blower(IBlower):
    def __init__(
        self,
        name: BlowerName,
        non_feeding_power: BlowerPowerPercentage,
        blow_before_time: BlowDurationInSeconds,
        blow_after_time: BlowDurationInSeconds,
        current_power: BlowerPowerPercentage | None = None,
    ):
        self._id = BlowerId.generate()
        self._name = name
        self._non_feeding_power = non_feeding_power
        self._current_power = current_power or non_feeding_power
        self._blow_before_feeding_time = blow_before_time
        self._blow_after_feeding_time = blow_after_time
        self._created_at = datetime.utcnow()

    @property
    def id(self) -> BlowerId:
        return self._id

    @property
    def name(self) -> BlowerName:
        return self._name

    @name.setter
    def name(self, name: BlowerName) -> None:
        self._name = name

    @property
    def non_feeding_power(self) -> BlowerPowerPercentage:
        return self._non_feeding_power

    @non_feeding_power.setter
    def non_feeding_power(self, power: BlowerPowerPercentage) -> None:
        self._non_feeding_power = power

    @property
    def current_power(self) -> BlowerPowerPercentage:
        return self._current_power

    @current_power.setter
    def current_power(self, power: BlowerPowerPercentage) -> None:
        self._current_power = power

    @property
    def blow_before_feeding_time(self) -> BlowDurationInSeconds:
        return self._blow_before_feeding_time

    @blow_before_feeding_time.setter
    def blow_before_feeding_time(self, time: BlowDurationInSeconds) -> None:
        self._blow_before_feeding_time = time

    @property
    def blow_after_feeding_time(self) -> BlowDurationInSeconds:
        return self._blow_after_feeding_time

    @blow_after_feeding_time.setter
    def blow_after_feeding_time(self, time: BlowDurationInSeconds) -> None:
        self._blow_after_feeding_time = time

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def validate_power_is_safe(self, power_to_check: BlowerPowerPercentage) -> bool:
        if not isinstance(power_to_check, BlowerPowerPercentage):
            return False
        return True
