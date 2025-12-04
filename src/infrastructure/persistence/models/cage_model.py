from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, SQLModel, Relationship
from domain.aggregates.cage import Cage
from domain.enums import CageStatus
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
)

if TYPE_CHECKING:
    from .feeding_line_model import FeedingLineModel


class CageModel(SQLModel, table=True):
    __tablename__ = "cages"

    id: UUID = Field(primary_key=True)
    name: str = Field(unique=True, max_length=100)
    status: str
    created_at: datetime

    # Asignación a línea de alimentación
    line_id: Optional[UUID] = Field(
        default=None,
        foreign_key="feeding_lines.id",
        ondelete="SET NULL",
        index=True
    )
    slot_number: Optional[int] = Field(default=None)

    # Población
    current_fish_count: Optional[int] = Field(default=None)

    # Biometría (Weight en miligramos)
    avg_fish_weight_mg: Optional[int] = Field(default=None)

    # Configuración
    fcr: Optional[float] = Field(default=None)
    total_volume_m3: Optional[float] = Field(default=None)
    max_density_kg_m3: Optional[float] = Field(default=None)
    feeding_table_id: Optional[str] = Field(default=None, max_length=50)
    transport_time_sec: Optional[int] = Field(default=None)

    # Relationship
    feeding_line: Optional["FeedingLineModel"] = Relationship(back_populates="cages")

    @staticmethod
    def from_domain(cage: "Cage") -> "CageModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return CageModel(
            id=cage.id.value,
            name=str(cage.name),
            status=cage.status.value,
            created_at=cage.created_at,
            # Asignación a línea
            line_id=cage.line_id.value if cage.line_id else None,
            slot_number=cage.slot_number,
            # Población
            current_fish_count=cage.current_fish_count.value if cage.current_fish_count else None,
            # Biometría (convertir a miligramos)
            avg_fish_weight_mg=cage.avg_fish_weight.as_miligrams if cage.avg_fish_weight else None,
            # Configuración
            fcr=float(cage.fcr) if cage.fcr else None,
            total_volume_m3=cage.total_volume.as_cubic_meters if cage.total_volume else None,
            max_density_kg_m3=float(cage.max_density) if cage.max_density else None,
            feeding_table_id=str(cage.feeding_table_id) if cage.feeding_table_id else None,
            transport_time_sec=cage.transport_time.value if cage.transport_time else None,
        )

    def to_domain(self) -> "Cage":
        """Convierte modelo de persistencia a entidad de dominio."""
        cage = Cage(
            name=CageName(self.name),
            line_id=LineId(self.line_id) if self.line_id else None,
            slot_number=self.slot_number,
            avg_fish_weight=Weight.from_miligrams(self.avg_fish_weight_mg) if self.avg_fish_weight_mg is not None else None,
            fcr=FCR(self.fcr) if self.fcr is not None else None,
            total_volume=Volume.from_cubic_meters(self.total_volume_m3) if self.total_volume_m3 is not None else None,
            max_density=Density(self.max_density_kg_m3) if self.max_density_kg_m3 is not None else None,
            transport_time=BlowDurationInSeconds(self.transport_time_sec) if self.transport_time_sec is not None else None,
            status=CageStatus(self.status),
        )
        # Setear atributos privados
        cage._id = CageId(self.id)
        cage._created_at = self.created_at
        cage._current_fish_count = FishCount(self.current_fish_count) if self.current_fish_count is not None else None
        cage._feeding_table_id = FeedingTableId.from_string(self.feeding_table_id) if self.feeding_table_id else None
        return cage
