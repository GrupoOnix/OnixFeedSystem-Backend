"""Modelos de request/response para endpoints de autenticación."""

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request para login."""

    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario")
    password: str = Field(..., min_length=1, max_length=128, description="Contraseña")


class UserResponse(BaseModel):
    """Datos públicos del usuario."""

    id: str = Field(..., description="ID del usuario")
    username: str = Field(..., description="Nombre de usuario")
    name: str = Field(..., description="Nombre completo")
    role: str = Field(..., description="Rol del usuario")
    email: Optional[str] = Field(None, description="Email del usuario")


class RegisterRequest(BaseModel):
    """Request para registro de usuario."""

    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario")
    password: str = Field(..., min_length=6, max_length=128, description="Contraseña")
    name: str = Field(..., min_length=1, max_length=100, description="Nombre completo")
    role: str = Field(default="admin", description="Rol del usuario (admin, operator, viewer)")
    email: Optional[str] = Field(None, description="Email del usuario")


class LoginResponse(BaseModel):
    """Response del login exitoso."""

    access_token: str = Field(..., description="JWT token")
    token_type: str = Field(default="bearer", description="Tipo de token")
    user: UserResponse = Field(..., description="Datos del usuario")
    expires_in: int = Field(..., description="Segundos hasta expiración del token")
