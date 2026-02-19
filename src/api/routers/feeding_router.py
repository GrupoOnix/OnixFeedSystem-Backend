from datetime import date, datetime, time, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from zoneinfo import ZoneInfo

from api.dependencies import (
    get_cancel_feeding_use_case,
    get_cage_feeding_repo,
    get_cage_repo,
    get_feeding_event_repo,
    get_feeding_session_repo,
    get_line_repo,
    get_pause_feeding_use_case,
    get_resume_feeding_use_case,
    get_simulated_machine,
    get_start_cyclic_feeding_use_case,
    get_start_manual_feeding_use_case,
    get_system_config_repo,
    get_update_blower_power_use_case,
    get_update_feeding_rate_use_case,
)
from api.models.feeding_models import (
    ActiveSessionItem,
    BatchStatusResponse,
    BatchStatusSessionCyclic,
    BatchStatusSessionManual,
    CageFeedingStatusItem,
    CageHistorySummary,
    CageVisitHistory,
    CancelFeedingRequest,
    CyclicFeedingRequest,
    CyclicFeedingResponse,
    CyclicSessionStatusResponse,
    FeedingActionResponse,
    FeedingSessionStatusResponse,
    ManualFeedingRequest,
    ManualFeedingResponse,
    PauseFeedingRequest,
    RateChartPoint,
    ResumeFeedingRequest,
    SessionHistoryDetail,
    SessionHistoryItem,
    TimelineEvent,
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
    UpdateBlowerPowerUseCase,
    UpdateFeedingRateUseCase,
)
from application.use_cases.feeding.start_cyclic_feeding_use_case import (
    StartCyclicFeedingUseCase,
)
from application.use_cases.feeding.start_manual_feeding_use_case import (
    StartManualFeedingUseCase,
)
from domain.entities.cage_feeding import CageFeedingMode
from domain.entities.feeding_event import FeedingEventType
from domain.value_objects import CageId, LineId
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.persistence.repositories.cage_repository import CageRepository
from infrastructure.persistence.repositories.feeding_event_repository import FeedingEventRepository
from infrastructure.persistence.repositories.feeding_line_repository import FeedingLineRepository
from infrastructure.persistence.repositories.feeding_session_repository import FeedingSessionRepository
from infrastructure.persistence.repositories.system_config_repository import SystemConfigRepository
from infrastructure.services.simulated_machine import SimulatedMachine


router = APIRouter(prefix="/feeding", tags=["Feeding"])


@router.post("/manual/start", status_code=status.HTTP_201_CREATED)
async def start_manual_feeding(
    request: ManualFeedingRequest,
    use_case: Annotated[StartManualFeedingUseCase, Depends(get_start_manual_feeding_use_case)]
) -> ManualFeedingResponse:
    try:
        return await use_case.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al iniciar alimentación manual: {str(e)}"
        )


@router.post("/cyclic/start", status_code=status.HTTP_201_CREATED)
async def start_cyclic_feeding(
    request: CyclicFeedingRequest,
    use_case: Annotated[StartCyclicFeedingUseCase, Depends(get_start_cyclic_feeding_use_case)],
) -> CyclicFeedingResponse:
    try:
        return await use_case.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al iniciar alimentación cíclica: {str(e)}",
        )


@router.patch("/sessions/{session_id}/rate")
async def update_feeding_rate(
    session_id: str,
    request: UpdateRateRequest,
    use_case: Annotated[UpdateFeedingRateUseCase, Depends(get_update_feeding_rate_use_case)],
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


@router.post("/sessions/{session_id}/pause")
async def pause_feeding(
    session_id: str,
    request: PauseFeedingRequest,
    use_case: Annotated[PauseFeedingUseCase, Depends(get_pause_feeding_use_case)],
) -> FeedingActionResponse:
    try:
        await use_case.execute(session_id, request.operator_id, request.reason)
        return FeedingActionResponse(message="Alimentación pausada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/sessions/{session_id}/resume")
async def resume_feeding(
    session_id: str,
    request: ResumeFeedingRequest,
    use_case: Annotated[ResumeFeedingUseCase, Depends(get_resume_feeding_use_case)],
) -> FeedingActionResponse:
    try:
        await use_case.execute(session_id, request.operator_id)
        return FeedingActionResponse(message="Alimentación reanudada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/sessions/{session_id}/cancel")
async def cancel_feeding(
    session_id: str,
    request: CancelFeedingRequest,
    use_case: Annotated[CancelFeedingUseCase, Depends(get_cancel_feeding_use_case)],
) -> FeedingActionResponse:
    try:
        await use_case.execute(session_id, request.operator_id, request.reason)
        return FeedingActionResponse(message="Alimentación cancelada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/sessions/{session_id}/blower")
async def update_blower_power(
    session_id: str,
    request: UpdateBlowerRequest,
    use_case: Annotated[UpdateBlowerPowerUseCase, Depends(get_update_blower_power_use_case)],
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
    session_id: str,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    cage_feeding_repo: Annotated[CageFeedingRepository, Depends(get_cage_feeding_repo)],
    machine: Annotated[SimulatedMachine, Depends(get_simulated_machine)],
) -> CyclicSessionStatusResponse:
    try:
        session = await session_repo.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sesión {session_id} no encontrada")

        status_data = await build_cyclic_status(session, cage_feeding_repo, machine)

        cages = [
            CageFeedingStatusItem(**cage_data)
            for cage_data in status_data["cages_summary"]
        ]

        return CyclicSessionStatusResponse(
            session_id=status_data["session_id"],
            session_status=status_data["status"],
            line_id=status_data["line_id"],
            total_programmed_kg=status_data["total_programmed_kg"],
            total_dispensed_kg=status_data["total_dispensed_kg"],
            total_rounds=status_data["total_rounds"],
            current_round=status_data["current_round"],
            active_cage_id=status_data["active_cage_id"],
            dispensed_kg_live=status_data["dispensed_kg_live"],
            current_stage=status_data["current_stage"],
            is_running=status_data["is_running"],
            is_paused=status_data["is_paused"],
            current_flow_rate_kg_per_min=status_data["current_flow_rate_kg_per_min"],
            cages=cages,
            server_timestamp=status_data["server_timestamp"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/sessions")
async def list_sessions_history(
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    config_repo: Annotated[SystemConfigRepository, Depends(get_system_config_repo)],
    line_repo: Annotated[FeedingLineRepository, Depends(get_line_repo)],
    date_param: Optional[str] = Query(default=None, alias="date", description="Fecha YYYY-MM-DD (default: hoy en timezone del sistema)"),
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

        if line_id:
            sessions = [s for s in sessions if s.line_id == line_id]
        if status_filter:
            sessions = [s for s in sessions if s.status.value == status_filter]

        line_name_cache: dict[str, str] = {}

        result = []
        for s in sessions:
            if s.line_id not in line_name_cache:
                feeding_line = await line_repo.find_by_id(LineId.from_string(s.line_id))
                line_name_cache[s.line_id] = feeding_line.name.value if feeding_line else s.line_id

            duration = None
            if s.actual_start and s.actual_end:
                duration = (s.actual_end - s.actual_start).total_seconds()
            result.append(SessionHistoryItem(
                session_id=s.id,
                type=s.type.value,
                status=s.status.value,
                line_id=s.line_id,
                line_name=line_name_cache[s.line_id],
                operator_id=s.operator_id,
                started_at=s.actual_start,
                ended_at=s.actual_end,
                duration_seconds=duration,
                total_programmed_kg=s.total_programmed_kg,
                total_dispensed_kg=s.total_dispensed_kg,
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/sessions/{session_id}")
async def get_session_history_detail(
    session_id: str,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    event_repo: Annotated[FeedingEventRepository, Depends(get_feeding_event_repo)],
    line_repo: Annotated[FeedingLineRepository, Depends(get_line_repo)],
    cage_repo: Annotated[CageRepository, Depends(get_cage_repo)],
) -> SessionHistoryDetail:
    try:
        session = await session_repo.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sesión {session_id} no encontrada")

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
            cages.append(CageHistorySummary(
                cage_id=cf.cage_id,
                cage_name=cage_name_cache[cf.cage_id],
                mode=cf.mode.value,
                programmed_kg=cf.programmed_kg,
                total_dispensed_kg=cf.dispensed_kg,
                programmed_visits=cf.programmed_visits,
                completed_visits=cf.completed_visits,
                avg_visit_duration_seconds=avg_duration,
            ))

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

        return SessionHistoryDetail(
            session_id=session.id,
            type=session.type.value,
            status=session.status.value,
            line_id=session.line_id,
            line_name=line_name,
            operator_id=session.operator_id,
            started_at=session.actual_start,
            ended_at=session.actual_end,
            duration_seconds=duration,
            total_programmed_kg=session.total_programmed_kg,
            total_dispensed_kg=session.total_dispensed_kg,
            cages=cages,
            timeline=timeline,
            rate_chart=rate_chart,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/sessions/{session_id}/cages/{cage_id}/visits")
async def get_cage_visit_history(
    session_id: str,
    cage_id: str,
    event_repo: Annotated[FeedingEventRepository, Depends(get_feeding_event_repo)],
    cage_repo: Annotated[CageRepository, Depends(get_cage_repo)],
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
            visits.append(VisitHistoryItem(
                visit_number=e.data.get("visit_number", 0),
                dispensed_kg=dispensed_grams / 1000,
                dispensed_grams=dispensed_grams,
                duration_seconds=e.data.get("duration_seconds", 0.0),
                completed_at=e.timestamp,
            ))

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
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
) -> List[ActiveSessionItem]:
    try:
        sessions = await session_repo.find_active_sessions(hours_back=24)
        return [
            ActiveSessionItem(
                session_id=s.id,
                line_id=s.line_id,
                type=s.type.value,
                status=s.status.value,
                started_at=s.actual_start,
            )
            for s in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/status/batch")
async def get_batch_session_status(
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    cage_feeding_repo: Annotated[CageFeedingRepository, Depends(get_cage_feeding_repo)],
    machine: Annotated[SimulatedMachine, Depends(get_simulated_machine)],
    session_ids: str = Query(..., description="Comma-separated session UUIDs"),
) -> BatchStatusResponse:
    try:
        session_id_list = [sid.strip() for sid in session_ids.split(',') if sid.strip()]
        if not session_id_list:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_ids no puede estar vacío")
        if len(session_id_list) > 50:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Máximo 50 sesiones por request")

        results = []
        for session_id in session_id_list:
            try:
                session = await session_repo.find_by_id(session_id)
                if not session:
                    continue

                if session.type.value == "MANUAL":
                    status_data = await build_manual_status(session, machine)
                    results.append(BatchStatusSessionManual(**status_data))
                elif session.type.value == "CYCLIC":
                    status_data = await build_cyclic_status(session, cage_feeding_repo, machine)
                    results.append(BatchStatusSessionCyclic(**status_data))
            except Exception:
                continue

        return BatchStatusResponse(
            sessions=results,
            server_timestamp=datetime.now(timezone.utc)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/{session_id}/status")
async def get_feeding_status(
    session_id: str,
    session_repo: Annotated[FeedingSessionRepository, Depends(get_feeding_session_repo)],
    machine: Annotated[SimulatedMachine, Depends(get_simulated_machine)],
) -> FeedingSessionStatusResponse:
    try:
        session = await session_repo.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sesión {session_id} no encontrada")

        status_data = await build_manual_status(session, machine)

        return FeedingSessionStatusResponse(
            session_id=status_data["session_id"],
            session_status=status_data["status"],
            line_id=status_data["line_id"],
            cage_id=status_data["cage_id"],
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
