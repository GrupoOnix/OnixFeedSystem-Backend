from application.dtos.food_dtos import CreateFoodRequest, FoodDetailResponse, FoodDTO
from domain.aggregates.food import Food
from domain.exceptions import DuplicateFoodCodeError, DuplicateFoodNameError
from domain.repositories import IFoodRepository
from domain.value_objects import FoodName


class CreateFoodUseCase:
    """Caso de uso para crear un nuevo alimento."""

    def __init__(self, food_repository: IFoodRepository):
        self._food_repository = food_repository

    async def execute(self, request: CreateFoodRequest) -> FoodDetailResponse:
        """
        Ejecuta el caso de uso para crear un nuevo alimento.

        Args:
            request: CreateFoodRequest con los datos del nuevo alimento

        Returns:
            FoodDetailResponse con los datos del alimento creado

        Raises:
            DuplicateFoodNameError: Si ya existe un alimento con ese nombre
            DuplicateFoodCodeError: Si ya existe un alimento con ese código
            ValueError: Si los datos son inválidos
        """
        # Validar que el nombre no exista
        food_name = FoodName(request.name)
        existing_by_name = await self._food_repository.find_by_name(food_name)
        if existing_by_name:
            raise DuplicateFoodNameError(
                f"Ya existe un alimento con el nombre '{request.name}'"
            )

        # Validar que el código no exista
        existing_by_code = await self._food_repository.find_by_code(request.code)
        if existing_by_code:
            raise DuplicateFoodCodeError(
                f"Ya existe un alimento con el código '{request.code}'"
            )

        # Crear el agregado
        food = Food(
            name=food_name,
            provider=request.provider,
            code=request.code,
            ppk=request.ppk,
            size_mm=request.size_mm,
            active=request.active,
        )

        # Persistir
        await self._food_repository.save(food)

        # Retornar response
        return FoodDetailResponse(food=self._to_dto(food))

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
