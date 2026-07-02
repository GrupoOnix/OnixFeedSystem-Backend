"""Servicio de creación y decodificación de tokens JWT."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from infrastructure.security.jwt_config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)


class TokenError(Exception):
    """Error genérico relacionado con tokens JWT."""

    pass


class TokenExpiredError(TokenError):
    """El token ha expirado."""

    pass


class TokenInvalidError(TokenError):
    """El token es inválido."""

    pass


@dataclass(frozen=True)
class TokenPayload:
    """Payload decodificado de un token JWT."""

    user_id: str
    username: str
    role: str
    is_superadmin: bool


class TokenService:
    """Servicio para crear y validar tokens JWT de acceso."""

    @staticmethod
    def create_access_token(
        user_id: str,
        username: str,
        role: str,
        is_superadmin: bool,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Crea un token JWT de acceso."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = datetime.now(timezone.utc) + expires_delta
        payload: dict[str, Any] = {
            "sub": user_id,
            "username": username,
            "role": role,
            "is_superadmin": is_superadmin,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }

        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> TokenPayload:
        """Decodifica y valida un token JWT de acceso."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("El token ha expirado") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError("El token es inválido") from exc

        if payload.get("type") != "access":
            raise TokenInvalidError("El token no es de acceso")

        return TokenPayload(
            user_id=payload["sub"],
            username=payload["username"],
            role=payload["role"],
            is_superadmin=payload["is_superadmin"],
        )
