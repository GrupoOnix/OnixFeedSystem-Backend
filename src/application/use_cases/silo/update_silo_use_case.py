from application.dtos.silo_dtos import SiloDTO, UpdateSiloRequest
from domain.exceptions import DuplicateSiloNameError, SiloNotFoundError
from domain.repositories import ISiloRepository
from domain.value_objects import SiloId, SiloName, Weight


class UpdateSiloUseCase:
    """Caso de uso para actualizar un silo existente."""

    def __init__(self, silo_repository: ISiloRepository):
        self._silo_repository = silo_repository

    async def execute(self, silo_id: str, request: UpdateSiloRequest) -> SiloDTO:
        """
        Ejecuta el caso de uso para actualizar un silo.

        Args:
            silo_id: ID del silo a actualizar
            request: UpdateSiloRequest con los campos a actualizar

        Returns:
            SiloDTO con los datos actualizados del silo

        Raises:
            SiloNotFoundError: Si el silo no existe
            DuplicateSiloNameError: Si el nuevo nombre ya existe
            ValueError: Si la nueva capacidad es menor al stock actual
        """
        # Buscar el silo
        silo_id_vo = SiloId.from_string(silo_id)
        silo = await self._silo_repository.find_by_id(silo_id_vo)

        if not silo:
            raise SiloNotFoundError(f"Silo con ID {silo_id} no encontrado")

        # Actualizar nombre si se proporciona
        if request.name is not None:
            new_name = SiloName(request.name)
            # Validar que no exista otro silo con ese nombre
            existing_silo = await self._silo_repository.find_by_name(new_name)
            if existing_silo and existing_silo.id != silo.id:
                raise DuplicateSiloNameError(
                    f"Ya existe un silo con el nombre '{request.name}'"
                )
            silo.name = new_name

        # Actualizar capacidad si se proporciona
        if request.capacity_kg is not None:
            new_capacity = Weight.from_kg(request.capacity_kg)
            # El setter valida que la nueva capacidad >= stock actual
            silo.capacity = new_capacity

        # Actualizar stock si se proporciona
        if request.stock_level_kg is not None:
            new_stock_level = Weight.from_kg(request.stock_level_kg)
            # El setter valida que el stock <= capacidad
            silo.stock_level = new_stock_level

        # Persistir cambios
        await self._silo_repository.save(silo)

        # Obtener información actualizada con línea asignada
        result = await self._silo_repository.find_by_id_with_line_info(silo_id_vo)

        if result:
            _, line_id, line_name = result
        else:
            line_id, line_name = None, None

        # Retornar DTO
        return self._to_dto(silo, line_id, line_name)

    def _to_dto(self, silo, line_id=None, line_name=None) -> SiloDTO:
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
