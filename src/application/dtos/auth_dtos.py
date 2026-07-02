"""DTOs para el módulo de autenticación y gestión de usuarios."""

from dataclasses import dataclass
from datetime import datetime
from typing import List


# =============================================================================
# REQUEST DTOs
# =============================================================================


@dataclass
class LoginRequest:
    """Request para iniciar sesión."""

    username: str
    password: str


@dataclass
class RegisterUserRequest:
    """Request para registrar un nuevo usuario."""

    username: str
    full_name: str
    password: str
    role: str = "user"


@dataclass
class ChangePasswordRequest:
    """Request para cambiar la contraseña propia."""

    current_password: str
    new_password: str


@dataclass
class ResetPasswordRequest:
    """Request para resetear la contraseña de un usuario."""

    new_password: str


@dataclass
class UpdateUserStatusRequest:
    """Request para activar/desactivar un usuario."""

    is_active: bool


@dataclass
class UpdateUserRoleRequest:
    """Request para cambiar el rol de un usuario."""

    role: str


# =============================================================================
# RESPONSE DTOs
# =============================================================================


@dataclass
class UserResponse:
    """Response con los datos públicos de un usuario."""

    id: str
    username: str
    full_name: str
    role: str
    is_superadmin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class LoginResponse:
    """Response de inicio de sesión exitoso."""

    access_token: str
    token_type: str
    user: UserResponse


@dataclass
class ListUsersResponse:
    """Response para listar usuarios."""

    users: List[UserResponse]
