from datetime import datetime

from domain.value_objects import SiloId, SiloName, Weight


class Silo:
    def __init__(
        self, name: SiloName, capacity: Weight, stock_level: Weight = Weight.zero()
    ):
        if stock_level > capacity:
            raise ValueError("El stock no puede ser mayor que la capacidad.")

        self._id = SiloId.generate()
        self._name = name
        self._capacity = capacity
        self._stock_level = stock_level
        self._is_assigned = False  # FA4: Control de asignación 1-a-1
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
    def created_at(self) -> datetime:
        """Fecha de creación del silo."""
        return self._created_at

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
