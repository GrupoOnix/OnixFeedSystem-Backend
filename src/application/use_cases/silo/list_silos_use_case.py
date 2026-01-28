from application.dtos.silo_dtos import ListSilosRequest, ListSilosResponse, SiloDTO
from domain.repositories import ISiloRepository


class ListSilosUseCase:
    """Caso de uso para listar silos con filtros opcionales."""

    def __init__(self, silo_repository: ISiloRepository):
        self._silo_repository = silo_repository

    async def execute(self, request: ListSilosRequest) -> ListSilosResponse:
        """
        Ejecuta el caso de uso para listar silos.

        Args:
            request: Request con filtros opcionales (is_assigned)

        Returns:
            ListSilosResponse con la lista de silos y sus líneas asociadas
        """
        # Obtener silos con información de línea
        silos_with_line = await self._silo_repository.find_all_with_line_info(
            is_assigned=request.is_assigned
        )

        # Convertir a DTOs
        silo_dtos = [
            self._to_dto(silo, line_id, line_name)
            for silo, line_id, line_name in silos_with_line
        ]

        return ListSilosResponse(silos=silo_dtos)

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
            food_id=str(silo.food_id) if silo.food_id else None,
        )
