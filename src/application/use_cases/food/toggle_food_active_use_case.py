from application.dtos.food_dtos import FoodDTO, ToggleFoodActiveRequest
from domain.aggregates.food import Food
from domain.exceptions import FoodNotFoundError
from domain.repositories import IFoodRepository
from domain.value_objects import FoodId


class ToggleFoodActiveUseCase:
    """Caso de uso para activar/desactivar un alimento."""

    def __init__(self, food_repository: IFoodRepository):
        self._food_repository = food_repository

    async def execute(
        self, food_id_str: str, request: ToggleFoodActiveRequest
    ) -> FoodDTO:
        """
        Ejecuta el caso de uso para cambiar el estado activo de un alimento.

        Args:
            food_id_str: ID del alimento en formato string
            request: ToggleFoodActiveRequest con el nuevo estado

        Returns:
            FoodDTO con los datos actualizados del alimento

        Raises:
            FoodNotFoundError: Si el alimento no existe
            ValueError: Si el alimento ya está en el estado solicitado
        """
        food_id = FoodId.from_string(food_id_str)
        food = await self._food_repository.find_by_id(food_id)

        if not food:
            raise FoodNotFoundError(f"Alimento con ID {food_id_str} no encontrado")

        # Cambiar estado según request
        if request.active:
            food.activate()
        else:
            food.deactivate()

        # Persistir cambios
        await self._food_repository.save(food)

        return self._to_dto(food)

    def _to_dto(self, food: Food) -> FoodDTO:
        """Convierte un agregado Food a FoodDTO."""
        return FoodDTO(
            id=str(food.id),
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
            display_name=food.get_display_name(),
        )
