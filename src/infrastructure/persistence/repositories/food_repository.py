from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.food import Food
from domain.repositories import IFoodRepository
from domain.value_objects import FoodId, FoodName, UserId
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
            existing.active = food.active
            existing.updated_at = food.updated_at
            existing.user_id = food.user_id.value if food.user_id else existing.user_id
        else:
            # Crear nuevo registro
            food_model = FoodModel.from_domain(food)
            self.session.add(food_model)

        await self.session.flush()

    async def find_by_id(self, food_id: FoodId, user_id: UserId) -> Optional[Food]:
        """Busca un alimento por su ID, filtrado por usuario."""
        result = await self.session.execute(
            select(FoodModel).where(
                FoodModel.id == food_id.value,
                FoodModel.user_id == user_id.value,
            )
        )
        food_model = result.scalar_one_or_none()
        return food_model.to_domain() if food_model else None

    async def find_by_name(self, name: FoodName, user_id: UserId) -> Optional[Food]:
        """Busca un alimento por su nombre, filtrado por usuario."""
        result = await self.session.execute(
            select(FoodModel).where(
                FoodModel.name == str(name),
                FoodModel.user_id == user_id.value,
            )
        )
        food_model = result.scalar_one_or_none()
        return food_model.to_domain() if food_model else None

    async def find_by_code(self, code: str, user_id: UserId) -> Optional[Food]:
        """Busca un alimento por su código de producto, filtrado por usuario."""
        result = await self.session.execute(
            select(FoodModel).where(
                FoodModel.code == code,
                FoodModel.user_id == user_id.value,
            )
        )
        food_model = result.scalar_one_or_none()
        return food_model.to_domain() if food_model else None

    async def get_all(self, user_id: UserId) -> List[Food]:
        """Obtiene todos los alimentos de un usuario."""
        result = await self.session.execute(
            select(FoodModel).where(FoodModel.user_id == user_id.value).order_by(FoodModel.name)
        )
        food_models = result.scalars().all()
        return [model.to_domain() for model in food_models]

    async def get_active(self, user_id: UserId) -> List[Food]:
        """Obtiene solo los alimentos activos de un usuario."""
        result = await self.session.execute(
            select(FoodModel)
            .where(
                FoodModel.active.is_(True),
                FoodModel.user_id == user_id.value,
            )
            .order_by(FoodModel.name)
        )
        food_models = result.scalars().all()
        return [model.to_domain() for model in food_models]

    async def delete(self, food_id: FoodId, user_id: UserId) -> None:
        """Elimina un alimento del usuario."""
        result = await self.session.execute(
            select(FoodModel).where(
                FoodModel.id == food_id.value,
                FoodModel.user_id == user_id.value,
            )
        )
        food_model = result.scalar_one_or_none()
        if food_model:
            await self.session.delete(food_model)
            await self.session.flush()
