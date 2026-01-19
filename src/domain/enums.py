from enum import Enum


class CageStatus(Enum):
    AVAILABLE = "Disponible"
    IN_USE = "En Uso"
    MAINTENANCE = "Mantenimiento"


class PopulationEventType(Enum):
    """Tipo de evento que afecta la población de una jaula."""

    INITIAL_STOCK = "INITIAL_STOCK"  # Siembra inicial
    RESTOCK = "RESTOCK"  # Resiembra / adición de peces
    MORTALITY = "MORTALITY"  # Mortalidad
    HARVEST = "HARVEST"  # Cosecha (extracción parcial o total)
    TRANSFER_IN = "TRANSFER_IN"  # Transferencia desde otra jaula
    TRANSFER_OUT = "TRANSFER_OUT"  # Transferencia hacia otra jaula
    BIOMETRY = "BIOMETRY"  # Actualización de peso promedio (sin cambio de cantidad)
    ADJUSTMENT = "ADJUSTMENT"  # Ajuste manual / corrección de inventario


class SensorType(Enum):
    TEMPERATURE = "Temperatura"
    PRESSURE = "Presión"
    FLOW = "Caudal"


class DoserType(Enum):
    PULSE_DOSER = "PULSE_DOSER"
    VARI_DOSER = "VARI_DOSER"
    SCREW_DOSER = "SCREW_DOSER"


class SessionStatus(Enum):
    """Estado de la sesión diaria (contenedor)."""

    ACTIVE = "Active"  # Sesión abierta, puede tener operaciones
    CLOSED = "Closed"  # Sesión cerrada (fin del día)


class OperationStatus(Enum):
    """Estado de una operación individual."""

    RUNNING = "Running"  # Operación en curso
    PAUSED = "Paused"  # Operación congelada temporalmente
    COMPLETED = "Completed"  # Operación finalizada exitosamente
    STOPPED = "Stopped"  # Operación detenida manualmente
    FAILED = "Failed"  # Operación fallida por error


class FeedingMode(Enum):
    MANUAL = "Manual"
    CYCLIC = "Ciclico"
    PROGRAMMED = "Programado"


class FeedingEventType(Enum):
    # 1. Intervención Humana (El "Qué hizo el operador")
    COMMAND = "Command"  # Start, Stop, Pause, Resume
    # 2. Ajustes Finos (El "Cómo lo modificó")
    PARAM_CHANGE = "ParamChange"  # Cambió tasa, cambió blower en caliente
    # 3. Comportamiento de la Máquina (El "Qué pasó solo")
    SYSTEM_STATUS = (
        "SystemStatus"  # Fin automático de ciclo, Cambio de jaula automático
    )
    # 4. Salud del Sistema (El "Qué salió mal")
    ALARM = "Alarm"  # Error de PLC, Timeout, Emergencia


class OperationEventType(Enum):
    """Tipos de eventos específicos de operación."""

    STARTED = "Started"
    PAUSED = "Paused"
    RESUMED = "Resumed"
    PARAM_CHANGE = "ParamChange"
    COMPLETED = "Completed"
    STOPPED = "Stopped"
    FAILED = "Failed"


# ============================================================================
# Enums de Alertas
# ============================================================================


class AlertType(Enum):
    """Tipo/severidad de la alerta."""

    CRITICAL = "CRITICAL"  # Atención inmediata requerida
    WARNING = "WARNING"  # Requiere seguimiento
    INFO = "INFO"  # Información general
    SUCCESS = "SUCCESS"  # Operación exitosa


class AlertStatus(Enum):
    """Estado del ciclo de vida de una alerta."""

    UNREAD = "UNREAD"  # Nueva, no vista
    READ = "READ"  # Vista pero no resuelta
    RESOLVED = "RESOLVED"  # Resuelta
    ARCHIVED = "ARCHIVED"  # Archivada


class AlertCategory(Enum):
    """Categoría de la alerta según su origen."""

    SYSTEM = "SYSTEM"  # Sistema general
    DEVICE = "DEVICE"  # Dispositivos (blower, doser, selector)
    FEEDING = "FEEDING"  # Operaciones de alimentación
    INVENTORY = "INVENTORY"  # Inventario (silos)
    MAINTENANCE = "MAINTENANCE"  # Mantenimiento programado
    CONNECTION = "CONNECTION"  # Conectividad


class ScheduledAlertFrequency(Enum):
    """Frecuencia de repetición de alertas programadas."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM_DAYS = "CUSTOM_DAYS"
