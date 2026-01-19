"""
Background tasks para FastAPI.

Este módulo contiene las tareas en segundo plano que se ejecutan
periódicamente durante el ciclo de vida de la aplicación.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.repositories import (
    AlertRepository,
    ScheduledAlertRepository,
)
from infrastructure.services.alert_scheduler_service import AlertSchedulerService

logger = logging.getLogger(__name__)

# Variable global para controlar el task
_scheduler_task: Optional[asyncio.Task] = None


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


@asynccontextmanager
async def lifespan_with_scheduler(app: FastAPI):
    """
    Lifespan context manager que inicia el scheduler de alertas.

    Uso en main.py:
        from infrastructure.services.background_tasks import lifespan_with_scheduler

        app = FastAPI(lifespan=lifespan_with_scheduler)
    """
    global _scheduler_task

    # Startup
    logger.info("Iniciando background tasks...")
    _scheduler_task = asyncio.create_task(scheduled_alerts_job())

    yield

    # Shutdown
    logger.info("Deteniendo background tasks...")
    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
    logger.info("Background tasks detenidos")
