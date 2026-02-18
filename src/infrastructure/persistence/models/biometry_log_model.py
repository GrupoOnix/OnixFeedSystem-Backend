from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from domain.value_objects.biometry_log_entry import BiometryLogEntry
from domain.value_objects import CageId


class BiometryLogModel(SQLModel, table=True):
    __tablename__ = "cage_biometry_log"

    biometry_id: UUID = Field(default_factory=uuid4, primary_key=True)
    cage_id: UUID = Field(foreign_key="cages.id", nullable=False, index=True, ondelete="CASCADE")

    # Valores anteriores (snapshot)
    old_fish_count: Optional[int] = Field(default=None)
    old_average_weight_g: Optional[float] = Field(default=None)

    # Valores nuevos
    new_fish_count: Optional[int] = Field(default=None)
    new_average_weight_g: Optional[float] = Field(default=None)

    # Metadata del muestreo
    sampling_date: date = Field(nullable=False)
    note: Optional[str] = Field(default=None)

    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(entry: BiometryLogEntry) -> "BiometryLogModel":
        """Convierte VO de dominio a modelo de persistencia."""
        return BiometryLogModel(
            biometry_id=entry.biometry_id,
            cage_id=entry.cage_id.value,
            old_fish_count=entry.old_fish_count,
            old_average_weight_g=entry.old_average_weight_g,
            new_fish_count=entry.new_fish_count,
            new_average_weight_g=entry.new_average_weight_g,
            sampling_date=entry.sampling_date,
            note=entry.note,
            created_at=entry.created_at,
        )

    def to_domain(self) -> BiometryLogEntry:
        """Convierte modelo de persistencia a VO de dominio."""
        return BiometryLogEntry(
            biometry_id=self.biometry_id,
            cage_id=CageId(self.cage_id),
            old_fish_count=self.old_fish_count,
            old_average_weight_g=self.old_average_weight_g,
            new_fish_count=self.new_fish_count,
            new_average_weight_g=self.new_average_weight_g,
            sampling_date=self.sampling_date,
            note=self.note,
            created_at=self.created_at,
        )
