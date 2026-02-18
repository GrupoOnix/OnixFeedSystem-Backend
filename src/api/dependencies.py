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
    ListBiometryUseCase,
    ListCagesUseCase,
    ListConfigChangesUseCase,
    ListMortalityUseCase,
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
    SetCoolerPowerUseCase,
    SetDoserRateUseCase,
    SetDoserSpeedUseCase,
    TurnBlowerOffUseCase,
    TurnBlowerOnUseCase,
    TurnCoolerOffUseCase,
    TurnCoolerOnUseCase,
    TurnDoserOffUseCase,
    TurnDoserOnUseCase,
)
# REMOVED: Old feeding use cases - system being rewritten
# from application.use_cases.feeding.control_feeding_use_case import (
#     PauseFeedingSessionUseCase,
#     ResumeFeedingSessionUseCase,
# )
# from application.use_cases.feeding.start_feeding_use_case import (
#     StartFeedingSessionUseCase,
# )
# from application.use_cases.feeding.stop_feeding_use_case import (
#     StopFeedingSessionUseCase,
# )
# from application.use_cases.feeding.update_feeding_use_case import (
#     UpdateFeedingParametersUseCase,
# )
from application.services.feeding_orchestrator import FeedingOrchestrator
from application.use_cases.feeding.control_feeding_use_cases import (
    CancelFeedingUseCase,
    PauseFeedingUseCase,
    ResumeFeedingUseCase,
    UpdateBlowerPowerUseCase,
    UpdateFeedingRateUseCase,
)
from application.use_cases.feeding.start_manual_feeding_use_case import (
    StartManualFeedingUseCase,
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
from infrastructure.persistence.database import async_session_maker, get_session
from infrastructure.persistence.repositories import (
    AlertRepository,
    BiometryLogRepository,
    CageFeedingRepository,
    CageGroupRepository,
    CageRepository,
    ConfigChangeLogRepository,
    FeedingEventRepository,
    FeedingLineRepository,
    FoodRepository,
    MortalityLogRepository,
    ScheduledAlertRepository,
    SiloRepository,
)
from infrastructure.persistence.repositories.blower_repository import BlowerRepository
from infrastructure.persistence.repositories.cooler_repository import CoolerRepository
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
from infrastructure.persistence.repositories.system_config_repository import SystemConfigRepository
from infrastructure.services.plc_simulator import PLCSimulator
from infrastructure.services.simulated_machine import SimulatedMachine
from application.use_cases.system_config import CheckScheduleUseCase, GetSystemConfigUseCase, UpdateSystemConfigUseCase

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


async def get_cage_group_repo(session: AsyncSession = Depends(get_session)) -> CageGroupRepository:
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


async def get_blower_repo(
    session: AsyncSession = Depends(get_session),
) -> BlowerRepository:
    """Crea instancia del repositorio de blowers."""
    return BlowerRepository(session)


async def get_cooler_repo(
    session: AsyncSession = Depends(get_session),
) -> CoolerRepository:
    """Crea instancia del repositorio de coolers."""
    return CoolerRepository(session)


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


async def get_cage_feeding_repo(
    session: AsyncSession = Depends(get_session),
) -> CageFeedingRepository:
    """Crea instancia del repositorio de alimentaciones de jaulas."""
    return CageFeedingRepository(session)


async def get_feeding_event_repo(
    session: AsyncSession = Depends(get_session),
) -> FeedingEventRepository:
    """Crea instancia del repositorio de eventos de alimentación."""
    return FeedingEventRepository(session)


async def get_system_config_repo(
    session: AsyncSession = Depends(get_session),
) -> SystemConfigRepository:
    """Crea instancia del repositorio de configuración del sistema."""
    return SystemConfigRepository(session)


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


_simulated_machine_instance: Optional[SimulatedMachine] = None


def get_simulated_machine() -> SimulatedMachine:
    global _simulated_machine_instance
    if _simulated_machine_instance is None:
        _simulated_machine_instance = SimulatedMachine()
    return _simulated_machine_instance


def get_feeding_orchestrator(
    machine: SimulatedMachine = Depends(get_simulated_machine),
) -> FeedingOrchestrator:
    return FeedingOrchestrator(
        machine=machine,
        session_factory=async_session_maker,
    )


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


async def get_set_doser_speed_use_case(
    doser_repo: DoserRepository = Depends(get_doser_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> SetDoserSpeedUseCase:
    """Crea instancia del caso de uso de control de velocidad de motor del doser."""
    return SetDoserSpeedUseCase(
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


async def get_set_cooler_power_use_case(
    cooler_repo: CoolerRepository = Depends(get_cooler_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> SetCoolerPowerUseCase:
    """Crea instancia del caso de uso de control directo de cooler."""
    return SetCoolerPowerUseCase(
        cooler_repository=cooler_repo,
        machine_service=machine_service,
    )


async def get_turn_cooler_on_use_case(
    cooler_repo: CoolerRepository = Depends(get_cooler_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> TurnCoolerOnUseCase:
    """Crea instancia del caso de uso de encendido de cooler."""
    return TurnCoolerOnUseCase(
        cooler_repository=cooler_repo,
        machine_service=machine_service,
    )


async def get_turn_cooler_off_use_case(
    cooler_repo: CoolerRepository = Depends(get_cooler_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service),
) -> TurnCoolerOffUseCase:
    """Crea instancia del caso de uso de apagado de cooler."""
    return TurnCoolerOffUseCase(
        cooler_repository=cooler_repo,
        machine_service=machine_service,
    )


# ============================================================================
# Dependencias de Casos de Uso - Feeding (Manual)
# ============================================================================


async def get_start_manual_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    cage_feeding_repo: CageFeedingRepository = Depends(get_cage_feeding_repo),
    event_repo: FeedingEventRepository = Depends(get_feeding_event_repo),
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    silo_repo: SiloRepository = Depends(get_silo_repo),
    slot_assignment_repo: SlotAssignmentRepository = Depends(get_slot_assignment_repo),
    orchestrator: FeedingOrchestrator = Depends(get_feeding_orchestrator),
    system_config_repo: SystemConfigRepository = Depends(get_system_config_repo),
) -> StartManualFeedingUseCase:
    """Crea instancia del caso de uso de inicio de alimentación manual."""
    return StartManualFeedingUseCase(
        session_repository=session_repo,
        cage_feeding_repository=cage_feeding_repo,
        event_repository=event_repo,
        line_repository=line_repo,
        cage_repository=cage_repo,
        silo_repository=silo_repo,
        slot_assignment_repository=slot_assignment_repo,
        orchestrator=orchestrator,
        system_config_repository=system_config_repo,
    )


# ============================================================================
# Dependencias de Casos de Uso - Feeding (Control)
# ============================================================================


async def get_update_feeding_rate_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    cage_feeding_repo: CageFeedingRepository = Depends(get_cage_feeding_repo),
    event_repo: FeedingEventRepository = Depends(get_feeding_event_repo),
    machine: SimulatedMachine = Depends(get_simulated_machine),
) -> UpdateFeedingRateUseCase:
    return UpdateFeedingRateUseCase(
        session_repo=session_repo,
        cage_feeding_repo=cage_feeding_repo,
        event_repo=event_repo,
        machine=machine,
    )


async def get_pause_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    event_repo: FeedingEventRepository = Depends(get_feeding_event_repo),
    machine: SimulatedMachine = Depends(get_simulated_machine),
) -> PauseFeedingUseCase:
    return PauseFeedingUseCase(
        session_repo=session_repo,
        event_repo=event_repo,
        machine=machine,
    )


async def get_resume_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    event_repo: FeedingEventRepository = Depends(get_feeding_event_repo),
    machine: SimulatedMachine = Depends(get_simulated_machine),
) -> ResumeFeedingUseCase:
    return ResumeFeedingUseCase(
        session_repo=session_repo,
        event_repo=event_repo,
        machine=machine,
    )


async def get_cancel_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    event_repo: FeedingEventRepository = Depends(get_feeding_event_repo),
    machine: SimulatedMachine = Depends(get_simulated_machine),
) -> CancelFeedingUseCase:
    return CancelFeedingUseCase(
        session_repo=session_repo,
        event_repo=event_repo,
        machine=machine,
    )


async def get_update_blower_power_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    machine: SimulatedMachine = Depends(get_simulated_machine),
) -> UpdateBlowerPowerUseCase:
    return UpdateBlowerPowerUseCase(
        session_repo=session_repo,
        machine=machine,
    )


# ============================================================================
# Dependencias de Casos de Uso - System Config
# ============================================================================


async def get_get_system_config_use_case(
    config_repo: SystemConfigRepository = Depends(get_system_config_repo),
) -> GetSystemConfigUseCase:
    return GetSystemConfigUseCase(config_repository=config_repo)


async def get_update_system_config_use_case(
    config_repo: SystemConfigRepository = Depends(get_system_config_repo),
) -> UpdateSystemConfigUseCase:
    return UpdateSystemConfigUseCase(config_repository=config_repo)


async def get_check_schedule_use_case(
    config_repo: SystemConfigRepository = Depends(get_system_config_repo),
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> CheckScheduleUseCase:
    return CheckScheduleUseCase(
        config_repository=config_repo,
        line_repository=line_repo,
        cage_repository=cage_repo,
    )


# ============================================================================
# Dependencias de Servicios - Alert Trigger
# ============================================================================


async def get_alert_trigger_service(
    alert_repo: AlertRepository = Depends(get_alert_repo),
) -> AlertTriggerService:
    """Crea instancia del servicio de triggers de alertas."""
    return AlertTriggerService(alert_repository=alert_repo)


AlertTriggerServiceDep = Annotated[AlertTriggerService, Depends(get_alert_trigger_service)]


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
    return UpdateSiloUseCase(silo_repository=silo_repo, alert_trigger_service=alert_trigger_service)


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
    # operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # DEPRECATED
) -> GetCageUseCase:
    """Crea instancia del caso de uso de obtención de jaula."""
    return GetCageUseCase(cage_repository=cage_repo, operation_repository=None)  # TODO: Remove operation_repository


async def get_list_cages_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    # operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # DEPRECATED
) -> ListCagesUseCase:
    """Crea instancia del caso de uso de listado de jaulas."""
    return ListCagesUseCase(cage_repository=cage_repo, operation_repository=None)  # TODO: Remove operation_repository


async def get_update_cage_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    # operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # DEPRECATED
) -> UpdateCageUseCase:
    """Crea instancia del caso de uso de actualización de jaula."""
    return UpdateCageUseCase(cage_repository=cage_repo, operation_repository=None)  # TODO: Remove operation_repository


async def get_delete_cage_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
) -> DeleteCageUseCase:
    """Crea instancia del caso de uso de eliminación de jaula."""
    return DeleteCageUseCase(cage_repository=cage_repo)


async def get_update_cage_config_use_case(
    cage_repo: CageRepository = Depends(get_cage_repo),
    # operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # DEPRECATED
) -> UpdateCageConfigUseCase:
    """Crea instancia del caso de uso de actualización de configuración."""
    return UpdateCageConfigUseCase(cage_repository=cage_repo, operation_repository=None)  # TODO: Remove operation_repository


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
    return RegisterMortalityUseCase(cage_repository=cage_repo, event_repository=event_repo)


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
    return AdjustPopulationUseCase(cage_repository=cage_repo, event_repository=event_repo)


async def get_population_history_use_case(
    event_repo: PopulationEventRepository = Depends(get_population_event_repo),
) -> GetPopulationHistoryUseCase:
    """Crea instancia del caso de uso de historial de población."""
    return GetPopulationHistoryUseCase(event_repository=event_repo)


async def get_biometry_log_repo(
    session: AsyncSession = Depends(get_session),
) -> BiometryLogRepository:
    """Crea instancia del repositorio de logs de biometría."""
    return BiometryLogRepository(session)


async def get_mortality_log_repo(
    session: AsyncSession = Depends(get_session),
) -> MortalityLogRepository:
    """Crea instancia del repositorio de logs de mortalidad."""
    return MortalityLogRepository(session)


async def get_config_change_log_repo(
    session: AsyncSession = Depends(get_session),
) -> ConfigChangeLogRepository:
    """Crea instancia del repositorio de logs de cambios de configuración."""
    return ConfigChangeLogRepository(session)


async def get_list_biometry_use_case(
    biometry_log_repo: BiometryLogRepository = Depends(get_biometry_log_repo),
) -> ListBiometryUseCase:
    """Crea instancia del caso de uso de listado de biometría."""
    return ListBiometryUseCase(biometry_log_repository=biometry_log_repo)


async def get_list_mortality_use_case(
    mortality_log_repo: MortalityLogRepository = Depends(get_mortality_log_repo),
) -> ListMortalityUseCase:
    """Crea instancia del caso de uso de listado de mortalidad."""
    return ListMortalityUseCase(mortality_log_repository=mortality_log_repo)


async def get_list_config_changes_use_case(
    config_change_log_repo: ConfigChangeLogRepository = Depends(get_config_change_log_repo),
) -> ListConfigChangesUseCase:
    """Crea instancia del caso de uso de listado de cambios de configuración."""
    return ListConfigChangesUseCase(config_change_log_repository=config_change_log_repo)


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
# REMOVED: Old feeding use cases - system being rewritten
# All feeding-related use cases will be recreated from scratch


# ============================================================================
# Type Aliases para Endpoints - System Layout
# ============================================================================

SyncUseCaseDep = Annotated[SyncSystemLayoutUseCase, Depends(get_sync_use_case)]

GetUseCaseDep = Annotated[GetSystemLayoutUseCase, Depends(get_get_use_case)]


# ============================================================================
# Type Aliases para Endpoints - Feeding Line
# ============================================================================

ListFeedingLinesUseCaseDep = Annotated[ListFeedingLinesUseCase, Depends(get_list_feeding_lines_use_case)]

GetFeedingLineUseCaseDep = Annotated[GetFeedingLineUseCase, Depends(get_get_feeding_line_use_case)]

UpdateSelectorUseCaseDep = Annotated[UpdateSelectorUseCase, Depends(get_update_selector_use_case)]

MoveSelectorToSlotUseCaseDep = Annotated[MoveSelectorToSlotUseCase, Depends(get_move_selector_to_slot_use_case)]

ResetSelectorPositionUseCaseDep = Annotated[ResetSelectorPositionUseCase, Depends(get_reset_selector_position_use_case)]

UpdateBlowerUseCaseDep = Annotated[UpdateBlowerUseCase, Depends(get_update_blower_use_case)]

UpdateDoserUseCaseDep = Annotated[UpdateDoserUseCase, Depends(get_update_doser_use_case)]

GetSensorReadingsUseCaseDep = Annotated[GetSensorReadingsUseCase, Depends(get_sensor_readings_use_case)]

GetLineSensorsUseCaseDep = Annotated[GetLineSensorsUseCase, Depends(get_line_sensors_use_case)]

UpdateSensorUseCaseDep = Annotated[UpdateSensorUseCase, Depends(get_update_sensor_use_case)]


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

ToggleFoodActiveUseCaseDep = Annotated[ToggleFoodActiveUseCase, Depends(get_toggle_food_active_use_case)]


# ============================================================================
# Type Aliases para Endpoints - Cage
# ============================================================================

CreateCageUseCaseDep = Annotated[CreateCageUseCase, Depends(get_create_cage_use_case)]

GetCageUseCaseDep = Annotated[GetCageUseCase, Depends(get_get_cage_use_case)]

ListCagesUseCaseDep = Annotated[ListCagesUseCase, Depends(get_list_cages_use_case)]

UpdateCageUseCaseDep = Annotated[UpdateCageUseCase, Depends(get_update_cage_use_case)]

DeleteCageUseCaseDep = Annotated[DeleteCageUseCase, Depends(get_delete_cage_use_case)]

UpdateCageConfigUseCaseDep = Annotated[UpdateCageConfigUseCase, Depends(get_update_cage_config_use_case)]

SetPopulationUseCaseDep = Annotated[SetPopulationUseCase, Depends(get_set_population_use_case)]

RegisterMortalityUseCaseDep = Annotated[RegisterMortalityUseCase, Depends(get_register_mortality_use_case)]

UpdateBiometryUseCaseDep = Annotated[UpdateBiometryUseCase, Depends(get_update_biometry_use_case)]

HarvestUseCaseDep = Annotated[HarvestUseCase, Depends(get_harvest_use_case)]

AdjustPopulationUseCaseDep = Annotated[AdjustPopulationUseCase, Depends(get_adjust_population_use_case)]

GetPopulationHistoryUseCaseDep = Annotated[GetPopulationHistoryUseCase, Depends(get_population_history_use_case)]

ListBiometryUseCaseDep = Annotated[ListBiometryUseCase, Depends(get_list_biometry_use_case)]

ListMortalityUseCaseDep = Annotated[ListMortalityUseCase, Depends(get_list_mortality_use_case)]

ListConfigChangesUseCaseDep = Annotated[ListConfigChangesUseCase, Depends(get_list_config_changes_use_case)]


# ============================================================================
# Type Aliases para Endpoints - Cage Group
# ============================================================================

CreateCageGroupUseCaseDep = Annotated[CreateCageGroupUseCase, Depends(get_create_cage_group_use_case)]

ListCageGroupsUseCaseDep = Annotated[ListCageGroupsUseCase, Depends(get_list_cage_groups_use_case)]

GetCageGroupUseCaseDep = Annotated[GetCageGroupUseCase, Depends(get_get_cage_group_use_case)]

UpdateCageGroupUseCaseDep = Annotated[UpdateCageGroupUseCase, Depends(get_update_cage_group_use_case)]

DeleteCageGroupUseCaseDep = Annotated[DeleteCageGroupUseCase, Depends(get_delete_cage_group_use_case)]


# ============================================================================
# Type Aliases para Endpoints - Feeding
# ============================================================================
# REMOVED: Old feeding use case type aliases - system being rewritten

CheckScheduleUseCaseDep = Annotated[CheckScheduleUseCase, Depends(get_check_schedule_use_case)]

StartManualFeedingUseCaseDep = Annotated[StartManualFeedingUseCase, Depends(get_start_manual_feeding_use_case)]

UpdateFeedingRateUseCaseDep = Annotated[UpdateFeedingRateUseCase, Depends(get_update_feeding_rate_use_case)]

PauseFeedingUseCaseDep = Annotated[PauseFeedingUseCase, Depends(get_pause_feeding_use_case)]

ResumeFeedingUseCaseDep = Annotated[ResumeFeedingUseCase, Depends(get_resume_feeding_use_case)]

CancelFeedingUseCaseDep = Annotated[CancelFeedingUseCase, Depends(get_cancel_feeding_use_case)]

UpdateBlowerPowerUseCaseDep = Annotated[UpdateBlowerPowerUseCase, Depends(get_update_blower_power_use_case)]


# ============================================================================
# Type Aliases para Endpoints - Device Control
# ============================================================================

SetBlowerPowerUseCaseDep = Annotated[SetBlowerPowerUseCase, Depends(get_set_blower_power_use_case)]

SetDoserRateUseCaseDep = Annotated[SetDoserRateUseCase, Depends(get_set_doser_rate_use_case)]

SetDoserSpeedUseCaseDep = Annotated[SetDoserSpeedUseCase, Depends(get_set_doser_speed_use_case)]

MoveSelectorDirectUseCaseDep = Annotated[MoveSelectorToSlotDirectUseCase, Depends(get_move_selector_direct_use_case)]

ResetSelectorDirectUseCaseDep = Annotated[ResetSelectorDirectUseCase, Depends(get_reset_selector_direct_use_case)]

TurnBlowerOnUseCaseDep = Annotated[TurnBlowerOnUseCase, Depends(get_turn_blower_on_use_case)]

TurnBlowerOffUseCaseDep = Annotated[TurnBlowerOffUseCase, Depends(get_turn_blower_off_use_case)]

TurnDoserOnUseCaseDep = Annotated[TurnDoserOnUseCase, Depends(get_turn_doser_on_use_case)]

TurnDoserOffUseCaseDep = Annotated[TurnDoserOffUseCase, Depends(get_turn_doser_off_use_case)]

SetCoolerPowerUseCaseDep = Annotated[SetCoolerPowerUseCase, Depends(get_set_cooler_power_use_case)]

TurnCoolerOnUseCaseDep = Annotated[TurnCoolerOnUseCase, Depends(get_turn_cooler_on_use_case)]

TurnCoolerOffUseCaseDep = Annotated[TurnCoolerOffUseCase, Depends(get_turn_cooler_off_use_case)]


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

GetUnreadCountUseCaseDep = Annotated[GetUnreadCountUseCase, Depends(get_unread_count_use_case)]

UpdateAlertUseCaseDep = Annotated[UpdateAlertUseCase, Depends(get_update_alert_use_case)]

MarkAlertReadUseCaseDep = Annotated[MarkAlertReadUseCase, Depends(get_mark_alert_read_use_case)]

SnoozeAlertUseCaseDep = Annotated[SnoozeAlertUseCase, Depends(get_snooze_alert_use_case)]

MarkAllAlertsReadUseCaseDep = Annotated[MarkAllAlertsReadUseCase, Depends(get_mark_all_alerts_read_use_case)]

CreateAlertUseCaseDep = Annotated[CreateAlertUseCase, Depends(get_create_alert_use_case)]

ListSnoozedAlertsUseCaseDep = Annotated[ListSnoozedAlertsUseCase, Depends(get_list_snoozed_alerts_use_case)]

UnsnoozeAlertUseCaseDep = Annotated[UnsnoozeAlertUseCase, Depends(get_unsnooze_alert_use_case)]

GetAlertCountsUseCaseDep = Annotated[GetAlertCountsUseCase, Depends(get_alert_counts_use_case)]

GetSnoozedCountUseCaseDep = Annotated[GetSnoozedCountUseCase, Depends(get_snoozed_count_use_case)]


# ============================================================================
# Type Aliases para Endpoints - Scheduled Alerts
# ============================================================================

ListScheduledAlertsUseCaseDep = Annotated[ListScheduledAlertsUseCase, Depends(get_list_scheduled_alerts_use_case)]

CreateScheduledAlertUseCaseDep = Annotated[CreateScheduledAlertUseCase, Depends(get_create_scheduled_alert_use_case)]

UpdateScheduledAlertUseCaseDep = Annotated[UpdateScheduledAlertUseCase, Depends(get_update_scheduled_alert_use_case)]

DeleteScheduledAlertUseCaseDep = Annotated[DeleteScheduledAlertUseCase, Depends(get_delete_scheduled_alert_use_case)]

ToggleScheduledAlertUseCaseDep = Annotated[ToggleScheduledAlertUseCase, Depends(get_toggle_scheduled_alert_use_case)]
