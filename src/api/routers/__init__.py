"""
Routers de la API REST.

Organización:
- system_layout: UC-01 (Sincronización del layout completo del sistema)
- cages: Gestión de jaulas (queries y commands)
- silos: CRUD de silos
- foods: CRUD de alimentos
- feeding_lines: Gestión de líneas de alimentación (listado y consulta)
- feeding: Operaciones de alimentación (UC-02, UC-03)
- sensor: Lecturas en tiempo real de sensores
- alerts: Sistema de alertas y alertas programadas
"""

from fastapi import APIRouter

from . import (
    alerts_router,
    cage_group_router,
    cage_router,
    device_control_router,
    feeding_line_router,
    feeding_router,
    food_router,
    sensor_router,
    silo_router,
    system_config_router,
    system_layout,
)

# Router principal que agrupa todos los sub-routers
api_router = APIRouter(prefix="/api")

# Registrar routers por funcionalidad
api_router.include_router(system_layout.router)
api_router.include_router(system_config_router.router)
api_router.include_router(cage_router.router)
api_router.include_router(cage_group_router.router)
api_router.include_router(silo_router.router)
api_router.include_router(food_router.router)
api_router.include_router(feeding_line_router.router)
api_router.include_router(feeding_router.router)
api_router.include_router(sensor_router.router)
api_router.include_router(device_control_router.router)
api_router.include_router(alerts_router.router)

__all__ = ["api_router"]
