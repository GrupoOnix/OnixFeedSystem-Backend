"""
Mappers para convertir entre modelos de API (Pydantic) y DTOs de aplicación.

Estos mappers mantienen la separación de capas:
- API Layer (Pydantic) ← → Application Layer (DTOs)
"""

from .response_mapper import ResponseMapper

__all__ = ['ResponseMapper']
