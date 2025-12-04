"""Sistema de inyección de dependencias para FastAPI."""

from typing import Annotated, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.database import get_session
from infrastructure.persistence.repositories import (
    SiloRepository,
    CageRepository,
    FeedingLineRepository,
    FeedingOperationRepository
)
from infrastructure.persistence.repositories.biometry_log_repository import BiometryLogRepository
from infrastructure.persistence.repositories.mortality_log_repository import MortalityLogRepository
from infrastructure.persistence.repositories.config_change_log_repository import ConfigChangeLogRepository
from infrastructure.persistence.repositories.feeding_session_repository import FeedingSessionRepository
from infrastructure.services.plc_simulator import PLCSimulator
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
from application.use_cases.feeding.start_feeding_use_case import StartFeedingSessionUseCase
from application.use_cases.feeding.stop_feeding_use_case import StopFeedingSessionUseCase
from application.use_cases.feeding.control_feeding_use_case import PauseFeedingSessionUseCase, ResumeFeedingSessionUseCase
from application.use_cases.feeding.update_feeding_use_case import UpdateFeedingParametersUseCase
from domain.factories import ComponentFactory
from domain.interfaces import IFeedingMachine

# ============================================================================
# Dependencias de Repositorios
# ============================================================================

async def get_silo_repo(
    session: AsyncSession = Depends(get_session)
) -> SiloRepository:
    """Crea instancia del repositorio de silos."""
    return SiloRepository(session)


async def get_cage_repo(
    session: AsyncSession = Depends(get_session)
) -> CageRepository:
    """Crea instancia del repositorio de jaulas."""
    return CageRepository(session)


async def get_line_repo(
    session: AsyncSession = Depends(get_session)
) -> FeedingLineRepository:
    """Crea instancia del repositorio de líneas de alimentación."""
    return FeedingLineRepository(session)


async def get_biometry_log_repo(
    session: AsyncSession = Depends(get_session)
) -> BiometryLogRepository:
    """Crea instancia del repositorio de logs de biometría."""
    return BiometryLogRepository(session)


async def get_mortality_log_repo(
    session: AsyncSession = Depends(get_session)
) -> MortalityLogRepository:
    """Crea instancia del repositorio de logs de mortalidad."""
    return MortalityLogRepository(session)


async def get_config_change_log_repo(
    session: AsyncSession = Depends(get_session)
) -> ConfigChangeLogRepository:
    """Crea instancia del repositorio de logs de cambios de configuración."""
    return ConfigChangeLogRepository(session)


async def get_feeding_session_repo(
    session: AsyncSession = Depends(get_session)
) -> FeedingSessionRepository:
    """Crea instancia del repositorio de sesiones de alimentación."""
    return FeedingSessionRepository(session)


async def get_feeding_operation_repo(
    session: AsyncSession = Depends(get_session)
) -> FeedingOperationRepository:
    """Crea instancia del repositorio de operaciones de alimentación."""
    return FeedingOperationRepository(session)

# ============================================================================
# Servicios de Infraestructura
# ============================================================================

# Singleton del simulador PLC (mantiene estado en memoria)
_plc_simulator_instance: Optional[PLCSimulator] = None


def get_machine_service() -> IFeedingMachine:
    """
    Retorna instancia singleton del simulador PLC.
    En producción, esto sería reemplazado por el cliente Modbus real.
    """
    global _plc_simulator_instance
    if _plc_simulator_instance is None:
        _plc_simulator_instance = PLCSimulator()
    return _plc_simulator_instance


def get_component_factory() -> ComponentFactory:
    """Crea instancia de la fábrica de componentes del dominio."""
    return ComponentFactory()


# ============================================================================
# Dependencias de Casos de Uso - System Layout
# ============================================================================

async def get_sync_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    silo_repo: SiloRepository = Depends(get_silo_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    factory: ComponentFactory = Depends(get_component_factory)
) -> SyncSystemLayoutUseCase:
    """Crea instancia del caso de uso de sincronización del trazado del sistema."""
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
    """Crea instancia del caso de uso de obtención del trazado del sistema."""
    return GetSystemLayoutUseCase(
        line_repo=line_repo,
        silo_repo=silo_repo,
        cage_repo=cage_repo
    )


# ============================================================================
# Dependencias de Casos de Uso - Cage
# ============================================================================

async def get_list_cages_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo)
) -> ListCagesUseCase:
    """Crea instancia del caso de uso de listado de jaulas."""
    return ListCagesUseCase(cage_repository=cage_repo)


async def get_register_biometry_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    biometry_log_repo: BiometryLogRepository = Depends(get_biometry_log_repo)
) -> RegisterBiometryUseCase:
    """Crea instancia del caso de uso de registro de biometría."""
    return RegisterBiometryUseCase(
        cage_repository=cage_repo,
        biometry_log_repository=biometry_log_repo
    )


async def get_list_biometry_use_case(
    biometry_log_repo: BiometryLogRepository = Depends(get_biometry_log_repo)
) -> ListBiometryUseCase:
    """Crea instancia del caso de uso de listado de biometrías."""
    return ListBiometryUseCase(biometry_log_repository=biometry_log_repo)


async def get_register_mortality_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    mortality_log_repo: MortalityLogRepository = Depends(get_mortality_log_repo)
) -> RegisterMortalityUseCase:
    """Crea instancia del caso de uso de registro de mortalidad."""
    return RegisterMortalityUseCase(
        cage_repository=cage_repo,
        mortality_log_repository=mortality_log_repo
    )


async def get_list_mortality_use_case(
    mortality_log_repo: MortalityLogRepository = Depends(get_mortality_log_repo)
) -> ListMortalityUseCase:
    """Crea instancia del caso de uso de listado de mortalidades."""
    return ListMortalityUseCase(mortality_log_repository=mortality_log_repo)


async def get_update_cage_config_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    config_log_repo: ConfigChangeLogRepository = Depends(get_config_change_log_repo)
) -> UpdateCageConfigUseCase:
    """Crea instancia del caso de uso de actualización de configuración de jaula."""
    return UpdateCageConfigUseCase(
        cage_repository=cage_repo,
        config_change_log_repository=config_log_repo
    )


async def get_list_config_changes_use_case(
    config_log_repo: ConfigChangeLogRepository = Depends(get_config_change_log_repo)
) -> ListConfigChangesUseCase:
    """Crea instancia del caso de uso de listado de cambios de configuración."""
    return ListConfigChangesUseCase(config_change_log_repository=config_log_repo)


# ============================================================================
# Dependencias de Casos de Uso - Feeding
# ============================================================================

async def get_start_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> StartFeedingSessionUseCase:
    """Crea instancia del caso de uso de inicio de alimentación."""
    return StartFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        line_repository=line_repo,
        cage_repository=cage_repo,
        machine_service=machine_service
    )


async def get_stop_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> StopFeedingSessionUseCase:
    """Crea instancia del caso de uso de detención de alimentación."""
    return StopFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        machine_service=machine_service
    )


async def get_pause_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> PauseFeedingSessionUseCase:
    """Crea instancia del caso de uso de pausa de alimentación."""
    return PauseFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        machine_service=machine_service
    )


async def get_resume_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> ResumeFeedingSessionUseCase:
    """Crea instancia del caso de uso de reanudación de alimentación."""
    return ResumeFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        machine_service=machine_service
    )


async def get_update_feeding_params_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> UpdateFeedingParametersUseCase:
    """Crea instancia del caso de uso de actualización de parámetros de alimentación."""
    return UpdateFeedingParametersUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        machine_service=machine_service
    )

# ============================================================================
# Type Aliases para Endpoints - System Layout
# ============================================================================

SyncUseCaseDep = Annotated[
    SyncSystemLayoutUseCase,
    Depends(get_sync_use_case)
]

GetUseCaseDep = Annotated[
    GetSystemLayoutUseCase,
    Depends(get_get_use_case)
]


# ============================================================================
# Type Aliases para Endpoints - Cage
# ============================================================================

ListCagesUseCaseDep = Annotated[
    ListCagesUseCase,
    Depends(get_list_cages_use_case)
]

RegisterBiometryUseCaseDep = Annotated[
    RegisterBiometryUseCase,
    Depends(get_register_biometry_use_case)
]

ListBiometryUseCaseDep = Annotated[
    ListBiometryUseCase,
    Depends(get_list_biometry_use_case)
]

RegisterMortalityUseCaseDep = Annotated[
    RegisterMortalityUseCase,
    Depends(get_register_mortality_use_case)
]

ListMortalityUseCaseDep = Annotated[
    ListMortalityUseCase,
    Depends(get_list_mortality_use_case)
]

UpdateCageConfigUseCaseDep = Annotated[
    UpdateCageConfigUseCase,
    Depends(get_update_cage_config_use_case)
]

ListConfigChangesUseCaseDep = Annotated[
    ListConfigChangesUseCase,
    Depends(get_list_config_changes_use_case)
]


# ============================================================================
# Type Aliases para Endpoints - Feeding
# ============================================================================

StartFeedingUseCaseDep = Annotated[
    StartFeedingSessionUseCase,
    Depends(get_start_feeding_use_case)
]

StopFeedingUseCaseDep = Annotated[
    StopFeedingSessionUseCase,
    Depends(get_stop_feeding_use_case)
]

PauseFeedingUseCaseDep = Annotated[
    PauseFeedingSessionUseCase,
    Depends(get_pause_feeding_use_case)
]

ResumeFeedingUseCaseDep = Annotated[
    ResumeFeedingSessionUseCase,
    Depends(get_resume_feeding_use_case)
]

UpdateFeedingParamsUseCaseDep = Annotated[
    UpdateFeedingParametersUseCase,
    Depends(get_update_feeding_params_use_case)
]
