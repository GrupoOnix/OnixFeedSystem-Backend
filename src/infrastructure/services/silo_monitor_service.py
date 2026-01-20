"""
Servicio de monitoreo de niveles de silos.

Este servicio verifica periódicamente los niveles de todos los silos
y genera alertas cuando detecta niveles bajos.
"""

import logging

from application.services.alert_trigger_service import AlertTriggerService
from domain.aggregates.silo import Silo
from domain.repositories import IAlertRepository, ISiloRepository

logger = logging.getLogger(__name__)


class SiloMonitorService:
    """
    Servicio que monitorea los niveles de silos y genera alertas.

    Diseñado para ejecutarse periódicamente (cada 5 minutos)
    como un background task de FastAPI.
    
    Usa los umbrales configurados de cada silo individual.
    """

    def __init__(
        self,
        silo_repository: ISiloRepository,
        alert_repository: IAlertRepository,
    ):
        self._silo_repo = silo_repository
        self._alert_trigger_service = AlertTriggerService(alert_repository)

    async def check_all_silos(self) -> int:
        """
        Verifica todos los silos y genera alertas para niveles bajos.

        Returns:
            Cantidad de alertas generadas en esta ejecución.
        """
        all_silos = await self._silo_repo.get_all()
        alerts_generated = 0

        for silo in all_silos:
            try:
                if await self._check_and_alert_silo(silo):
                    alerts_generated += 1
            except Exception as e:
                logger.error(
                    f"Error al verificar silo {silo.id} ({silo.name}): {e}",
                    exc_info=True,
                )

        if alerts_generated > 0:
            logger.info(f"Alertas de nivel bajo generadas: {alerts_generated}")

        return alerts_generated

    async def _check_and_alert_silo(self, silo: Silo) -> bool:
        """
        Verifica un silo individual y genera/actualiza alerta si es necesario.
        Usa los umbrales configurados del silo.

        Args:
            silo: El silo a verificar

        Returns:
            True si se generó o actualizó una alerta, False en caso contrario
        """
        # Calcular porcentaje de llenado
        capacity_kg = silo.capacity.as_kg
        current_level_kg = silo.stock_level.as_kg

        # Evitar división por cero
        if capacity_kg == 0:
            return False

        percentage = (current_level_kg / capacity_kg) * 100
        silo_id = str(silo.id)

        # Si el nivel está bajo el umbral WARNING del silo, generar o actualizar alerta
        if percentage < silo.warning_threshold_percentage:
            await self._alert_trigger_service.silo_low_level(
                silo_id=silo_id,
                silo_name=str(silo.name),
                current_level=current_level_kg,
                max_capacity=capacity_kg,
                percentage=percentage,
                critical_threshold=silo.critical_threshold_percentage,
            )
            logger.info(
                f"Alerta de nivel bajo procesada: {silo.name} ({percentage:.1f}%)"
            )
            return True

        return False

    def reset_alert_tracking(self) -> None:
        """
        Método mantenido por compatibilidad pero ya no es necesario.
        
        El tracking de alertas ahora se maneja automáticamente
        buscando alertas existentes en la base de datos.
        """
        logger.info("reset_alert_tracking() llamado - método deprecado, no hace nada")
