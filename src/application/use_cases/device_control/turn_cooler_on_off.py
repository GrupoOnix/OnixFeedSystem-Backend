"""Caso de uso para encender/apagar cooler."""

from uuid import UUID

from domain.dtos import CoolerCommand
from domain.interfaces import IFeedingMachine
from domain.value_objects import CoolerPowerPercentage
from infrastructure.persistence.repositories.cooler_repository import CoolerRepository


class TurnCoolerOnUseCase:
    """Enciende el cooler a su potencia configurada."""

    def __init__(
        self,
        cooler_repository: CoolerRepository,
        machine_service: IFeedingMachine,
    ):
        self._cooler_repo = cooler_repository
        self._machine = machine_service

    async def execute(self, cooler_id: str) -> None:
        """
        Enciende el cooler a su cooling_power_percentage configurada.

        Args:
            cooler_id: ID del cooler

        Raises:
            ValueError: Si el cooler no existe
        """
        cooler_uuid = UUID(cooler_id)
        result = await self._cooler_repo.find_by_id_with_context(cooler_uuid)

        if not result:
            raise ValueError(f"Cooler {cooler_id} no encontrado")

        cooler = result.cooler

        # Encender cooler
        cooler.turn_on()

        # Crear comando con contexto completo
        command = CoolerCommand(
            cooler_id=str(cooler_uuid),
            cooler_name=str(cooler.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            power_percentage=cooler.cooling_power_percentage.value,
        )

        # Enviar comando al PLC
        await self._machine.set_cooler_power(command)

        # Persistir en DB
        await self._cooler_repo.update(cooler_uuid, cooler)


class TurnCoolerOffUseCase:
    """Apaga el cooler (potencia a 0%)."""

    def __init__(
        self,
        cooler_repository: CoolerRepository,
        machine_service: IFeedingMachine,
    ):
        self._cooler_repo = cooler_repository
        self._machine = machine_service

    async def execute(self, cooler_id: str) -> None:
        """
        Apaga el cooler (potencia a 0%).

        Args:
            cooler_id: ID del cooler

        Raises:
            ValueError: Si el cooler no existe
        """
        cooler_uuid = UUID(cooler_id)
        result = await self._cooler_repo.find_by_id_with_context(cooler_uuid)

        if not result:
            raise ValueError(f"Cooler {cooler_id} no encontrado")

        cooler = result.cooler

        # Apagar cooler
        cooler.turn_off()
        cooler.cooling_power_percentage = CoolerPowerPercentage(0.0)

        # Crear comando con contexto completo
        command = CoolerCommand(
            cooler_id=str(cooler_uuid),
            cooler_name=str(cooler.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            power_percentage=0.0,
        )

        # Enviar comando al PLC
        await self._machine.set_cooler_power(command)

        # Persistir en DB
        await self._cooler_repo.update(cooler_uuid, cooler)
