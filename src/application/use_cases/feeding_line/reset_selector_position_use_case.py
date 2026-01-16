"""Caso de uso para reiniciar la posición del selector."""

from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import LineId


class ResetSelectorPositionUseCase:
    """Caso de uso para reiniciar la posición del selector a neutral/home."""

    def __init__(self, feeding_line_repository: IFeedingLineRepository):
        self._feeding_line_repository = feeding_line_repository

    async def execute(self, line_id: str) -> None:
        """
        Reinicia la posición del selector a None (posición neutral/home).

        Esta operación se usa típicamente:
        - Al finalizar una sesión de alimentación
        - En caso de error o emergencia
        - Al inicializar el sistema

        Args:
            line_id: ID de la línea de alimentación

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
        """
        # Obtener línea
        feeding_line = await self._feeding_line_repository.find_by_id(LineId(line_id))

        if not feeding_line:
            raise FeedingLineNotFoundException(
                f"Línea de alimentación con ID {line_id} no encontrada"
            )

        # Reiniciar posición del selector
        feeding_line.selector.reset_position()

        # Persistir cambios
        await self._feeding_line_repository.save(feeding_line)
