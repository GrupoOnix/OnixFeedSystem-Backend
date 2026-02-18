from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from domain.value_objects.mortality_log_entry import MortalityLogEntry
from domain.value_objects import CageId


class MortalityLogModel(SQLModel, table=True):
    __tablename__ = "cage_mortality_log"

    mortality_id: UUID = Field(default_factory=uuid4, primary_key=True)
    cage_id: UUID = Field(foreign_key="cages.id", nullable=False, index=True, ondelete="CASCADE")

    dead_fish_count: int = Field(nullable=False)
    mortality_date: date = Field(nullable=False, index=True)
    note: Optional[str] = Field(default=None)

    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(entry: MortalityLogEntry) -> "MortalityLogModel":
        """Convierte VO de dominio a modelo de persistencia."""
        return MortalityLogModel(
            mortality_id=entry.mortality_id,
            cage_id=entry.cage_id.value,
            dead_fish_count=entry.dead_fish_count,
            mortality_date=entry.mortality_date,
            note=entry.note,
            created_at=entry.created_at,
        )

    def to_domain(self) -> MortalityLogEntry:
        """Convierte modelo de persistencia a VO de dominio."""
        return MortalityLogEntry(
            mortality_id=self.mortality_id,
            cage_id=CageId(self.cage_id),
            dead_fish_count=self.dead_fish_count,
            mortality_date=self.mortality_date,
            note=self.note,
            created_at=self.created_at,
        )
