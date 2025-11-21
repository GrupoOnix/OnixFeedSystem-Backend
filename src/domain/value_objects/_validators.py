"""
Funciones de validación compartidas para Value Objects.
"""
import re


def validate_name_format(value: str, field_name: str = "El nombre") -> None:
    """
    Función de validación interna reutilizable para todos los VOs de Nombres.
    
    Reglas:
    1. Debe ser un string.
    2. No puede estar vacío (después de quitar espacios).
    3. No puede exceder los 100 caracteres.
    4. Solo puede contener alfanuméricos, espacios, guiones (-) y guiones bajos (_).
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} debe ser una cadena")

    trimmed_value = value.strip()
    
    if len(trimmed_value) == 0:
        raise ValueError(f"{field_name} no puede estar vacío")
    
    if len(value) > 100:
        raise ValueError(f"{field_name} no debe exceder 100 caracteres (recibió {len(value)})")
    
    # ^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\s_-]+$
    # ^                              -> inicio del string
    # [a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\s_-] -> permite letras (con tildes), ñ, ü, números, espacios, guión bajo, guión
    # +                              -> uno o más de esos caracteres
    # $                              -> fin del string
    if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\s_-]+$', value):
        raise ValueError(
            f"{field_name} solo puede contener letras (incluyendo tildes y ñ), "
            f"números, espacios, guiones (-) y guiones bajos (_)"
        )
