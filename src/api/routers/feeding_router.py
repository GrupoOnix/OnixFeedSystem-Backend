from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import (
    get_cancel_feeding_use_case,
    get_cage_feeding_repo,
    get_feeding_session_repo,
    get_pause_feeding_use_case,
    get_resume_feeding_use_case,
    get_simulated_machine,
    get_start_cyclic_feeding_use_case,
    get_start_manual_feeding_use_case,
    get_update_blower_power_use_case,
    get_update_feeding_rate_use_case,
)
from api.models.feeding_models import (
    CageFeedingStatusItem,
    CancelFeedingRequest,
    CyclicFeedingRequest,
    CyclicFeedingResponse,
    CyclicSessionStatusResponse,
    FeedingActionResponse,
    FeedingSessionStatusResponse,
    ManualFeedingRequest,
    ManualFeedingResponse,
    PauseFeedingRequest,
    ResumeFeedingRequest,
    UpdateBlowerRequest,
    UpdateBlowerResponse,
    UpdateRateRequest,
    UpdateRateResponse,
)
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
from domain.value_objects import LineId
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.persistence.repositories.feeding_session_repository import FeedingSessionRepository
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

        cf_list = await cage_feeding_repo.find_by_session(session_id)
        if not cf_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay cage feedings para esta sesión")

        machine_status = await machine.get_status(LineId.from_string(session.line_id))

        # Calcular ronda actual: mínimo de completed_visits entre jaulas no-FASTING + 1
        active_cfs = [cf for cf in cf_list if cf.mode != CageFeedingMode.FASTING]
        total_rounds = max((cf.programmed_visits for cf in active_cfs), default=0)
        if session.status.value == "COMPLETED":
            current_round = total_rounds
        elif active_cfs:
            current_round = min(cf.completed_visits for cf in active_cfs) + 1
        else:
            current_round = 0

        # Jaula activa: la primera (por execution_order) que aún no completó la ronda actual
        active_cf = next(
            (cf for cf in cf_list
             if cf.mode != CageFeedingMode.FASTING
             and cf.completed_visits < current_round),
            None,
        ) if session.status.value == "IN_PROGRESS" else None

        # Totales
        total_dispensed_kg = sum(cf.dispensed_kg for cf in cf_list)

        # Si hay visita activa, mostrar kg en vivo de la máquina para esa jaula
        live_dispensed = machine_status.dispensed_kg if active_cf else 0.0

        cages = [
            CageFeedingStatusItem(
                cage_id=cf.cage_id,
                mode=cf.mode.value,
                status=cf.status.value,
                execution_order=cf.execution_order,
                programmed_kg=cf.programmed_kg,
                dispensed_kg=cf.dispensed_kg,
                programmed_visits=cf.programmed_visits,
                completed_visits=cf.completed_visits,
                visits_completion_percentage=round(cf.visits_completion_percentage(), 2),
                kg_completion_percentage=round(cf.completion_percentage(), 2),
            )
            for cf in cf_list
        ]

        return CyclicSessionStatusResponse(
            session_id=session.id,
            session_status=session.status.value,
            line_id=session.line_id,
            total_programmed_kg=session.total_programmed_kg,
            total_dispensed_kg=round(total_dispensed_kg, 3),
            total_rounds=total_rounds,
            current_round=current_round,
            active_cage_id=active_cf.cage_id if active_cf else None,
            dispensed_kg_live=live_dispensed,
            current_stage=machine_status.current_stage.value,
            is_running=machine_status.is_running,
            is_paused=machine_status.is_paused,
            current_flow_rate_kg_per_min=machine_status.current_flow_rate_kg_per_min,
            cages=cages,
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

        cf_list = session.cage_feedings
        current_cf = next((cf for cf in cf_list if cf.status.value == "IN_PROGRESS"), None)
        if not current_cf and cf_list:
            current_cf = cf_list[0]
        if not current_cf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay cage feeding en esta sesión")

        machine_status = await machine.get_status(LineId.from_string(session.line_id))

        live_dispensed = machine_status.dispensed_kg if session.status.value == "IN_PROGRESS" else current_cf.dispensed_kg
        programmed = current_cf.programmed_kg
        completion = (live_dispensed / programmed * 100) if programmed > 0 else 0.0

        return FeedingSessionStatusResponse(
            session_id=session.id,
            session_status=session.status.value,
            line_id=session.line_id,
            cage_id=current_cf.cage_id,
            programmed_kg=programmed,
            dispensed_kg_bd=current_cf.dispensed_kg,
            dispensed_kg_live=live_dispensed,
            rate_kg_per_min=current_cf.rate_kg_per_min,
            current_flow_rate_kg_per_min=machine_status.current_flow_rate_kg_per_min,
            is_running=machine_status.is_running,
            is_paused=machine_status.is_paused,
            completion_percentage=round(completion, 2),
            current_stage=machine_status.current_stage.value,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
