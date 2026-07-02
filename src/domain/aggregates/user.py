"""Aggregate Root para Usuarios del Sistema."""

from datetime import datetime, timezone
from enum import Enum

from domain.value_objects.identifiers import UserId


class UserRole(str, Enum):
    """Roles disponibles para los usuarios del sistema."""

    USER = "user"
    ADMIN = "admin"


class User:
    """
    Aggregate Root que representa un usuario del sistema.

    Responsabilidades:
    - Identidad y credenciales del usuario
    - Rol y estado activo/inactivo
    - Flag de superadministrador
    """

    def __init__(
        self,
        username: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.USER,
        is_superadmin: bool = False,
        is_active: bool = True,
    ):
        """
        Crea un nuevo usuario.

        Args:
            username: Nombre de usuario único (legible)
            full_name: Nombre completo para mostrar en el frontend
            hashed_password: Hash de la contraseña
            role: Rol del usuario (user o admin)
            is_superadmin: Indica si tiene permisos de superadmin
            is_active: Indica si el usuario puede autenticarse

        Raises:
            ValueError: Si username o full_name están vacíos
        """
        if not username or not username.strip():
            raise ValueError("El username no puede estar vacío")
        if not full_name or not full_name.strip():
            raise ValueError("El nombre completo no puede estar vacío")
        if not hashed_password or not hashed_password.strip():
            raise ValueError("El hash de contraseña no puede estar vacío")

        self._id = UserId.generate()
        self._username = username.strip()
        self._full_name = full_name.strip()
        self._hashed_password = hashed_password
        self._role = role
        self._is_superadmin = is_superadmin
        self._is_active = is_active
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)

    # =========================================================================
    # PROPIEDADES DE IDENTIDAD
    # =========================================================================

    @property
    def id(self) -> UserId:
        """ID único del usuario."""
        return self._id

    @property
    def username(self) -> str:
        """Nombre de usuario único."""
        return self._username

    @property
    def full_name(self) -> str:
        """Nombre completo para mostrar."""
        return self._full_name

    @property
    def hashed_password(self) -> str:
        """Hash de la contraseña."""
        return self._hashed_password

    @property
    def role(self) -> UserRole:
        """Rol del usuario."""
        return self._role

    @property
    def is_superadmin(self) -> bool:
        """Indica si es superadministrador."""
        return self._is_superadmin

    @property
    def is_active(self) -> bool:
        """Indica si el usuario está activo."""
        return self._is_active

    @property
    def created_at(self) -> datetime:
        """Fecha de creación del usuario."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Fecha de última actualización del usuario."""
        return self._updated_at

    # =========================================================================
    # MÉTODOS DE DOMINIO
    # =========================================================================

    def change_password(self, new_hashed_password: str) -> None:
        """Actualiza el hash de contraseña del usuario."""
        if not new_hashed_password or not new_hashed_password.strip():
            raise ValueError("El hash de contraseña no puede estar vacío")
        self._hashed_password = new_hashed_password
        self._updated_at = datetime.now(timezone.utc)

    def update_role(self, role: UserRole) -> None:
        """Actualiza el rol del usuario."""
        self._role = role
        self._updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """Activa al usuario."""
        self._is_active = True
        self._updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Desactiva al usuario."""
        self._is_active = False
        self._updated_at = datetime.now(timezone.utc)

    def promote_to_superadmin(self) -> None:
        """Promueve al usuario a superadmin."""
        self._is_superadmin = True
        self._updated_at = datetime.now(timezone.utc)

    def demote_from_superadmin(self) -> None:
        """Quita los permisos de superadmin."""
        self._is_superadmin = False
        self._updated_at = datetime.now(timezone.utc)

    def is_admin(self) -> bool:
        """Indica si el usuario es admin o superadmin."""
        return self._role == UserRole.ADMIN or self._is_superadmin

    # =========================================================================
    # MÉTODOS DE RECONSTRUCCIÓN (para repositorio)
    # =========================================================================

    def _set_id(self, user_id: UserId) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._id = user_id

    def _set_created_at(self, created_at: datetime) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._created_at = created_at

    def _set_updated_at(self, updated_at: datetime) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._updated_at = updated_at

    # =========================================================================
    # FACTORY METHOD
    # =========================================================================

    @classmethod
    def create(
        cls,
        username: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.USER,
        is_superadmin: bool = False,
        is_active: bool = True,
    ) -> "User":
        """Factory method para crear un nuevo usuario."""
        return cls(
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            is_superadmin=is_superadmin,
            is_active=is_active,
        )

    @classmethod
    def reconstruct(
        cls,
        user_id: UserId,
        username: str,
        full_name: str,
        hashed_password: str,
        role: UserRole,
        is_superadmin: bool,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
    ) -> "User":
        """Reconstruye un usuario desde persistencia sin generar nuevo ID."""
        user = cls(
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            is_superadmin=is_superadmin,
            is_active=is_active,
        )
        user._set_id(user_id)
        user._set_created_at(created_at)
        user._set_updated_at(updated_at)
        return user
