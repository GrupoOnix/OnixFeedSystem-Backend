"""
Servicio de scheduler para alertas programadas.

Este servicio verifica periódicamente las alertas programadas
y crea alertas cuando corresponde según la configuración.
"""

import logging
from datetime import datetime, timezone

from domain.aggregates.alert import Alert
from domain.enums import AlertCategory
from domain.repositories import IAlertRepository, IScheduledAlertRepository

logger = logging.getLogger(__name__)


class AlertSchedulerService:
    """
    Servicio que verifica y dispara alertas programadas.

    Diseñado para ejecutarse periódicamente (cada 60 segundos)
    como un background task de FastAPI.
    """

    def __init__(
        self,
        scheduled_alert_repo: IScheduledAlertRepository,
        alert_repo: IAlertRepository,
    ):
        self._scheduled_alert_repo = scheduled_alert_repo
        self._alert_repo = alert_repo

    async def check_and_trigger_alerts(self) -> int:
        """
        Verifica alertas programadas y crea alertas cuando corresponde.

        Returns:
            Cantidad de alertas disparadas.
        """
        now = datetime.now(timezone.utc)
        triggered_count = 0

        # Obtener solo alertas activas
        scheduled_alerts = await self._scheduled_alert_repo.get_active()

        for sa in scheduled_alerts:
            try:
                if sa.should_trigger(now):
                    # Crear alerta
                    alert = Alert(
                        type=sa.type,
                        category=AlertCategory.MAINTENANCE,
                        title=sa.title,
                        message=sa.message,
                        source=sa.device_name,
                        metadata={
                            "scheduled_alert_id": str(sa.id),
                            "maintenance_date": sa.next_trigger_date.isoformat(),
                            **(sa.metadata or {}),
                        },
                    )
                    await self._alert_repo.save(alert)

                    # Marcar como disparada (actualiza next_trigger_date)
                    sa.mark_triggered()
                    await self._scheduled_alert_repo.save(sa)

                    triggered_count += 1
                    logger.info(
                        f"Alerta programada disparada: {sa.title} "
                        f"(scheduled_alert_id={sa.id})"
                    )

            except Exception as e:
                logger.error(
                    f"Error al procesar alerta programada {sa.id}: {e}",
                    exc_info=True,
                )

        return triggered_count
