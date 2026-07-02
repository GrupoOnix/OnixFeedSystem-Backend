"""Use case para cambiar la contraseña propia."""

from application.dtos.auth_dtos import ChangePasswordRequest
from domain.exceptions import InvalidCredentialsError
from domain.repositories import IUserRepository
from domain.value_objects.identifiers import UserId
from infrastructure.security.password_service import PasswordService


class ChangePasswordUseCase:
    """Caso de uso para que un usuario cambie su propia contraseña."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: PasswordService,
    ):
        self.user_repository = user_repository
        self.password_service = password_service

    async def execute(self, user_id: str, request: ChangePasswordRequest) -> None:
        """
        Cambia la contraseña del usuario autenticado.

        Args:
            user_id: ID del usuario autenticado
            request: Contraseña actual y nueva contraseña

        Raises:
            InvalidCredentialsError: Si la contraseña actual es incorrecta
            ValueError: Si el usuario no existe o la nueva contraseña es inválida
        """
        user = await self.user_repository.find_by_id(UserId.from_string(user_id))
        if user is None:
            raise ValueError("Usuario no encontrado")

        if not self.password_service.verify_password(request.current_password, user.hashed_password):
            raise InvalidCredentialsError("La contraseña actual es incorrecta")

        if not request.new_password or len(request.new_password) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres")

        new_hashed = self.password_service.hash_password(request.new_password)
        user.change_password(new_hashed)
        await self.user_repository.save(user)
