from datetime import datetime
from typing import TYPE_CHECKING, List
from uuid import UUID as PyUUID

from sqlalchemy import BigInteger, Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from domain.aggregates.silo import Silo
from domain.value_objects import SiloId, SiloName, Weight
from .doser_silo_model import DoserSiloModel

if TYPE_CHECKING:
    from .doser_model import DoserModel


class SiloModel(SQLModel, table=True):
    __tablename__ = "silos"

    id: PyUUID = Field(primary_key=True)
    name: str = Field(unique=True, max_length=100)
    capacity_mg: int = Field(sa_column=Column(BigInteger(), nullable=False))
    warning_threshold_percentage: float = Field(default=20.0)
    critical_threshold_percentage: float = Field(default=10.0)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    dosers: List["DoserModel"] = Relationship(
        back_populates="silos",
        link_model=DoserSiloModel,
    )

    @staticmethod
    def from_domain(silo: "Silo") -> "SiloModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return SiloModel(
            id=silo.id.value,
            name=str(silo.name),
            capacity_mg=silo.capacity.as_miligrams,
            warning_threshold_percentage=silo.warning_threshold_percentage,
            critical_threshold_percentage=silo.critical_threshold_percentage,
            created_at=silo._created_at,
        )

    def to_domain(self) -> "Silo":
        """Convierte modelo de persistencia a entidad de dominio."""
        silo = Silo(
            name=SiloName(self.name),
            capacity=Weight.from_miligrams(self.capacity_mg),
        )
        silo._id = SiloId(self.id)
        silo._warning_threshold_percentage = self.warning_threshold_percentage
        silo._critical_threshold_percentage = self.critical_threshold_percentage
        silo._created_at = self.created_at
        return silo
