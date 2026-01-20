"""
Servicio centralizado para disparar alertas desde el sistema.

Este servicio proporciona métodos para crear alertas desde diferentes
partes del sistema (triggers automáticos, validaciones, etc.).
"""

from typing import Any, Dict, List, Optional, Tuple

from domain.aggregates.alert import Alert
from domain.enums import AlertCategory, AlertType
from domain.repositories import IAlertRepository
from domain.value_objects import AlertId


class AlertTriggerService:
    """
    Servicio centralizado para disparar alertas desde diferentes partes del sistema.

    Otros use cases pueden inyectar este servicio para crear alertas cuando
    detectan condiciones que requieren notificación al usuario.

    NOTA: Todos los mensajes están en español.
    """

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    # =========================================================================
    # TRIGGERS PRIORITARIOS (Implementados)
    # =========================================================================

    async def silo_low_level(
        self,
        silo_id: str,
        silo_name: str,
        current_level: float,
        max_capacity: float,
        percentage: float,
        critical_threshold: float = 10.0,
    ) -> Optional[AlertId]:
        """
        Nivel bajo de silo.

        Si ya existe una alerta activa para este silo, la actualiza.
        Si existe una alerta silenciada, NO hace nada (evita duplicados).
        Si no existe ninguna alerta, crea una nueva.

        Args:
            silo_id: ID del silo.
            silo_name: Nombre del silo.
            current_level: Nivel actual en kg.
            max_capacity: Capacidad máxima en kg.
            percentage: Porcentaje actual de llenado.
            critical_threshold: Umbral crítico del silo (default 10.0%).

        Returns:
            ID de la alerta (existente o nueva), o None si está silenciada.
        """
        # Determinar tipo de alerta usando el umbral crítico del silo
        alert_type = (
            AlertType.CRITICAL if percentage < critical_threshold else AlertType.WARNING
        )

        # Preparar mensaje y metadata
        message = (
            f"El silo está al {percentage:.1f}% de capacidad "
            f"({current_level:.0f}/{max_capacity:.0f} kg)"
        )
        metadata = {
            "silo_id": silo_id,
            "current_level": current_level,
            "max_capacity": max_capacity,
            "percentage": percentage,
        }

        # Buscar cualquier alerta para este silo (incluyendo silenciadas)
        any_alert = await self._alert_repo.find_any_by_silo(silo_id)

        if any_alert:
            # Si la alerta está silenciada, NO hacer nada (evitar duplicados)
            if any_alert.is_snoozed:
                return None  # No crear ni actualizar

            # Si la alerta está activa (no silenciada), actualizarla
            any_alert.update_content(
                message=message,
                metadata=metadata,
                type=alert_type,
            )
            await self._alert_repo.save(any_alert)
            return any_alert.id
        else:
            # No existe ninguna alerta, crear una nueva
            return await self._create_alert(
                type=alert_type,
                category=AlertCategory.INVENTORY,
                title=f"Nivel bajo en {silo_name}",
                message=message,
                source=silo_name,
                metadata=metadata,
            )

    async def sensor_out_of_range(
        self,
        sensor_id: str,
        sensor_name: str,
        line_id: str,
        line_name: str,
        current_value: float,
        normal_range: Tuple[float, float],
        unit: str,
    ) -> AlertId:
        """
        Sensor fuera de rango.

        Args:
            sensor_id: ID del sensor.
            sensor_name: Nombre del sensor.
            line_id: ID de la línea.
            line_name: Nombre de la línea.
            current_value: Valor actual de la lectura.
            normal_range: Tupla (min, max) del rango normal.
            unit: Unidad de medida (ej: "PSI", "°C").

        Returns:
            ID de la alerta creada.
        """
        return await self._create_alert(
            type=AlertType.WARNING,
            category=AlertCategory.DEVICE,
            title=f"Sensor fuera de rango: {sensor_name}",
            message=f"Valor actual: {current_value} {unit}. Rango normal: {normal_range[0]}-{normal_range[1]} {unit}",
            source=f"{sensor_name} - {line_name}",
            metadata={
                "sensor_id": sensor_id,
                "line_id": line_id,
                "line_name": line_name,
                "current_value": current_value,
                "normal_range": list(normal_range),
                "unit": unit,
            },
        )

    async def device_incomplete_config(
        self,
        device_id: str,
        device_type: str,  # "Blower", "Doser", "Selector"
        device_name: str,
        line_id: str,
        line_name: str,
        missing_fields: List[str],
    ) -> AlertId:
        """
        Dispositivo con configuración incompleta o incorrecta.

        Args:
            device_id: ID del dispositivo.
            device_type: Tipo de dispositivo (Blower, Doser, Selector).
            device_name: Nombre del dispositivo.
            line_id: ID de la línea.
            line_name: Nombre de la línea.
            missing_fields: Lista de campos faltantes o incorrectos.

        Returns:
            ID de la alerta creada.
        """
        missing_str = ", ".join(missing_fields)
        return await self._create_alert(
            type=AlertType.WARNING,
            category=AlertCategory.DEVICE,
            title=f"Configuración incompleta: {device_name}",
            message=f"El {device_type.lower()} tiene campos sin configurar: {missing_str}",
            source=f"{device_name} - {line_name}",
            metadata={
                "device_id": device_id,
                "device_type": device_type,
                "line_id": line_id,
                "line_name": line_name,
                "missing_fields": missing_fields,
            },
        )

    # =========================================================================
    # TRIGGERS FUTUROS (Preparados para implementación)
    # =========================================================================

    async def device_error(
        self,
        device_id: str,
        device_name: str,
        line_id: str,
        line_name: str,
        error_code: str,
        error_message: str,
    ) -> AlertId:
        """
        Dispositivo reporta error.

        FUTURO: Requiere comunicación con PLC para detectar errores.
        """
        return await self._create_alert(
            type=AlertType.CRITICAL,
            category=AlertCategory.DEVICE,
            title=f"Error en {device_name}",
            message=error_message,
            source=f"{device_name} - {line_name}",
            metadata={
                "device_id": device_id,
                "line_id": line_id,
                "line_name": line_name,
                "error_code": error_code,
            },
        )

    async def connection_lost(
        self,
        device_id: str,
        device_name: str,
        line_id: str,
        line_name: str,
        last_seen: str,  # ISO format datetime string
    ) -> AlertId:
        """
        Sin heartbeat de dispositivo (timeout).

        FUTURO: Requiere monitoreo de conexión con dispositivos.
        """
        return await self._create_alert(
            type=AlertType.WARNING,
            category=AlertCategory.CONNECTION,
            title=f"Sin conexión: {device_name}",
            message=f"No se recibe señal del dispositivo desde {last_seen}",
            source=f"{device_name} - {line_name}",
            metadata={
                "device_id": device_id,
                "line_id": line_id,
                "line_name": line_name,
                "last_seen": last_seen,
            },
        )

    async def feeding_operation_failed(
        self,
        operation_id: str,
        line_id: str,
        line_name: str,
        cage_id: str,
        cage_name: str,
        reason: str,
        amount_dispensed: float,
        amount_target: float,
    ) -> AlertId:
        """
        Operación de feeding falla.

        FUTURO: Requiere detección de fallos en operaciones.
        """
        return await self._create_alert(
            type=AlertType.CRITICAL,
            category=AlertCategory.FEEDING,
            title="Fallo en operación de alimentación",
            message=f"La operación falló: {reason}. Dispensado: {amount_dispensed:.1f}kg de {amount_target:.1f}kg objetivo",
            source=f"{line_name} - {cage_name}",
            metadata={
                "operation_id": operation_id,
                "line_id": line_id,
                "line_name": line_name,
                "cage_id": cage_id,
                "cage_name": cage_name,
                "reason": reason,
                "amount_dispensed": amount_dispensed,
                "amount_target": amount_target,
            },
        )

    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    async def create_custom_alert(
        self,
        type: AlertType,
        category: AlertCategory,
        title: str,
        message: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlertId:
        """
        Crea una alerta personalizada.

        Usar para casos no cubiertos por los métodos específicos.
        """
        return await self._create_alert(
            type=type,
            category=category,
            title=title,
            message=message,
            source=source,
            metadata=metadata,
        )

    async def _create_alert(
        self,
        type: AlertType,
        category: AlertCategory,
        title: str,
        message: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlertId:
        """Método interno para crear y guardar una alerta."""
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
