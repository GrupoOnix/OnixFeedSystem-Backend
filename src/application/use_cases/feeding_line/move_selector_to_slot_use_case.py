"""Caso de uso para mover el selector a un slot específico."""

from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import LineId


class MoveSelectorToSlotUseCase:
    """Caso de uso para mover el selector de una línea a un slot específico."""

    def __init__(self, feeding_line_repository: IFeedingLineRepository):
        self._feeding_line_repository = feeding_line_repository

    async def execute(self, line_id: str, slot_number: int) -> None:
        """
        Mueve el selector a un slot específico.

        Args:
            line_id: ID de la línea de alimentación
            slot_number: Número de slot destino (1 a capacity del selector)

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
            ValueError: Si el slot está fuera del rango válido
        """
        # Obtener línea
        feeding_line = await self._feeding_line_repository.find_by_id(LineId(line_id))

        if not feeding_line:
            raise FeedingLineNotFoundException(
                f"Línea de alimentación con ID {line_id} no encontrada"
            )

        # Mover selector (la validación se hace en el método del dominio)
        feeding_line.selector.move_to_slot(slot_number)

        # Persistir cambios
        await self._feeding_line_repository.save(feeding_line)
