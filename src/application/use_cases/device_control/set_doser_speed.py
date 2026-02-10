"""Caso de uso para establecer la velocidad del motor del dosificador."""

from uuid import UUID

from domain.dtos import DoserCommand
from domain.interfaces import IFeedingMachine
from infrastructure.persistence.repositories.doser_repository import DoserRepository


class SetDoserSpeedUseCase:
    """
    Caso de uso para establecer la velocidad del motor del dosificador.

    Envía un porcentaje de velocidad directamente al PLC sin conversión.
    Útil para calibración, donde se necesita controlar la potencia del motor
    antes de encender el dosificador para un pulso de calibración.
    """

    def __init__(
        self,
        doser_repository: DoserRepository,
        machine_service: IFeedingMachine,
    ):
        self._doser_repo = doser_repository
        self._machine = machine_service

    async def execute(self, doser_id: str, speed_percentage: int) -> None:
        """
        Establece la velocidad del motor de un doser específico.

        Args:
            doser_id: ID del doser
            speed_percentage: Velocidad del motor (1-100%)

        Raises:
            ValueError: Si el doser no existe
        """
        doser_uuid = UUID(doser_id)

        result = await self._doser_repo.find_by_id_with_context(doser_uuid)
        if not result:
            raise ValueError(f"Doser {doser_id} no encontrado")

        doser = result.doser

        command = DoserCommand(
            doser_id=str(doser_uuid),
            doser_name=str(doser.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            rate_percentage=float(speed_percentage),
        )

        await self._machine.set_doser_rate(command)

        # Persistir el speed_percentage en el doser
        doser.speed_percentage = speed_percentage
        await self._doser_repo.update(doser_uuid, doser)
