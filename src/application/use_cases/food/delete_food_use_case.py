from domain.exceptions import FoodNotFoundError
from domain.repositories import IFoodRepository
from domain.value_objects import FoodId


class DeleteFoodUseCase:
    """Caso de uso para eliminar un alimento."""

    def __init__(self, food_repository: IFoodRepository):
        self._food_repository = food_repository

    async def execute(self, food_id_str: str) -> None:
        """
        Ejecuta el caso de uso para eliminar un alimento.

        Args:
            food_id_str: ID del alimento en formato string

        Raises:
            FoodNotFoundError: Si el alimento no existe
        """
        food_id = FoodId.from_string(food_id_str)
        food = await self._food_repository.find_by_id(food_id)

        if not food:
            raise FoodNotFoundError(f"Alimento con ID {food_id_str} no encontrado")

        await self._food_repository.delete(food_id)
