"""Servicio de hashing y verificación de contraseñas con bcrypt."""

import bcrypt


class PasswordService:
    """Servicio para hashear y verificar contraseñas usando bcrypt."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash bcrypt para la contraseña dada."""
        password_bytes = password.encode("utf-8")
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verifica una contraseña contra un hash bcrypt."""
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
