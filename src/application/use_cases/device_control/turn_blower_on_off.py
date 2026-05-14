"""Caso de uso para encender/apagar blower."""

from uuid import UUID

from domain.dtos import BlowerCommand
from domain.interfaces import IFeedingMachine
from domain.value_objects import BlowerPowerPercentage
from infrastructure.persistence.repositories.blower_repository import BlowerRepository


class TurnBlowerOnUseCase:
    """Enciende el blower a su potencia configurada."""

    def __init__(
        self,
        blower_repository: BlowerRepository,
        machine_service: IFeedingMachine,
    ):
        self._blower_repo = blower_repository
        self._machine = machine_service

    async def execute(self, blower_id: str) -> None:
        """
        Enciende el blower a su potencia non_feeding_power.

        Args:
            blower_id: ID del blower

        Raises:
            ValueError: Si el blower no existe
        """
        blower_uuid = UUID(blower_id)
        result = await self._blower_repo.find_by_id_with_context(blower_uuid)

        if not result:
            raise ValueError(f"Blower {blower_id} no encontrado")

        blower = result.blower

        # Encender a la potencia configurada
        blower.current_power = blower.non_feeding_power

        # Crear comando con contexto completo
        command = BlowerCommand(
            blower_id=str(blower_uuid),
            blower_name=str(blower.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            power_percentage=blower.current_power.value,
        )

        # Enviar comando al PLC
        await self._machine.set_blower_power(command)

        # Persistir en DB
        await self._blower_repo.update(blower_uuid, blower)


class TurnBlowerOffUseCase:
    """Apaga el blower (potencia a 0%)."""

    def __init__(
        self,
        blower_repository: BlowerRepository,
        machine_service: IFeedingMachine,
    ):
        self._blower_repo = blower_repository
        self._machine = machine_service

    async def execute(self, blower_id: str) -> None:
        """
        Apaga el blower (potencia a 0%).

        Args:
            blower_id: ID del blower

        Raises:
            ValueError: Si el blower no existe
        """
        blower_uuid = UUID(blower_id)
        result = await self._blower_repo.find_by_id_with_context(blower_uuid)

        if not result:
            raise ValueError(f"Blower {blower_id} no encontrado")

        blower = result.blower

        # Apagar (potencia a 0)
        blower.current_power = BlowerPowerPercentage(0.0)

        # Crear comando con contexto completo
        command = BlowerCommand(
            blower_id=str(blower_uuid),
            blower_name=str(blower.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            power_percentage=0.0,
        )

        # Enviar comando al PLC
        await self._machine.set_blower_power(command)

        # Persistir en DB
        await self._blower_repo.update(blower_uuid, blower)
