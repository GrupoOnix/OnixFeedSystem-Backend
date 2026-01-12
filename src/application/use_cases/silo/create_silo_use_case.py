from application.dtos.silo_dtos import CreateSiloRequest, SiloDTO
from domain.aggregates import Silo
from domain.exceptions import DuplicateSiloNameError
from domain.repositories import ISiloRepository
from domain.value_objects import SiloName, Weight


class CreateSiloUseCase:
    """Caso de uso para crear un nuevo silo."""

    def __init__(self, silo_repository: ISiloRepository):
        self._silo_repository = silo_repository

    async def execute(self, request: CreateSiloRequest) -> SiloDTO:
        """
        Ejecuta el caso de uso para crear un nuevo silo.

        Args:
            request: CreateSiloRequest con los datos del nuevo silo

        Returns:
            SiloDTO con los datos del silo creado

        Raises:
            DuplicateSiloNameError: Si ya existe un silo con ese nombre
            ValueError: Si los datos son inválidos (capacity < stock_level, etc.)
        """
        # Validar que el nombre no exista
        silo_name = SiloName(request.name)
        existing_silo = await self._silo_repository.find_by_name(silo_name)
        if existing_silo:
            raise DuplicateSiloNameError(
                f"Ya existe un silo con el nombre '{request.name}'"
            )

        # Crear value objects
        capacity = Weight.from_kg(request.capacity_kg)
        stock_level = Weight.from_kg(request.stock_level_kg)

        # Crear el agregado (valida que stock_level <= capacity)
        silo = Silo(name=silo_name, capacity=capacity, stock_level=stock_level)

        # Persistir
        await self._silo_repository.save(silo)

        # Retornar DTO (silo recién creado no tiene línea asignada aún)
        return self._to_dto(silo, line_id=None, line_name=None)

    def _to_dto(self, silo: Silo, line_id=None, line_name=None) -> SiloDTO:
        """Convierte un agregado Silo a SiloDTO."""
        return SiloDTO(
            id=str(silo.id),
            name=str(silo.name),
            capacity_kg=silo.capacity.as_kg,
            stock_level_kg=silo.stock_level.as_kg,
            is_assigned=silo.is_assigned,
            created_at=silo.created_at,
            line_id=line_id,
            line_name=line_name,
        )
