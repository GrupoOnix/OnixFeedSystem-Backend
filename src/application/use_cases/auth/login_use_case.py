"""Caso de uso: Login de usuario."""

from typing import Optional

from application.services.auth_service import AuthService
from domain.aggregates.user import User
from domain.repositories import IUserRepository


class LoginResult:
    """Resultado del login."""

    def __init__(self, user: User, access_token: str, expires_in: int):
        self.user = user
        self.access_token = access_token
        self.expires_in = expires_in


class LoginUseCase:
    """Caso de uso para autenticar un usuario."""

    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def execute(self, username: str, password: str) -> Optional[LoginResult]:
        """
        Autentica un usuario con username y password.

        Returns:
            LoginResult si las credenciales son válidas, None si no lo son
        """
        user = await self._user_repository.find_by_username(username)
        if not user:
            return None

        if not AuthService.verify_password(password, user.password_hash, user.password_salt):
            return None

        token = AuthService.create_token(
            user_id=str(user.id),
            username=user.username,
        )

        return LoginResult(
            user=user,
            access_token=token,
            expires_in=AuthService.get_expiration_seconds(),
        )
