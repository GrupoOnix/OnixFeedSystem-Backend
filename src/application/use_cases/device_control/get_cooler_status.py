"""Caso de uso para obtener el status actual de un cooler."""

from uuid import UUID

from application.dtos.device_control_dtos import CoolerStatusResponse
from infrastructure.persistence.repositories.cooler_repository import CoolerRepository


class GetCoolerStatusUseCase:
    def __init__(self, cooler_repository: CoolerRepository):
        self._cooler_repo = cooler_repository

    async def execute(self, cooler_id: str) -> CoolerStatusResponse:
        cooler = await self._cooler_repo.find_by_id(UUID(cooler_id))
        if not cooler:
            raise ValueError(f"Cooler {cooler_id} no encontrado")

        return CoolerStatusResponse(
            cooler_id=cooler_id,
            is_on=cooler.is_on,
            current_power=cooler.cooling_power_percentage.value,
        )
