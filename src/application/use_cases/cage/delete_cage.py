"""Use case para eliminar una jaula."""

from domain.repositories import ICageRepository
from domain.value_objects.identifiers import CageId


class DeleteCageUseCase:
    """Caso de uso para eliminar una jaula."""

    def __init__(self, cage_repository: ICageRepository):
        self.cage_repository = cage_repository

    async def execute(self, cage_id: str) -> None:
        """
        Elimina una jaula.

        Args:
            cage_id: ID de la jaula a eliminar

        Raises:
            ValueError: Si la jaula no existe
        """
        cage_id_vo = CageId.from_string(cage_id)

        # Verificar que existe
        exists = await self.cage_repository.exists(cage_id_vo)
        if not exists:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Eliminar
        await self.cage_repository.delete(cage_id_vo)
