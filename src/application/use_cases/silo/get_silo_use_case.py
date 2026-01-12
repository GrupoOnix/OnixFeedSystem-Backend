from application.dtos.silo_dtos import SiloDTO
from domain.exceptions import SiloNotFoundError
from domain.repositories import ISiloRepository
from domain.value_objects import SiloId


class GetSiloUseCase:
    """Caso de uso para obtener un silo por su ID."""

    def __init__(self, silo_repository: ISiloRepository):
        self._silo_repository = silo_repository

    async def execute(self, silo_id: str) -> SiloDTO:
        """
        Ejecuta el caso de uso para obtener un silo por ID.

        Args:
            silo_id: ID del silo como string

        Returns:
            SiloDTO con los datos del silo y su línea asociada

        Raises:
            SiloNotFoundError: Si el silo no existe
        """
        # Convertir string a value object
        silo_id_vo = SiloId.from_string(silo_id)

        # Buscar silo con información de línea
        result = await self._silo_repository.find_by_id_with_line_info(silo_id_vo)

        if not result:
            raise SiloNotFoundError(f"Silo con ID {silo_id} no encontrado")

        silo, line_id, line_name = result

        # Convertir a DTO
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
