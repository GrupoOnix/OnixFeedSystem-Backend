"""Casos de uso para calibración de dosificadores."""

import asyncio
from typing import List
from uuid import UUID

from application.dtos.device_control_dtos import (
    DoserCalibrationRequest,
    DoserCalibrationResponse,
)
from application.use_cases.device_control.manual_control_guard import require_manual_control
from domain.dtos import DoserCommand
from domain.interfaces import IFeedingMachine
from infrastructure.persistence.models.doser_calibration_model import DoserCalibrationModel
from infrastructure.persistence.repositories.doser_repository import DoserRepository


class SaveDoserCalibrationUseCase:
    def __init__(self, doser_repository: DoserRepository):
        self._doser_repo = doser_repository

    async def execute(self, doser_id: str, request: DoserCalibrationRequest) -> DoserCalibrationResponse:
        doser_uuid = UUID(doser_id)
        calibration = DoserCalibrationModel(
            doser_id=doser_uuid,
            grams_per_second=request.grams_per_second,
            method=request.method,
            sample_average_grams=request.sample_average_grams,
            pulse_count=request.pulse_count,
            active_time_seconds=request.active_time_seconds,
            target_grams=request.target_grams,
            runtime_seconds=request.runtime_seconds,
            created_by=request.created_by,
        )
        saved = await self._doser_repo.update_calibration(doser_uuid, calibration)
        return _to_response(saved)


class ListDoserCalibrationHistoryUseCase:
    def __init__(self, doser_repository: DoserRepository):
        self._doser_repo = doser_repository

    async def execute(self, doser_id: str) -> List[DoserCalibrationResponse]:
        doser_uuid = UUID(doser_id)
        doser = await self._doser_repo.find_by_id(doser_uuid)
        if not doser:
            raise ValueError(f"Doser {doser_id} no encontrado")

        history = await self._doser_repo.list_calibration_history(doser_uuid)
        return [_to_response(item) for item in history]


class RunDoserPulsesUseCase:
    def __init__(
        self,
        doser_repository: DoserRepository,
        machine_service: IFeedingMachine,
    ):
        self._doser_repo = doser_repository
        self._machine = machine_service

    async def execute(self, doser_id: str, pulse_count: int) -> None:
        result = await self._doser_repo.find_by_id_with_context(UUID(doser_id))
        if not result:
            raise ValueError(f"Doser {doser_id} no encontrado")

        require_manual_control(result.line_name, result.line_status)
        doser = result.doser
        if doser.pulse_on_time is None:
            raise ValueError("El doser no tiene pulse_on_time configurado")
        if doser.pulse_off_time is None:
            raise ValueError("El doser no tiene pulse_off_time configurado")

        command_on = _build_doser_command(
            result=result,
            doser_id=doser_id,
            rate_percentage=float(doser.pulse_speed or doser.speed_percentage),
        )
        command_off = _build_doser_command(result=result, doser_id=doser_id, rate_percentage=0.0)

        try:
            for index in range(pulse_count):
                await self._machine.set_doser_rate(command_on)
                await asyncio.sleep(doser.pulse_on_time)
                await self._machine.set_doser_rate(command_off)
                if index < pulse_count - 1 and doser.pulse_off_time > 0:
                    await asyncio.sleep(doser.pulse_off_time)
        finally:
            await self._machine.set_doser_rate(command_off)


class RunDoserForDurationUseCase:
    def __init__(
        self,
        doser_repository: DoserRepository,
        machine_service: IFeedingMachine,
    ):
        self._doser_repo = doser_repository
        self._machine = machine_service

    async def execute(self, doser_id: str, duration_seconds: float) -> None:
        result = await self._doser_repo.find_by_id_with_context(UUID(doser_id))
        if not result:
            raise ValueError(f"Doser {doser_id} no encontrado")

        require_manual_control(result.line_name, result.line_status)
        doser = result.doser
        command_on = _build_doser_command(
            result=result,
            doser_id=doser_id,
            rate_percentage=float(doser.pulse_speed or doser.speed_percentage),
        )
        command_off = _build_doser_command(result=result, doser_id=doser_id, rate_percentage=0.0)

        try:
            await self._machine.set_doser_rate(command_on)
            await asyncio.sleep(duration_seconds)
        finally:
            await self._machine.set_doser_rate(command_off)


def _to_response(model: DoserCalibrationModel) -> DoserCalibrationResponse:
    return DoserCalibrationResponse(
        id=str(model.id),
        created_at=model.created_at,
        grams_per_second=model.grams_per_second,
        method=model.method,
        pulse_count=model.pulse_count,
        target_grams=model.target_grams,
        runtime_seconds=model.runtime_seconds,
        sample_average_grams=model.sample_average_grams,
        active_time_seconds=model.active_time_seconds,
        created_by=model.created_by,
    )


def _build_doser_command(result, doser_id: str, rate_percentage: float) -> DoserCommand:
    doser = result.doser
    return DoserCommand(
        doser_id=doser_id,
        doser_name=str(doser.name),
        line_id=str(result.line_id),
        line_name=result.line_name,
        rate_percentage=rate_percentage,
    )
