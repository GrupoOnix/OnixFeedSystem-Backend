"""Sistema de inyección de dependencias para FastAPI."""

from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.services import AlertTriggerService
from application.use_cases import GetSystemLayoutUseCase, SyncSystemLayoutUseCase
from application.use_cases.alerts import (
    CreateAlertUseCase,
    CreateScheduledAlertUseCase,
    DeleteScheduledAlertUseCase,
    GetAlertCountsUseCase,
    GetSnoozedCountUseCase,
    GetUnreadCountUseCase,
    ListAlertsUseCase,
    ListScheduledAlertsUseCase,
    ListSnoozedAlertsUseCase,
    MarkAlertReadUseCase,
    MarkAllAlertsReadUseCase,
    SnoozeAlertUseCase,
    ToggleScheduledAlertUseCase,
    UnsnoozeAlertUseCase,
    UpdateAlertUseCase,
    UpdateScheduledAlertUseCase,
)
from application.use_cases.cage import (
    AdjustPopulationUseCase,
    CreateCageUseCase,
    DeleteCageUseCase,
    GetCageUseCase,
    GetPopulationHistoryUseCase,
    HarvestUseCase,
    ListCagesUseCase,
    RegisterMortalityUseCase,
    SetPopulationUseCase,
    UpdateBiometryUseCase,
    UpdateCageConfigUseCase,
    UpdateCageUseCase,
)
from application.use_cases.cage_group import (
    CreateCageGroupUseCase,
    DeleteCageGroupUseCase,
    GetCageGroupUseCase,
    ListCageGroupsUseCase,
    UpdateCageGroupUseCase,
)
from application.use_cases.device_control import (
    MoveSelectorToSlotDirectUseCase,
    ResetSelectorDirectUseCase,
    SetBlowerPowerUseCase,
    SetDoserRateUseCase,
    TurnBlowerOffUseCase,
    TurnBlowerOnUseCase,
    TurnDoserOffUseCase,
    TurnDoserOnUseCase,
)
from application.use_cases.feeding.control_feeding_use_case import (
    PauseFeedingSessionUseCase,
    ResumeFeedingSessionUseCase,
)
from application.use_cases.feeding.start_feeding_use_case import (
    StartFeedingSessionUseCase,
)
from application.use_cases.feeding.stop_feeding_use_case import (
    StopFeedingSessionUseCase,
)
from application.use_cases.feeding.update_feeding_use_case import (
    UpdateFeedingParametersUseCase,
)
from application.use_cases.feeding_line import (
    GetFeedingLineUseCase,
    ListFeedingLinesUseCase,
    MoveSelectorToSlotUseCase,
    ResetSelectorPositionUseCase,
    UpdateBlowerUseCase,
    UpdateDoserUseCase,
    UpdateSelectorUseCase,
)
from application.use_cases.food import (
    CreateFoodUseCase,
    DeleteFoodUseCase,
    GetFoodUseCase,
    ListFoodsUseCase,
    ToggleFoodActiveUseCase,
    UpdateFoodUseCase,
)
from application.use_cases.sensors import (
    GetLineSensorsUseCase,
    GetSensorReadingsUseCase,
    UpdateSensorUseCase,
)
from application.use_cases.silo import (
    CreateSiloUseCase,
    DeleteSiloUseCase,
    GetSiloUseCase,
    ListSilosUseCase,
    UpdateSiloUseCase,
)
from domain.factories import ComponentFactory
from domain.interfaces import IFeedingMachine
from infrastructure.persistence.database import get_session
from infrastructure.persistence.repositories import (
    AlertRepository,
    CageGroupRepository,
    CageRepository,
    FeedingLineRepository,
    FeedingOperationRepository,
    FoodRepository,
    ScheduledAlertRepository,
    SiloRepository,
)
from infrastructure.persistence.repositories.blower_repository import BlowerRepository
from infrastructure.persistence.repositories.doser_repository import DoserRepository
from infrastructure.persistence.repositories.feeding_session_repository import (
    FeedingSessionRepository,
)
from infrastructure.persistence.repositories.population_event_repository import (
    PopulationEventRepository,
)
from infrastructure.persistence.repositories.selector_repository import (
    SelectorRepository,
)
from infrastructure.persistence.repositories.slot_assignment_repository import (
    SlotAssignmentRepository,
)
from infrastructure.services.plc_simulator import PLCSimulator

# ============================================================================
# Dependencias de Repositorios
# ============================================================================


async def get_silo_repo(session: AsyncSession = Depends(get_session)) -> SiloRepository:
    """Crea instancia del repositorio de silos."""
    return SiloRepository(session)


async def get_food_repo(session: AsyncSession = Depends(get_session)) -> FoodRepository:
    """Crea instancia del repositorio de alimentos."""
    return FoodRepository(session)


async def get_cage_repo(session: AsyncSession = Depends(get_session)) -> CageRepository:
    """Crea instancia del repositorio de jaulas."""
    return CageRepository(session)


async def get_cage_group_repo(
    session: AsyncSession = Depends(get_session)
) -> CageGroupRepository:
    """Crea instancia del repositorio de grupos de jaulas."""
    return CageGroupRepository(session)


async def get_population_event_repo(
    session: AsyncSession = Depends(get_session),
) -> PopulationEventRepository:
    """Crea instancia del repositorio de eventos de población."""
    return PopulationEventRepository(session)


async def get_slot_assignment_repo(
    session: AsyncSession = Depends(get_session),
) -> SlotAssignmentRepository:
    """Crea instancia del repositorio de asignaciones de slots."""
    return SlotAssignmentRepository(session)


async def get_line_repo(
    session: AsyncSession = Depends(get_session),
) -> FeedingLineRepository:
    """Crea instancia del repositorio de líneas de alimentación."""
    return FeedingLineRepository(session)


async def get_feeding_session_repo(
    session: AsyncSession = Depends(get_session),
) -> FeedingSessionRepository:
    """Crea instancia del repositorio de sesiones de alimentación."""
    return FeedingSessionRepository(session)


async def get_feeding_operation_repo(
    session: AsyncSession = Depends(get_session),
) -> FeedingOperationRepository:
    """Crea instancia del repositorio de operaciones de alimentación."""
    return FeedingOperationRepository(session)


async def get_blower_repo(
    session: AsyncSession = Depends(get_session),
) -> BlowerRepository:
    """Crea instancia del repositorio de blowers."""
    return BlowerRepository(session)


async def get_doser_repo(
    session: AsyncSession = Depends(get_session),
) -> DoserRepository:
    """Crea instancia del repositorio de dosers."""
    return DoserRepository(session)


async def get_selector_repo(
    session: AsyncSession = Depends(get_session),
) -> SelectorRepository:
    """Crea instancia del repositorio de selectors."""
    return SelectorRepository(session)


async def get_alert_repo(
    session: AsyncSession = Depends(get_session),
) -> AlertRepository:
    """Crea instancia del repositorio de alertas."""
    return AlertRepository(session)


async def get_scheduled_alert_repo(
    session: AsyncSession = Depends(get_session),
) -> ScheduledAlertRepository:
    """Crea instancia del repositorio de alertas programadas."""
    return ScheduledAlertRepository(session)


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
# Dependencias de Casos de Uso - Feeding Line
# ============================================================================


async def get_list_feeding_lines_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    session: AsyncSession = Depends(get_session),
) -> ListFeedingLinesUseCase:
    """Crea instancia del caso de uso de listado de líneas de alimentación."""
    return ListFeedingLinesUseCase(feeding_line_repository=line_repo, session=session)


async def get_get_feeding_line_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    session: AsyncSession = Depends(get_session),
) -> GetFeedingLineUseCase:
    """Crea instancia del caso de uso de obtención de línea de alimentación."""
    return GetFeedingLineUseCase(feeding_line_repository=line_repo, session=session)


async def get_update_selector_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
) -> UpdateSelectorUseCase:
    """Crea instancia del caso de uso de actualización de selector."""
    return UpdateSelectorUseCase(feeding_line_repository=line_repo)


async def get_move_selector_to_slot_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
) -> MoveSelectorToSlotUseCase:
    """Crea instancia del caso de uso de movimiento de selector a slot."""
    return MoveSelectorToSlotUseCase(feeding_line_repository=line_repo)


async def get_reset_selector_position_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
) -> ResetSelectorPositionUseCase:
    """Crea instancia del caso de uso de reinicio de posición de selector."""
    return ResetSelectorPositionUseCase(feeding_line_repository=line_repo)


async def get_update_blower_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
) -> UpdateBlowerUseCase:
    """Crea instancia del caso de uso de actualización de blower."""
    return UpdateBlowerUseCase(feeding_line_repository=line_repo)


async def get_update_doser_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
) -> UpdateDoserUseCase:
    """Crea instancia del caso de uso de actualización de doser."""
    return UpdateDoserUseCase(feeding_line_repository=line_repo)


async def get_sensor_readings_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> GetSensorReadingsUseCase:
    """Crea instancia del caso de uso de obtención de lecturas de sensores."""
    return GetSensorReadingsUseCase(
        feeding_line_repo=line_repo,
        feeding_machine=machine_service,
    )


async def get_line_sensors_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
) -> GetLineSensorsUseCase:
    """Crea instancia del caso de uso de listado de sensores de una línea."""
    return GetLineSensorsUseCase(feeding_line_repo=line_repo)


async def get_update_sensor_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
) -> UpdateSensorUseCase:
    """Crea instancia del caso de uso de actualización de sensor."""
    return UpdateSensorUseCase(feeding_line_repo=line_repo)


# ============================================================================
# Dependencias de Casos de Uso - Device Control
# ============================================================================


async def get_set_blower_power_use_case(
    blower_repo: BlowerRepository = Depends(get_blower_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> SetBlowerPowerUseCase:
    """Crea instancia del caso de uso de control directo de blower."""
    return SetBlowerPowerUseCase(
        blower_repository=blower_repo,
        machine_service=machine_service,
    )


async def get_set_doser_rate_use_case(
    doser_repo: DoserRepository = Depends(get_doser_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> SetDoserRateUseCase:
    """Crea instancia del caso de uso de control directo de doser."""
    return SetDoserRateUseCase(
        doser_repository=doser_repo,
        machine_service=machine_service,
    )


async def get_move_selector_direct_use_case(
    selector_repo: SelectorRepository = Depends(get_selector_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> MoveSelectorToSlotDirectUseCase:
    """Crea instancia del caso de uso de movimiento directo de selector."""
    return MoveSelectorToSlotDirectUseCase(
        selector_repository=selector_repo,
        machine_service=machine_service,
    )


async def get_reset_selector_direct_use_case(
    selector_repo: SelectorRepository = Depends(get_selector_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> ResetSelectorDirectUseCase:
    """Crea instancia del caso de uso de reseteo directo de selector."""
    return ResetSelectorDirectUseCase(
        selector_repository=selector_repo,
        machine_service=machine_service,
    )


async def get_turn_blower_on_use_case(
    blower_repo: BlowerRepository = Depends(get_blower_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> TurnBlowerOnUseCase:
    """Crea instancia del caso de uso de encendido de blower."""
    return TurnBlowerOnUseCase(
        blower_repository=blower_repo,
        machine_service=machine_service,
    )


async def get_turn_blower_off_use_case(
    blower_repo: BlowerRepository = Depends(get_blower_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> TurnBlowerOffUseCase:
    """Crea instancia del caso de uso de apagado de blower."""
    return TurnBlowerOffUseCase(
        blower_repository=blower_repo,
        machine_service=machine_service,
    )


async def get_turn_doser_on_use_case(
    doser_repo: DoserRepository = Depends(get_doser_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> TurnDoserOnUseCase:
    """Crea instancia del caso de uso de encendido de doser."""
    return TurnDoserOnUseCase(
        doser_repository=doser_repo,
        machine_service=machine_service,
    )


async def get_turn_doser_off_use_case(
    doser_repo: DoserRepository = Depends(get_doser_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> TurnDoserOffUseCase:
    """Crea instancia del caso de uso de apagado de doser."""
    return TurnDoserOffUseCase(
        doser_repository=doser_repo,
        machine_service=machine_service,
    )


# ============================================================================
# Dependencias de Servicios - Alert Trigger
# ============================================================================


async def get_alert_trigger_service(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> AlertTriggerService:
    """Crea instancia del servicio de triggers de alertas."""
    return AlertTriggerService(alert_repository=alert_repo)


AlertTriggerServiceDep = Annotated[
    AlertTriggerService, Depends(get_alert_trigger_service)
]


# ============================================================================
# Dependencias de Casos de Uso - Silo
# ============================================================================


async def get_list_silos_use_case(
    silo_repo: SiloRepository = Depends(get_silo_repo),
) -> ListSilosUseCase:
    """Crea instancia del caso de uso de listado de silos."""
    return ListSilosUseCase(silo_repository=silo_repo)


async def get_get_silo_use_case(
    silo_repo: SiloRepository = Depends(get_silo_repo),
) -> GetSiloUseCase:
    """Crea instancia del caso de uso de obtención de silo."""
    return GetSiloUseCase(silo_repository=silo_repo)


async def get_create_silo_use_case(
    silo_repo: SiloRepository = Depends(get_silo_repo),
) -> CreateSiloUseCase:
    """Crea instancia del caso de uso de creación de silo."""
    return CreateSiloUseCase(silo_repository=silo_repo)


async def get_update_silo_use_case(
    silo_repo: SiloRepository = Depends(get_silo_repo),
    alert_trigger_service: "AlertTriggerService" = Depends(get_alert_trigger_service),
) -> UpdateSiloUseCase:
    """Crea instancia del caso de uso de actualización de silo."""
    return UpdateSiloUseCase(
        silo_repository=silo_repo, alert_trigger_service=alert_trigger_service
    )


async def get_delete_silo_use_case(
    silo_repo: SiloRepository = Depends(get_silo_repo),
) -> DeleteSiloUseCase:
    """Crea instancia del caso de uso de eliminación de silo."""
    return DeleteSiloUseCase(silo_repository=silo_repo)


# ============================================================================
# Dependencias de Casos de Uso - Food
# ============================================================================


async def get_list_foods_use_case(
    food_repo: FoodRepository = Depends(get_food_repo),
) -> ListFoodsUseCase:
    """Crea instancia del caso de uso de listado de alimentos."""
    return ListFoodsUseCase(food_repository=food_repo)


async def get_get_food_use_case(
    food_repo: FoodRepository = Depends(get_food_repo),
) -> GetFoodUseCase:
    """Crea instancia del caso de uso de obtención de alimento."""
    return GetFoodUseCase(food_repository=food_repo)


async def get_create_food_use_case(
    food_repo: FoodRepository = Depends(get_food_repo),
) -> CreateFoodUseCase:
    """Crea instancia del caso de uso de creación de alimento."""
    return CreateFoodUseCase(food_repository=food_repo)


async def get_update_food_use_case(
    food_repo: FoodRepository = Depends(get_food_repo),
) -> UpdateFoodUseCase:
    """Crea instancia del caso de uso de actualización de alimento."""
    return UpdateFoodUseCase(food_repository=food_repo)


async def get_delete_food_use_case(
    food_repo: FoodRepository = Depends(get_food_repo),
) -> DeleteFoodUseCase:
    """Crea instancia del caso de uso de eliminación de alimento."""
    return DeleteFoodUseCase(food_repository=food_repo)


async def get_toggle_food_active_use_case(
    food_repo: FoodRepository = Depends(get_food_repo),
) -> ToggleFoodActiveUseCase:
    """Crea instancia del caso de uso de activación/desactivación de alimento."""
    return ToggleFoodActiveUseCase(food_repository=food_repo)


# ============================================================================
# Dependencias de Casos de Uso - System Layout
# ============================================================================


async def get_sync_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    silo_repo: SiloRepository = Depends(get_silo_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    slot_assignment_repo: SlotAssignmentRepository = Depends(get_slot_assignment_repo),
    factory: ComponentFactory = Depends(get_component_factory),
) -> SyncSystemLayoutUseCase:
    """Crea instancia del caso de uso de sincronización del trazado del sistema."""
    return SyncSystemLayoutUseCase(
        line_repo=line_repo,
        silo_repo=silo_repo,
        cage_repo=cage_repo,
        slot_assignment_repo=slot_assignment_repo,
        component_factory=factory,
    )


async def get_get_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    silo_repo: SiloRepository = Depends(get_silo_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    slot_assignment_repo: SlotAssignmentRepository = Depends(get_slot_assignment_repo),
) -> GetSystemLayoutUseCase:
    """Crea instancia del caso de uso de obtención del trazado del sistema."""
    return GetSystemLayoutUseCase(
        line_repo=line_repo,
        silo_repo=silo_repo,
        cage_repo=cage_repo,
        slot_assignment_repo=slot_assignment_repo,
    )


# ============================================================================
# Dependencias de Casos de Uso - Cage
# ============================================================================


async def get_create_cage_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> CreateCageUseCase:
    """Crea instancia del caso de uso de creación de jaula."""
    return CreateCageUseCase(cage_repository=cage_repo)


async def get_get_cage_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> GetCageUseCase:
    """Crea instancia del caso de uso de obtención de jaula."""
    return GetCageUseCase(cage_repository=cage_repo)


async def get_list_cages_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> ListCagesUseCase:
    """Crea instancia del caso de uso de listado de jaulas."""
    return ListCagesUseCase(cage_repository=cage_repo)


async def get_update_cage_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> UpdateCageUseCase:
    """Crea instancia del caso de uso de actualización de jaula."""
    return UpdateCageUseCase(cage_repository=cage_repo)


async def get_delete_cage_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> DeleteCageUseCase:
    """Crea instancia del caso de uso de eliminación de jaula."""
    return DeleteCageUseCase(cage_repository=cage_repo)


async def get_update_cage_config_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> UpdateCageConfigUseCase:
    """Crea instancia del caso de uso de actualización de configuración."""
    return UpdateCageConfigUseCase(cage_repository=cage_repo)


async def get_set_population_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    event_repo: PopulationEventRepository = Depends(get_population_event_repo),
) -> SetPopulationUseCase:
    """Crea instancia del caso de uso de establecer población."""
    return SetPopulationUseCase(cage_repository=cage_repo, event_repository=event_repo)


async def get_register_mortality_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    event_repo: PopulationEventRepository = Depends(get_population_event_repo),
) -> RegisterMortalityUseCase:
    """Crea instancia del caso de uso de registro de mortalidad."""
    return RegisterMortalityUseCase(
        cage_repository=cage_repo, event_repository=event_repo
    )


async def get_update_biometry_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    event_repo: PopulationEventRepository = Depends(get_population_event_repo),
) -> UpdateBiometryUseCase:
    """Crea instancia del caso de uso de actualización de biometría."""
    return UpdateBiometryUseCase(cage_repository=cage_repo, event_repository=event_repo)


async def get_harvest_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    event_repo: PopulationEventRepository = Depends(get_population_event_repo),
) -> HarvestUseCase:
    """Crea instancia del caso de uso de cosecha."""
    return HarvestUseCase(cage_repository=cage_repo, event_repository=event_repo)


async def get_adjust_population_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    event_repo: PopulationEventRepository = Depends(get_population_event_repo),
) -> AdjustPopulationUseCase:
    """Crea instancia del caso de uso de ajuste de población."""
    return AdjustPopulationUseCase(
        cage_repository=cage_repo, event_repository=event_repo
    )


async def get_population_history_use_case(
    event_repo: PopulationEventRepository = Depends(get_population_event_repo),
) -> GetPopulationHistoryUseCase:
    """Crea instancia del caso de uso de historial de población."""
    return GetPopulationHistoryUseCase(event_repository=event_repo)


# ============================================================================
# Dependencias de Casos de Uso - Cage Group
# ============================================================================


async def get_create_cage_group_use_case(
    group_repo: CageGroupRepository = Depends(get_cage_group_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> CreateCageGroupUseCase:
    """Crea instancia del caso de uso de creación de grupo de jaulas."""
    return CreateCageGroupUseCase(group_repository=group_repo, cage_repository=cage_repo)


async def get_list_cage_groups_use_case(
    group_repo: CageGroupRepository = Depends(get_cage_group_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> ListCageGroupsUseCase:
    """Crea instancia del caso de uso de listado de grupos de jaulas."""
    return ListCageGroupsUseCase(group_repository=group_repo, cage_repository=cage_repo)


async def get_get_cage_group_use_case(
    group_repo: CageGroupRepository = Depends(get_cage_group_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> GetCageGroupUseCase:
    """Crea instancia del caso de uso de obtención de grupo de jaulas."""
    return GetCageGroupUseCase(group_repository=group_repo, cage_repository=cage_repo)


async def get_update_cage_group_use_case(
    group_repo: CageGroupRepository = Depends(get_cage_group_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> UpdateCageGroupUseCase:
    """Crea instancia del caso de uso de actualización de grupo de jaulas."""
    return UpdateCageGroupUseCase(group_repository=group_repo, cage_repository=cage_repo)


async def get_delete_cage_group_use_case(
    group_repo: CageGroupRepository = Depends(get_cage_group_repo),
) -> DeleteCageGroupUseCase:
    """Crea instancia del caso de uso de eliminación de grupo de jaulas."""
    return DeleteCageGroupUseCase(group_repository=group_repo)


# ============================================================================
# Dependencias de Casos de Uso - Feeding
# ============================================================================


async def get_start_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> StartFeedingSessionUseCase:
    """Crea instancia del caso de uso de inicio de alimentación."""
    return StartFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        line_repository=line_repo,
        cage_repository=cage_repo,
        machine_service=machine_service,
    )


async def get_stop_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> StopFeedingSessionUseCase:
    """Crea instancia del caso de uso de detención de alimentación."""
    return StopFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        machine_service=machine_service,
    )


async def get_pause_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> PauseFeedingSessionUseCase:
    """Crea instancia del caso de uso de pausa de alimentación."""
    return PauseFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        machine_service=machine_service,
    )


async def get_resume_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> ResumeFeedingSessionUseCase:
    """Crea instancia del caso de uso de reanudación de alimentación."""
    return ResumeFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        machine_service=machine_service,
    )


async def get_update_feeding_params_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> UpdateFeedingParametersUseCase:
    """Crea instancia del caso de uso de actualización de parámetros de alimentación."""
    return UpdateFeedingParametersUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,
        machine_service=machine_service,
    )


# ============================================================================
# Type Aliases para Endpoints - System Layout
# ============================================================================

SyncUseCaseDep = Annotated[SyncSystemLayoutUseCase, Depends(get_sync_use_case)]

GetUseCaseDep = Annotated[GetSystemLayoutUseCase, Depends(get_get_use_case)]


# ============================================================================
# Type Aliases para Endpoints - Feeding Line
# ============================================================================

ListFeedingLinesUseCaseDep = Annotated[
    ListFeedingLinesUseCase, Depends(get_list_feeding_lines_use_case)
]

GetFeedingLineUseCaseDep = Annotated[
    GetFeedingLineUseCase, Depends(get_get_feeding_line_use_case)
]

UpdateSelectorUseCaseDep = Annotated[
    UpdateSelectorUseCase, Depends(get_update_selector_use_case)
]

MoveSelectorToSlotUseCaseDep = Annotated[
    MoveSelectorToSlotUseCase, Depends(get_move_selector_to_slot_use_case)
]

ResetSelectorPositionUseCaseDep = Annotated[
    ResetSelectorPositionUseCase, Depends(get_reset_selector_position_use_case)
]

UpdateBlowerUseCaseDep = Annotated[
    UpdateBlowerUseCase, Depends(get_update_blower_use_case)
]

UpdateDoserUseCaseDep = Annotated[
    UpdateDoserUseCase, Depends(get_update_doser_use_case)
]

GetSensorReadingsUseCaseDep = Annotated[
    GetSensorReadingsUseCase, Depends(get_sensor_readings_use_case)
]

GetLineSensorsUseCaseDep = Annotated[
    GetLineSensorsUseCase, Depends(get_line_sensors_use_case)
]

UpdateSensorUseCaseDep = Annotated[
    UpdateSensorUseCase, Depends(get_update_sensor_use_case)
]


# ============================================================================
# Type Aliases para Endpoints - Silo
# ============================================================================

ListSilosUseCaseDep = Annotated[ListSilosUseCase, Depends(get_list_silos_use_case)]

GetSiloUseCaseDep = Annotated[GetSiloUseCase, Depends(get_get_silo_use_case)]

CreateSiloUseCaseDep = Annotated[CreateSiloUseCase, Depends(get_create_silo_use_case)]

UpdateSiloUseCaseDep = Annotated[UpdateSiloUseCase, Depends(get_update_silo_use_case)]

DeleteSiloUseCaseDep = Annotated[DeleteSiloUseCase, Depends(get_delete_silo_use_case)]


# ============================================================================
# Type Aliases para Endpoints - Food
# ============================================================================

ListFoodsUseCaseDep = Annotated[ListFoodsUseCase, Depends(get_list_foods_use_case)]

GetFoodUseCaseDep = Annotated[GetFoodUseCase, Depends(get_get_food_use_case)]

CreateFoodUseCaseDep = Annotated[CreateFoodUseCase, Depends(get_create_food_use_case)]

UpdateFoodUseCaseDep = Annotated[UpdateFoodUseCase, Depends(get_update_food_use_case)]

DeleteFoodUseCaseDep = Annotated[DeleteFoodUseCase, Depends(get_delete_food_use_case)]

ToggleFoodActiveUseCaseDep = Annotated[
    ToggleFoodActiveUseCase, Depends(get_toggle_food_active_use_case)
]


# ============================================================================
# Type Aliases para Endpoints - Cage
# ============================================================================

CreateCageUseCaseDep = Annotated[CreateCageUseCase, Depends(get_create_cage_use_case)]

GetCageUseCaseDep = Annotated[GetCageUseCase, Depends(get_get_cage_use_case)]

ListCagesUseCaseDep = Annotated[ListCagesUseCase, Depends(get_list_cages_use_case)]

UpdateCageUseCaseDep = Annotated[UpdateCageUseCase, Depends(get_update_cage_use_case)]

DeleteCageUseCaseDep = Annotated[DeleteCageUseCase, Depends(get_delete_cage_use_case)]

UpdateCageConfigUseCaseDep = Annotated[
    UpdateCageConfigUseCase, Depends(get_update_cage_config_use_case)
]

SetPopulationUseCaseDep = Annotated[
    SetPopulationUseCase, Depends(get_set_population_use_case)
]

RegisterMortalityUseCaseDep = Annotated[
    RegisterMortalityUseCase, Depends(get_register_mortality_use_case)
]

UpdateBiometryUseCaseDep = Annotated[
    UpdateBiometryUseCase, Depends(get_update_biometry_use_case)
]

HarvestUseCaseDep = Annotated[HarvestUseCase, Depends(get_harvest_use_case)]

AdjustPopulationUseCaseDep = Annotated[
    AdjustPopulationUseCase, Depends(get_adjust_population_use_case)
]

GetPopulationHistoryUseCaseDep = Annotated[
    GetPopulationHistoryUseCase, Depends(get_population_history_use_case)
]


# ============================================================================
# Type Aliases para Endpoints - Cage Group
# ============================================================================

CreateCageGroupUseCaseDep = Annotated[
    CreateCageGroupUseCase, Depends(get_create_cage_group_use_case)
]

ListCageGroupsUseCaseDep = Annotated[
    ListCageGroupsUseCase, Depends(get_list_cage_groups_use_case)
]

GetCageGroupUseCaseDep = Annotated[
    GetCageGroupUseCase, Depends(get_get_cage_group_use_case)
]

UpdateCageGroupUseCaseDep = Annotated[
    UpdateCageGroupUseCase, Depends(get_update_cage_group_use_case)
]

DeleteCageGroupUseCaseDep = Annotated[
    DeleteCageGroupUseCase, Depends(get_delete_cage_group_use_case)
]


# ============================================================================
# Type Aliases para Endpoints - Feeding
# ============================================================================

StartFeedingUseCaseDep = Annotated[
    StartFeedingSessionUseCase, Depends(get_start_feeding_use_case)
]

StopFeedingUseCaseDep = Annotated[
    StopFeedingSessionUseCase, Depends(get_stop_feeding_use_case)
]

PauseFeedingUseCaseDep = Annotated[
    PauseFeedingSessionUseCase, Depends(get_pause_feeding_use_case)
]

ResumeFeedingUseCaseDep = Annotated[
    ResumeFeedingSessionUseCase, Depends(get_resume_feeding_use_case)
]

UpdateFeedingParamsUseCaseDep = Annotated[
    UpdateFeedingParametersUseCase, Depends(get_update_feeding_params_use_case)
]


# ============================================================================
# Type Aliases para Endpoints - Device Control
# ============================================================================

SetBlowerPowerUseCaseDep = Annotated[
    SetBlowerPowerUseCase, Depends(get_set_blower_power_use_case)
]

SetDoserRateUseCaseDep = Annotated[
    SetDoserRateUseCase, Depends(get_set_doser_rate_use_case)
]

MoveSelectorDirectUseCaseDep = Annotated[
    MoveSelectorToSlotDirectUseCase, Depends(get_move_selector_direct_use_case)
]

ResetSelectorDirectUseCaseDep = Annotated[
    ResetSelectorDirectUseCase, Depends(get_reset_selector_direct_use_case)
]

TurnBlowerOnUseCaseDep = Annotated[
    TurnBlowerOnUseCase, Depends(get_turn_blower_on_use_case)
]

TurnBlowerOffUseCaseDep = Annotated[
    TurnBlowerOffUseCase, Depends(get_turn_blower_off_use_case)
]

TurnDoserOnUseCaseDep = Annotated[
    TurnDoserOnUseCase, Depends(get_turn_doser_on_use_case)
]

TurnDoserOffUseCaseDep = Annotated[
    TurnDoserOffUseCase, Depends(get_turn_doser_off_use_case)
]


# ============================================================================
# Dependencias de Casos de Uso - Alerts
# ============================================================================


async def get_list_alerts_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> ListAlertsUseCase:
    """Crea instancia del caso de uso de listado de alertas."""
    return ListAlertsUseCase(alert_repository=alert_repo)


async def get_unread_count_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> GetUnreadCountUseCase:
    """Crea instancia del caso de uso de contador de alertas no leídas."""
    return GetUnreadCountUseCase(alert_repository=alert_repo)


async def get_update_alert_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> UpdateAlertUseCase:
    """Crea instancia del caso de uso de actualización de alerta."""
    return UpdateAlertUseCase(alert_repository=alert_repo)


async def get_mark_alert_read_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> MarkAlertReadUseCase:
    """Crea instancia del caso de uso de marcar alerta como leída."""
    return MarkAlertReadUseCase(alert_repository=alert_repo)


async def get_snooze_alert_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> SnoozeAlertUseCase:
    """Crea instancia del caso de uso de silenciar alerta."""
    return SnoozeAlertUseCase(alert_repository=alert_repo)


async def get_mark_all_alerts_read_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> MarkAllAlertsReadUseCase:
    """Crea instancia del caso de uso de marcar todas las alertas como leídas."""
    return MarkAllAlertsReadUseCase(alert_repository=alert_repo)


async def get_create_alert_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> CreateAlertUseCase:
    """Crea instancia del caso de uso de creación de alerta (interno)."""
    return CreateAlertUseCase(alert_repository=alert_repo)


async def get_list_snoozed_alerts_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> ListSnoozedAlertsUseCase:
    """Crea instancia del caso de uso de listado de alertas silenciadas."""
    return ListSnoozedAlertsUseCase(alert_repository=alert_repo)


async def get_unsnooze_alert_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> UnsnoozeAlertUseCase:
    """Crea instancia del caso de uso de reactivar alerta."""
    return UnsnoozeAlertUseCase(alert_repository=alert_repo)


async def get_alert_counts_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> GetAlertCountsUseCase:
    """Crea instancia del caso de uso de contadores de alertas."""
    return GetAlertCountsUseCase(alert_repository=alert_repo)


async def get_snoozed_count_use_case(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> GetSnoozedCountUseCase:
    """Crea instancia del caso de uso de contador de alertas silenciadas."""
    return GetSnoozedCountUseCase(alert_repository=alert_repo)


# ============================================================================
# Dependencias de Casos de Uso - Scheduled Alerts
# ============================================================================


async def get_list_scheduled_alerts_use_case(
    scheduled_alert_repo: ScheduledAlertRepository = Depends(get_scheduled_alert_repo),
) -> ListScheduledAlertsUseCase:
    """Crea instancia del caso de uso de listado de alertas programadas."""
    return ListScheduledAlertsUseCase(scheduled_alert_repository=scheduled_alert_repo)


async def get_create_scheduled_alert_use_case(
    scheduled_alert_repo: ScheduledAlertRepository = Depends(get_scheduled_alert_repo),
) -> CreateScheduledAlertUseCase:
    """Crea instancia del caso de uso de creación de alerta programada."""
    return CreateScheduledAlertUseCase(scheduled_alert_repository=scheduled_alert_repo)


async def get_update_scheduled_alert_use_case(
    scheduled_alert_repo: ScheduledAlertRepository = Depends(get_scheduled_alert_repo),
) -> UpdateScheduledAlertUseCase:
    """Crea instancia del caso de uso de actualización de alerta programada."""
    return UpdateScheduledAlertUseCase(scheduled_alert_repository=scheduled_alert_repo)


async def get_delete_scheduled_alert_use_case(
    scheduled_alert_repo: ScheduledAlertRepository = Depends(get_scheduled_alert_repo),
) -> DeleteScheduledAlertUseCase:
    """Crea instancia del caso de uso de eliminación de alerta programada."""
    return DeleteScheduledAlertUseCase(scheduled_alert_repository=scheduled_alert_repo)


async def get_toggle_scheduled_alert_use_case(
    scheduled_alert_repo: ScheduledAlertRepository = Depends(get_scheduled_alert_repo),
) -> ToggleScheduledAlertUseCase:
    """Crea instancia del caso de uso de activación/desactivación de alerta programada."""
    return ToggleScheduledAlertUseCase(scheduled_alert_repository=scheduled_alert_repo)


# ============================================================================
# Type Aliases para Endpoints - Alerts
# ============================================================================

ListAlertsUseCaseDep = Annotated[ListAlertsUseCase, Depends(get_list_alerts_use_case)]

GetUnreadCountUseCaseDep = Annotated[
    GetUnreadCountUseCase, Depends(get_unread_count_use_case)
]

UpdateAlertUseCaseDep = Annotated[
    UpdateAlertUseCase, Depends(get_update_alert_use_case)
]

MarkAlertReadUseCaseDep = Annotated[
    MarkAlertReadUseCase, Depends(get_mark_alert_read_use_case)
]

SnoozeAlertUseCaseDep = Annotated[
    SnoozeAlertUseCase, Depends(get_snooze_alert_use_case)
]

MarkAllAlertsReadUseCaseDep = Annotated[
    MarkAllAlertsReadUseCase, Depends(get_mark_all_alerts_read_use_case)
]

CreateAlertUseCaseDep = Annotated[
    CreateAlertUseCase, Depends(get_create_alert_use_case)
]

ListSnoozedAlertsUseCaseDep = Annotated[
    ListSnoozedAlertsUseCase, Depends(get_list_snoozed_alerts_use_case)
]

UnsnoozeAlertUseCaseDep = Annotated[
    UnsnoozeAlertUseCase, Depends(get_unsnooze_alert_use_case)
]

GetAlertCountsUseCaseDep = Annotated[
    GetAlertCountsUseCase, Depends(get_alert_counts_use_case)
]

GetSnoozedCountUseCaseDep = Annotated[
    GetSnoozedCountUseCase, Depends(get_snoozed_count_use_case)
]


# ============================================================================
# Type Aliases para Endpoints - Scheduled Alerts
# ============================================================================

ListScheduledAlertsUseCaseDep = Annotated[
    ListScheduledAlertsUseCase, Depends(get_list_scheduled_alerts_use_case)
]

CreateScheduledAlertUseCaseDep = Annotated[
    CreateScheduledAlertUseCase, Depends(get_create_scheduled_alert_use_case)
]

UpdateScheduledAlertUseCaseDep = Annotated[
    UpdateScheduledAlertUseCase, Depends(get_update_scheduled_alert_use_case)
]

DeleteScheduledAlertUseCaseDep = Annotated[
    DeleteScheduledAlertUseCase, Depends(get_delete_scheduled_alert_use_case)
]

ToggleScheduledAlertUseCaseDep = Annotated[
    ToggleScheduledAlertUseCase, Depends(get_toggle_scheduled_alert_use_case)
]
