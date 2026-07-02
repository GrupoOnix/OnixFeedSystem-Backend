"""Use case para eliminar un grupo de jaulas."""

from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.repositories import ICageGroupActivityLogRepository, ICageGroupRepository
from domain.value_objects import CageGroupActivityLogEntry
from domain.value_objects.identifiers import CageGroupId


class DeleteCageGroupUseCase:
    """Caso de uso para eliminar un grupo de jaulas."""

    def __init__(
        self,
        group_repository: ICageGroupRepository,
        activity_log_repository: ICageGroupActivityLogRepository,
    ):
        self.group_repository = group_repository
        self.activity_log_repository = activity_log_repository

    async def execute(self, group_id: str, actor: str) -> None:
        """
        Elimina un grupo de jaulas.

        Args:
            group_id: ID del grupo a eliminar
            actor: Usuario que realiza la acción

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

        # 2. Registrar actividad antes de eliminar
        await self.activity_log_repository.save(
            CageGroupActivityLogEntry.create(
                cage_group_id=group.id,
                event_type=ActivityLogEventType.INFO,
                category=ActivityLogCategory.CONFIG,
                message="Grupo de jaulas eliminado",
                details=f"Nombre: {group.name}",
                actor=actor,
            )
        )

        # 3. Eliminar
        await self.group_repository.delete(group_id_obj)
