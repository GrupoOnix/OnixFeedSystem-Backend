"""Use case para registrar un nuevo usuario."""

from application.dtos.auth_dtos import RegisterUserRequest, UserResponse
from domain.aggregates.user import User, UserRole
from domain.exceptions import InsufficientPermissionsError, UserAlreadyExistsError
from domain.repositories import IUserRepository
from infrastructure.security.password_service import PasswordService


class RegisterUserUseCase:
    """Caso de uso para registrar un nuevo usuario."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: PasswordService,
    ):
        self.user_repository = user_repository
        self.password_service = password_service

    async def execute(
        self,
        request: RegisterUserRequest,
        creator_is_superadmin: bool = False,
    ) -> UserResponse:
        """
        Crea un nuevo usuario.

        Args:
            request: Datos del usuario a crear
            creator_is_superadmin: Indica si el creador es superadmin

        Returns:
            UserResponse con los datos del usuario creado

        Raises:
            UserAlreadyExistsError: Si el username ya existe
            InsufficientPermissionsError: Si se intenta crear un admin sin ser superadmin
            ValueError: Si el rol es inválido
        """
        role = self._parse_role(request.role)

        if role == UserRole.ADMIN and not creator_is_superadmin:
            raise InsufficientPermissionsError("Solo un superadmin puede crear usuarios admin")

        if await self.user_repository.exists_by_username(request.username):
            raise UserAlreadyExistsError(f"Ya existe un usuario con el username '{request.username}'")

        hashed_password = self.password_service.hash_password(request.password)
        user = User.create(
            username=request.username,
            full_name=request.full_name,
            hashed_password=hashed_password,
            role=role,
        )

        await self.user_repository.save(user)
        return self._to_response(user)

    def _parse_role(self, role: str) -> UserRole:
        """Parsea y valida el rol solicitado."""
        try:
            return UserRole(role.lower())
        except ValueError as exc:
            raise ValueError(f"Rol inválido: '{role}'. Roles válidos: user, admin") from exc

    def _to_response(self, user: User) -> UserResponse:
        """Convierte un usuario a response DTO."""
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
