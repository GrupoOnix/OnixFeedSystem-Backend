from enum import Enum


class CageStatus(Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"


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
    TEMPERATURE = "TEMPERATURE"
    PRESSURE = "PRESSURE"
    FLOW = "FLOW"


class DoserType(Enum):
    PULSE_DOSER = "PULSE_DOSER"
    VARI_DOSER = "VARI_DOSER"
    SCREW_DOSER = "SCREW_DOSER"


class SessionStatus(Enum):
    """Estado de la sesión diaria (contenedor)."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class OperationStatus(Enum):
    """Estado de una operación individual."""

    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class FeedingMode(Enum):
    MANUAL = "MANUAL"
    CYCLIC = "CYCLIC"
    PROGRAMMED = "PROGRAMMED"


class FeedingEventType(Enum):
    COMMAND = "COMMAND"
    PARAM_CHANGE = "PARAM_CHANGE"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    ALARM = "ALARM"


class OperationEventType(Enum):
    STARTED = "STARTED"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    PARAM_CHANGE = "PARAM_CHANGE"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


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


# ============================================================================
# Enums de Comida y Visita
# ============================================================================


class FeedingStrategy(Enum):
    """Feeding strategy type."""

    MANUAL = "manual"
    CYCLIC = "ciclica"
    PROGRAMMED = "programada"


class FeedingSessionStatus(Enum):
    """Feeding session lifecycle status."""

    SCHEDULED = "programada"
    IN_PROGRESS = "en_curso"
    PAUSED = "pausada"
    COMPLETED = "completada"
    CANCELLED = "cancelada"
    INTERRUPTED = "interrumpida"


class TipoComida(Enum):
    """Tipo de comida según su programación."""

    MANUAL = "MANUAL"
    CICLICA = "CICLICA"
    PROGRAMADA = "PROGRAMADA"


class EstadoComida(Enum):
    """Estado del ciclo de vida de una comida."""

    PROGRAMADA = "PROGRAMADA"
    EN_CURSO = "EN_CURSO"
    PAUSADA = "PAUSADA"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"
    INTERRUMPIDA = "INTERRUMPIDA"


class EstadoVisita(Enum):
    """Estado del ciclo de vida de una visita."""

    PENDIENTE = "PENDIENTE"  # Creada, esperando ejecución
    EN_CURSO = "EN_CURSO"  # Ejecutándose actualmente
    COMPLETADA = "COMPLETADA"  # Finalizada exitosamente
    CANCELADA = "CANCELADA"  # Cancelada o interrumpida
