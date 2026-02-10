"""Caso de uso para establecer la tasa de dosificación directamente."""

from uuid import UUID

from domain.dtos import DoserCommand
from domain.interfaces import IFeedingMachine
from domain.value_objects import DosingRate
from infrastructure.persistence.repositories.doser_repository import DoserRepository


class SetDoserRateUseCase:
    """
    Caso de uso para control directo del doser.

    Permite establecer la tasa de dosificación sin estar en una sesión de alimentación.
    Útil para pruebas, mantenimiento y control manual desde el frontend.
    """

    def __init__(
        self,
        doser_repository: DoserRepository,
        machine_service: IFeedingMachine,
    ):
        self._doser_repo = doser_repository
        self._machine = machine_service

    async def execute(self, doser_id: str, rate_kg_min: float) -> None:
        """
        Establece la tasa de dosificación de un doser específico.

        Args:
            doser_id: ID del doser
            rate_kg_min: Tasa de dosificación en kg/min

        Raises:
            ValueError: Si el doser no existe o la tasa está fuera de rango
        """
        # Convertir ID a UUID
        doser_uuid = UUID(doser_id)

        # Buscar doser con contexto
        result = await self._doser_repo.find_by_id_with_context(doser_uuid)
        if not result:
            raise ValueError(f"Doser {doser_id} no encontrado")

        doser = result.doser

        # Crear value object con validación
        rate = DosingRate(rate_kg_min)

        # Actualizar tasa del doser (valida que esté dentro del rango)
        doser.current_rate = rate

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

        # Guardar cambios en DB
        await self._doser_repo.update(doser_uuid, doser)
