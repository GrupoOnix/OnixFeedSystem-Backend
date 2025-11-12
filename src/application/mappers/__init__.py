"""
Mappers de la Capa de Aplicación

Responsables de convertir entre entidades de dominio y DTOs de aplicación.
"""

from .domain_to_dto_mapper import DomainToDTOMapper

__all__ = [
    'DomainToDTOMapper',
]
