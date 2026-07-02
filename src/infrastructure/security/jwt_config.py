"""Configuración de JWT para autenticación."""

import os


def _get_required_env(key: str) -> str:
    """Obtiene una variable de entorno requerida."""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Variable de entorno '{key}' no encontrada. Revisa tu archivo .env.")
    return value


JWT_SECRET_KEY = _get_required_env("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
