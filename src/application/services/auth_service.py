"""Servicio de autenticación: JWT y hashing de contraseñas."""

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt


# Configuración por defecto (se puede overridear via env vars)
JWT_SECRET = os.getenv("JWT_SECRET", "onix-demo-secret-key-2026")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_ALGORITHM = "HS256"


class AuthService:
    """Servicio de autenticación simple para demo."""

    # ---- Password hashing (SHA256 + salt) ----

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Genera hash SHA256 con salt para una contraseña.

        Returns:
            Tupla (password_hash, salt)
        """
        if salt is None:
            salt = os.urandom(32).hex()
        salted = f"{salt}{password}"
        password_hash = hashlib.sha256(salted.encode("utf-8")).hexdigest()
        return password_hash, salt

    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verifica una contraseña contra su hash y salt."""
        computed_hash, _ = AuthService.hash_password(password, salt)
        return computed_hash == password_hash

    # ---- JWT ----

    @staticmethod
    def create_token(user_id: str, username: str) -> str:
        """
        Crea un JWT token.

        Returns:
            Token JWT como string
        """
        payload = {
            "sub": user_id,
            "username": username,
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[dict[str, Any]]:
        """
        Decodifica y valida un JWT token.

        Returns:
            Payload del token si es válido, None si es inválido o expirado
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def get_expiration_seconds() -> int:
        """Retorna los segundos de expiración del token."""
        return JWT_EXPIRATION_HOURS * 3600
