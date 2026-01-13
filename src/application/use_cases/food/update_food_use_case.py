from application.dtos.food_dtos import FoodDTO, UpdateFoodRequest
from domain.aggregates.food import Food
from domain.exceptions import (
    DuplicateFoodCodeError,
    DuplicateFoodNameError,
    FoodNotFoundError,
)
from domain.repositories import IFoodRepository
from domain.value_objects import FoodId, FoodName


class UpdateFoodUseCase:
    """Caso de uso para actualizar un alimento."""

    def __init__(self, food_repository: IFoodRepository):
        self._food_repository = food_repository

    async def execute(self, food_id_str: str, request: UpdateFoodRequest) -> FoodDTO:
        """
        Ejecuta el caso de uso para actualizar un alimento.

        Args:
            food_id_str: ID del alimento en formato string
            request: UpdateFoodRequest con los datos a actualizar

        Returns:
            FoodDTO con los datos actualizados del alimento

        Raises:
            FoodNotFoundError: Si el alimento no existe
            DuplicateFoodNameError: Si el nuevo nombre ya está en uso
            DuplicateFoodCodeError: Si el nuevo código ya está en uso
            ValueError: Si los datos son inválidos
        """
        # Buscar alimento
        food_id = FoodId.from_string(food_id_str)
        food = await self._food_repository.find_by_id(food_id)

        if not food:
            raise FoodNotFoundError(f"Alimento con ID {food_id_str} no encontrado")

        # Validar nombre si se está actualizando
        if request.name is not None:
            new_name = FoodName(request.name)
            existing_by_name = await self._food_repository.find_by_name(new_name)
            if existing_by_name and str(existing_by_name.id) != food_id_str:
                raise DuplicateFoodNameError(
                    f"Ya existe un alimento con el nombre '{request.name}'"
                )

        # Validar código si se está actualizando
        if request.code is not None:
            existing_by_code = await self._food_repository.find_by_code(request.code)
            if existing_by_code and str(existing_by_code.id) != food_id_str:
                raise DuplicateFoodCodeError(
                    f"Ya existe un alimento con el código '{request.code}'"
                )

        # Actualizar información básica
        if request.name or request.provider or request.code:
            food.update_basic_info(
                name=FoodName(request.name) if request.name else None,
                provider=request.provider,
                code=request.code,
            )

        # Actualizar propiedades físicas
        if request.ppk or request.size_mm or request.kg_per_liter:
            food.update_physical_properties(
                ppk=request.ppk,
                size_mm=request.size_mm,
                kg_per_liter=request.kg_per_liter,
            )

        # Actualizar energía
        if request.energy is not None:
            food.update_energy(request.energy)

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
