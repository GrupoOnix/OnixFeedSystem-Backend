from application.dtos.food_dtos import FoodDTO, ListFoodsResponse
from domain.aggregates.food import Food
from domain.repositories import IFoodRepository


class ListFoodsUseCase:
    """Caso de uso para listar alimentos."""

    def __init__(self, food_repository: IFoodRepository):
        self._food_repository = food_repository

    async def execute(self, active_only: bool = False) -> ListFoodsResponse:
        """
        Ejecuta el caso de uso para listar alimentos.

        Args:
            active_only: Si es True, solo retorna alimentos activos

        Returns:
            ListFoodsResponse con la lista de alimentos
        """
        if active_only:
            foods = await self._food_repository.get_active()
        else:
            foods = await self._food_repository.get_all()

        # Convertir a DTOs
        food_dtos = [self._to_dto(food) for food in foods]

        return ListFoodsResponse(foods=food_dtos)

    def _to_dto(self, food: Food) -> FoodDTO:
        """Convierte un agregado Food a FoodDTO."""
        return FoodDTO(
            id=str(food.id),
            name=str(food.name),
            provider=food.provider,
            code=food.code,
            ppk=food.ppk,
            size_mm=food.size_mm,
            active=food.active,
            created_at=food.created_at,
            updated_at=food.updated_at,
            display_name=food.get_display_name(),
        )
