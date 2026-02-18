"""Caso de uso para obtener el status actual de un doser."""

from uuid import UUID

from application.dtos.device_control_dtos import DoserStatusResponse
from infrastructure.persistence.repositories.doser_repository import DoserRepository


class GetDoserStatusUseCase:
    def __init__(self, doser_repository: DoserRepository):
        self._doser_repo = doser_repository

    async def execute(self, doser_id: str) -> DoserStatusResponse:
        doser = await self._doser_repo.find_by_id(UUID(doser_id))
        if not doser:
            raise ValueError(f"Doser {doser_id} no encontrado")

        return DoserStatusResponse(
            doser_id=doser_id,
            is_running=doser.is_on,
            current_rate_kg_min=doser.current_rate.value,
        )
