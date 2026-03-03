"""Caso de uso: Registro de nuevo usuario."""

from application.services.auth_service import AuthService
from domain.aggregates.user import User
from domain.repositories import IUserRepository


class RegisterUserUseCase:
    """Caso de uso para registrar un nuevo usuario en el sistema."""

    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def execute(
        self,
        username: str,
        password: str,
        name: str,
        role: str = "admin",
        email: str | None = None,
    ) -> User:
        """
        Registra un nuevo usuario.

        Raises:
            ValueError: Si el username ya existe o los datos son inválidos
        """
        # Verificar que el username no esté en uso
        existing = await self._user_repository.find_by_username(username.strip().lower())
        if existing is not None:
            raise ValueError(f"El username '{username}' ya está en uso")

        # Hashear la contraseña
        password_hash, salt = AuthService.hash_password(password)

        # Crear el aggregate
        user = User(
            username=username,
            password_hash=password_hash,
            password_salt=salt,
            name=name,
            role=role,
            email=email,
        )

        # Persistir
        await self._user_repository.save(user)

        return user
