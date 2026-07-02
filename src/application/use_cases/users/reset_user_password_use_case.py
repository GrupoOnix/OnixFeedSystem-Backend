"""Use case para resetear la contraseña de un usuario."""

from application.dtos.auth_dtos import ResetPasswordRequest, UserResponse
from domain.exceptions import InsufficientPermissionsError
from domain.repositories import IUserRepository
from domain.value_objects.identifiers import UserId
from infrastructure.security.password_service import PasswordService


class ResetUserPasswordUseCase:
    """Caso de uso para que un superadmin resetee la contraseña de cualquier usuario."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: PasswordService,
    ):
        self.user_repository = user_repository
        self.password_service = password_service

    async def execute(
        self,
        user_id: str,
        request: ResetPasswordRequest,
        requester_id: str,
        requester_is_superadmin: bool,
    ) -> UserResponse:
        """
        Resetea la contraseña de un usuario.

        Args:
            user_id: ID del usuario a modificar
            request: Nueva contraseña
            requester_id: ID del usuario que realiza la acción
            requester_is_superadmin: Indica si el solicitante es superadmin

        Returns:
            UserResponse con los datos actualizados del usuario

        Raises:
            ValueError: Si el usuario no existe o la contraseña es inválida
            InsufficientPermissionsError: Si no es superadmin o se intenta resetear la propia contraseña
        """
        if not requester_is_superadmin:
            raise InsufficientPermissionsError("Solo un superadmin puede resetear contraseñas")

        if user_id == requester_id:
            raise InsufficientPermissionsError(
                "No puedes resetear tu propia contraseña desde aquí; usa cambiar contraseña"
            )

        user = await self.user_repository.find_by_id(UserId.from_string(user_id))
        if user is None:
            raise ValueError("Usuario no encontrado")

        if not request.new_password or len(request.new_password) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres")

        new_hashed = self.password_service.hash_password(request.new_password)
        user.change_password(new_hashed)
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
