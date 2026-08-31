"""Ejecutor asíncrono y seguro de intentos de calibración.

La UI sólo solicita iniciar/detener un intento. El ciclo ON/OFF vive aquí para
que un cierre de la pestaña no deje el dosificador encendido.
"""

import asyncio
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from domain.dtos import DoserCommand
from domain.interfaces import IFeedingMachine
from infrastructure.persistence.models.doser_calibration_session_model import (
    DoserCalibrationAttemptModel,
    DoserCalibrationSessionModel,
)


class DoserCalibrationRunner:
    def __init__(self, machine: IFeedingMachine, session_factory: Callable[[], AsyncSession]) -> None:
        self._machine = machine
        self._session_factory = session_factory
        self._tasks: dict[UUID, asyncio.Task[None]] = {}

    def start(
        self, attempt_id: UUID, *, doser_id: UUID, doser_name: str, line_id: UUID, line_name: str, speed: int
    ) -> None:
        if attempt_id in self._tasks and not self._tasks[attempt_id].done():
            raise ValueError("El intento ya se está ejecutando")
        self._tasks[attempt_id] = asyncio.create_task(
            self._run(attempt_id, doser_id, doser_name, line_id, line_name, speed)
        )

    async def stop(self, attempt_id: UUID) -> None:
        task = self._tasks.get(attempt_id)
        if task and not task.done():
            task.cancel()

    async def _run(
        self, attempt_id: UUID, doser_id: UUID, doser_name: str, line_id: UUID, line_name: str, speed: int
    ) -> None:
        command_on = DoserCommand(str(doser_id), doser_name, str(line_id), line_name, float(speed))
        command_off = DoserCommand(str(doser_id), doser_name, str(line_id), line_name, 0.0)
        try:
            async with self._session_factory() as session:
                attempt = await session.get(DoserCalibrationAttemptModel, attempt_id)
                if attempt is None:
                    return
                calibration = await session.get(DoserCalibrationSessionModel, attempt.session_id)
                if calibration is None:
                    return
                attempt.status = "RUNNING"
                attempt.started_at = datetime.now(timezone.utc)
                calibration.status = "RUNNING"
                calibration.heartbeat_at = datetime.now(timezone.utc)
                await session.commit()

                for index in range(attempt.pulse_count):
                    await self._machine.set_doser_rate(command_on)
                    await asyncio.sleep(calibration.pulse_on_time)
                    await self._machine.set_doser_rate(command_off)
                    if index < attempt.pulse_count - 1 and calibration.pulse_off_time:
                        await asyncio.sleep(calibration.pulse_off_time)

                attempt.status = "AWAITING_MEASUREMENT"
                attempt.completed_at = datetime.now(timezone.utc)
                calibration.status = "AWAITING_MEASUREMENT"
                calibration.heartbeat_at = datetime.now(timezone.utc)
                await session.commit()
        except asyncio.CancelledError:
            async with self._session_factory() as session:
                attempt = await session.get(DoserCalibrationAttemptModel, attempt_id)
                if attempt:
                    attempt.status = "INTERRUPTED"
                    attempt.completed_at = datetime.now(timezone.utc)
                    calibration = await session.get(DoserCalibrationSessionModel, attempt.session_id)
                    if calibration:
                        calibration.status = "INTERRUPTED"
                    await session.commit()
            raise
        except Exception:
            async with self._session_factory() as session:
                attempt = await session.get(DoserCalibrationAttemptModel, attempt_id)
                if attempt:
                    attempt.status = "FAILED"
                    attempt.completed_at = datetime.now(timezone.utc)
                    calibration = await session.get(DoserCalibrationSessionModel, attempt.session_id)
                    if calibration:
                        calibration.status = "FAILED"
                    await session.commit()
        finally:
            await self._machine.set_doser_rate(command_off)
