"""Caso de uso para encender/apagar doser."""

from uuid import UUID

from domain.dtos import DoserCommand
from domain.interfaces import IFeedingMachine
from infrastructure.persistence.repositories.doser_repository import DoserRepository


class TurnDoserOnUseCase:
    """Enciende el doser usando su tasa configurada."""

    def __init__(
        self,
        doser_repository: DoserRepository,
        machine_service: IFeedingMachine,
    ):
        self._doser_repo = doser_repository
        self._machine = machine_service

    async def execute(self, doser_id: str) -> None:
        """
        Enciende el doser a su tasa configurada.

        Args:
            doser_id: ID del doser

        Raises:
            ValueError: Si el doser no existe o no tiene un rate válido configurado
        """
        doser_uuid = UUID(doser_id)
        result = await self._doser_repo.find_by_id_with_context(doser_uuid)

        if not result:
            raise ValueError(f"Doser {doser_id} no encontrado")

        doser = result.doser

        # Encender el doser (valida que current_rate esté en rango)
        doser.turn_on()

        # Crear comando usando speed_percentage configurado por el operador
        command = DoserCommand(
            doser_id=str(doser_uuid),
            doser_name=str(doser.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            rate_percentage=float(doser.speed_percentage),
        )

        # Enviar comando al PLC
        await self._machine.set_doser_rate(command)

        # Persistir en DB
        await self._doser_repo.update(doser_uuid, doser)


class TurnDoserOffUseCase:
    """Apaga el doser manteniendo su configuración de rate."""

    def __init__(
        self,
        doser_repository: DoserRepository,
        machine_service: IFeedingMachine,
    ):
        self._doser_repo = doser_repository
        self._machine = machine_service

    async def execute(self, doser_id: str) -> None:
        """
        Apaga el doser.
        
        El current_rate configurado se mantiene guardado para cuando
        se vuelva a encender.

        Args:
            doser_id: ID del doser

        Raises:
            ValueError: Si el doser no existe
        """
        doser_uuid = UUID(doser_id)
        result = await self._doser_repo.find_by_id_with_context(doser_uuid)

        if not result:
            raise ValueError(f"Doser {doser_id} no encontrado")

        doser = result.doser

        # Apagar el doser (mantiene current_rate guardado)
        doser.stop()

        # Crear comando con rate 0% para el PLC
        command = DoserCommand(
            doser_id=str(doser_uuid),
            doser_name=str(doser.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            rate_percentage=0.0,
        )

        # Enviar comando al PLC
        await self._machine.set_doser_rate(command)

        # Persistir en DB
        await self._doser_repo.update(doser_uuid, doser)
