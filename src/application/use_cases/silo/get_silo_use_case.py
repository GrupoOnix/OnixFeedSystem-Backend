from application.dtos.silo_dtos import SiloDTO
from domain.exceptions import SiloNotFoundError
from domain.repositories import ISiloRepository
from domain.value_objects import SiloId
from application.mappers.silo_inventory_mapper import to_batch_dto


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

        silo, line_ids, line_names = result

        # Convertir a DTO
        return self._to_dto(silo, line_ids, line_names)

    def _to_dto(self, silo, line_ids=None, line_names=None) -> SiloDTO:
        """Convierte un agregado Silo a SiloDTO."""
        line_ids = line_ids or []
        line_names = line_names or []
        return SiloDTO(
            id=str(silo.id),
            name=str(silo.name),
            capacity_kg=silo.capacity.as_kg,
            total_stock_kg=silo.total_stock.as_kg,
            reserved_stock_kg=silo.reserved_stock.as_kg,
            available_stock_kg=silo.available_stock.as_kg,
            fill_percentage=silo.fill_percentage,
            is_assigned=silo.is_assigned,
            created_at=silo.created_at,
            line_id=line_ids[0] if line_ids else None,
            line_name=line_names[0] if line_names else None,
            line_ids=line_ids,
            line_names=line_names,
            active_batches=[to_batch_dto(batch) for batch in silo.active_batches],
        )
