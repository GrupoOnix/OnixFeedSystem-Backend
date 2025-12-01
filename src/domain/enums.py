from enum import Enum


class CageStatus(Enum):
    AVAILABLE = "Disponible"
    IN_USE = "En Uso"
    MAINTENANCE = "Mantenimiento"


class SensorType(Enum):
    TEMPERATURE = "Temperatura"
    PRESSURE = "Presión"
    FLOW = "Caudal"

class DoserType(Enum):
    PULSE_DOSER = "PULSE_DOSER"
    VARI_DOSER = "VARI_DOSER"
    SCREW_DOSER = "SCREW_DOSER"


class SessionStatus(Enum):
    CREATED = "Created"
    RUNNING = "Running"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    FAILED = "Failed"

class FeedingMode(Enum):
    MANUAL = "Manual"
    CYCLIC = "Ciclico"
    PROGRAMMED = "Programado"

class FeedingEventType(Enum):
    # 1. Intervención Humana (El "Qué hizo el operador")
    COMMAND = "Command"           # Start, Stop, Pause, Resume
    # 2. Ajustes Finos (El "Cómo lo modificó")
    PARAM_CHANGE = "ParamChange"  # Cambió tasa, cambió blower en caliente
    # 3. Comportamiento de la Máquina (El "Qué pasó solo")
    SYSTEM_STATUS = "SystemStatus" # Fin automático de ciclo, Cambio de jaula automático
    # 4. Salud del Sistema (El "Qué salió mal")
    ALARM = "Alarm"               # Error de PLC, Timeout, Emergencia