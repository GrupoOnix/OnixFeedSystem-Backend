"""Use case para resetear la contraseña de un usuario."""

import random

from application.dtos.auth_dtos import ResetPasswordRequest, ResetPasswordResponse
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
    ) -> ResetPasswordResponse:
        """
        Resetea la contraseña de un usuario generando una contraseña temporal.

        Args:
            user_id: ID del usuario a modificar
            request: Request vacío (el backend genera la contraseña)
            requester_id: ID del usuario que realiza la acción
            requester_is_superadmin: Indica si el solicitante es superadmin

        Returns:
            ResetPasswordResponse con los datos actualizados del usuario y la contraseña temporal

        Raises:
            ValueError: Si el usuario no existe
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

        temporary_password = self._generate_temporary_password()
        new_hashed = self.password_service.hash_password(temporary_password)
        user.force_password_change(new_hashed)
        await self.user_repository.save(user)
        return self._to_response(user, temporary_password)

    def _generate_temporary_password(self) -> str:
        """Genera una contraseña temporal numérica de 6 dígitos."""
        return str(random.randint(100000, 999999))

    def _to_response(self, user, temporary_password: str) -> ResetPasswordResponse:
        """Convierte un usuario a response DTO incluyendo la contraseña temporal."""
        return ResetPasswordResponse(
            id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            is_superadmin=user.is_superadmin,
            is_active=user.is_active,
            must_change_password=user.must_change_password,
            created_at=user.created_at,
            updated_at=user.updated_at,
            temporary_password=temporary_password,
        )
