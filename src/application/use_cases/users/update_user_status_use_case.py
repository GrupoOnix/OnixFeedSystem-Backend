"""Use case para activar o desactivar un usuario."""

from application.dtos.auth_dtos import UpdateUserStatusRequest, UserResponse
from domain.exceptions import InsufficientPermissionsError
from domain.repositories import IUserRepository
from domain.value_objects.identifiers import UserId


class UpdateUserStatusUseCase:
    """Caso de uso para cambiar el estado activo/inactivo de un usuario."""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(
        self,
        user_id: str,
        request: UpdateUserStatusRequest,
        requester_id: str,
        requester_is_superadmin: bool,
        requester_is_admin: bool,
    ) -> UserResponse:
        """
        Activa o desactiva un usuario.

        Args:
            user_id: ID del usuario a modificar
            request: Nuevo estado
            requester_id: ID del usuario que realiza la acción
            requester_is_superadmin: Indica si el solicitante es superadmin
            requester_is_admin: Indica si el solicitante es admin

        Returns:
            UserResponse con los datos actualizados del usuario

        Raises:
            ValueError: Si el usuario no existe
            InsufficientPermissionsError: Si no tiene permisos para modificar al usuario
        """
        if user_id == requester_id:
            raise InsufficientPermissionsError("No puedes cambiar tu propio estado")

        user = await self.user_repository.find_by_id(UserId.from_string(user_id))
        if user is None:
            raise ValueError("Usuario no encontrado")

        target_is_admin_or_super = user.role.value == "admin" or user.is_superadmin

        if target_is_admin_or_super and not requester_is_superadmin:
            raise InsufficientPermissionsError("Solo un superadmin puede modificar el estado de admins o superadmins")

        if not requester_is_superadmin and not requester_is_admin:
            raise InsufficientPermissionsError("No tienes permisos para modificar usuarios")

        if request.is_active:
            user.activate()
        else:
            user.deactivate()

        await self.user_repository.save(user)
        return self._to_response(user)

    def _to_response(self, user) -> UserResponse:
        """Convierte un usuario a response DTO."""
        return UserResponse(
            id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            is_superadmin=user.is_superadmin,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
