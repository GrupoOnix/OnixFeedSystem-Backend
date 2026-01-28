from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.food import Food
from domain.repositories import IFoodRepository
from domain.value_objects import FoodId, FoodName
from infrastructure.persistence.models.food_model import FoodModel


class FoodRepository(IFoodRepository):
    """Implementación del repositorio de alimentos."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, food: Food) -> None:
        """Guarda o actualiza un alimento."""
        existing = await self.session.get(FoodModel, food.id.value)

        if existing:
            # Actualizar campos
            existing.name = str(food.name)
            existing.provider = food.provider
            existing.code = food.code
            existing.ppk = food.ppk
            existing.size_mm = food.size_mm
            existing.energy = food.energy
            existing.kg_per_liter = food.kg_per_liter
            existing.active = food.active
            existing.updated_at = food.updated_at
        else:
            # Crear nuevo registro
            food_model = FoodModel.from_domain(food)
            self.session.add(food_model)

        await self.session.flush()

    async def find_by_id(self, food_id: FoodId) -> Optional[Food]:
        """Busca un alimento por su ID."""
        food_model = await self.session.get(FoodModel, food_id.value)
        return food_model.to_domain() if food_model else None

    async def find_by_name(self, name: FoodName) -> Optional[Food]:
        """Busca un alimento por su nombre."""
        result = await self.session.execute(
            select(FoodModel).where(FoodModel.name == str(name))
        )
        food_model = result.scalar_one_or_none()
        return food_model.to_domain() if food_model else None

    async def find_by_code(self, code: str) -> Optional[Food]:
        """Busca un alimento por su código de producto."""
        result = await self.session.execute(
            select(FoodModel).where(FoodModel.code == code)
        )
        food_model = result.scalar_one_or_none()
        return food_model.to_domain() if food_model else None

    async def get_all(self) -> List[Food]:
        """Obtiene todos los alimentos."""
        result = await self.session.execute(select(FoodModel).order_by(FoodModel.name))
        food_models = result.scalars().all()
        return [model.to_domain() for model in food_models]

    async def get_active(self) -> List[Food]:
        """Obtiene solo los alimentos activos."""
        result = await self.session.execute(
            select(FoodModel).where(FoodModel.active.is_(True)).order_by(FoodModel.name)
        )
        food_models = result.scalars().all()
        return [model.to_domain() for model in food_models]

    async def delete(self, food_id: FoodId) -> None:
        """Elimina un alimento."""
        food_model = await self.session.get(FoodModel, food_id.value)
        if food_model:
            await self.session.delete(food_model)
            await self.session.flush()
