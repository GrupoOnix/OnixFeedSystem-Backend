from datetime import datetime
from typing import Optional
from domain.enums import CageStatus
from domain.exceptions import CageNotAvailableException
from domain.value_objects import (
    CageId,
    CageName,
    FishCount,
    Weight,
    FCR,
    Volume,
    Density,
    FeedingTableId,
    BlowDurationInSeconds,
    LineId,
    SlotNumber,
)


class Cage:
    def __init__(
        self,
        name: CageName,
        initial_fish_count: Optional[FishCount] = None,
        avg_fish_weight: Optional[Weight] = None,
        fcr: Optional[FCR] = None,
        total_volume: Optional[Volume] = None,
        max_density: Optional[Density] = None,
        transport_time: Optional[BlowDurationInSeconds] = None,
        status: CageStatus = CageStatus.AVAILABLE,
    ):
        self._id = CageId.generate()
        self._name = name
        self._status = status
        self._created_at = datetime.utcnow()

        # Población
        self._initial_fish_count = initial_fish_count
        self._current_fish_count = initial_fish_count

        # Biometría
        self._avg_fish_weight = avg_fish_weight

        # Configuración
        self._fcr = fcr
        self._total_volume = total_volume
        self._max_density = max_density
        self._feeding_table_id: Optional[FeedingTableId] = None
        self._transport_time = transport_time

        # Relaciones (referencias de conveniencia, la verdad la tiene FeedingLine)
        self._line_id: Optional[LineId] = None
        self._slot_number: Optional[SlotNumber] = None
        # TODO: Considerar agregar métodos privados _set_line_reference() y _clear_line_reference() para uso de repositorios

    @property
    def id(self) -> CageId:
        return self._id

    @property
    def name(self) -> CageName:
        return self._name

    @name.setter
    def name(self, new_name: CageName) -> None:
        self._name = new_name

    @property
    def status(self) -> CageStatus:
        return self._status

    @status.setter
    def status(self, new_status: CageStatus) -> None:
        self._status = new_status

    # Población
    @property
    def initial_fish_count(self) -> Optional[FishCount]:
        return self._initial_fish_count

    @property
    def current_fish_count(self) -> Optional[FishCount]:
        return self._current_fish_count

    # Biometría
    @property
    def avg_fish_weight(self) -> Optional[Weight]:
        return self._avg_fish_weight

    @property
    def biomass(self) -> Weight:
        """Biomasa calculada: (cantidad_peces * peso_promedio)"""
        if self._current_fish_count is None or self._avg_fish_weight is None:
            return Weight.zero()

        total_grams = self._current_fish_count.value * self._avg_fish_weight.as_grams
        return Weight.from_kg(total_grams / 1000.0)

    # Configuración
    @property
    def fcr(self) -> FCR:
        return self._fcr

    @fcr.setter
    def fcr(self, new_fcr: FCR) -> None:
        self._fcr = new_fcr

    @property
    def total_volume(self) -> Optional[Volume]:
        return self._total_volume

    @total_volume.setter
    def total_volume(self, new_volume: Optional[Volume]) -> None:
        self._total_volume = new_volume

    @property
    def max_density(self) -> Optional[Density]:
        return self._max_density

    @max_density.setter
    def max_density(self, new_density: Optional[Density]) -> None:
        self._max_density = new_density

    @property
    def feeding_table_id(self) -> Optional[FeedingTableId]:
        return self._feeding_table_id

    @feeding_table_id.setter
    def feeding_table_id(self, table_id: Optional[FeedingTableId]) -> None:
        self._feeding_table_id = table_id

    @property
    def transport_time(self) -> BlowDurationInSeconds:
        return self._transport_time

    @transport_time.setter
    def transport_time(self, new_time: BlowDurationInSeconds) -> None:
        self._transport_time = new_time

    # Relaciones
    @property
    def line_id(self) -> Optional[LineId]:
        return self._line_id

    @property
    def slot_number(self) -> Optional[SlotNumber]:
        return self._slot_number

    # Propiedades calculadas
    @property
    def survival_rate(self) -> float:
        """Tasa de supervivencia en porcentaje."""
        if self._initial_fish_count is None or self._current_fish_count is None:
            return 0.0

        if self._initial_fish_count.value == 0:
            return 0.0

        return (self._current_fish_count.value / self._initial_fish_count.value) * 100

    @property
    def mortality_count(self) -> FishCount:
        """Cantidad total de peces muertos desde la siembra."""
        if self._initial_fish_count is None or self._current_fish_count is None:
            return FishCount(0)

        dead_count = self._initial_fish_count.value - self._current_fish_count.value
        return FishCount(dead_count)

    @property
    def current_density(self) -> Optional[Density]:
        """Densidad actual en kg/m³ (si hay volumen configurado)."""
        if self._total_volume is None:
            return None

        if self._total_volume.as_cubic_meters == 0:
            return None

        biomass_kg = self.biomass.as_kg
        if biomass_kg == 0:
            return None

        density_value = biomass_kg / self._total_volume.as_cubic_meters
        return Density(density_value)

    # Métodos de negocio

    def register_mortality(self, dead_count: FishCount) -> None:
        """
        Registra mortalidad para reportes y estadísticas.
        NO modifica current_fish_count.
        El registro se guarda en cage_mortality_log.
        """
        if self._current_fish_count is None:
            raise ValueError("No se puede registrar mortalidad sin población establecida")

        if dead_count.value <= 0:
            raise ValueError("La cantidad de peces muertos debe ser mayor a 0")

    def update_fish_count(self, new_count: FishCount) -> None:
        """
        Actualiza el conteo de peces.
        El operador puede modificar esto libremente (recuento físico, ajustes, etc.)
        """
        if self._initial_fish_count is None:
            raise ValueError("No hay población establecida")

        if new_count.value < 0:
            raise ValueError("El conteo de peces no puede ser negativo")

        self._current_fish_count = new_count

    def update_biometry(self, new_avg_weight: Weight) -> None:
        """Actualiza el peso promedio de los peces."""
        if new_avg_weight.as_grams <= 0:
            raise ValueError("El peso promedio debe ser mayor a 0")

        self._avg_fish_weight = new_avg_weight

    def set_initial_population(self, fish_count: FishCount, avg_weight: Weight) -> None:
        """Establece la población inicial de la jaula (siembra)."""
        if self._initial_fish_count is not None:
            raise ValueError("La población inicial ya fue establecida")

        if fish_count.value <= 0:
            raise ValueError("La cantidad de peces debe ser mayor a 0")

        if avg_weight.as_grams <= 0:
            raise ValueError("El peso promedio debe ser mayor a 0")

        self._initial_fish_count = fish_count
        self._current_fish_count = fish_count
        self._avg_fish_weight = avg_weight
        