from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from domain.aggregates.food import Food
from domain.value_objects import FoodId, FoodName, UserId


class FoodModel(SQLModel, table=True):
    """Modelo de persistencia para Food."""

    __tablename__ = "foods"
    __table_args__ = (
        UniqueConstraint("name", "user_id", name="uq_foods_name_user"),
        UniqueConstraint("code", "user_id", name="uq_foods_code_user"),
    )

    id: UUID = Field(primary_key=True)
    name: str = Field(max_length=100)
    provider: str = Field(max_length=150)
    code: str = Field(max_length=50)
    ppk: float = Field(gt=0)  # Pellets por kilo
    size_mm: float = Field(gt=0)  # Tamaño del pellet en mm
    active: bool = Field(default=True)
    user_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True),
    )
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(food: Food) -> "FoodModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return FoodModel(
            id=food.id.value,
            name=str(food.name),
            provider=food.provider,
            code=food.code,
            ppk=food.ppk,
            size_mm=food.size_mm,
            active=food.active,
            user_id=food.user_id.value if food.user_id else None,
            created_at=food.created_at,
            updated_at=food.updated_at,
        )

    def to_domain(self) -> Food:
        """Convierte modelo de persistencia a entidad de dominio."""
        food = Food(
            name=FoodName(self.name),
            provider=self.provider,
            code=self.code,
            ppk=self.ppk,
            size_mm=self.size_mm,
            active=self.active,
        )
        # Restaurar valores internos
        food._id = FoodId(self.id)
        food._created_at = self.created_at
        food._updated_at = self.updated_at
        if self.user_id:
            food._user_id = UserId(self.user_id)
        return food
