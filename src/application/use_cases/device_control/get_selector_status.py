"""Caso de uso para obtener el status actual de un selector."""

from uuid import UUID

from application.dtos.device_control_dtos import SelectorStatusResponse
from infrastructure.persistence.repositories.selector_repository import SelectorRepository


class GetSelectorStatusUseCase:
    def __init__(self, selector_repository: SelectorRepository):
        self._selector_repo = selector_repository

    async def execute(self, selector_id: str) -> SelectorStatusResponse:
        selector = await self._selector_repo.find_by_id(UUID(selector_id))
        if not selector:
            raise ValueError(f"Selector {selector_id} no encontrado")

        return SelectorStatusResponse(
            selector_id=selector_id,
            current_slot=selector.current_slot,
        )
