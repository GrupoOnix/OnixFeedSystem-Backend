from datetime import date, datetime, time, timezone
from typing import Annotated, Any, List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from zoneinfo import ZoneInfo

from api.dependencies import (
    AccessibleFeedingSessionDep,
    CurrentUserDep,
    get_cancel_feeding_use_case,
    get_cage_feeding_repo,
    get_cage_repo,
    get_daily_feeding_summary_use_case,
    get_feeding_rate_timeline_use_case,
    get_feeding_event_repo,
    get_feeding_session_repo,
    get_get_last_selected_feeding_mode_use_case,
    get_get_last_valid_cyclic_feeding_config_use_case,
    get_get_last_valid_manual_feeding_config_use_case,
    get_line_repo,
    get_list_last_selected_feeding_modes_use_case,
    get_list_last_valid_cyclic_feeding_configs_use_case,
    get_list_last_valid_manual_feeding_configs_use_case,
    get_pause_feeding_use_case,
    get_scheduled_feeding_plan_repo,
    get_scheduled_feeding_planner,
    get_resume_feeding_use_case,
    get_simulated_machine,
    get_start_cyclic_feeding_use_case,
    get_start_manual_feeding_use_case,
    get_silo_inventory_repo,
    get_system_config_repo,
    get_update_blower_power_use_case,
    get_update_cage_mode_use_case,
    get_update_cyclic_cage_amount_use_case,
    get_update_cyclic_cage_rate_use_case,
    get_update_feeding_amount_use_case,
    get_update_feeding_rate_use_case,
    get_user_repo,
    get_upsert_last_selected_feeding_mode_use_case,
    get_upsert_last_valid_cyclic_feeding_config_use_case,
    get_upsert_last_valid_manual_feeding_config_use_case,
)
from application.dtos.manual_feeding_config_dtos import (
    LastSelectedFeedingModePayload,
    LastSelectedFeedingModeResponse,
    LastValidCyclicFeedingConfigPayload,
    LastValidCyclicFeedingConfigResponse,
    LastValidManualFeedingConfigPayload,
    LastValidManualFeedingConfigResponse,
)
from api.models.feeding_models import (
    ActiveSessionItem,
    BatchStatusResponse,
    BatchConsumptionItem,
    BatchStatusSessionCyclic,
    BatchStatusSessionManual,
    CageHistorySummary,
    CageVisitHistory,
    CancelFeedingRequest,
    CyclicFeedingRequest,
    CyclicFeedingResponse,
    CyclicSessionStatusResponse,
    DailyFeedingSummaryResponse,
    DailyFeedingStatsResponse,
    FeedingActionResponse,
    FeedingRateTimelineResponse,
    FeedingSessionStatusResponse,
    ManualFeedingRequest,
    ManualFeedingResponse,
    ScheduledFeedingPlanRequest,
    ScheduledFeedingPlanResponse,
    PauseFeedingRequest,
    RateChartPoint,
    ResumeFeedingRequest,
    SessionHistoryDetail,
    SessionHistoryItem,
    TimelineEvent,
    UpdateCageModeRequest,
    UpdateCageModeResponse,
    UpdateAmountRequest,
    UpdateAmountResponse,
    UpdateBlowerRequest,
    UpdateBlowerResponse,
    UpdateRateRequest,
    UpdateRateResponse,
    VisitHistoryItem,
)
from api.helpers.feeding_status_builders import build_manual_status, build_cyclic_status
from application.use_cases.feeding.control_feeding_use_cases import (
    CancelFeedingUseCase,
    PauseFeedingUseCase,
    ResumeFeedingUseCase,
    UpdateCageModeUseCase,
    UpdateCyclicCageAmountUseCase,
    UpdateCyclicCageRateUseCase,
    UpdateBlowerPowerUseCase,
    UpdateFeedingAmountUseCase,
    UpdateFeedingRateUseCase,
)
from application.use_cases.feeding.start_cyclic_feeding_use_case import (
    StartCyclicFeedingUseCase,
)
from application.use_cases.feeding.start_manual_feeding_use_case import (
    StartManualFeedingUseCase,
)
from application.use_cases.feeding.manual_feeding_config_use_cases import (
    GetLastSelectedFeedingModeUseCase,
    GetLastValidCyclicFeedingConfigUseCase,
    GetLastValidManualFeedingConfigUseCase,
    ListLastSelectedFeedingModesUseCase,
    ListLastValidCyclicFeedingConfigsUseCase,
    ListLastValidManualFeedingConfigsUseCase,
    UpsertLastSelectedFeedingModeUseCase,
    UpsertLastValidCyclicFeedingConfigUseCase,
    UpsertLastValidManualFeedingConfigUseCase,
)
from application.use_cases.feeding.get_daily_feeding_summary_use_case import (
    GetDailyFeedingSummaryUseCase,
)
from application.use_cases.feeding.get_feeding_rate_timeline_use_case import (
    GetFeedingRateTimelineUseCase,
)
from application.services.scheduled_feeding_planner import ScheduledFeedingPlanner
from domain.entities.feeding_event import FeedingEventType
from domain.entities.feeding_session import SessionStatus
from domain.exceptions import FeedingLineUnavailableException
from domain.value_objects import CageId, LineId, UserId
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.persistence.repositories.cage_repository import CageRepository
from infrastructure.persistence.repositories.feeding_event_repository import FeedingEventRepository
from infrastructure.persistence.repositories.feeding_line_repository import FeedingLineRepository
from infrastructure.persistence.repositories.feeding_session_repository import FeedingSessionRepository
from infrastructure.persistence.repositories.silo_inventory_repository import (
    SiloInventoryRepository,
)
from infrastructure.persistence.repositories.system_config_repository import SystemConfigRepository
from infrastructure.persistence.repositories.user_repository import UserRepository
from infrastructure.persistence.repositories.scheduled_feeding_plan_repository import (
    ScheduledFeedingPlanRepository,
)
from infrastructure.persistence.models.scheduled_feeding_plan_model import (
    ScheduledFeedingPlanModel,
)
from infrastructure.services.simulated_machine import SimulatedMachine
from domain.services.scheduled_feeding_time import calculate_remaining_seconds, calculate_window_seconds


router = APIRouter(prefix="/feeding", tags=["Feeding"])


def _scheduled_plan_response(plan: ScheduledFeedingPlanModel) -> ScheduledFeedingPlanResponse:
    cage_plans = plan.cage_plans
    window_seconds = calculate_window_seconds(plan.start_time, plan.end_time)
    return ScheduledFeedingPlanResponse(
        id=str(plan.id),
        name=plan.name,
        line_id=str(plan.line_id),
        group_id=str(plan.group_id),
        doser_id=str(plan.doser_id),
        silo_id=str(plan.silo_id),
        start_time=plan.start_time,
        end_time=plan.end_time,
        timezone=plan.timezone,
        blower_power_percentage=plan.blower_power_percentage,
        wait_after_visit_seconds=plan.wait_after_visit_seconds,
        total_rounds=plan.total_rounds,
        total_requested_kg=plan.total_requested_kg,
        total_planned_kg=plan.total_planned_kg,
        rounding_excess_kg=round(plan.total_planned_kg - plan.total_requested_kg, 6),
        estimated_total_seconds=plan.estimated_total_seconds,
        window_seconds=window_seconds,
        remaining_seconds=calculate_remaining_seconds(window_seconds, plan.estimated_total_seconds),
        cage_plans=cage_plans,
        last_run_on=plan.last_run_on,
        last_session_id=plan.last_session_id,
    )


def _is_admin(current_user: CurrentUserDep) -> bool:
    return current_user.is_superadmin or current_user.role == "admin"


def _assert_plan_access(plan: ScheduledFeedingPlanModel, current_user: CurrentUserDep) -> None:
    if not _is_admin(current_user) and plan.created_by_id != UUID(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan programado no encontrado")


@router.post("/scheduled/preview", response_model=ScheduledFeedingPlanResponse)
async def preview_scheduled_feeding_plan(
    current_user: CurrentUserDep,
    request: ScheduledFeedingPlanRequest,
    planner: Annotated[ScheduledFeedingPlanner, Depends(get_scheduled_feeding_planner)],
) -> ScheduledFeedingPlanResponse:
    try:
        return await planner.calculate(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/scheduled", response_model=list[ScheduledFeedingPlanResponse])
async def list_scheduled_feeding_plans(
    current_user: CurrentUserDep,
    repository: Annotated[ScheduledFeedingPlanRepository, Depends(get_scheduled_feeding_plan_repo)],
) -> list[ScheduledFeedingPlanResponse]:
    plans = (
        await repository.list() if _is_admin(current_user) else await repository.list_for_owner(UUID(current_user.id))
    )
    return [_scheduled_plan_response(plan) for plan in plans]


@router.post("/scheduled", response_model=ScheduledFeedingPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_feeding_plan(
    current_user: CurrentUserDep,
    request: ScheduledFeedingPlanRequest,
    planner: Annotated[ScheduledFeedingPlanner, Depends(get_scheduled_feeding_planner)],
    repository: Annotated[ScheduledFeedingPlanRepository, Depends(get_scheduled_feeding_plan_repo)],
) -> ScheduledFeedingPlanResponse:
    try:
        calculated = await planner.calculate(request)
        line_id = UUID(calculated.line_id)
        await repository.lock_line_schedule(line_id)
        if await repository.find_by_line(line_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La línea ya tiene un plan diario; modifícalo en lugar de crear otro",
            )
        plan = ScheduledFeedingPlanModel(
            line_id=UUID(calculated.line_id),
            group_id=UUID(calculated.group_id),
            doser_id=UUID(calculated.doser_id),
            silo_id=UUID(calculated.silo_id),
            name=calculated.name,
            start_time=calculated.start_time,
            end_time=calculated.end_time,
            timezone=calculated.timezone,
            blower_power_percentage=calculated.blower_power_percentage,
            wait_after_visit_seconds=calculated.wait_after_visit_seconds,
            total_rounds=calculated.total_rounds,
            total_requested_kg=calculated.total_requested_kg,
            total_planned_kg=calculated.total_planned_kg,
            estimated_total_seconds=calculated.estimated_total_seconds,
            cage_plans=[item.model_dump() for item in calculated.cage_plans],
            created_by_id=UUID(current_user.id),
            created_by_name=current_user.username,
        )
        await repository.save(plan)
        return _scheduled_plan_response(plan)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/scheduled/{plan_id}", response_model=ScheduledFeedingPlanResponse)
async def update_scheduled_feeding_plan(
    current_user: CurrentUserDep,
    plan_id: UUID,
    request: ScheduledFeedingPlanRequest,
    planner: Annotated[ScheduledFeedingPlanner, Depends(get_scheduled_feeding_planner)],
    repository: Annotated[ScheduledFeedingPlanRepository, Depends(get_scheduled_feeding_plan_repo)],
) -> ScheduledFeedingPlanResponse:
    plan = await repository.find_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan programado no encontrado")
    _assert_plan_access(plan, current_user)
    if request.line_id != str(plan.line_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El plan no puede cambiar de línea")
    try:
        calculated = await planner.calculate(request)
        for field in (
            "group_id", "doser_id", "silo_id", "name", "start_time", "end_time", "timezone",
            "blower_power_percentage", "wait_after_visit_seconds", "total_rounds",
            "total_requested_kg", "total_planned_kg", "estimated_total_seconds",
        ):
            value = getattr(calculated, field)
            if field in {"group_id", "doser_id", "silo_id"}:
                value = UUID(value)
            setattr(plan, field, value)
        plan.cage_plans = [item.model_dump() for item in calculated.cage_plans]
        await repository.save(plan)
        return _scheduled_plan_response(plan)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/scheduled/{plan_id}/start-preview", response_model=ScheduledFeedingPlanResponse)
async def preview_scheduled_feeding_start(
    current_user: CurrentUserDep,
    plan_id: UUID,
    planner: Annotated[ScheduledFeedingPlanner, Depends(get_scheduled_feeding_planner)],
    repository: Annotated[ScheduledFeedingPlanRepository, Depends(get_scheduled_feeding_plan_repo)],
) -> ScheduledFeedingPlanResponse:
    plan = await repository.find_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan programado no encontrado")
    _assert_plan_access(plan, current_user)
    try:
        preview = await planner.calculate_execution(plan)
        preview.id = str(plan.id)
        return preview
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/scheduled/{plan_id}/start", response_model=CyclicFeedingResponse, status_code=status.HTTP_201_CREATED)
async def start_scheduled_feeding_plan(
    current_user: CurrentUserDep,
    plan_id: UUID,
    planner: Annotated[ScheduledFeedingPlanner, Depends(get_scheduled_feeding_planner)],
    repository: Annotated[ScheduledFeedingPlanRepository, Depends(get_scheduled_feeding_plan_repo)],
    use_case: Annotated[StartCyclicFeedingUseCase, Depends(get_start_cyclic_feeding_use_case)],
) -> CyclicFeedingResponse:
    plan = await repository.find_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan programado no encontrado")
    _assert_plan_access(plan, current_user)
    try:
        execution = await planner.calculate_execution(plan)
        zone = ZoneInfo(plan.timezone)
        local_now = datetime.now(zone)
        deadline = datetime.combine(local_now.date(), time.fromisoformat(plan.end_time), tzinfo=zone)
        result = await use_case.execute(
            CyclicFeedingRequest(
                line_id=str(plan.line_id),
                group_id=str(plan.group_id),
                doser_id=str(plan.doser_id),
                silo_id=str(plan.silo_id),
                blower_power_percentage=plan.blower_power_percentage,
                wait_after_visit_seconds=execution.wait_after_visit_seconds,
                allow_overtime=True,
                hard_deadline_at=deadline,
                execute_pause_physically=True,
                cage_configs=[
                    {
                        "cage_id": item.cage_id,
                        "quantity_kg": item.planned_kg,
                        "visits": execution.total_rounds,
                        "visit_quantities_kg": item.quantity_schedule_kg,
                        "rate_kg_per_min": item.rate_kg_per_min,
                        "mode": item.mode,
                    }
                    for item in execution.cage_plans
                ],
            ),
            operator_id=str(current_user.id),
            operator_name=current_user.full_name,
            actor=current_user.username,
            execution_context={
                "source": "SCHEDULED_PLAN",
                "scheduled_plan_id": str(plan.id),
                "scheduled_plan_name": plan.name,
                "timezone": plan.timezone,
            },
        )
        plan.last_session_id = result.session_id
        plan.last_run_on = local_now.date().isoformat()
        await repository.save(plan)
        return result
    except FeedingLineUnavailableException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/scheduled/{plan_id}/sessions/{session_id}/restore")
async def restore_scheduled_execution_from_base_plan(
    current_user: CurrentUserDep,
    plan_id: UUID,
    session_id: str,
    repository: Annotated[ScheduledFeedingPlanRepository, Depends(get_scheduled_feeding_plan_repo)],
    cage_feeding_repo: Annotated[CageFeedingRepository, Depends(get_cage_feeding_repo)],
    machine: Annotated[SimulatedMachine, Depends(get_simulated_machine)],
    amount_use_case: Annotated[UpdateCyclicCageAmountUseCase, Depends(get_update_cyclic_cage_amount_use_case)],
    rate_use_case: Annotated[UpdateCyclicCageRateUseCase, Depends(get_update_cyclic_cage_rate_use_case)],
    mode_use_case: Annotated[UpdateCageModeUseCase, Depends(get_update_cage_mode_use_case)],
) -> dict[str, Any]:
    plan = await repository.find_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan programado no encontrado")
    _assert_plan_access(plan, current_user)
    if plan.last_session_id != session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La sesión no pertenece a este plan")
    try:
        feedings = await cage_feeding_repo.find_by_session(session_id)
        by_cage = {item.cage_id: item for item in feedings}
        machine_status = await machine.get_status(LineId.from_string(str(plan.line_id)))
        restored: list[str] = []
        for base in plan.cage_plans:
            current = by_cage.get(base["cage_id"])
            if not current or base["mode"] == "FASTING" or current.completed_visits >= current.programmed_visits:
                continue
            live = machine_status.dispensed_kg if machine_status.cage_feeding_id == current.id else 0.0
            if base["mode"] == "NORMAL":
                safe_total = max(float(base["planned_kg"]), current.dispensed_kg + live)
                await amount_use_case.execute(session_id, current.cage_id, safe_total)
                await rate_use_case.execute(session_id, current.cage_id, float(base["rate_kg_per_min"]))
            await mode_use_case.execute(
                session_id=session_id,
                cage_id=current.cage_id,
                new_mode=base["mode"],
                operator_id=str(current_user.id),
            )
            restored.append(current.cage_id)
        return {"message": "Configuración original restaurada y tiempo restante recalculado", "cage_ids": restored}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/scheduled/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_feeding_plan(
    current_user: CurrentUserDep,
    plan_id: UUID,
    repository: Annotated[ScheduledFeedingPlanRepository, Depends(get_scheduled_feeding_plan_repo)],
) -> None:
    plan = await repository.find_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan programado no encontrado")
    _assert_plan_access(plan, current_user)
    await repository.delete(plan)


@router.post("/manual/start", status_code=status.HTTP_201_CREATED)
async def start_manual_feeding(
    current_user: CurrentUserDep,
    request: ManualFeedingRequest,
    use_case: Annotated[StartManualFeedingUseCase, Depends(get_start_manual_feeding_use_case)],
) -> ManualFeedingResponse:
    try:
        return await use_case.execute(
            request,
            operator_id=str(current_user.id),
            operator_name=current_user.full_name,
            actor=current_user.username,
        )
    except FeedingLineUnavailableException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al iniciar alimentación manual: {str(e)}",
        )


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_feeding(
    current_user: CurrentUserDep,
    request: ManualFeedingRequest,
    use_case: Annotated[StartManualFeedingUseCase, Depends(get_start_manual_feeding_use_case)],
) -> ManualFeedingResponse:
    return await start_manual_feeding(
        current_user=current_user,
        request=request,
        use_case=use_case,
    )


@router.get("/manual/last-valid-configs")
async def list_last_valid_manual_feeding_configs(
    current_user: CurrentUserDep,
    use_case: Annotated[
        ListLastValidManualFeedingConfigsUseCase,
        Depends(get_list_last_valid_manual_feeding_configs_use_case),
    ],
) -> dict[str, LastValidManualFeedingConfigResponse]:
    return await use_case.execute()


@router.get("/manual/lines/{line_id}/last-valid-config")
async def get_last_valid_manual_feeding_config(
    current_user: CurrentUserDep,
    line_id: str,
    use_case: Annotated[
        GetLastValidManualFeedingConfigUseCase,
        Depends(get_get_last_valid_manual_feeding_config_use_case),
    ],
) -> LastValidManualFeedingConfigResponse:
    try:
        return await use_case.execute(line_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/manual/lines/{line_id}/last-valid-config")
async def upsert_last_valid_manual_feeding_config(
    current_user: CurrentUserDep,
    line_id: str,
    request: LastValidManualFeedingConfigPayload,
    use_case: Annotated[
        UpsertLastValidManualFeedingConfigUseCase,
        Depends(get_upsert_last_valid_manual_feeding_config_use_case),
    ],
) -> LastValidManualFeedingConfigResponse:
    try:
        return await use_case.execute(line_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/line-mode-preferences")
async def list_last_selected_feeding_modes(
    current_user: CurrentUserDep,
    use_case: Annotated[
        ListLastSelectedFeedingModesUseCase,
        Depends(get_list_last_selected_feeding_modes_use_case),
    ],
) -> dict[str, LastSelectedFeedingModeResponse]:
    return await use_case.execute()


@router.get("/lines/{line_id}/mode-preference")
async def get_last_selected_feeding_mode(
    current_user: CurrentUserDep,
    line_id: str,
    use_case: Annotated[
        GetLastSelectedFeedingModeUseCase,
        Depends(get_get_last_selected_feeding_mode_use_case),
    ],
) -> LastSelectedFeedingModeResponse:
    try:
        return await use_case.execute(line_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/lines/{line_id}/mode-preference")
async def upsert_last_selected_feeding_mode(
    current_user: CurrentUserDep,
    line_id: str,
    request: LastSelectedFeedingModePayload,
    use_case: Annotated[
        UpsertLastSelectedFeedingModeUseCase,
        Depends(get_upsert_last_selected_feeding_mode_use_case),
    ],
) -> LastSelectedFeedingModeResponse:
    try:
        return await use_case.execute(line_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cyclic/last-valid-configs")
async def list_last_valid_cyclic_feeding_configs(
    current_user: CurrentUserDep,
    use_case: Annotated[
        ListLastValidCyclicFeedingConfigsUseCase,
        Depends(get_list_last_valid_cyclic_feeding_configs_use_case),
    ],
) -> dict[str, LastValidCyclicFeedingConfigResponse]:
    return await use_case.execute()


@router.get("/cyclic/lines/{line_id}/last-valid-config")
async def get_last_valid_cyclic_feeding_config(
    current_user: CurrentUserDep,
    line_id: str,
    use_case: Annotated[
        GetLastValidCyclicFeedingConfigUseCase,
        Depends(get_get_last_valid_cyclic_feeding_config_use_case),
    ],
) -> LastValidCyclicFeedingConfigResponse:
    try:
        return await use_case.execute(line_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/cyclic/lines/{line_id}/last-valid-config")
async def upsert_last_valid_cyclic_feeding_config(
    current_user: CurrentUserDep,
    line_id: str,
    request: LastValidCyclicFeedingConfigPayload,
    use_case: Annotated[
        UpsertLastValidCyclicFeedingConfigUseCase,
        Depends(get_upsert_last_valid_cyclic_feeding_config_use_case),
    ],
) -> LastValidCyclicFeedingConfigResponse:
    try:
        return await use_case.execute(line_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cyclic/start", status_code=status.HTTP_201_CREATED)
async def start_cyclic_feeding(
    current_user: CurrentUserDep,
    request: CyclicFeedingRequest,
    use_case: Annotated[StartCyclicFeedingUseCase, Depends(get_start_cyclic_feeding_use_case)],
) -> CyclicFeedingResponse:
    try:
        return await use_case.execute(
            request,
            operator_id=str(current_user.id),
            operator_name=current_user.full_name,
            actor=current_user.username,
        )
    except FeedingLineUnavailableException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al iniciar alimentación cíclica: {str(e)}",
        )


@router.patch("/sessions/{session_id}/rate")
async def update_feeding_rate(
    current_user: CurrentUserDep,
    session_id: str,
    request: UpdateRateRequest,
    use_case: Annotated[UpdateFeedingRateUseCase, Depends(get_update_feeding_rate_use_case)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> UpdateRateResponse:
    try:
        new_rate = await use_case.execute(session_id, request.rate_kg_per_min)
        return UpdateRateResponse(
            message="Tasa de alimentación actualizada",
            new_rate_kg_per_min=new_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/sessions/{session_id}/amount")
async def update_feeding_amount(
    current_user: CurrentUserDep,
    session_id: str,
    request: UpdateAmountRequest,
    use_case: Annotated[UpdateFeedingAmountUseCase, Depends(get_update_feeding_amount_use_case)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> UpdateAmountResponse:
    try:
        new_amount = await use_case.execute(session_id, request.amount_kg)
        return UpdateAmountResponse(
            message="Cantidad de alimentación actualizada",
            new_amount_kg=new_amount,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/sessions/{session_id}/cages/{cage_id}/mode")
async def update_cage_mode(
    current_user: CurrentUserDep,
    session_id: str,
    cage_id: str,
    request: UpdateCageModeRequest,
    use_case: Annotated[UpdateCageModeUseCase, Depends(get_update_cage_mode_use_case)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> UpdateCageModeResponse:
    try:
        previous_mode, new_mode = await use_case.execute(
            session_id=session_id,
            cage_id=cage_id,
            new_mode=request.mode,
            operator_id=str(current_user.id),
        )
        return UpdateCageModeResponse(
            message="Modo de jaula actualizado para próximas visitas",
            cage_id=cage_id,
            previous_mode=previous_mode,
            new_mode=new_mode,
            applied_immediately=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/sessions/{session_id}/cages/{cage_id}/amount")
async def update_cyclic_cage_amount(
    current_user: CurrentUserDep,
    session_id: str,
    cage_id: str,
    request: UpdateAmountRequest,
    use_case: Annotated[
        UpdateCyclicCageAmountUseCase,
        Depends(get_update_cyclic_cage_amount_use_case),
    ],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> UpdateAmountResponse:
    try:
        update = await use_case.execute(session_id, cage_id, request.amount_kg)
        return UpdateAmountResponse(
            message="Cantidad de alimentación de jaula actualizada",
            new_amount_kg=update.total_amount_kg,
            current_visit_target_kg=update.current_visit_target_kg,
            remaining_visit_quantities_kg=update.remaining_visit_quantities_kg,
            applied_immediately=update.applied_immediately,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/sessions/{session_id}/cages/{cage_id}/rate")
async def update_cyclic_cage_rate(
    current_user: CurrentUserDep,
    session_id: str,
    cage_id: str,
    request: UpdateRateRequest,
    use_case: Annotated[
        UpdateCyclicCageRateUseCase,
        Depends(get_update_cyclic_cage_rate_use_case),
    ],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> UpdateRateResponse:
    try:
        new_rate = await use_case.execute(session_id, cage_id, request.rate_kg_per_min)
        return UpdateRateResponse(
            message="Tasa de alimentación de jaula actualizada",
            new_rate_kg_per_min=new_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/sessions/{session_id}/pause")
async def pause_feeding(
    current_user: CurrentUserDep,
    session_id: str,
    request: PauseFeedingRequest,
    use_case: Annotated[PauseFeedingUseCase, Depends(get_pause_feeding_use_case)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> FeedingActionResponse:
    try:
        await use_case.execute(
            session_id,
            operator_id=str(current_user.id),
            actor=current_user.username,
            reason=request.reason,
        )
        return FeedingActionResponse(message="Alimentación pausada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/sessions/{session_id}/resume")
async def resume_feeding(
    current_user: CurrentUserDep,
    session_id: str,
    request: ResumeFeedingRequest,
    use_case: Annotated[ResumeFeedingUseCase, Depends(get_resume_feeding_use_case)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> FeedingActionResponse:
    try:
        await use_case.execute(
            session_id,
            operator_id=str(current_user.id),
            actor=current_user.username,
        )
        return FeedingActionResponse(message="Alimentación reanudada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/sessions/{session_id}/cancel")
async def cancel_feeding(
    current_user: CurrentUserDep,
    session_id: str,
    request: CancelFeedingRequest,
    use_case: Annotated[CancelFeedingUseCase, Depends(get_cancel_feeding_use_case)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> FeedingActionResponse:
    try:
        await use_case.execute(
            session_id,
            operator_id=str(current_user.id),
            actor=current_user.username,
            reason=request.reason,
        )
        return FeedingActionResponse(message="Alimentación cancelada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/sessions/{session_id}/blower")
async def update_blower_power(
    current_user: CurrentUserDep,
    session_id: str,
    request: UpdateBlowerRequest,
    use_case: Annotated[UpdateBlowerPowerUseCase, Depends(get_update_blower_power_use_case)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> UpdateBlowerResponse:
    try:
        power = await use_case.execute(session_id, request.power_percentage)
        return UpdateBlowerResponse(
            message="Potencia del blower actualizada",
            power_percentage=power,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/{session_id}/cyclic-status")
async def get_cyclic_feeding_status(
    current_user: CurrentUserDep,
    session_id: str,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    cage_feeding_repo: Annotated[CageFeedingRepository, Depends(get_cage_feeding_repo)],
    cage_repo: Annotated[CageRepository, Depends(get_cage_repo)],
    line_repo: Annotated[FeedingLineRepository, Depends(get_line_repo)],
    machine: Annotated[SimulatedMachine, Depends(get_simulated_machine)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> CyclicSessionStatusResponse:
    try:
        session = await session_repo.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sesión {session_id} no encontrada")

        status_data = await build_cyclic_status(session, cage_feeding_repo, cage_repo, line_repo, machine)

        from api.models.feeding_models import CageSummaryItem, ActiveCageInfo

        cages_summary = [CageSummaryItem(**cage_data) for cage_data in status_data["cages_summary"]]

        active_cage = ActiveCageInfo(**status_data["active_cage"]) if status_data["active_cage"] else None

        return CyclicSessionStatusResponse(
            session_id=status_data["session_id"],
            session_status=status_data["status"],
            line_id=status_data["line_id"],
            started_at=status_data["started_at"],
            total_programmed_kg=status_data["total_programmed_kg"],
            total_dispensed_kg=status_data["total_dispensed_kg"],
            overall_completion_percentage=status_data["overall_completion_percentage"],
            total_rounds=status_data["total_rounds"],
            current_round=status_data["current_round"],
            active_cage=active_cage,
            cages_summary=cages_summary,
            execution_context=status_data["execution_context"],
            server_timestamp=status_data["server_timestamp"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats/daily")
async def get_daily_feeding_stats(
    current_user: CurrentUserDep,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    config_repo: Annotated[SystemConfigRepository, Depends(get_system_config_repo)],
    date_param: Optional[str] = Query(default=None, alias="date", description="Fecha YYYY-MM-DD (default: hoy)"),
    line_id: Optional[str] = Query(default=None, description="Filtrar por línea"),
) -> DailyFeedingStatsResponse:
    try:
        system_config = await config_repo.get()
        tz = ZoneInfo(system_config.timezone_id)

        if date_param:
            target_date = date.fromisoformat(date_param)
        else:
            target_date = datetime.now(tz).date()

        day_start = datetime.combine(target_date, time.min, tzinfo=tz).astimezone(timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=tz).astimezone(timezone.utc)

        sessions = await session_repo.list_by_date_range(day_start, day_end)

        if not _is_admin(current_user):
            sessions = [session for session in sessions if session.operator_id == current_user.id]

        if line_id:
            sessions = [s for s in sessions if s.line_id == line_id]

        total_dispensed_kg = sum(s.total_dispensed_kg for s in sessions)
        total_programmed_kg = sum(s.total_programmed_kg for s in sessions)
        sessions_completed = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)
        sessions_in_progress = sum(1 for s in sessions if s.status in (SessionStatus.IN_PROGRESS, SessionStatus.PAUSED))

        return DailyFeedingStatsResponse(
            date=target_date.isoformat(),
            total_dispensed_kg=round(total_dispensed_kg, 2),
            total_programmed_kg=round(total_programmed_kg, 2),
            sessions_completed=sessions_completed,
            sessions_in_progress=sessions_in_progress,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats/daily-summary")
async def get_daily_feeding_summary(
    current_user: CurrentUserDep,
    use_case: Annotated[GetDailyFeedingSummaryUseCase, Depends(get_daily_feeding_summary_use_case)],
    start_date: date = Query(description="Fecha inicial YYYY-MM-DD"),
    end_date: date = Query(description="Fecha final YYYY-MM-DD"),
    line_id: Optional[UUID] = Query(default=None, description="Filtrar por línea"),
    type: Optional[Literal["MANUAL", "CYCLIC"]] = Query(default=None, description="Filtrar por tipo"),
) -> DailyFeedingSummaryResponse:
    try:
        dto = await use_case.execute(
            start_date=start_date,
            end_date=end_date,
            line_id=str(line_id) if line_id else None,
            feeding_type=type,
            operator_id=None if _is_admin(current_user) else current_user.id,
        )
        return DailyFeedingSummaryResponse.model_validate(dto, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats/rate-timeline")
async def get_feeding_rate_timeline(
    current_user: CurrentUserDep,
    use_case: Annotated[GetFeedingRateTimelineUseCase, Depends(get_feeding_rate_timeline_use_case)],
    start_at: datetime = Query(description="Inicio del rango en ISO UTC"),
    end_at: datetime = Query(description="Fin del rango en ISO UTC"),
    line_id: Optional[UUID] = Query(default=None, description="Filtrar por línea"),
    cage_id: Optional[UUID] = Query(default=None, description="Filtrar por jaula"),
    type: Optional[Literal["MANUAL", "CYCLIC"]] = Query(default=None, description="Filtrar por tipo"),
    bucket_seconds: int = Query(default=60, ge=1, le=3600),
    include_series: Literal["lines", "cages", "sessions"] = Query(default="lines"),
) -> FeedingRateTimelineResponse:
    try:
        dto = await use_case.execute(
            start_at=start_at,
            end_at=end_at,
            line_id=str(line_id) if line_id else None,
            cage_id=str(cage_id) if cage_id else None,
            feeding_type=type,
            bucket_seconds=bucket_seconds,
            include_series=include_series,
            operator_id=None if _is_admin(current_user) else current_user.id,
        )
        return FeedingRateTimelineResponse.model_validate(dto, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/sessions")
async def list_sessions_history(
    current_user: CurrentUserDep,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    config_repo: Annotated[SystemConfigRepository, Depends(get_system_config_repo)],
    line_repo: Annotated[FeedingLineRepository, Depends(get_line_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    date_param: Optional[str] = Query(
        default=None,
        alias="date",
        description="Fecha YYYY-MM-DD (default: hoy en timezone del sistema)",
    ),
    line_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
) -> List[SessionHistoryItem]:
    try:
        system_config = await config_repo.get()
        tz = ZoneInfo(system_config.timezone_id)

        if date_param:
            target_date = date.fromisoformat(date_param)
        else:
            target_date = datetime.now(tz).date()

        day_start = datetime.combine(target_date, time.min, tzinfo=tz).astimezone(timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=tz).astimezone(timezone.utc)

        sessions = await session_repo.list_by_date_range(day_start, day_end)

        if not _is_admin(current_user):
            sessions = [session for session in sessions if session.operator_id == current_user.id]

        if line_id:
            sessions = [s for s in sessions if s.line_id == line_id]
        if status_filter:
            sessions = [s for s in sessions if s.status.value == status_filter]

        line_name_cache: dict[str, str] = {}
        operator_name_cache: dict[str, Optional[str]] = {}

        operator_ids = {s.operator_id for s in sessions if s.operator_id}
        for operator_id in operator_ids:
            user = await user_repo.find_by_id(UserId.from_string(operator_id))
            operator_name_cache[operator_id] = user.full_name if user else None

        result = []
        for s in sessions:
            if s.line_id not in line_name_cache:
                feeding_line = await line_repo.find_by_id(LineId.from_string(s.line_id))
                line_name_cache[s.line_id] = feeding_line.name.value if feeding_line else s.line_id

            duration = None
            if s.actual_start and s.actual_end:
                duration = (s.actual_end - s.actual_start).total_seconds()
            result.append(
                SessionHistoryItem(
                    session_id=s.id,
                    type=s.type.value,
                    status=s.status.value,
                    line_id=s.line_id,
                    line_name=line_name_cache[s.line_id],
                    operator_id=s.operator_id,
                    operator_name=operator_name_cache.get(s.operator_id),
                    started_at=s.actual_start,
                    ended_at=s.actual_end,
                    duration_seconds=duration,
                    total_programmed_kg=s.total_programmed_kg,
                    total_dispensed_kg=s.total_dispensed_kg,
                )
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/sessions/{session_id}")
async def get_session_history_detail(
    current_user: CurrentUserDep,
    session_id: str,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    event_repo: Annotated[FeedingEventRepository, Depends(get_feeding_event_repo)],
    line_repo: Annotated[FeedingLineRepository, Depends(get_line_repo)],
    cage_repo: Annotated[CageRepository, Depends(get_cage_repo)],
    inventory_repo: Annotated[SiloInventoryRepository, Depends(get_silo_inventory_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> SessionHistoryDetail:
    try:
        session = await session_repo.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sesión {session_id} no encontrada")

        operator_name = None
        if session.operator_id:
            user = await user_repo.find_by_id(UserId.from_string(session.operator_id))
            operator_name = user.full_name if user else None

        feeding_line = await line_repo.find_by_id(LineId.from_string(session.line_id))
        line_name = feeding_line.name.value if feeding_line else session.line_id

        all_events = await event_repo.find_by_session(session_id)
        all_events_asc = sorted(all_events, key=lambda e: e.timestamp)

        timeline_types = {
            FeedingEventType.SESSION_STARTED,
            FeedingEventType.SESSION_PAUSED,
            FeedingEventType.SESSION_RESUMED,
            FeedingEventType.SESSION_CANCELLED,
            FeedingEventType.SESSION_INTERRUPTED,
            FeedingEventType.SESSION_COMPLETED,
            FeedingEventType.RATE_CHANGED,
            FeedingEventType.CAGE_MODE_CHANGED,
        }

        timeline = [
            TimelineEvent(
                timestamp=e.timestamp,
                event_type=e.event_type.value,
                data=e.data,
            )
            for e in all_events_asc
            if e.event_type in timeline_types
        ]

        visit_completed_events = [e for e in all_events_asc if e.event_type == FeedingEventType.VISIT_COMPLETED]

        cage_visit_durations: dict[str, list[float]] = {}
        for e in visit_completed_events:
            cid = e.data.get("cage_id")
            dur = e.data.get("duration_seconds")
            if cid and dur is not None:
                cage_visit_durations.setdefault(cid, []).append(dur)

        cage_name_cache: dict[str, str] = {}
        cages = []
        for cf in session.cage_feedings:
            if cf.cage_id not in cage_name_cache:
                cage = await cage_repo.find_by_id(CageId.from_string(cf.cage_id))
                cage_name_cache[cf.cage_id] = cage.name.value if cage else cf.cage_id
            durations = cage_visit_durations.get(cf.cage_id, [])
            avg_duration = sum(durations) / len(durations) if durations else None
            cages.append(
                CageHistorySummary(
                    cage_id=cf.cage_id,
                    cage_name=cage_name_cache[cf.cage_id],
                    mode=cf.mode.value,
                    programmed_kg=cf.programmed_kg,
                    total_dispensed_kg=cf.dispensed_kg,
                    programmed_visits=cf.programmed_visits,
                    completed_visits=cf.completed_visits,
                    avg_visit_duration_seconds=avg_duration,
                )
            )

        rate_changed_events = [e for e in all_events_asc if e.event_type == FeedingEventType.RATE_CHANGED]

        rate_chart: List[RateChartPoint] = []
        normal_cfs = [cf for cf in session.cage_feedings if cf.mode.value == "NORMAL"]
        if normal_cfs and session.actual_start:
            initial_rate = normal_cfs[0].rate_kg_per_min
            rate_chart.append(RateChartPoint(timestamp=session.actual_start, rate_kg_per_min=initial_rate))
            last_rate = initial_rate
            for e in rate_changed_events:
                new_rate = e.data.get("new_rate", last_rate)
                rate_chart.append(RateChartPoint(timestamp=e.timestamp, rate_kg_per_min=new_rate))
                last_rate = new_rate
            end_time = session.actual_end or datetime.now(timezone.utc)
            if rate_chart and rate_chart[-1].timestamp != end_time:
                rate_chart.append(RateChartPoint(timestamp=end_time, rate_kg_per_min=last_rate))

        duration = None
        if session.actual_start and session.actual_end:
            duration = (session.actual_end - session.actual_start).total_seconds()
        batch_consumptions = [
            BatchConsumptionItem(**item) for item in await inventory_repo.list_session_consumptions(session_id)
        ]

        return SessionHistoryDetail(
            session_id=session.id,
            type=session.type.value,
            status=session.status.value,
            line_id=session.line_id,
            line_name=line_name,
            operator_id=session.operator_id,
            operator_name=operator_name,
            started_at=session.actual_start,
            ended_at=session.actual_end,
            duration_seconds=duration,
            total_programmed_kg=session.total_programmed_kg,
            total_dispensed_kg=session.total_dispensed_kg,
            cages=cages,
            timeline=timeline,
            rate_chart=rate_chart,
            batch_consumptions=batch_consumptions,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/sessions/{session_id}/cages/{cage_id}/visits")
async def get_cage_visit_history(
    current_user: CurrentUserDep,
    session_id: str,
    cage_id: str,
    event_repo: Annotated[FeedingEventRepository, Depends(get_feeding_event_repo)],
    cage_repo: Annotated[CageRepository, Depends(get_cage_repo)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> CageVisitHistory:
    try:
        cage = await cage_repo.find_by_id(CageId.from_string(cage_id))
        cage_name = cage.name.value if cage else cage_id

        visit_events = await event_repo.find_by_type(session_id, FeedingEventType.VISIT_COMPLETED)
        cage_events = sorted(
            [e for e in visit_events if e.data.get("cage_id") == cage_id],
            key=lambda e: e.timestamp,
        )

        visits = []
        for e in cage_events:
            dispensed_grams = e.data.get("dispensed_grams", 0.0)
            visits.append(
                VisitHistoryItem(
                    visit_number=e.data.get("visit_number", 0),
                    dispensed_kg=dispensed_grams / 1000,
                    dispensed_grams=dispensed_grams,
                    duration_seconds=e.data.get("duration_seconds", 0.0),
                    completed_at=e.timestamp,
                    is_empty_visit=e.data.get("is_empty_visit", False),
                )
            )

        total_dispensed = sum(v.dispensed_kg for v in visits)
        avg_duration = sum(v.duration_seconds for v in visits) / len(visits) if visits else None

        return CageVisitHistory(
            session_id=session_id,
            cage_id=cage_id,
            cage_name=cage_name,
            visits=visits,
            total_dispensed_kg=total_dispensed,
            avg_duration_seconds=avg_duration,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/active")
async def list_active_sessions(
    current_user: CurrentUserDep,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
) -> List[ActiveSessionItem]:
    try:
        sessions = await session_repo.find_active_sessions(hours_back=24)
        if not _is_admin(current_user):
            sessions = [session for session in sessions if session.operator_id == current_user.id]
        return [
            ActiveSessionItem(
                session_id=s.id,
                line_id=s.line_id,
                type=s.type.value,
                status=s.status.value,
                started_at=s.actual_start,
                execution_context=s.execution_context,
            )
            for s in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/status/batch")
async def get_batch_session_status(
    current_user: CurrentUserDep,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    cage_feeding_repo: Annotated[CageFeedingRepository, Depends(get_cage_feeding_repo)],
    cage_repo: Annotated[CageRepository, Depends(get_cage_repo)],
    line_repo: Annotated[FeedingLineRepository, Depends(get_line_repo)],
    machine: Annotated[SimulatedMachine, Depends(get_simulated_machine)],
    session_ids: str = Query(..., description="Comma-separated session UUIDs"),
) -> BatchStatusResponse:
    try:
        session_id_list = [sid.strip() for sid in session_ids.split(",") if sid.strip()]
        if not session_id_list:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_ids no puede estar vacío")
        if len(session_id_list) > 50:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Máximo 50 sesiones por request")

        from api.models.feeding_models import CageSummaryItem, ActiveCageInfo

        results: list[Any] = []
        for session_id in session_id_list:
            try:
                session = await session_repo.find_by_id(session_id)
                if not session:
                    continue
                if not _is_admin(current_user) and session.operator_id != current_user.id:
                    continue

                if session.type.value == "MANUAL":
                    status_data = await build_manual_status(session, cage_repo, machine)
                    results.append(BatchStatusSessionManual(**status_data))
                elif session.type.value == "CYCLIC":
                    status_data = await build_cyclic_status(session, cage_feeding_repo, cage_repo, line_repo, machine)
                    cages_summary = [CageSummaryItem(**cage_data) for cage_data in status_data["cages_summary"]]
                    active_cage = ActiveCageInfo(**status_data["active_cage"]) if status_data["active_cage"] else None
                    results.append(
                        BatchStatusSessionCyclic(
                            session_id=status_data["session_id"],
                            line_id=status_data["line_id"],
                            type=status_data["type"],
                            status=status_data["status"],
                            started_at=status_data["started_at"],
                            total_programmed_kg=status_data["total_programmed_kg"],
                            total_dispensed_kg=status_data["total_dispensed_kg"],
                            overall_completion_percentage=status_data["overall_completion_percentage"],
                            current_round=status_data["current_round"],
                            total_rounds=status_data["total_rounds"],
                            active_cage=active_cage,
                            cages_summary=cages_summary,
                            execution_context=status_data["execution_context"],
                            server_timestamp=status_data["server_timestamp"],
                        )
                    )
            except Exception:
                continue

        return BatchStatusResponse(sessions=results, server_timestamp=datetime.now(timezone.utc))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/{session_id}/status")
async def get_feeding_status(
    current_user: CurrentUserDep,
    session_id: str,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    cage_repo: Annotated[CageRepository, Depends(get_cage_repo)],
    machine: Annotated[SimulatedMachine, Depends(get_simulated_machine)],
    accessible_session: AccessibleFeedingSessionDep = None,
) -> FeedingSessionStatusResponse:
    try:
        session = await session_repo.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sesión {session_id} no encontrada")

        status_data = await build_manual_status(session, cage_repo, machine)

        return FeedingSessionStatusResponse(
            session_id=status_data["session_id"],
            session_status=status_data["status"],
            line_id=status_data["line_id"],
            started_at=status_data["started_at"],
            cage_id=status_data["cage_id"],
            cage_name=status_data["cage_name"],
            programmed_kg=status_data["programmed_kg"],
            dispensed_kg_bd=status_data["dispensed_kg_bd"],
            dispensed_kg_live=status_data["dispensed_kg_live"],
            rate_kg_per_min=session.cage_feedings[0].rate_kg_per_min,
            current_flow_rate_kg_per_min=status_data["current_flow_rate_kg_per_min"],
            is_running=status_data["is_running"],
            is_paused=status_data["is_paused"],
            completion_percentage=status_data["completion_percentage"],
            current_stage=status_data["current_stage"],
            server_timestamp=status_data["server_timestamp"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
