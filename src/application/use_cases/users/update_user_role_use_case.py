"""Use case para cambiar el rol de un usuario."""

from application.dtos.auth_dtos import UpdateUserRoleRequest, UserResponse
from domain.aggregates.user import UserRole
from domain.exceptions import InsufficientPermissionsError
from domain.repositories import IUserRepository
from domain.value_objects.identifiers import UserId


class UpdateUserRoleUseCase:
    """Caso de uso para cambiar el rol de un usuario."""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(
        self,
        user_id: str,
        request: UpdateUserRoleRequest,
        requester_id: str,
        requester_is_superadmin: bool,
    ) -> UserResponse:
        """
        Cambia el rol de un usuario.

        Args:
            user_id: ID del usuario a modificar
            request: Nuevo rol
            requester_id: ID del usuario que realiza la acción
            requester_is_superadmin: Indica si el solicitante es superadmin

        Returns:
            UserResponse con los datos actualizados del usuario

        Raises:
            ValueError: Si el usuario no existe o el rol es inválido
            InsufficientPermissionsError: Si no es superadmin o se intenta cambiar el propio rol
        """
        if not requester_is_superadmin:
            raise InsufficientPermissionsError("Solo un superadmin puede cambiar roles de usuario")

        if user_id == requester_id:
            raise InsufficientPermissionsError("No puedes cambiar tu propio rol")

        user = await self.user_repository.find_by_id(UserId.from_string(user_id))
        if user is None:
            raise ValueError("Usuario no encontrado")

        try:
            new_role = UserRole(request.role.lower())
        except ValueError as exc:
            raise ValueError(f"Rol inválido: '{request.role}'. Roles válidos: user, admin") from exc

        user.update_role(new_role)
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
