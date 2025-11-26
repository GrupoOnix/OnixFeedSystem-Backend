"""Sistema de inyección de dependencias para FastAPI."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.database import get_session
from infrastructure.persistence.repositories import (
    SiloRepository,
    CageRepository,
    FeedingLineRepository
)
from infrastructure.persistence.repositories.biometry_log_repository import BiometryLogRepository
from infrastructure.persistence.repositories.mortality_log_repository import MortalityLogRepository
from infrastructure.persistence.repositories.config_change_log_repository import ConfigChangeLogRepository
from application.use_cases import (
    SyncSystemLayoutUseCase,
    GetSystemLayoutUseCase
)
from application.use_cases.cage import ListCagesUseCase
from application.use_cases.cage.register_biometry_use_case import RegisterBiometryUseCase
from application.use_cases.cage.list_biometry_use_case import ListBiometryUseCase
from application.use_cases.cage.register_mortality_use_case import RegisterMortalityUseCase
from application.use_cases.cage.list_mortality_use_case import ListMortalityUseCase
from application.use_cases.cage.update_cage_config_use_case import UpdateCageConfigUseCase
from application.use_cases.cage.list_config_changes_use_case import ListConfigChangesUseCase
from domain.factories import ComponentFactory


# ============================================================================
# Dependencias de Repositorios
# ============================================================================

async def get_silo_repo(
    session: AsyncSession = Depends(get_session)
) -> SiloRepository:
    return SiloRepository(session)


async def get_cage_repo(
    session: AsyncSession = Depends(get_session)
) -> CageRepository:
    return CageRepository(session)


async def get_line_repo(
    session: AsyncSession = Depends(get_session)
) -> FeedingLineRepository:
    return FeedingLineRepository(session)


async def get_biometry_log_repo(
    session: AsyncSession = Depends(get_session)
) -> BiometryLogRepository:
    return BiometryLogRepository(session)


async def get_mortality_log_repo(
    session: AsyncSession = Depends(get_session)
) -> MortalityLogRepository:
    return MortalityLogRepository(session)


async def get_config_change_log_repo(
    session: AsyncSession = Depends(get_session)
) -> ConfigChangeLogRepository:
    return ConfigChangeLogRepository(session)


def get_component_factory() -> ComponentFactory:
    return ComponentFactory()


# ============================================================================
# Dependencias de Casos de Uso
# ============================================================================

async def get_sync_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    silo_repo: SiloRepository = Depends(get_silo_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    factory: ComponentFactory = Depends(get_component_factory)
) -> SyncSystemLayoutUseCase:
    return SyncSystemLayoutUseCase(
        line_repo=line_repo,
        silo_repo=silo_repo,
        cage_repo=cage_repo,
        component_factory=factory
    )


async def get_get_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    silo_repo: SiloRepository = Depends(get_silo_repo),
    cage_repo: CageRepository = Depends(get_cage_repo)
) -> GetSystemLayoutUseCase:
    return GetSystemLayoutUseCase(
        line_repo=line_repo,
        silo_repo=silo_repo,
        cage_repo=cage_repo
    )


async def get_list_cages_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo)
) -> ListCagesUseCase:
    return ListCagesUseCase(cage_repository=cage_repo)


async def get_register_biometry_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    biometry_log_repo: BiometryLogRepository = Depends(get_biometry_log_repo)
) -> RegisterBiometryUseCase:
    return RegisterBiometryUseCase(
        cage_repository=cage_repo,
        biometry_log_repository=biometry_log_repo
    )


async def get_list_biometry_use_case(
    biometry_log_repo: BiometryLogRepository = Depends(get_biometry_log_repo)
) -> ListBiometryUseCase:
    return ListBiometryUseCase(biometry_log_repository=biometry_log_repo)


async def get_register_mortality_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    mortality_log_repo: MortalityLogRepository = Depends(get_mortality_log_repo)
) -> RegisterMortalityUseCase:
    return RegisterMortalityUseCase(
        cage_repository=cage_repo,
        mortality_log_repository=mortality_log_repo
    )


async def get_list_mortality_use_case(
    mortality_log_repo: MortalityLogRepository = Depends(get_mortality_log_repo)
) -> ListMortalityUseCase:
    return ListMortalityUseCase(mortality_log_repository=mortality_log_repo)


async def get_update_cage_config_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    config_log_repo: ConfigChangeLogRepository = Depends(get_config_change_log_repo)
) -> UpdateCageConfigUseCase:
    return UpdateCageConfigUseCase(
        cage_repository=cage_repo,
        config_change_log_repository=config_log_repo
    )


async def get_list_config_changes_use_case(
    config_log_repo: ConfigChangeLogRepository = Depends(get_config_change_log_repo)
) -> ListConfigChangesUseCase:
    return ListConfigChangesUseCase(config_change_log_repository=config_log_repo)


# ============================================================================
# Type Aliases para Endpoints
# ============================================================================

SyncUseCaseDep = Annotated[SyncSystemLayoutUseCase, Depends(get_sync_use_case)]
GetUseCaseDep = Annotated[GetSystemLayoutUseCase, Depends(get_get_use_case)]
ListCagesUseCaseDep = Annotated[ListCagesUseCase, Depends(get_list_cages_use_case)]
RegisterBiometryUseCaseDep = Annotated[RegisterBiometryUseCase, Depends(get_register_biometry_use_case)]
ListBiometryUseCaseDep = Annotated[ListBiometryUseCase, Depends(get_list_biometry_use_case)]
RegisterMortalityUseCaseDep = Annotated[RegisterMortalityUseCase, Depends(get_register_mortality_use_case)]
ListMortalityUseCaseDep = Annotated[ListMortalityUseCase, Depends(get_list_mortality_use_case)]
UpdateCageConfigUseCaseDep = Annotated[UpdateCageConfigUseCase, Depends(get_update_cage_config_use_case)]
ListConfigChangesUseCaseDep = Annotated[ListConfigChangesUseCase, Depends(get_list_config_changes_use_case)]
