"""Caso de uso para resetear el selector directamente."""

from uuid import UUID

from domain.dtos import SelectorCommand
from domain.interfaces import IFeedingMachine
from infrastructure.persistence.repositories.selector_repository import (
    SelectorRepository,
)


class ResetSelectorDirectUseCase:
    """
    Caso de uso para resetear la posición del selector.

    Permite resetear el selector a posición neutral (None) sin estar en una
    sesión de alimentación. Útil para pruebas, mantenimiento y control manual
    desde el frontend.
    """

    def __init__(
        self,
        selector_repository: SelectorRepository,
        machine_service: IFeedingMachine,
    ):
        self._selector_repo = selector_repository
        self._machine = machine_service

    async def execute(self, selector_id: str) -> None:
        """
        Resetea la posición de un selector específico a neutral.

        Args:
            selector_id: ID del selector

        Raises:
            ValueError: Si el selector no existe
        """
        # Convertir ID a UUID
        selector_uuid = UUID(selector_id)

        # Buscar selector con contexto
        result = await self._selector_repo.find_by_id_with_context(selector_uuid)
        if not result:
            raise ValueError(f"Selector {selector_id} no encontrado")

        selector = result.selector

        # Resetear selector
        selector.reset_position()

        # Crear comando con contexto completo (slot_number=None indica reset)
        command = SelectorCommand(
            selector_id=str(selector_uuid),
            selector_name=str(selector.name),
            line_id=str(result.line_id),
            line_name=result.line_name,
            slot_number=None,
        )

        # Enviar comando al PLC
        await self._machine.move_selector(command)

        # Guardar cambios en DB
        await self._selector_repo.update(selector_uuid, selector)
