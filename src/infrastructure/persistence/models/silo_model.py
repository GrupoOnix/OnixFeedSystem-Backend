from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel

from domain.aggregates.silo import Silo
from domain.value_objects import FoodId, SiloId, SiloName, UserId, Weight


class SiloModel(SQLModel, table=True):
    __tablename__ = "silos"
    __table_args__ = (UniqueConstraint("name", "user_id", name="uq_silos_name_user"),)

    id: PyUUID = Field(primary_key=True)
    name: str = Field(max_length=100)
    capacity_mg: int = Field(sa_column=Column(BigInteger(), nullable=False))
    stock_level_mg: int = Field(sa_column=Column(BigInteger(), nullable=False))
    food_id: Optional[PyUUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), ForeignKey("foods.id", ondelete="SET NULL")),
    )
    is_assigned: bool
    user_id: Optional[PyUUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True),
    )
    warning_threshold_percentage: float = Field(default=20.0)
    critical_threshold_percentage: float = Field(default=10.0)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(silo: "Silo") -> "SiloModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return SiloModel(
            id=silo.id.value,
            name=str(silo.name),
            capacity_mg=silo.capacity.as_miligrams,
            stock_level_mg=silo.stock_level.as_miligrams,
            food_id=silo.food_id.value if silo.food_id else None,
            is_assigned=silo.is_assigned,
            user_id=silo.user_id.value if silo.user_id else None,
            warning_threshold_percentage=silo.warning_threshold_percentage,
            critical_threshold_percentage=silo.critical_threshold_percentage,
            created_at=silo._created_at,
        )

    def to_domain(self) -> "Silo":
        """Convierte modelo de persistencia a entidad de dominio."""
        silo = Silo(
            name=SiloName(self.name),
            capacity=Weight.from_miligrams(self.capacity_mg),
            stock_level=Weight.from_miligrams(self.stock_level_mg),
            food_id=FoodId(self.food_id) if self.food_id else None,
        )
        silo._id = SiloId(self.id)
        silo._is_assigned = self.is_assigned
        silo._warning_threshold_percentage = self.warning_threshold_percentage
        silo._critical_threshold_percentage = self.critical_threshold_percentage
        silo._created_at = self.created_at
        if self.user_id:
            silo._user_id = UserId(self.user_id)
        return silo
