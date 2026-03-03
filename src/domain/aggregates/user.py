"""Aggregate Root: User."""

from datetime import datetime, timezone
from typing import Optional

from domain.value_objects.identifiers import UserId


class User:
    """
    Agregado raíz: User

    Representa un usuario del sistema. Implementación simple para demo.
    """

    def __init__(
        self,
        username: str,
        password_hash: str,
        password_salt: str,
        name: str,
        role: str = "admin",
        email: Optional[str] = None,
    ):
        self._validate_username(username)
        self._validate_name(name)
        self._validate_role(role)

        self._id: UserId = UserId.generate()
        self._username: str = username.strip().lower()
        self._password_hash: str = password_hash
        self._password_salt: str = password_salt
        self._name: str = name.strip()
        self._role: str = role
        self._email: Optional[str] = email.strip() if email else None
        self._created_at: datetime = datetime.now(timezone.utc)

    # ---- Validaciones ----

    @staticmethod
    def _validate_username(username: str) -> None:
        if not username or not username.strip():
            raise ValueError("El username no puede estar vacío")
        if len(username.strip()) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise ValueError("El nombre no puede estar vacío")

    @staticmethod
    def _validate_role(role: str) -> None:
        valid_roles = ("admin", "operator", "viewer")
        if role not in valid_roles:
            raise ValueError(f"Rol inválido: '{role}'. Valores permitidos: {', '.join(valid_roles)}")

    # ---- Properties ----

    @property
    def id(self) -> UserId:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def password_salt(self) -> str:
        return self._password_salt

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> str:
        return self._role

    @property
    def email(self) -> Optional[str]:
        return self._email

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ---- Setters internos para reconstrucción desde persistencia ----

    def _set_id(self, user_id: UserId) -> None:
        self._id = user_id

    def _set_created_at(self, created_at: datetime) -> None:
        self._created_at = created_at

    def __repr__(self) -> str:
        return f"User(id={self._id}, username={self._username}, name={self._name}, role={self._role})"
