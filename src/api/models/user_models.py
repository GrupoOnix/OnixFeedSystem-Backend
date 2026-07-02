"""Modelos de API para gestión de usuarios."""

from typing import List

from pydantic import BaseModel, Field

from application.dtos.auth_dtos import ListUsersResponse
from api.models.auth_models import UserResponseModel


class RegisterUserRequestModel(BaseModel):
    """Request para registrar un nuevo usuario."""

    username: str = Field(..., min_length=1, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    role: str = Field(default="user", pattern="^(user|admin)$")


class UpdateUserStatusRequestModel(BaseModel):
    """Request para activar/desactivar un usuario."""

    is_active: bool = Field(..., description="Nuevo estado del usuario")


class UpdateUserRoleRequestModel(BaseModel):
    """Request para cambiar el rol de un usuario."""

    role: str = Field(..., pattern="^(user|admin)$")


class ResetPasswordRequestModel(BaseModel):
    """Request para resetear la contraseña de un usuario."""

    new_password: str = Field(..., min_length=6, max_length=255)


class ListUsersResponseModel(BaseModel):
    """Response para listar usuarios."""

    users: List[UserResponseModel] = Field(..., description="Lista de usuarios")

    @staticmethod
    def from_dto(dto: ListUsersResponse) -> "ListUsersResponseModel":
        """Convierte un DTO de aplicación a modelo de API."""
        return ListUsersResponseModel(users=[UserResponseModel.from_dto(user) for user in dto.users])
