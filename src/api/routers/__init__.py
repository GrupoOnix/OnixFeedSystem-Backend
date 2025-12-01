"""
Routers de la API REST.

Organización:
- system_layout: UC-01 (Sincronización del layout completo del sistema)
- cages: Gestión de jaulas (queries y commands)

Futuros routers:
- feeding_lines: CRUD de líneas de alimentación
- silos: CRUD de silos
- feeding_operations: Operaciones de alimentación (UC-02, UC-03)
"""

from fastapi import APIRouter
from . import system_layout, cage_router, feeding_router

# Router principal que agrupa todos los sub-routers
api_router = APIRouter(prefix="/api")

# Registrar routers por funcionalidad
api_router.include_router(system_layout.router)
api_router.include_router(cage_router.router)
api_router.include_router(feeding_router.router)

__all__ = ['api_router']
