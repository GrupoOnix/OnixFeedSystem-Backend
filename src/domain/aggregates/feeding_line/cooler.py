"""
Entidad de dominio: Cooler (Enfriador de Aire)

El cooler es un componente opcional de la línea de alimentación que enfría
el aire entre el Blower y el Doser para proteger la calidad del alimento.
"""

from datetime import datetime, timezone

from domain.interfaces import ICooler
from domain.value_objects import (
    CoolerId,
    CoolerName,
    CoolerPowerPercentage,
)


class Cooler(ICooler):
    """
    Enfriador de aire para línea de alimentación.

    El cooler reduce la temperatura del aire generado por el blower
    antes de que llegue al dosificador, protegiendo así el alimento.

    Atributos:
        - id: Identificador único del cooler
        - name: Nombre descriptivo
        - is_on: Estado encendido/apagado
        - cooling_power_percentage: Potencia de enfriamiento (0-100%)
        - created_at: Timestamp de creación
    """

    def __init__(
        self,
        name: CoolerName,
        cooling_power_percentage: CoolerPowerPercentage,
        is_on: bool = False,
    ):
        """
        Crea una nueva instancia de Cooler.

        Args:
            name: Nombre del cooler
            cooling_power_percentage: Potencia de enfriamiento inicial
            is_on: Estado inicial (por defecto apagado)
        """
        self._id = CoolerId.generate()
        self._name = name
        self._is_on = is_on
        self._cooling_power_percentage = cooling_power_percentage
        self._created_at = datetime.now(timezone.utc)

    # -----------------
    # Properties
    # -----------------

    @property
    def id(self) -> CoolerId:
        return self._id

    @property
    def name(self) -> CoolerName:
        return self._name

    @name.setter
    def name(self, name: CoolerName) -> None:
        self._name = name

    @property
    def is_on(self) -> bool:
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool) -> None:
        self._is_on = value

    @property
    def cooling_power_percentage(self) -> CoolerPowerPercentage:
        return self._cooling_power_percentage

    @cooling_power_percentage.setter
    def cooling_power_percentage(self, power: CoolerPowerPercentage) -> None:
        """
        Actualiza la potencia de enfriamiento.

        Valida que la potencia sea segura antes de asignar.

        Raises:
            ValueError: Si la potencia no es válida
        """
        if not self.validate_power_is_safe(power):
            raise ValueError(f"La potencia {power} no es segura para este cooler")
        self._cooling_power_percentage = power

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # -----------------
    # Métodos de Comportamiento
    # -----------------

    def turn_on(self) -> None:
        """Enciende el cooler."""
        self._is_on = True

    def turn_off(self) -> None:
        """Apaga el cooler."""
        self._is_on = False

    def validate_power_is_safe(self, power: CoolerPowerPercentage) -> bool:
        """
        Valida que la potencia de enfriamiento sea segura.

        Por ahora, solo valida que sea una instancia correcta de CoolerPowerPercentage.
        En el futuro puede incluir lógicas más complejas.

        Args:
            power: Potencia a validar

        Returns:
            True si la potencia es segura, False en caso contrario
        """
        return isinstance(power, CoolerPowerPercentage)
