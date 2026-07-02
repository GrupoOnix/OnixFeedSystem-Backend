"""Modelos de API para autenticación."""

from datetime import datetime

from pydantic import BaseModel, Field

from application.dtos.auth_dtos import LoginResponse, UserResponse


class UserResponseModel(BaseModel):
    """Modelo de respuesta con los datos públicos de un usuario."""

    id: str = Field(..., description="ID único del usuario (UUID)")
    username: str = Field(..., description="Nombre de usuario único")
    full_name: str = Field(..., description="Nombre completo para mostrar")
    role: str = Field(..., description="Rol del usuario: user o admin")
    is_superadmin: bool = Field(..., description="Indica si es superadmin")
    is_active: bool = Field(..., description="Indica si el usuario está activo")
    created_at: datetime = Field(..., description="Fecha de creación (UTC)")
    updated_at: datetime = Field(..., description="Fecha de última actualización (UTC)")

    @staticmethod
    def from_dto(dto: UserResponse) -> "UserResponseModel":
        """Convierte un DTO de aplicación a modelo de API."""
        return UserResponseModel(
            id=dto.id,
            username=dto.username,
            full_name=dto.full_name,
            role=dto.role,
            is_superadmin=dto.is_superadmin,
            is_active=dto.is_active,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class LoginRequestModel(BaseModel):
    """Request para iniciar sesión con username y password."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=255)


class LoginResponseModel(BaseModel):
    """Response de inicio de sesión exitoso."""

    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(..., description="Tipo de token (bearer)")
    user: UserResponseModel = Field(..., description="Datos del usuario autenticado")

    @staticmethod
    def from_dto(dto: LoginResponse) -> "LoginResponseModel":
        """Convierte un DTO de aplicación a modelo de API."""
        return LoginResponseModel(
            access_token=dto.access_token,
            token_type=dto.token_type,
            user=UserResponseModel.from_dto(dto.user),
        )


class ChangePasswordRequestModel(BaseModel):
    """Request para cambiar la contraseña propia."""

    current_password: str = Field(..., min_length=1, max_length=255)
    new_password: str = Field(..., min_length=6, max_length=255)
