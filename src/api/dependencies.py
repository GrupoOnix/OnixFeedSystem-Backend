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
from application.use_cases import (
    SyncSystemLayoutUseCase,
    GetSystemLayoutUseCase
)
from application.use_cases.cage import ListCagesUseCase
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


# ============================================================================
# Type Aliases para Endpoints
# ============================================================================

SyncUseCaseDep = Annotated[SyncSystemLayoutUseCase, Depends(get_sync_use_case)]
GetUseCaseDep = Annotated[GetSystemLayoutUseCase, Depends(get_get_use_case)]
