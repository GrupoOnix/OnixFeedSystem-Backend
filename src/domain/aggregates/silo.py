from datetime import datetime
from typing import Optional

from domain.value_objects import FoodId, SiloId, SiloName, Weight


class Silo:
    def __init__(
        self,
        name: SiloName,
        capacity: Weight,
        stock_level: Weight = Weight.zero(),
        food_id: Optional[FoodId] = None,
        warning_threshold_percentage: float = 20.0,
        critical_threshold_percentage: float = 10.0,
    ):
        if stock_level > capacity:
            raise ValueError("El stock no puede ser mayor que la capacidad.")
        
        if warning_threshold_percentage <= critical_threshold_percentage:
            raise ValueError(
                "El umbral de advertencia debe ser mayor que el umbral crítico."
            )
        
        if not (0 <= critical_threshold_percentage <= 100):
            raise ValueError("Los umbrales deben estar entre 0 y 100.")
        
        if not (0 <= warning_threshold_percentage <= 100):
            raise ValueError("Los umbrales deben estar entre 0 y 100.")

        self._id = SiloId.generate()
        self._name = name
        self._capacity = capacity
        self._stock_level = stock_level
        self._food_id = food_id
        self._is_assigned = False  # FA4: Control de asignación 1-a-1
        self._warning_threshold_percentage = warning_threshold_percentage
        self._critical_threshold_percentage = critical_threshold_percentage
        self._created_at = datetime.utcnow()

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
        if new_capacity < self._stock_level:
            raise ValueError(
                f"La nueva capacidad ({new_capacity}) no puede ser menor "
                f"al stock actual ({self._stock_level})"
            )
        self._capacity = new_capacity

    @property
    def stock_level(self) -> Weight:
        return self._stock_level

    @stock_level.setter
    def stock_level(self, new_stock_level: Weight) -> None:
        """
        Actualiza el nivel de stock del silo.

        Regla de negocio: El stock no puede ser mayor a la capacidad del silo.
        """
        if new_stock_level > self._capacity:
            raise ValueError(
                f"El stock ({new_stock_level}) no puede ser mayor "
                f"a la capacidad del silo ({self._capacity})"
            )
        self._stock_level = new_stock_level

    @property
    def is_assigned(self) -> bool:
        """Indica si el silo ya está asignado a un dosificador."""
        return self._is_assigned

    @property
    def food_id(self) -> Optional[FoodId]:
        """ID del alimento asignado al silo (opcional)."""
        return self._food_id

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
            raise ValueError(
                "El umbral de advertencia debe ser mayor que el umbral crítico."
            )
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
            raise ValueError(
                "El umbral crítico debe ser menor que el umbral de advertencia."
            )
        self._critical_threshold_percentage = value

    def assign_to_doser(self) -> None:
        """
        Marca el silo como asignado a un dosificador.

        Regla FA4: Un silo solo puede estar asignado a un dosificador a la vez.
        """
        if self._is_assigned:
            raise ValueError(
                f"El silo '{self.name}' ya está asignado a otro dosificador"
            )
        self._is_assigned = True

    def release_from_doser(self) -> None:
        """Libera el silo para que pueda ser asignado a otro dosificador."""
        self._is_assigned = False

    def assign_food(self, food_id: FoodId) -> None:
        """
        Asigna un tipo de alimento al silo.

        Args:
            food_id: ID del alimento a asignar
        """
        self._food_id = food_id

    def remove_food(self) -> None:
        """Remueve la asignación de alimento del silo."""
        self._food_id = None
