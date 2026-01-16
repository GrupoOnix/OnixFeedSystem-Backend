from datetime import datetime
from typing import Optional

from domain.interfaces import ISelector
from domain.value_objects import (
    SelectorCapacity,
    SelectorId,
    SelectorName,
    SelectorSpeedProfile,
)


class Selector(ISelector):
    def __init__(
        self,
        name: SelectorName,
        capacity: SelectorCapacity,
        speed_profile: SelectorSpeedProfile,
        current_slot: Optional[int] = None,
    ):
        self._id = SelectorId.generate()
        self._name: SelectorName = name
        self._capacity = capacity
        self._speed_profile = speed_profile
        self._current_slot: Optional[int] = current_slot
        self._created_at = datetime.utcnow()  # TODO revisar que hacer con esto

    @property
    def id(self) -> SelectorId:
        return self._id

    @property
    def name(self) -> SelectorName:
        return self._name

    @name.setter
    def name(self, name: SelectorName) -> None:
        self._name = name

    @property
    def capacity(self) -> SelectorCapacity:
        return self._capacity

    @property
    def speed_profile(self) -> SelectorSpeedProfile:
        return self._speed_profile

    @speed_profile.setter
    def speed_profile(self, new_profile: SelectorSpeedProfile) -> None:
        self._speed_profile = new_profile

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def current_slot(self) -> Optional[int]:
        return self._current_slot

    @current_slot.setter
    def current_slot(self, slot: Optional[int]) -> None:
        if slot is not None:
            if not self.validate_slot(slot):
                raise ValueError(
                    f"Slot {slot} está fuera del rango válido (1-{self._capacity.value})"
                )
        self._current_slot = slot

    def validate_slot(self, slot_number: int) -> bool:
        return 1 <= slot_number <= self._capacity.value

    def move_to_slot(self, slot_number: int) -> None:
        """
        Mueve el selector a un slot específico.

        Args:
            slot_number: Número de slot destino (1 a capacity)

        Raises:
            ValueError: Si el slot está fuera del rango válido
        """
        if not self.validate_slot(slot_number):
            raise ValueError(
                f"No se puede mover a slot {slot_number}. "
                f"El slot debe estar entre 1 y {self._capacity.value}"
            )
        self._current_slot = slot_number

    def reset_position(self) -> None:
        """
        Reinicia la posición del selector a None (posición neutral/home).

        Esta operación típicamente se ejecuta:
        - Al finalizar una sesión de alimentación
        - En caso de error o emergencia
        - Al inicializar el sistema
        """
        self._current_slot = None
