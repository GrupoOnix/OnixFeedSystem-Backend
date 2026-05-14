"""Caso de uso para establecer la potencia del blower directamente."""

from uuid import UUID

from domain.dtos import BlowerCommand
from domain.interfaces import IFeedingMachine
from domain.value_objects import BlowerPowerPercentage
from infrastructure.persistence.repositories.blower_repository import BlowerRepository


class SetBlowerPowerUseCase:
    """
    Caso de uso para control directo del blower.

    Permite establecer la potencia del blower sin estar en una sesión de alimentación.
    Útil para pruebas, mantenimiento y control manual desde el frontend.
    """

    def __init__(
        self,
        blower_repository: BlowerRepository,
        machine_service: IFeedingMachine,
    ):
        self._blower_repo = blower_repository
        self._machine = machine_service

    async def execute(self, blower_id: str, power_percentage: float) -> None:
        """
        Establece la potencia de un blower específico.

        Args:
            blower_id: ID del blower
            power_percentage: Potencia a establecer (0-100%)

        Raises:
            ValueError: Si el blower no existe o la potencia está fuera de rango
        """
        # Convertir ID a UUID
        blower_uuid = UUID(blower_id)

        # Buscar blower con contexto
        result = await self._blower_repo.find_by_id_with_context(blower_uuid)
        if not result:
            raise ValueError(f"Blower {blower_id} no encontrado")

        blower = result.blower

        # Crear value object con validación
        power = BlowerPowerPercentage(power_percentage)

        # Actualizar potencia del blower
        blower.current_power = power

        # Crear comando con contexto completo
        command = BlowerCommand(
            blower_id=str(blower_uuid),
            blower_name=str(blower.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            power_percentage=power.value,
        )

        # Enviar comando al PLC
        await self._machine.set_blower_power(command)

        # Guardar cambios en DB
        await self._blower_repo.update(blower_uuid, blower)
