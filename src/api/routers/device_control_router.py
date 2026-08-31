"""Router para control directo de devices (blower, doser, selector)."""

from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import (
    GetBlowerStatusUseCaseDep,
    GetCoolerStatusUseCaseDep,
    GetDoserStatusUseCaseDep,
    GetSelectorStatusUseCaseDep,
    ListDoserCalibrationHistoryUseCaseDep,
    MoveSelectorDirectUseCaseDep,
    ResetSelectorDirectUseCaseDep,
    RunDoserForDurationUseCaseDep,
    RunDoserPulsesUseCaseDep,
    SaveDoserCalibrationUseCaseDep,
    SetBlowerPowerUseCaseDep,
    SetCoolerPowerUseCaseDep,
    SetDoserRateUseCaseDep,
    SetDoserSpeedUseCaseDep,
    TurnBlowerOffUseCaseDep,
    TurnBlowerOnUseCaseDep,
    TurnCoolerOffUseCaseDep,
    TurnCoolerOnUseCaseDep,
    TurnDoserOffUseCaseDep,
    TurnDoserOnUseCaseDep,
    CurrentUserDep,
    get_machine_service,
    get_current_admin_user,
)
from infrastructure.persistence.database import async_session_maker, get_session
from infrastructure.persistence.models.doser_calibration_session_model import (
    DoserCalibrationAttemptModel,
    DoserCalibrationSessionModel,
)
from infrastructure.persistence.models.doser_model import DoserModel
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel
from infrastructure.persistence.models.system_config_model import SystemConfigModel
from infrastructure.services.doser_calibration_runner import DoserCalibrationRunner
from application.dtos.device_control_dtos import (
    BlowerStatusResponse,
    CoolerStatusResponse,
    DoserCalibrationRequest,
    DoserCalibrationResponse,
    CalibrationAttemptResponse,
    RecordCalibrationMeasurementsRequest,
    CalibrationSessionResponse,
    DoserStatusResponse,
    MoveSelectorRequest,
    RunDoserDurationRequest,
    RunDoserPulsesRequest,
    RecordCalibrationMeasurementRequest,
    SelectorStatusResponse,
    SetBlowerPowerRequest,
    SetCoolerPowerRequest,
    SetDoserRateRequest,
    SetDoserSpeedRequest,
    StartCalibrationAttemptRequest,
    StartCalibrationSessionRequest,
)
from domain.exceptions import DomainException

router = APIRouter(
    prefix="/device-control",
    tags=["Device Control"],
    dependencies=[Depends(get_current_admin_user)],
)

_calibration_runner: DoserCalibrationRunner | None = None


def _get_calibration_runner() -> DoserCalibrationRunner:
    global _calibration_runner
    if _calibration_runner is None:
        _calibration_runner = DoserCalibrationRunner(get_machine_service(), async_session_maker)
    return _calibration_runner


def _attempt_response(attempt: DoserCalibrationAttemptModel) -> CalibrationAttemptResponse:
    return CalibrationAttemptResponse(
        id=str(attempt.id),
        sequence=attempt.sequence,
        status=attempt.status,
        pulse_count=attempt.pulse_count,
        active_time_seconds=attempt.active_time_seconds,
        expected_grams=attempt.expected_grams,
        measured_grams=attempt.measured_grams,
        error_percentage=attempt.error_percentage,
        included=attempt.included,
    )


async def _session_response(
    session: AsyncSession, calibration: DoserCalibrationSessionModel
) -> CalibrationSessionResponse:
    attempts = list(
        (
            await session.execute(
                select(DoserCalibrationAttemptModel)
                .where(DoserCalibrationAttemptModel.session_id == calibration.id)
                .order_by(DoserCalibrationAttemptModel.sequence)
            )
        )
        .scalars()
        .all()
    )
    final_rate = None
    if calibration.final_calibration_id:
        from infrastructure.persistence.models.doser_calibration_model import DoserCalibrationModel

        final = await session.get(DoserCalibrationModel, calibration.final_calibration_id)
        final_rate = final.grams_per_second if final else None
    return CalibrationSessionResponse(
        id=str(calibration.id),
        doser_id=str(calibration.doser_id),
        line_id=str(calibration.line_id),
        status=calibration.status,
        target_grams=calibration.target_grams,
        pulse_on_time=calibration.pulse_on_time,
        pulse_off_time=calibration.pulse_off_time,
        speed_percentage=calibration.speed_percentage,
        tolerance_percentage=calibration.tolerance_percentage,
        final_grams_per_second=final_rate,
        attempts=[_attempt_response(item) for item in attempts],
    )


@router.post("/blowers/{blower_id}/on", status_code=status.HTTP_200_OK)
async def turn_blower_on(
    current_user: CurrentUserDep,
    blower_id: str,
    use_case: TurnBlowerOnUseCaseDep,
) -> Dict[str, str]:
    """
    Enciende un blower específico.

    El blower se enciende a su potencia non_feeding_power configurada.

    - **blower_id**: ID del blower (UUID)
    """
    try:
        await use_case.execute(blower_id)
        return {"message": "Blower turned on successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/blowers/{blower_id}/off", status_code=status.HTTP_200_OK)
async def turn_blower_off(
    current_user: CurrentUserDep,
    blower_id: str,
    use_case: TurnBlowerOffUseCaseDep,
) -> Dict[str, str]:
    """
    Apaga un blower específico.

    El blower se apaga (potencia a 0%).

    - **blower_id**: ID del blower (UUID)
    """
    try:
        await use_case.execute(blower_id)
        return {"message": "Blower turned off successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/blowers/{blower_id}/set-power", status_code=status.HTTP_200_OK)
async def set_blower_power(
    current_user: CurrentUserDep,
    blower_id: str,
    request: SetBlowerPowerRequest,
    use_case: SetBlowerPowerUseCaseDep,
) -> Dict[str, str]:
    """
    Establece la potencia de un blower específico.

    Control manual del blower sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **blower_id**: ID del blower (UUID)
    - **power_percentage**: Potencia del blower (0-100%)
    """
    try:
        await use_case.execute(blower_id, request.power_percentage)
        return {"message": f"Blower power set to {request.power_percentage}% successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/on", status_code=status.HTTP_200_OK)
async def turn_doser_on(
    current_user: CurrentUserDep,
    doser_id: str,
    use_case: TurnDoserOnUseCaseDep,
) -> Dict[str, str]:
    """
    Enciende un doser específico.

    El doser se enciende a su tasa mínima del rango configurado.

    - **doser_id**: ID del doser (UUID)
    """
    try:
        await use_case.execute(doser_id)
        return {"message": "Doser turned on successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/off", status_code=status.HTTP_200_OK)
async def turn_doser_off(
    current_user: CurrentUserDep,
    doser_id: str,
    use_case: TurnDoserOffUseCaseDep,
) -> Dict[str, str]:
    """
    Apaga un doser específico.

    El doser se apaga (tasa a 0).

    - **doser_id**: ID del doser (UUID)
    """
    try:
        await use_case.execute(doser_id)
        return {"message": "Doser turned off successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/set-rate", status_code=status.HTTP_200_OK)
async def set_doser_rate(
    current_user: CurrentUserDep,
    doser_id: str,
    request: SetDoserRateRequest,
    use_case: SetDoserRateUseCaseDep,
) -> Dict[str, str]:
    """
    Establece la tasa de dosificación de un doser específico.

    Control manual del doser sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **doser_id**: ID del doser (UUID)
    - **rate_kg_min**: Tasa de dosificación en kg/min
    """
    try:
        await use_case.execute(doser_id, request.rate_kg_min)
        return {"message": f"Doser rate set to {request.rate_kg_min} kg/min successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/set-speed", status_code=status.HTTP_200_OK)
async def set_doser_speed(
    current_user: CurrentUserDep,
    doser_id: str,
    request: SetDoserSpeedRequest,
    use_case: SetDoserSpeedUseCaseDep,
) -> Dict[str, str]:
    """
    Establece la velocidad del motor de un doser específico.

    Envía el porcentaje de velocidad directamente al PLC.
    Útil para calibración de dosificadores.

    - **doser_id**: ID del doser (UUID)
    - **speed_percentage**: Velocidad del motor (1-100%)
    """
    try:
        await use_case.execute(doser_id, request.speed_percentage)
        return {"message": f"Doser speed set to {request.speed_percentage}%"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/dosers/{doser_id}/calibration",
    status_code=status.HTTP_201_CREATED,
    response_model=DoserCalibrationResponse,
)
async def save_doser_calibration(
    current_user: CurrentUserDep,
    doser_id: str,
    request: DoserCalibrationRequest,
    use_case: SaveDoserCalibrationUseCaseDep,
) -> DoserCalibrationResponse:
    """
    Guarda una calibración explícita del doser en g/s.

    max_rate se mantiene como capacidad/configuración en kg/min y se expone
    por separado en /system-layout.
    """
    try:
        return await use_case.execute(doser_id, request)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/dosers/{doser_id}/calibration/history",
    status_code=status.HTTP_200_OK,
    response_model=List[DoserCalibrationResponse],
)
async def get_doser_calibration_history(
    current_user: CurrentUserDep,
    doser_id: str,
    use_case: ListDoserCalibrationHistoryUseCaseDep,
) -> List[DoserCalibrationResponse]:
    """Obtiene el historial de calibraciones del doser."""
    try:
        return await use_case.execute(doser_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/dosers/{doser_id}/calibration/sessions",
    response_model=CalibrationSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_calibration_session(
    current_user: CurrentUserDep,
    doser_id: str,
    request: StartCalibrationSessionRequest,
    session: AsyncSession = Depends(get_session),
) -> CalibrationSessionResponse:
    """Abre una calibración manual. Sólo admite Pulse Dosers y una línea bloqueada."""
    doser = await session.get(DoserModel, UUID(doser_id))
    if not doser:
        raise HTTPException(status_code=404, detail="Doser no encontrado")
    if doser.doser_type != "PULSE_DOSER":
        raise HTTPException(status_code=400, detail="La calibración aún está disponible sólo para Pulse Doser")
    line = await session.get(FeedingLineModel, doser.line_id)
    if not line or line.status != "MANUAL_CONTROL":
        raise HTTPException(status_code=409, detail="Bloquea la línea en control manual antes de calibrar")
    if line.locked_by and line.locked_by != current_user.id:
        raise HTTPException(status_code=409, detail="La línea está bloqueada por otro usuario")
    if not doser.pulse_on_time or doser.pulse_off_time is None:
        raise HTTPException(status_code=400, detail="Configura los tiempos ON y OFF del doser antes de calibrar")
    existing = (
        await session.execute(
            select(DoserCalibrationSessionModel).where(
                DoserCalibrationSessionModel.line_id == line.id,
                DoserCalibrationSessionModel.status.in_(["PENDING", "RUNNING", "AWAITING_MEASUREMENT"]),
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe una calibración activa en esta línea")
    config = await session.get(SystemConfigModel, 1)
    tolerance = request.tolerance_percentage or (config.doser_calibration_tolerance_percentage if config else 5.0)
    calibration = DoserCalibrationSessionModel(
        doser_id=doser.id,
        line_id=line.id,
        target_grams=request.target_grams,
        pulse_on_time=doser.pulse_on_time,
        pulse_off_time=doser.pulse_off_time,
        speed_percentage=doser.pulse_speed or doser.speed_percentage,
        tolerance_percentage=tolerance,
        started_by=current_user.id,
    )
    session.add(calibration)
    await session.flush()
    await session.commit()
    return await _session_response(session, calibration)


@router.get("/dosers/{doser_id}/calibration/sessions/active", response_model=CalibrationSessionResponse | None)
async def get_active_calibration_session(
    current_user: CurrentUserDep, doser_id: str, session: AsyncSession = Depends(get_session)
) -> CalibrationSessionResponse | None:
    calibration = (
        await session.execute(
            select(DoserCalibrationSessionModel)
            .where(
                DoserCalibrationSessionModel.doser_id == UUID(doser_id),
                DoserCalibrationSessionModel.status.in_(["PENDING", "RUNNING", "AWAITING_MEASUREMENT"]),
            )
            .order_by(desc(DoserCalibrationSessionModel.created_at))
        )
    ).scalar_one_or_none()
    return await _session_response(session, calibration) if calibration else None


@router.post("/calibration-sessions/{session_id}/attempts", response_model=CalibrationSessionResponse)
async def start_calibration_attempt(
    current_user: CurrentUserDep,
    session_id: str,
    request: StartCalibrationAttemptRequest,
    session: AsyncSession = Depends(get_session),
) -> CalibrationSessionResponse:
    calibration = await session.get(DoserCalibrationSessionModel, UUID(session_id))
    if not calibration or calibration.status not in {"PENDING", "AWAITING_MEASUREMENT"}:
        raise HTTPException(status_code=409, detail="La sesión no está disponible para un nuevo intento")
    doser = await session.get(DoserModel, calibration.doser_id)
    line = await session.get(FeedingLineModel, calibration.line_id)
    if (
        not doser
        or not line
        or line.status != "MANUAL_CONTROL"
        or (line.locked_by and line.locked_by != current_user.id)
    ):
        raise HTTPException(status_code=409, detail="La línea debe permanecer bloqueada por el operador")
    total_seconds = (
        request.pulse_count * calibration.pulse_on_time + max(0, request.pulse_count - 1) * calibration.pulse_off_time
    )
    config = await session.get(SystemConfigModel, 1)
    max_pulses = config.doser_calibration_max_pulses if config else 10
    max_seconds = config.doser_calibration_max_attempt_seconds if config else 20
    if request.pulse_count > max_pulses or total_seconds > max_seconds:
        raise HTTPException(
            status_code=400,
            detail=f"El intento excede el límite seguro de {max_pulses} pulsos o {max_seconds} segundos",
        )
    previous = list(
        (
            await session.execute(
                select(DoserCalibrationAttemptModel).where(DoserCalibrationAttemptModel.session_id == calibration.id)
            )
        ).scalars()
    )
    expected = (
        doser.calibrated_grams_per_second * request.pulse_count * calibration.pulse_on_time
        if doser.calibrated_grams_per_second
        else None
    )
    attempt = DoserCalibrationAttemptModel(
        session_id=calibration.id,
        sequence=len(previous) + 1,
        pulse_count=request.pulse_count,
        active_time_seconds=request.pulse_count * calibration.pulse_on_time,
        expected_grams=expected,
    )
    session.add(attempt)
    await session.flush()
    # El ejecutor abre su propia transacción: el intento debe ser visible antes
    # de crear la tarea para evitar una carrera al devolver la respuesta.
    await session.commit()
    _get_calibration_runner().start(
        attempt.id,
        doser_id=doser.id,
        doser_name=doser.name,
        line_id=line.id,
        line_name=line.name,
        speed=calibration.speed_percentage,
    )
    return await _session_response(session, calibration)


@router.post("/calibration-attempts/{attempt_id}/measurement", response_model=CalibrationSessionResponse)
async def record_calibration_measurement(
    current_user: CurrentUserDep,
    attempt_id: str,
    request: RecordCalibrationMeasurementRequest,
    session: AsyncSession = Depends(get_session),
) -> CalibrationSessionResponse:
    attempt = await session.get(DoserCalibrationAttemptModel, UUID(attempt_id))
    if not attempt or attempt.status != "AWAITING_MEASUREMENT":
        raise HTTPException(status_code=409, detail="El intento aún no está listo para registrar una medición")
    calibration = await session.get(DoserCalibrationSessionModel, attempt.session_id)
    if not calibration:
        raise HTTPException(status_code=404, detail="Sesión de calibración no encontrada")
    attempt.measured_grams = request.measured_grams
    attempt.included = request.included
    attempt.error_percentage = ((request.measured_grams - calibration.target_grams) / calibration.target_grams) * 100
    attempt.status = "MEASURED"
    calibration.status = "PENDING"
    await session.flush()
    return await _session_response(session, calibration)


@router.post(
    "/calibration-sessions/{session_id}/measurements",
    response_model=CalibrationSessionResponse,
)
async def record_calibration_measurements(
    current_user: CurrentUserDep,
    session_id: str,
    request: RecordCalibrationMeasurementsRequest,
    session: AsyncSession = Depends(get_session),
) -> CalibrationSessionResponse:
    """Registra todos los pesajes pendientes de una sesión en una sola acción."""
    calibration = await session.get(DoserCalibrationSessionModel, UUID(session_id))
    if not calibration or calibration.status not in {"PENDING", "AWAITING_MEASUREMENT"}:
        raise HTTPException(status_code=409, detail="La sesión no está disponible para registrar mediciones")

    awaiting_attempts = list(
        (
            await session.execute(
                select(DoserCalibrationAttemptModel).where(
                    DoserCalibrationAttemptModel.session_id == calibration.id,
                    DoserCalibrationAttemptModel.status == "AWAITING_MEASUREMENT",
                )
            )
        ).scalars()
    )
    measurements_by_attempt = {item.attempt_id: item for item in request.measurements}
    awaiting_ids = {str(attempt.id) for attempt in awaiting_attempts}
    if set(measurements_by_attempt) != awaiting_ids:
        raise HTTPException(
            status_code=400,
            detail="Debes registrar una medición para cada intento pendiente",
        )

    for attempt in awaiting_attempts:
        measurement = measurements_by_attempt[str(attempt.id)]
        attempt.measured_grams = measurement.measured_grams
        attempt.included = measurement.included
        attempt.error_percentage = (
            (measurement.measured_grams - calibration.target_grams) / calibration.target_grams
        ) * 100
        attempt.status = "MEASURED"
    calibration.status = "PENDING"
    await session.flush()
    return await _session_response(session, calibration)


@router.post("/calibration-sessions/{session_id}/finalize", response_model=CalibrationSessionResponse)
async def finalize_calibration_session(
    current_user: CurrentUserDep, session_id: str, session: AsyncSession = Depends(get_session)
) -> CalibrationSessionResponse:
    """Consolida las muestras incluidas y activa el caudal medido del Pulse Doser."""
    from datetime import datetime, timezone
    from infrastructure.persistence.models.doser_calibration_model import DoserCalibrationModel

    calibration = await session.get(DoserCalibrationSessionModel, UUID(session_id))
    if not calibration or calibration.status not in {"PENDING", "AWAITING_MEASUREMENT"}:
        raise HTTPException(status_code=409, detail="La sesión no se puede finalizar")
    attempts = list(
        (
            await session.execute(
                select(DoserCalibrationAttemptModel).where(
                    DoserCalibrationAttemptModel.session_id == calibration.id,
                    DoserCalibrationAttemptModel.status == "MEASURED",
                    DoserCalibrationAttemptModel.included.is_(True),
                )
            )
        ).scalars()
    )
    if not attempts:
        raise HTTPException(status_code=400, detail="Registra al menos una muestra incluida antes de finalizar")
    total_grams = sum(item.measured_grams or 0 for item in attempts)
    total_active_seconds = sum(item.active_time_seconds for item in attempts)
    grams_per_second = total_grams / total_active_seconds
    within_tolerance = all(abs(item.error_percentage or 0) <= calibration.tolerance_percentage for item in attempts)
    result_status = "VERIFIED" if len(attempts) >= 3 and within_tolerance else "PROVISIONAL"
    doser = await session.get(DoserModel, calibration.doser_id)
    if not doser:
        raise HTTPException(status_code=404, detail="Doser no encontrado")
    saved = DoserCalibrationModel(
        doser_id=doser.id,
        grams_per_second=grams_per_second,
        method="PULSE_ITERATIVE",
        status=result_status,
        speed_percentage=calibration.speed_percentage,
        pulse_on_time=calibration.pulse_on_time,
        pulse_off_time=calibration.pulse_off_time,
        tolerance_percentage=calibration.tolerance_percentage,
        included_attempts=len(attempts),
        sample_average_grams=total_grams / len(attempts),
        pulse_count=sum(item.pulse_count for item in attempts),
        active_time_seconds=total_active_seconds,
        target_grams=calibration.target_grams,
        runtime_seconds=sum(item.active_time_seconds for item in attempts),
        created_by=current_user.id,
    )
    session.add(saved)
    doser.calibrated_grams_per_second = grams_per_second
    calibration.final_calibration_id = saved.id
    calibration.status = result_status
    calibration.completed_at = datetime.now(timezone.utc)
    await session.flush()
    return await _session_response(session, calibration)


@router.post("/calibration-attempts/{attempt_id}/stop", response_model=CalibrationSessionResponse)
async def stop_calibration_attempt(
    current_user: CurrentUserDep, attempt_id: str, session: AsyncSession = Depends(get_session)
) -> CalibrationSessionResponse:
    attempt = await session.get(DoserCalibrationAttemptModel, UUID(attempt_id))
    if not attempt:
        raise HTTPException(status_code=404, detail="Intento no encontrado")
    await _get_calibration_runner().stop(attempt.id)
    calibration = await session.get(DoserCalibrationSessionModel, attempt.session_id)
    if not calibration:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return await _session_response(session, calibration)


@router.post("/dosers/{doser_id}/run-pulses", status_code=status.HTTP_200_OK)
async def run_doser_pulses(
    current_user: CurrentUserDep,
    doser_id: str,
    request: RunDoserPulsesRequest,
    use_case: RunDoserPulsesUseCaseDep,
) -> Dict[str, str]:
    """Ejecuta pulsos de calibración controlados por backend."""
    try:
        await use_case.execute(doser_id, request.pulse_count)
        return {"message": f"Doser ran {request.pulse_count} pulses successfully"}

    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "no encontrado" in str(e) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/run-for-duration", status_code=status.HTTP_200_OK)
async def run_doser_for_duration(
    current_user: CurrentUserDep,
    doser_id: str,
    request: RunDoserDurationRequest,
    use_case: RunDoserForDurationUseCaseDep,
) -> Dict[str, str]:
    """Ejecuta el doser durante una duración acotada y lo apaga al finalizar."""
    try:
        await use_case.execute(doser_id, request.duration_seconds)
        return {"message": f"Doser ran for {request.duration_seconds} seconds successfully"}

    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "no encontrado" in str(e) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/selectors/{selector_id}/move", status_code=status.HTTP_200_OK)
async def move_selector(
    current_user: CurrentUserDep,
    selector_id: str,
    request: MoveSelectorRequest,
    use_case: MoveSelectorDirectUseCaseDep,
) -> Dict[str, str]:
    """
    Mueve un selector específico a un slot.

    Control manual del selector sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **selector_id**: ID del selector (UUID)
    - **slot_number**: Número de slot destino (1 a capacity)
    """
    try:
        await use_case.execute(selector_id, request.slot_number)
        return {"message": f"Selector moved to slot {request.slot_number} successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/selectors/{selector_id}/reset", status_code=status.HTTP_200_OK)
async def reset_selector(
    current_user: CurrentUserDep,
    selector_id: str,
    use_case: ResetSelectorDirectUseCaseDep,
) -> Dict[str, str]:
    """
    Resetea la posición de un selector específico a neutral.

    Control manual del selector sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **selector_id**: ID del selector (UUID)
    """
    try:
        await use_case.execute(selector_id)
        return {"message": "Selector position reset successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/blowers/{blower_id}/status", status_code=status.HTTP_200_OK)
async def get_blower_status(
    current_user: CurrentUserDep,
    blower_id: str,
    use_case: GetBlowerStatusUseCaseDep,
) -> BlowerStatusResponse:
    """
    Obtiene el estado actual de un blower específico.

    - **blower_id**: ID del blower (UUID)
    """
    try:
        return await use_case.execute(blower_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/dosers/{doser_id}/status", status_code=status.HTTP_200_OK)
async def get_doser_status(
    current_user: CurrentUserDep,
    doser_id: str,
    use_case: GetDoserStatusUseCaseDep,
) -> DoserStatusResponse:
    """
    Obtiene el estado actual de un doser específico.

    - **doser_id**: ID del doser (UUID)
    """
    try:
        return await use_case.execute(doser_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/selectors/{selector_id}/status", status_code=status.HTTP_200_OK)
async def get_selector_status(
    current_user: CurrentUserDep,
    selector_id: str,
    use_case: GetSelectorStatusUseCaseDep,
) -> SelectorStatusResponse:
    """
    Obtiene el estado actual de un selector específico.

    - **selector_id**: ID del selector (UUID)
    """
    try:
        return await use_case.execute(selector_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


# =========================================================================
# Cooler Control
# =========================================================================


@router.post("/coolers/{cooler_id}/on", status_code=status.HTTP_200_OK)
async def turn_cooler_on(
    current_user: CurrentUserDep,
    cooler_id: str,
    use_case: TurnCoolerOnUseCaseDep,
) -> Dict[str, str]:
    """
    Enciende un cooler específico.

    El cooler se enciende a su potencia cooling_power_percentage configurada.

    - **cooler_id**: ID del cooler (UUID)
    """
    try:
        await use_case.execute(cooler_id)
        return {"message": "Cooler turned on successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/coolers/{cooler_id}/off", status_code=status.HTTP_200_OK)
async def turn_cooler_off(
    current_user: CurrentUserDep,
    cooler_id: str,
    use_case: TurnCoolerOffUseCaseDep,
) -> Dict[str, str]:
    """
    Apaga un cooler específico.

    El cooler se apaga (potencia a 0%).

    - **cooler_id**: ID del cooler (UUID)
    """
    try:
        await use_case.execute(cooler_id)
        return {"message": "Cooler turned off successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/coolers/{cooler_id}/set-power", status_code=status.HTTP_200_OK)
async def set_cooler_power(
    current_user: CurrentUserDep,
    cooler_id: str,
    request: SetCoolerPowerRequest,
    use_case: SetCoolerPowerUseCaseDep,
) -> Dict[str, str]:
    """
    Establece la potencia de un cooler específico.

    Control manual del cooler sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **cooler_id**: ID del cooler (UUID)
    - **power_percentage**: Potencia del cooler (0-100%)
    """
    try:
        await use_case.execute(cooler_id, request.power_percentage)
        return {"message": f"Cooler power set to {request.power_percentage}% successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/coolers/{cooler_id}/status", status_code=status.HTTP_200_OK)
async def get_cooler_status(
    current_user: CurrentUserDep,
    cooler_id: str,
    use_case: GetCoolerStatusUseCaseDep,
) -> CoolerStatusResponse:
    """
    Obtiene el estado actual de un cooler específico.

    - **cooler_id**: ID del cooler (UUID)
    """
    try:
        return await use_case.execute(cooler_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
