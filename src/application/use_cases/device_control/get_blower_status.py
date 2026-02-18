"""Caso de uso para obtener el status actual de un blower."""

from uuid import UUID

from application.dtos.device_control_dtos import BlowerStatusResponse
from infrastructure.persistence.repositories.blower_repository import BlowerRepository


class GetBlowerStatusUseCase:
    def __init__(self, blower_repository: BlowerRepository):
        self._blower_repo = blower_repository

    async def execute(self, blower_id: str) -> BlowerStatusResponse:
        blower = await self._blower_repo.find_by_id(UUID(blower_id))
        if not blower:
            raise ValueError(f"Blower {blower_id} no encontrado")

        return BlowerStatusResponse(
            blower_id=blower_id,
            is_running=blower.current_power.value > 0,
            current_power=blower.current_power.value,
        )
