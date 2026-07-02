from datetime import datetime, timezone
from typing import TYPE_CHECKING

from domain.value_objects import SiloId, SiloName, Weight

if TYPE_CHECKING:
    from domain.entities.silo_inventory import SiloInventoryBatch


class Silo:
    def __init__(
        self,
        name: SiloName,
        capacity: Weight,
        warning_threshold_percentage: float = 20.0,
        critical_threshold_percentage: float = 10.0,
    ):
        if warning_threshold_percentage <= critical_threshold_percentage:
            raise ValueError("El umbral de advertencia debe ser mayor que el umbral crítico.")

        if not (0 <= critical_threshold_percentage <= 100):
            raise ValueError("Los umbrales deben estar entre 0 y 100.")

        if not (0 <= warning_threshold_percentage <= 100):
            raise ValueError("Los umbrales deben estar entre 0 y 100.")

        self._id = SiloId.generate()
        self._name = name
        self._capacity = capacity
        self._is_assigned = False
        self._total_stock = Weight.zero()
        self._reserved_stock = Weight.zero()
        self._active_batches: list["SiloInventoryBatch"] = []
        self._warning_threshold_percentage = warning_threshold_percentage
        self._critical_threshold_percentage = critical_threshold_percentage
        self._created_at = datetime.now(timezone.utc)

    @property
    def id(self) -> SiloId:
        return self._id

    @property
    def name(self) -> SiloName:
        return self._name

    @name.setter
    def name(self, new_name: SiloName) -> None:
        self._name = new_name

    @property
    def capacity(self) -> Weight:
        return self._capacity

    @capacity.setter
    def capacity(self, new_capacity: Weight) -> None:
        """
        Actualiza la capacidad del silo.

        Regla de negocio: La nueva capacidad no puede ser menor al stock actual.
        """
        if new_capacity < self._total_stock:
            raise ValueError(
                f"La nueva capacidad ({new_capacity}) no puede ser menor al stock actual ({self._total_stock})"
            )
        self._capacity = new_capacity

    @property
    def total_stock(self) -> Weight:
        return self._total_stock

    @property
    def reserved_stock(self) -> Weight:
        return self._reserved_stock

    @property
    def available_stock(self) -> Weight:
        return self._total_stock - self._reserved_stock

    @property
    def fill_percentage(self) -> float:
        if self._capacity.as_miligrams == 0:
            return 0.0
        return self._total_stock.as_miligrams / self._capacity.as_miligrams * 100

    @property
    def active_batches(self) -> list["SiloInventoryBatch"]:
        return list(self._active_batches)

    def load_inventory(
        self,
        total_stock: Weight,
        reserved_stock: Weight,
        active_batches: list["SiloInventoryBatch"],
    ) -> None:
        if total_stock > self._capacity:
            raise ValueError("El stock total no puede superar la capacidad del silo")
        if reserved_stock > total_stock:
            raise ValueError("El stock reservado no puede superar el stock total")
        self._total_stock = total_stock
        self._reserved_stock = reserved_stock
        self._active_batches = list(active_batches)

    @property
    def is_assigned(self) -> bool:
        """Indica si el silo ya está asignado a un dosificador."""
        return self._is_assigned

    @property
    def created_at(self) -> datetime:
        """Fecha de creación del silo."""
        return self._created_at

    @property
    def warning_threshold_percentage(self) -> float:
        """Umbral de advertencia en porcentaje (ej: 20.0 para 20%)."""
        return self._warning_threshold_percentage

    @warning_threshold_percentage.setter
    def warning_threshold_percentage(self, value: float) -> None:
        """
        Actualiza el umbral de advertencia.

        Regla de negocio: Debe ser mayor que el umbral crítico y estar entre 0-100.
        """
        if not (0 <= value <= 100):
            raise ValueError("El umbral debe estar entre 0 y 100.")
        if value <= self._critical_threshold_percentage:
            raise ValueError("El umbral de advertencia debe ser mayor que el umbral crítico.")
        self._warning_threshold_percentage = value

    @property
    def critical_threshold_percentage(self) -> float:
        """Umbral crítico en porcentaje (ej: 10.0 para 10%)."""
        return self._critical_threshold_percentage

    @critical_threshold_percentage.setter
    def critical_threshold_percentage(self, value: float) -> None:
        """
        Actualiza el umbral crítico.

        Regla de negocio: Debe ser menor que el umbral de advertencia y estar entre 0-100.
        """
        if not (0 <= value <= 100):
            raise ValueError("El umbral debe estar entre 0 y 100.")
        if value >= self._warning_threshold_percentage:
            raise ValueError("El umbral crítico debe ser menor que el umbral de advertencia.")
        self._critical_threshold_percentage = value

    def assign_to_doser(self) -> None:
        """
        Marca el silo como asignado a un dosificador.

        Un silo puede estar asignado a uno o más dosificadores.
        """
        self._is_assigned = True

    def release_from_doser(self) -> None:
        """Marca el silo como sin dosificadores asignados."""
        self._is_assigned = False
