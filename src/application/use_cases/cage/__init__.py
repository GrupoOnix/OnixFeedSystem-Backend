"""Use cases para el módulo de jaulas."""

from application.use_cases.cage.create_cage import CreateCageUseCase
from application.use_cases.cage.delete_cage import DeleteCageUseCase
from application.use_cases.cage.get_cage import GetCageUseCase
from application.use_cases.cage.get_population_history import (
    GetPopulationHistoryUseCase,
)
from application.use_cases.cage.list_biometry_use_case import ListBiometryUseCase
from application.use_cases.cage.list_cages import ListCagesUseCase
from application.use_cases.cage.list_config_changes_use_case import (
    ListConfigChangesUseCase,
)
from application.use_cases.cage.list_mortality_use_case import ListMortalityUseCase
from application.use_cases.cage.population import (
    AdjustPopulationUseCase,
    HarvestUseCase,
    RegisterMortalityUseCase,
    SetPopulationUseCase,
    UpdateBiometryUseCase,
)
from application.use_cases.cage.update_cage import UpdateCageUseCase
from application.use_cases.cage.update_cage_config import UpdateCageConfigUseCase

__all__ = [
    # CRUD
    "CreateCageUseCase",
    "GetCageUseCase",
    "ListCagesUseCase",
    "UpdateCageUseCase",
    "DeleteCageUseCase",
    # Configuración
    "UpdateCageConfigUseCase",
    # Población
    "SetPopulationUseCase",
    "RegisterMortalityUseCase",
    "UpdateBiometryUseCase",
    "HarvestUseCase",
    "AdjustPopulationUseCase",
    # Historial
    "GetPopulationHistoryUseCase",
    "ListBiometryUseCase",
    "ListMortalityUseCase",
    "ListConfigChangesUseCase",
]
