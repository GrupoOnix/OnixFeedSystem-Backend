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

        # Calcular porcentaje para el PLC basado en el rate configurado
        rate_percentage = self._calculate_rate_percentage(doser)

        # Crear comando con contexto completo
        command = DoserCommand(
            doser_id=str(doser_uuid),
            doser_name=str(doser.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            rate_percentage=rate_percentage,
        )

        # Enviar comando al PLC
        await self._machine.set_doser_rate(command)

        # Persistir en DB
        await self._doser_repo.update(doser_uuid, doser)

    def _calculate_rate_percentage(self, doser) -> float:
        """Calcula el porcentaje de velocidad basado en el rango del doser."""
        dosing_range = doser.dosing_range
        current_rate = doser.current_rate.value

        if dosing_range.max_rate == dosing_range.min_rate:
            return 100.0 if current_rate > 0 else 0.0

        # Mapear de kg/min a porcentaje (0-100%)
        range_span = dosing_range.max_rate - dosing_range.min_rate
        rate_in_range = current_rate - dosing_range.min_rate
        percentage = (rate_in_range / range_span) * 100.0

        # Asegurar que esté en rango válido
        return max(0.0, min(100.0, percentage))


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
