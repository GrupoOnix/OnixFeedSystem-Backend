"""Caso de uso para establecer la potencia del cooler directamente."""

from uuid import UUID

from domain.dtos import CoolerCommand
from domain.interfaces import IFeedingMachine
from domain.value_objects import CoolerPowerPercentage
from infrastructure.persistence.repositories.cooler_repository import CoolerRepository


class SetCoolerPowerUseCase:
    """
    Caso de uso para control directo del cooler.

    Permite establecer la potencia del cooler sin estar en una sesión de alimentación.
    Útil para pruebas, mantenimiento y control manual desde el frontend.
    """

    def __init__(
        self,
        cooler_repository: CoolerRepository,
        machine_service: IFeedingMachine,
    ):
        self._cooler_repo = cooler_repository
        self._machine = machine_service

    async def execute(self, cooler_id: str, power_percentage: float) -> None:
        """
        Establece la potencia de un cooler específico.

        Args:
            cooler_id: ID del cooler
            power_percentage: Potencia a establecer (0-100%)

        Raises:
            ValueError: Si el cooler no existe o la potencia está fuera de rango
        """
        # Convertir ID a UUID
        cooler_uuid = UUID(cooler_id)

        # Buscar cooler con contexto
        result = await self._cooler_repo.find_by_id_with_context(cooler_uuid)
        if not result:
            raise ValueError(f"Cooler {cooler_id} no encontrado")

        cooler = result.cooler

        # Crear value object con validación
        power = CoolerPowerPercentage(power_percentage)

        # Actualizar potencia del cooler
        cooler.cooling_power_percentage = power

        # Actualizar estado on/off según potencia
        if power_percentage > 0:
            cooler.turn_on()
        else:
            cooler.turn_off()

        # Crear comando con contexto completo
        command = CoolerCommand(
            cooler_id=str(cooler_uuid),
            cooler_name=str(cooler.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            power_percentage=power.value,
        )

        # Enviar comando al PLC
        await self._machine.set_cooler_power(command)

        # Guardar cambios en DB
        await self._cooler_repo.update(cooler_uuid, cooler)
