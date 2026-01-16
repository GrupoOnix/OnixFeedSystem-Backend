"""Caso de uso para mover el selector directamente."""

from uuid import UUID

from domain.dtos import SelectorCommand
from domain.interfaces import IFeedingMachine
from infrastructure.persistence.repositories.selector_repository import (
    SelectorRepository,
)


class MoveSelectorToSlotDirectUseCase:
    """
    Caso de uso para control directo del selector.

    Permite mover el selector a un slot específico sin estar en una sesión
    de alimentación. Útil para pruebas, mantenimiento y control manual desde
    el frontend.
    """

    def __init__(
        self,
        selector_repository: SelectorRepository,
        machine_service: IFeedingMachine,
    ):
        self._selector_repo = selector_repository
        self._machine = machine_service

    async def execute(self, selector_id: str, slot_number: int) -> None:
        """
        Mueve un selector específico a un slot.

        Args:
            selector_id: ID del selector
            slot_number: Número de slot destino (1 a capacity)

        Raises:
            ValueError: Si el selector no existe o el slot está fuera de rango
        """
        # Convertir ID a UUID
        selector_uuid = UUID(selector_id)

        # Buscar selector con contexto
        result = await self._selector_repo.find_by_id_with_context(selector_uuid)
        if not result:
            raise ValueError(f"Selector {selector_id} no encontrado")

        selector = result.selector

        # Mover selector (incluye validación de rango)
        selector.move_to_slot(slot_number)

        # Crear comando con contexto completo
        command = SelectorCommand(
            selector_id=str(selector_uuid),
            selector_name=str(selector.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            slot_number=slot_number,
        )

        # Enviar comando al PLC
        await self._machine.move_selector(command)

        # Guardar cambios en DB
        await self._selector_repo.update(selector_uuid, selector)
