"""
Mappers para convertir entre modelos de API (Pydantic) y DTOs de aplicación.

Estos mappers mantienen la separación de capas:
- API Layer (Pydantic) ← → Application Layer (DTOs)
"""

from .system_layout_mapper import SystemLayoutMapper

__all__ = ['SystemLayoutMapper']
