"""Use case para obtener el historial de población de una jaula."""

from typing import List, Optional

from application.dtos.cage_dtos import (
    PaginationInfo,
    PopulationEventResponse,
    PopulationHistoryResponse,
)
from domain.entities.population_event import PopulationEvent
from domain.enums import PopulationEventType
from domain.repositories import IPopulationEventRepository
from domain.value_objects.identifiers import CageId


class GetPopulationHistoryUseCase:
    """Caso de uso para obtener el historial de población de una jaula."""

    def __init__(self, event_repository: IPopulationEventRepository):
        self.event_repository = event_repository

    async def execute(
        self,
        cage_id: str,
        event_types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PopulationHistoryResponse:
        """
        Obtiene el historial de eventos de población.

        Args:
            cage_id: ID de la jaula
            event_types: Tipos de evento a filtrar (opcional)
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación

        Returns:
            PopulationHistoryResponse con los eventos y paginación
        """
        cage_id_vo = CageId.from_string(cage_id)

        # Convertir tipos de string a enum si se proporcionan
        type_filter = None
        if event_types:
            type_filter = [PopulationEventType(t) for t in event_types]

        # Obtener eventos
        events = await self.event_repository.list_by_cage(
            cage_id=cage_id_vo,
            event_types=type_filter,
            limit=limit,
            offset=offset,
        )

        # Contar total
        total = await self.event_repository.count_by_cage(
            cage_id=cage_id_vo,
            event_types=type_filter,
        )

        # Construir respuesta
        event_responses = [self._to_event_response(e) for e in events]

        pagination = PaginationInfo(
            total=total,
            limit=limit,
            offset=offset,
            has_next=(offset + limit) < total,
            has_previous=offset > 0,
        )

        return PopulationHistoryResponse(
            events=event_responses,
            pagination=pagination,
        )

    def _to_event_response(self, event: PopulationEvent) -> PopulationEventResponse:
        """Convierte la entidad a response DTO."""
        return PopulationEventResponse(
            id=str(event.id),
            cage_id=str(event.cage_id.value),
            event_type=event.event_type.value,
            event_date=event.event_date,
            fish_count_delta=event.fish_count_delta,
            new_fish_count=event.new_fish_count,
            avg_weight_grams=event.avg_weight_grams,
            biomass_kg=event.biomass_kg,
            note=event.note,
            created_at=event.created_at,
        )
