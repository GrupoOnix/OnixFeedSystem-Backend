"""Entidad que representa un evento de población en una jaula."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.enums import PopulationEventType
from domain.value_objects.identifiers import CageId


@dataclass
class PopulationEvent:
    """
    Representa un evento que afecta la población de una jaula.

    Registra cambios en la cantidad de peces y/o peso promedio,
    manteniendo un historial completo y auditable.
    """

    cage_id: CageId
    event_type: PopulationEventType
    event_date: date
    fish_count_delta: int  # Positivo = entrada, Negativo = salida, 0 = solo biometría
    new_fish_count: int  # Snapshot del total después del evento
    avg_weight_grams: Optional[float] = None  # Peso promedio al momento del evento
    note: Optional[str] = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Valida la consistencia del evento."""
        if self.new_fish_count < 0:
            raise ValueError("La cantidad de peces no puede ser negativa")

        if self.avg_weight_grams is not None and self.avg_weight_grams < 0:
            raise ValueError("El peso promedio no puede ser negativo")

        # Validar coherencia entre tipo de evento y delta
        if self.event_type == PopulationEventType.MORTALITY:
            if self.fish_count_delta > 0:
                raise ValueError("Mortalidad debe tener delta negativo o cero")

        if self.event_type in (
            PopulationEventType.INITIAL_STOCK,
            PopulationEventType.RESTOCK,
            PopulationEventType.TRANSFER_IN,
        ):
            if self.fish_count_delta < 0:
                raise ValueError(
                    f"{self.event_type.value} debe tener delta positivo o cero"
                )

        if self.event_type in (
            PopulationEventType.HARVEST,
            PopulationEventType.TRANSFER_OUT,
        ):
            if self.fish_count_delta > 0:
                raise ValueError(
                    f"{self.event_type.value} debe tener delta negativo o cero"
                )

        if self.event_type == PopulationEventType.BIOMETRY:
            if self.fish_count_delta != 0:
                raise ValueError("Biometría no debe cambiar la cantidad de peces")
            if self.avg_weight_grams is None:
                raise ValueError("Biometría requiere peso promedio")

    @property
    def biomass_kg(self) -> Optional[float]:
        """Calcula la biomasa en kg si hay peso promedio disponible."""
        if self.avg_weight_grams is None:
            return None
        return (self.new_fish_count * self.avg_weight_grams) / 1000

    @classmethod
    def create_initial_stock(
        cls,
        cage_id: CageId,
        fish_count: int,
        avg_weight_grams: float,
        event_date: date,
        note: Optional[str] = None,
    ) -> "PopulationEvent":
        """Crea un evento de siembra inicial."""
        return cls(
            cage_id=cage_id,
            event_type=PopulationEventType.INITIAL_STOCK,
            event_date=event_date,
            fish_count_delta=fish_count,
            new_fish_count=fish_count,
            avg_weight_grams=avg_weight_grams,
            note=note,
        )

    @classmethod
    def create_mortality(
        cls,
        cage_id: CageId,
        dead_count: int,
        new_total: int,
        event_date: date,
        avg_weight_grams: Optional[float] = None,
        note: Optional[str] = None,
    ) -> "PopulationEvent":
        """Crea un evento de mortalidad."""
        return cls(
            cage_id=cage_id,
            event_type=PopulationEventType.MORTALITY,
            event_date=event_date,
            fish_count_delta=-dead_count,
            new_fish_count=new_total,
            avg_weight_grams=avg_weight_grams,
            note=note,
        )

    @classmethod
    def create_biometry(
        cls,
        cage_id: CageId,
        current_fish_count: int,
        avg_weight_grams: float,
        event_date: date,
        note: Optional[str] = None,
    ) -> "PopulationEvent":
        """Crea un evento de biometría (solo actualiza peso)."""
        return cls(
            cage_id=cage_id,
            event_type=PopulationEventType.BIOMETRY,
            event_date=event_date,
            fish_count_delta=0,
            new_fish_count=current_fish_count,
            avg_weight_grams=avg_weight_grams,
            note=note,
        )

    @classmethod
    def create_harvest(
        cls,
        cage_id: CageId,
        harvested_count: int,
        new_total: int,
        event_date: date,
        avg_weight_grams: Optional[float] = None,
        note: Optional[str] = None,
    ) -> "PopulationEvent":
        """Crea un evento de cosecha."""
        return cls(
            cage_id=cage_id,
            event_type=PopulationEventType.HARVEST,
            event_date=event_date,
            fish_count_delta=-harvested_count,
            new_fish_count=new_total,
            avg_weight_grams=avg_weight_grams,
            note=note,
        )

    @classmethod
    def create_restock(
        cls,
        cage_id: CageId,
        added_count: int,
        new_total: int,
        avg_weight_grams: float,
        event_date: date,
        note: Optional[str] = None,
    ) -> "PopulationEvent":
        """Crea un evento de resiembra."""
        return cls(
            cage_id=cage_id,
            event_type=PopulationEventType.RESTOCK,
            event_date=event_date,
            fish_count_delta=added_count,
            new_fish_count=new_total,
            avg_weight_grams=avg_weight_grams,
            note=note,
        )

    @classmethod
    def create_adjustment(
        cls,
        cage_id: CageId,
        delta: int,
        new_total: int,
        event_date: date,
        avg_weight_grams: Optional[float] = None,
        note: Optional[str] = None,
    ) -> "PopulationEvent":
        """Crea un evento de ajuste de inventario."""
        return cls(
            cage_id=cage_id,
            event_type=PopulationEventType.ADJUSTMENT,
            event_date=event_date,
            fish_count_delta=delta,
            new_fish_count=new_total,
            avg_weight_grams=avg_weight_grams,
            note=note,
        )
