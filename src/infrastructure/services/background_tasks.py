"""
Background tasks para FastAPI.

Este módulo contiene las tareas en segundo plano que se ejecutan
periódicamente durante el ciclo de vida de la aplicación.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI

from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.repositories import (
    AlertRepository,
    ScheduledAlertRepository,
    SiloRepository,
    ScheduledFeedingPlanRepository,
    CageFeedingRepository,
    CageGroupRepository,
    CageRepository,
    FeedingEventRepository,
    FeedingLineRepository,
    FeedingSessionRepository,
    SlotAssignmentRepository,
    SystemConfigRepository,
    ActivityLogRepository,
    SiloInventoryRepository,
)
from infrastructure.services.alert_scheduler_service import AlertSchedulerService
from infrastructure.services.default_admin_service import seed_default_admin_if_needed
from infrastructure.services.silo_monitor_service import SiloMonitorService
from application.services.feeding_orchestrator import FeedingOrchestrator
from application.use_cases.feeding.start_cyclic_feeding_use_case import StartCyclicFeedingUseCase
from api.models.feeding_models import CageConfigInput, CyclicFeedingRequest
from infrastructure.persistence.database import async_session_maker

logger = logging.getLogger(__name__)

# Variables globales para controlar los tasks
_scheduler_task: Optional[asyncio.Task] = None
_silo_monitor_task: Optional[asyncio.Task] = None
_scheduled_feeding_task: Optional[asyncio.Task] = None


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


async def scheduled_feeding_job():
    """Dispara una vez al día los planes calculados y persistidos."""
    logger.info("Iniciando job de alimentación programada")
    while True:
        try:
            async with get_session_context() as session:
                plan_repo = ScheduledFeedingPlanRepository(session)
                for plan in await plan_repo.list():
                    if not plan.is_active:
                        continue
                    try:
                        now = datetime.now(ZoneInfo(plan.timezone))
                    except Exception:
                        now = datetime.now(ZoneInfo("America/Santiago"))
                    today = now.date().isoformat()
                    if now.strftime("%H:%M") != plan.start_time or plan.last_run_on == today:
                        continue
                    # Marcar antes de iniciar para que una falla no cree sesiones duplicadas cada minuto.
                    plan.last_run_on = today
                    plan.last_error = None
                    try:
                        request = CyclicFeedingRequest(
                            line_id=str(plan.line_id),
                            group_id=str(plan.group_id),
                            doser_id=str(plan.doser_id),
                            silo_id=str(plan.silo_id),
                            blower_power_percentage=plan.blower_power_percentage,
                            wait_after_visit_seconds=plan.wait_after_visit_seconds,
                            allow_overtime=True,
                            cage_configs=[
                                CageConfigInput(
                                    cage_id=item["cage_id"],
                                    quantity_kg=round(sum(item["quantity_schedule_kg"]), 6),
                                    visits=len(item["quantity_schedule_kg"]),
                                    visit_quantities_kg=item["quantity_schedule_kg"],
                                    rate_kg_per_min=item["rate_kg_per_min"],
                                    mode=item["mode"],
                                )
                                for item in plan.cage_plans
                            ],
                        )
                        # Import tardío para compartir el mismo simulador que usan los
                        # controles manuales, sin crear un ciclo de imports al iniciar FastAPI.
                        from api.dependencies import get_simulated_machine

                        use_case = StartCyclicFeedingUseCase(
                            session_repository=FeedingSessionRepository(session),
                            cage_feeding_repository=CageFeedingRepository(session),
                            event_repository=FeedingEventRepository(session),
                            line_repository=FeedingLineRepository(session),
                            cage_repository=CageRepository(session),
                            cage_group_repository=CageGroupRepository(session),
                            silo_repository=SiloRepository(session),
                            slot_assignment_repository=SlotAssignmentRepository(session),
                            orchestrator=FeedingOrchestrator(get_simulated_machine(), async_session_maker),
                            system_config_repository=SystemConfigRepository(session),
                            activity_log_repository=ActivityLogRepository(session),
                            inventory_repository=SiloInventoryRepository(session),
                        )
                        result = await use_case.execute(
                            request,
                            operator_id=str(plan.created_by_id or "00000000-0000-0000-0000-000000000000"),
                            operator_name=plan.created_by_name or "Programación diaria",
                            actor=plan.created_by_name or "scheduled-feeding",
                        )
                        plan.last_session_id = result.session_id
                        logger.info("Plan programado %s inició sesión %s", plan.id, result.session_id)
                    except Exception as exc:
                        plan.last_error = str(exc)[:500]
                        logger.error("No se pudo ejecutar plan programado %s: %s", plan.id, exc, exc_info=True)
                    await plan_repo.save(plan)
                await session.commit()
        except asyncio.CancelledError:
            logger.info("Job de alimentación programada cancelado")
            raise
        except Exception as exc:
            logger.error("Error en scheduled_feeding_job: %s", exc, exc_info=True)
        await asyncio.sleep(60)


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
    global _scheduler_task, _silo_monitor_task, _scheduled_feeding_task

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
    _scheduled_feeding_task = asyncio.create_task(scheduled_feeding_job())

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

    logger.info("Background tasks detenidos")
