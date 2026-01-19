"""Caso de uso interno para crear alertas desde triggers del sistema."""

from typing import Any, Dict, Optional

from domain.aggregates.alert import Alert
from domain.enums import AlertCategory, AlertType
from domain.repositories import IAlertRepository
from domain.value_objects import AlertId


class CreateAlertUseCase:
    """
    Caso de uso interno para crear alertas.

    Este caso de uso es usado por:
    - AlertTriggerService (para triggers automáticos)
    - AlertSchedulerService (para alertas programadas)

    No está expuesto directamente en la API (las alertas se crean
    desde triggers del sistema, no manualmente por usuarios).
    """

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(
        self,
        type: AlertType,
        category: AlertCategory,
        title: str,
        message: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlertId:
        """
        Crea una nueva alerta en el sistema.

        Args:
            type: Tipo/severidad de la alerta (CRITICAL, WARNING, INFO, SUCCESS).
            category: Categoría de la alerta (DEVICE, INVENTORY, FEEDING, etc.).
            title: Título corto de la alerta.
            message: Descripción detallada.
            source: Origen de la alerta (ej: "Soplador BL-001 - Línea 1").
            metadata: Datos adicionales en formato JSON.

        Returns:
            ID de la alerta creada.
        """
        alert = Alert(
            type=type,
            category=category,
            title=title,
            message=message,
            source=source,
            metadata=metadata,
        )

        await self._alert_repo.save(alert)
        return alert.id
