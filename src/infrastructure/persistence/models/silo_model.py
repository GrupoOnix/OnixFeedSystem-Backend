from datetime import datetime
from uuid import UUID
from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel
from domain.aggregates.silo import Silo
from domain.value_objects import SiloId, SiloName, Weight


class SiloModel(SQLModel, table=True):
    __tablename__ = "silos"

    id: UUID = Field(primary_key=True)
    name: str = Field(unique=True, max_length=100)
    capacity_mg: int = Field(sa_type=BigInteger())
    stock_level_mg: int = Field(sa_type=BigInteger())
    is_assigned: bool
    created_at: datetime

    @staticmethod
    def from_domain(silo: "Silo") -> "SiloModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return SiloModel(
            id=silo.id.value,
            name=str(silo.name),
            capacity_mg=silo.capacity.as_miligrams,
            stock_level_mg=silo.stock_level.as_miligrams,
            is_assigned=silo.is_assigned,
            created_at=silo._created_at,
        )

    def to_domain(self) -> "Silo":
        """Convierte modelo de persistencia a entidad de dominio."""
        silo = Silo(
            name=SiloName(self.name),
            capacity=Weight.from_miligrams(self.capacity_mg),
            stock_level=Weight.from_miligrams(self.stock_level_mg),
        )
        silo._id = SiloId(self.id)
        silo._is_assigned = self.is_assigned
        silo._created_at = self.created_at
        return silo
