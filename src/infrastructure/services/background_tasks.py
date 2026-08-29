"""
Background tasks para FastAPI.

Este módulo contiene las tareas en segundo plano que se ejecutan
periódicamente durante el ciclo de vida de la aplicación.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Optional

from fastapi import FastAPI

from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.repositories import (
    AlertRepository,
    ScheduledAlertRepository,
    SiloRepository,
)
from infrastructure.services.alert_scheduler_service import AlertSchedulerService
from infrastructure.services.default_admin_service import seed_default_admin_if_needed
from infrastructure.services.silo_monitor_service import SiloMonitorService
from infrastructure.services.feeding_execution_worker import FeedingExecutionWorker
from infrastructure.services.scheduled_feeding_dispatcher import ScheduledFeedingDispatcher
from infrastructure.persistence.database import async_session_maker

logger = logging.getLogger(__name__)

# Variables globales para controlar los tasks
_scheduler_task: Optional[asyncio.Task] = None
_silo_monitor_task: Optional[asyncio.Task] = None
_scheduled_feeding_task: Optional[asyncio.Task] = None
_feeding_execution_worker_task: Optional[asyncio.Task] = None


def _positive_int_from_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        if value > 0:
            return value
    except ValueError:
        pass
    logger.warning("%s debe ser un entero positivo; se usará %s", name, default)
    return default


async def scheduled_alerts_job():
    """
    Job que verifica alertas programadas cada 60 segundos.

    Este job:
    1. Crea una nueva sesión de base de datos
    2. Verifica todas las alertas programadas activas
    3. Crea alertas para las que corresponda
    4. Actualiza las fechas de próximo disparo
    5. Hace commit de los cambios
    """
    logger.info("Iniciando job de alertas programadas")

    while True:
        try:
            async with get_session_context() as session:
                scheduled_repo = ScheduledAlertRepository(session)
                alert_repo = AlertRepository(session)
                service = AlertSchedulerService(scheduled_repo, alert_repo)

                count = await service.check_and_trigger_alerts()

                if count > 0:
                    logger.info(f"Alertas programadas disparadas: {count}")

                await session.commit()

        except asyncio.CancelledError:
            logger.info("Job de alertas programadas cancelado")
            raise
        except Exception as e:
            logger.error(f"Error en scheduled_alerts_job: {e}", exc_info=True)

        # Esperar 60 segundos antes de la siguiente verificación
        await asyncio.sleep(60)


async def silo_monitor_job():
    """
    Job que monitorea niveles de silos cada 5 minutos.

    Este job:
    1. Crea una nueva sesión de base de datos
    2. Verifica todos los silos del sistema
    3. Genera alertas para silos con nivel bajo
    4. Hace commit de los cambios
    """
    logger.info("Iniciando job de monitoreo de silos")

    # Esperar 30 segundos antes de la primera ejecución
    # para dar tiempo a que el sistema se inicialice
    await asyncio.sleep(30)

    while True:
        try:
            async with get_session_context() as session:
                silo_repo = SiloRepository(session)
                alert_repo = AlertRepository(session)
                service = SiloMonitorService(silo_repo, alert_repo)

                count = await service.check_all_silos()

                if count > 0:
                    logger.info(f"Alertas de nivel bajo de silos generadas: {count}")

                await session.commit()

        except asyncio.CancelledError:
            logger.info("Job de monitoreo de silos cancelado")
            raise
        except Exception as e:
            logger.error(f"Error en silo_monitor_job: {e}", exc_info=True)

        # Esperar 5 minutos (300 segundos) antes de la siguiente verificación
        await asyncio.sleep(300)


async def scheduled_feeding_job(dispatcher: ScheduledFeedingDispatcher, poll_interval_seconds: int = 15):
    """Dispara una vez al día los planes calculados y persistidos."""
    logger.info("Iniciando job de alimentación programada")
    while True:
        try:
            await dispatcher.dispatch_due_plans()
        except asyncio.CancelledError:
            logger.info("Job de alimentación programada cancelado")
            raise
        except Exception as exc:
            logger.error("Error en scheduled_feeding_job: %s", exc, exc_info=True)
        await asyncio.sleep(poll_interval_seconds)


@asynccontextmanager
async def lifespan_with_scheduler(app: FastAPI):
    """
    Lifespan context manager que inicia los background jobs.

    Jobs iniciados:
    - Alertas programadas: cada 60 segundos
    - Monitoreo de silos: cada 5 minutos

    Uso en main.py:
        from infrastructure.services.background_tasks import lifespan_with_scheduler

        app = FastAPI(lifespan=lifespan_with_scheduler)
    """
    global _scheduler_task, _silo_monitor_task, _scheduled_feeding_task, _feeding_execution_worker_task

    # Startup
    logger.info("Iniciando background tasks...")

    # Crear admin por defecto si no existe
    try:
        async with get_session_context() as session:
            await seed_default_admin_if_needed(session)
    except Exception as e:
        logger.error("Error al crear administrador por defecto: %s", e, exc_info=True)

    _scheduler_task = asyncio.create_task(scheduled_alerts_job())
    _silo_monitor_task = asyncio.create_task(silo_monitor_job())
    # Cada proceso puede ejecutar un worker: PostgreSQL garantiza que solo uno
    # reclame cada job mediante SKIP LOCKED y leases persistidos.
    from api.dependencies import get_simulated_machine

    machine = get_simulated_machine()
    grace_minutes = _positive_int_from_env("SCHEDULED_FEEDING_GRACE_MINUTES", 15)
    poll_seconds = _positive_int_from_env("SCHEDULED_FEEDING_POLL_SECONDS", 15)
    scheduled_dispatcher = ScheduledFeedingDispatcher(
        machine,
        async_session_maker,
        grace_period=timedelta(minutes=grace_minutes),
    )
    _scheduled_feeding_task = asyncio.create_task(scheduled_feeding_job(scheduled_dispatcher, poll_seconds))
    feeding_worker = FeedingExecutionWorker(machine, async_session_maker)
    _feeding_execution_worker_task = asyncio.create_task(feeding_worker.run())

    yield

    # Shutdown
    logger.info("Deteniendo background tasks...")

    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass

    if _silo_monitor_task:
        _silo_monitor_task.cancel()
        try:
            await _silo_monitor_task
        except asyncio.CancelledError:
            pass

    if _scheduled_feeding_task:
        _scheduled_feeding_task.cancel()
        try:
            await _scheduled_feeding_task
        except asyncio.CancelledError:
            pass

    if _feeding_execution_worker_task:
        _feeding_execution_worker_task.cancel()
        try:
            await _feeding_execution_worker_task
        except asyncio.CancelledError:
            pass

    logger.info("Background tasks detenidos")
