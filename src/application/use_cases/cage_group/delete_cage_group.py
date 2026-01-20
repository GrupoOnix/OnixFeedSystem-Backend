"""Use case para eliminar un grupo de jaulas."""

from domain.repositories import ICageGroupRepository
from domain.value_objects.identifiers import CageGroupId


class DeleteCageGroupUseCase:
    """Caso de uso para eliminar un grupo de jaulas."""

    def __init__(self, group_repository: ICageGroupRepository):
        self.group_repository = group_repository

    async def execute(self, group_id: str) -> None:
        """
        Elimina un grupo de jaulas.

        Args:
            group_id: ID del grupo a eliminar

        Raises:
            ValueError: Si el grupo no existe

        Note:
            Esto es un hard delete (eliminación física).
            Las jaulas no se ven afectadas, solo se elimina la agrupación.
        """
        # 1. Buscar el grupo
        group_id_obj = CageGroupId.from_string(group_id)
        group = await self.group_repository.find_by_id(group_id_obj)

        if not group:
            raise ValueError(f"No existe un grupo con ID '{group_id}'")

        # 2. Eliminar
        await self.group_repository.delete(group_id_obj)
