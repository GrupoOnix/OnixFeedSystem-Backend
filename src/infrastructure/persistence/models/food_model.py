from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from domain.aggregates.food import Food
from domain.value_objects import FoodId, FoodName


class FoodModel(SQLModel, table=True):
    """Modelo de persistencia para Food."""

    __tablename__ = "foods"

    id: UUID = Field(primary_key=True)
    name: str = Field(unique=True, max_length=100)
    provider: str = Field(max_length=150)
    code: str = Field(unique=True, max_length=50)
    ppk: float = Field(gt=0)  # Pellets por kilo
    size_mm: float = Field(gt=0)  # Tamaño del pellet en mm
    energy: float = Field(gt=0)  # Energía en kcal/kg
    kg_per_liter: float = Field(gt=0)  # Densidad: kg por litro
    active: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime

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
            energy=food.energy,
            kg_per_liter=food.kg_per_liter,
            active=food.active,
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
            energy=self.energy,
            kg_per_liter=self.kg_per_liter,
            active=self.active,
        )
        # Restaurar valores internos
        food._id = FoodId(self.id)
        food._created_at = self.created_at
        food._updated_at = self.updated_at
        return food
