"""Use case para obtener el usuario actual desde un token JWT."""

from application.dtos.auth_dtos import UserResponse
from domain.exceptions import UserInactiveError, UserNotFoundException
from domain.repositories import IUserRepository
from domain.value_objects.identifiers import UserId
from infrastructure.security.token_service import TokenService


class GetCurrentUserUseCase:
    """Caso de uso para obtener el usuario autenticado a partir de un token."""

    def __init__(
        self,
        user_repository: IUserRepository,
        token_service: TokenService,
    ):
        self.user_repository = user_repository
        self.token_service = token_service

    async def execute(self, token: str) -> UserResponse:
        """
        Decodifica el token y devuelve los datos del usuario.

        Args:
            token: Token JWT de acceso

        Returns:
            UserResponse con los datos del usuario

        Raises:
            TokenExpiredError/TokenInvalidError: Si el token es inválido o expiró
            UserNotFoundException: Si el usuario no existe
            UserInactiveError: Si el usuario está desactivado
        """
        payload = self.token_service.decode_access_token(token)

        user = await self.user_repository.find_by_id(UserId.from_string(payload.user_id))
        if user is None:
            raise UserNotFoundException("Usuario no encontrado")

        if not user.is_active:
            raise UserInactiveError("El usuario está desactivado")

        return UserResponse(
            id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            is_superadmin=user.is_superadmin,
            is_active=user.is_active,
            must_change_password=user.must_change_password,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
