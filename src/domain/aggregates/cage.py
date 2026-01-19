"""Aggregate Root para Jaulas."""

from dataclasses import field
from datetime import date, datetime
from typing import Optional

from domain.entities.population_event import PopulationEvent
from domain.enums import CageStatus, PopulationEventType
from domain.value_objects.cage_configuration import CageConfiguration
from domain.value_objects.identifiers import CageId
from domain.value_objects.names import CageName


class Cage:
    """
    Aggregate Root que representa una jaula de peces.

    Responsabilidades:
    - Identidad y estado de la jaula
    - Gestión de población (cantidad de peces y peso promedio)
    - Configuración de alimentación

    NO es responsable de:
    - Asignación a líneas de alimentación (se maneja desde FeedingLine)
    """

    def __init__(
        self,
        name: CageName,
        config: Optional[CageConfiguration] = None,
        status: CageStatus = CageStatus.AVAILABLE,
    ):
        self._id = CageId.generate()
        self._name = name
        self._status = status
        self._created_at = datetime.utcnow()

        # Población
        self._fish_count: int = 0
        self._avg_weight_grams: Optional[float] = None

        # Configuración
        self._config = config or CageConfiguration.empty()

    # =========================================================================
    # PROPIEDADES DE IDENTIDAD
    # =========================================================================

    @property
    def id(self) -> CageId:
        return self._id

    @property
    def name(self) -> CageName:
        return self._name

    @property
    def status(self) -> CageStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # =========================================================================
    # PROPIEDADES DE POBLACIÓN
    # =========================================================================

    @property
    def fish_count(self) -> int:
        return self._fish_count

    @property
    def avg_weight_grams(self) -> Optional[float]:
        return self._avg_weight_grams

    @property
    def biomass_kg(self) -> float:
        """Biomasa calculada en kg: (cantidad_peces * peso_promedio_g) / 1000."""
        if self._avg_weight_grams is None or self._fish_count == 0:
            return 0.0
        return (self._fish_count * self._avg_weight_grams) / 1000.0

    @property
    def current_density_kg_m3(self) -> Optional[float]:
        """Densidad actual en kg/m³ (si hay volumen configurado)."""
        if self._config.volume_m3 is None or self._config.volume_m3 == 0:
            return None
        if self.biomass_kg == 0:
            return None
        return self.biomass_kg / self._config.volume_m3

    # =========================================================================
    # PROPIEDADES DE CONFIGURACIÓN
    # =========================================================================

    @property
    def config(self) -> CageConfiguration:
        return self._config

    # =========================================================================
    # MÉTODOS DE IDENTIDAD
    # =========================================================================

    def rename(self, new_name: CageName) -> None:
        """Cambia el nombre de la jaula."""
        self._name = new_name

    def set_available(self) -> None:
        """Marca la jaula como disponible."""
        self._status = CageStatus.AVAILABLE

    def set_in_use(self) -> None:
        """Marca la jaula como en uso."""
        self._status = CageStatus.IN_USE

    def set_maintenance(self) -> None:
        """Marca la jaula en mantenimiento."""
        self._status = CageStatus.MAINTENANCE

    # =========================================================================
    # MÉTODOS DE POBLACIÓN
    # =========================================================================

    def set_initial_population(
        self,
        fish_count: int,
        avg_weight_grams: float,
        event_date: date,
        note: Optional[str] = None,
    ) -> PopulationEvent:
        """
        Establece la población inicial de la jaula (siembra).

        Retorna el evento de población para persistir.
        """
        if fish_count <= 0:
            raise ValueError("La cantidad de peces debe ser mayor a 0")
        if avg_weight_grams <= 0:
            raise ValueError("El peso promedio debe ser mayor a 0")
        if self._fish_count > 0:
            raise ValueError(
                "La jaula ya tiene población. Use add_fish para agregar más."
            )

        self._fish_count = fish_count
        self._avg_weight_grams = avg_weight_grams

        return PopulationEvent.create_initial_stock(
            cage_id=self._id,
            fish_count=fish_count,
            avg_weight_grams=avg_weight_grams,
            event_date=event_date,
            note=note,
        )

    def add_fish(
        self,
        count: int,
        avg_weight_grams: Optional[float],
        event_date: date,
        note: Optional[str] = None,
    ) -> PopulationEvent:
        """
        Agrega peces a la jaula (resiembra).

        Si se proporciona avg_weight_grams, se actualiza el peso promedio.
        """
        if count <= 0:
            raise ValueError("La cantidad de peces a agregar debe ser mayor a 0")

        self._fish_count += count
        if avg_weight_grams is not None:
            if avg_weight_grams <= 0:
                raise ValueError("El peso promedio debe ser mayor a 0")
            self._avg_weight_grams = avg_weight_grams

        return PopulationEvent.create_restock(
            cage_id=self._id,
            added_count=count,
            new_total=self._fish_count,
            avg_weight_grams=avg_weight_grams or self._avg_weight_grams or 0,
            event_date=event_date,
            note=note,
        )

    def register_mortality(
        self,
        dead_count: int,
        event_date: date,
        note: Optional[str] = None,
    ) -> PopulationEvent:
        """
        Registra mortalidad y RESTA los peces del total.

        Retorna el evento de población para persistir.
        """
        if dead_count <= 0:
            raise ValueError("La cantidad de peces muertos debe ser mayor a 0")
        if dead_count > self._fish_count:
            raise ValueError(
                f"No se pueden registrar {dead_count} muertes. "
                f"Solo hay {self._fish_count} peces en la jaula."
            )

        self._fish_count -= dead_count

        return PopulationEvent.create_mortality(
            cage_id=self._id,
            dead_count=dead_count,
            new_total=self._fish_count,
            event_date=event_date,
            avg_weight_grams=self._avg_weight_grams,
            note=note,
        )

    def update_biometry(
        self,
        avg_weight_grams: float,
        event_date: date,
        note: Optional[str] = None,
    ) -> PopulationEvent:
        """
        Actualiza el peso promedio de los peces (biometría).

        No modifica la cantidad de peces.
        """
        if avg_weight_grams <= 0:
            raise ValueError("El peso promedio debe ser mayor a 0")

        self._avg_weight_grams = avg_weight_grams

        return PopulationEvent.create_biometry(
            cage_id=self._id,
            current_fish_count=self._fish_count,
            avg_weight_grams=avg_weight_grams,
            event_date=event_date,
            note=note,
        )

    def harvest(
        self,
        count: int,
        event_date: date,
        note: Optional[str] = None,
    ) -> PopulationEvent:
        """
        Registra una cosecha (extracción de peces).
        """
        if count <= 0:
            raise ValueError("La cantidad de peces a cosechar debe ser mayor a 0")
        if count > self._fish_count:
            raise ValueError(
                f"No se pueden cosechar {count} peces. "
                f"Solo hay {self._fish_count} peces en la jaula."
            )

        self._fish_count -= count

        return PopulationEvent.create_harvest(
            cage_id=self._id,
            harvested_count=count,
            new_total=self._fish_count,
            event_date=event_date,
            avg_weight_grams=self._avg_weight_grams,
            note=note,
        )

    def adjust_population(
        self,
        new_fish_count: int,
        event_date: date,
        note: Optional[str] = None,
    ) -> PopulationEvent:
        """
        Ajusta manualmente la población (corrección de inventario).

        Útil para reconciliar diferencias entre el sistema y conteos físicos.
        """
        if new_fish_count < 0:
            raise ValueError("La cantidad de peces no puede ser negativa")

        delta = new_fish_count - self._fish_count
        self._fish_count = new_fish_count

        return PopulationEvent.create_adjustment(
            cage_id=self._id,
            delta=delta,
            new_total=self._fish_count,
            event_date=event_date,
            avg_weight_grams=self._avg_weight_grams,
            note=note,
        )

    # =========================================================================
    # MÉTODOS DE CONFIGURACIÓN
    # =========================================================================

    def update_config(self, new_config: CageConfiguration) -> None:
        """Actualiza la configuración de la jaula."""
        self._config = new_config

    # =========================================================================
    # MÉTODOS DE RECONSTRUCCIÓN (para repositorio)
    # =========================================================================

    def _set_id(self, cage_id: CageId) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._id = cage_id

    def _set_created_at(self, created_at: datetime) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._created_at = created_at

    def _set_fish_count(self, count: int) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._fish_count = count

    def _set_avg_weight_grams(self, weight: Optional[float]) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._avg_weight_grams = weight

    def _set_status(self, status: CageStatus) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._status = status

    # =========================================================================
    # FACTORY METHOD
    # =========================================================================

    @classmethod
    def create(
        cls,
        name: str,
        config: Optional[CageConfiguration] = None,
    ) -> "Cage":
        """
        Factory method para crear una nueva jaula.

        Args:
            name: Nombre de la jaula
            config: Configuración opcional

        Returns:
            Nueva instancia de Cage
        """
        return cls(
            name=CageName(name),
            config=config,
            status=CageStatus.AVAILABLE,
        )
