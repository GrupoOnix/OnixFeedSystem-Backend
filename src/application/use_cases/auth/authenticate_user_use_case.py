"""Use case para autenticar un usuario."""

from application.dtos.auth_dtos import LoginRequest, LoginResponse, UserResponse
from domain.exceptions import InvalidCredentialsError, UserInactiveError
from domain.repositories import IUserRepository
from infrastructure.security.password_service import PasswordService
from infrastructure.security.token_service import TokenService


class AuthenticateUserUseCase:
    """Caso de uso para autenticar un usuario y emitir un token JWT."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ):
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service

    async def execute(self, request: LoginRequest) -> LoginResponse:
        """
        Autentica un usuario con username y password.

        Args:
            request: Credenciales de acceso

        Returns:
            LoginResponse con el token y datos del usuario

        Raises:
            InvalidCredentialsError: Si las credenciales son inválidas
            UserInactiveError: Si el usuario está desactivado
        """
        user = await self.user_repository.find_by_username(request.username)
        if user is None:
            raise InvalidCredentialsError("Credenciales inválidas")

        if not self.password_service.verify_password(request.password, user.hashed_password):
            raise InvalidCredentialsError("Credenciales inválidas")

        if not user.is_active:
            raise UserInactiveError("El usuario está desactivado")

        access_token = self.token_service.create_access_token(
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
            is_superadmin=user.is_superadmin,
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=self._to_response(user),
        )

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
