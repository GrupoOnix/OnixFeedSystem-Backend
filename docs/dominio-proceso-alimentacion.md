# Dominio: Proceso de Alimentación

**Versión:** 1.0
**Fecha:** 2025-12-04
**Contexto:** Bounded Context de Alimentación (Feeding Context)

Este documento define el modelo de dominio para el proceso de alimentación en sistemas de acuicultura, siguiendo principios de Domain-Driven Design (DDD) y Clean Architecture.

---

## 1. Visión General

El dominio de alimentación modela el proceso completo de dispensar alimento a jaulas de peces, desde el inicio de una sesión diaria hasta la finalización de operaciones individuales. El sistema sigue el patrón **Orchestrator (Backend) → Autonomous Executor (PLC)**.

### Responsabilidades del Dominio:
- Gestión de sesiones operativas diarias
- Control del ciclo de vida de operaciones de alimentación
- Validación de reglas de negocio (invariantes)
- Traducción de intenciones lógicas a configuraciones físicas
- Auditoría mediante eventos de dominio

---

## 2. Aggregate Root: `FeedingSession`

Representa una sesión operativa diaria de alimentación para una línea específica. Es la **raíz del agregado** y el punto de entrada para cualquier modificación de estado en el proceso de alimentación.

### 2.1 Responsabilidades

- Garantizar consistencia transaccional del día operativo
- Mantener acumuladores globales de dispensado
- Gestionar el ciclo de vida de operaciones
- Validar invariantes antes de cambios de estado
- Generar eventos de dominio para auditoría

### 2.2 Invariantes

1. **Una sesión activa por línea**: Solo puede existir una `FeedingSession` con estado `ACTIVE` por `LineId`
2. **Operación única activa**: No puede iniciar nueva operación si existe `current_operation` en estado `RUNNING` o `PAUSED`
3. **Cierre limpio**: No puede cerrar sesión con operación activa

### 2.3 Atributos

```python
class FeedingSession:
    # Identidad
    _id: SessionId                          # UUID único de la sesión
    _line_id: LineId                        # Línea de alimentación asociada
    _date: datetime                         # Fecha de la sesión (día operativo)
    _status: SessionStatus                  # ACTIVE | CLOSED

    # Acumuladores del día
    _total_dispensed_kg: Weight             # Total dispensado en la sesión
    _dispensed_by_slot: Dict[int, Weight]   # Dispensado por slot físico

    # Referencia a operación actual
    _current_operation: Optional[FeedingOperation]  # Operación en curso (si existe)

    # Auditoría
    _session_events: List[FeedingEvent]     # Eventos a nivel de sesión
    _created_at: datetime                   # Timestamp de creación
```

### 2.4 Métodos de Negocio

#### Gestión del Ciclo de Vida

```python
def __init__(self, line_id: LineId) -> None:
    """
    Crea una nueva sesión de alimentación.
    Estado inicial: ACTIVE
    """

def close_session(self) -> None:
    """
    Cierra la sesión al final del día.
    Precondición: current_operation debe ser None
    """
```

#### Gestión de Operaciones

```python
async def start_operation(
    self,
    cage_id: CageId,
    strategy: IFeedingStrategy,
    machine: IFeedingMachine
) -> OperationId:
    """
    Inicia una nueva operación de alimentación.

    Flujo:
    1. Validar invariante: no hay operación activa (RUNNING/PAUSED)
    2. Obtener configuración del PLC desde la estrategia
    3. Crear nueva FeedingOperation
    4. Enviar configuración al PLC
    5. Registrar como current_operation
    6. Log evento de sesión

    Returns:
        OperationId de la operación creada

    Raises:
        DomainException: Si ya hay operación activa
    """

async def stop_current_operation(
    self,
    machine: IFeedingMachine
) -> None:
    """
    Finaliza la operación actual (STOP = destruir contexto).

    Flujo:
    1. Validar que existe current_operation
    2. Enviar comando STOP al PLC
    3. Cerrar operación (status → STOPPED)
    4. Actualizar acumuladores de sesión
    5. Liberar slot (current_operation → None)
    6. Log evento de sesión

    Idempotente: Si no hay operación, no hace nada.
    """

async def pause_current_operation(
    self,
    machine: IFeedingMachine
) -> None:
    """
    Pausa temporalmente la operación actual (PAUSE = congelar tiempo).

    Flujo:
    1. Validar que existe current_operation
    2. Validar status == RUNNING
    3. Enviar comando PAUSE al PLC
    4. Transición: operation.status → PAUSED
    5. Log evento

    Nota: La operación sigue siendo current_operation.
    El PLC mantiene RAM (contadores, punteros).

    Raises:
        DomainException: Si no hay operación o no está RUNNING
    """

async def resume_current_operation(
    self,
    machine: IFeedingMachine
) -> None:
    """
    Reanuda una operación pausada.

    Flujo:
    1. Validar que existe current_operation
    2. Validar status == PAUSED
    3. Enviar comando RESUME al PLC
    4. Transición: operation.status → RUNNING
    5. Log evento

    Raises:
        DomainException: Si no hay operación o no está PAUSED
    """

async def update_current_operation_params(
    self,
    blower_speed: Optional[float] = None,
    doser_speed: Optional[float] = None,
    machine: IFeedingMachine
) -> None:
    """
    Actualiza parámetros de la operación en caliente (hot swap).

    Flujo:
    1. Validar que existe current_operation
    2. Validar status == RUNNING
    3. Obtener configuración actual de la operación
    4. Aplicar delta (merge de valores nuevos)
    5. Crear nueva estrategia con valores actualizados
    6. Obtener nueva MachineConfiguration
    7. Enviar nueva configuración al PLC
    8. Actualizar operation.applied_config
    9. Log evento con diff de cambios

    Nota: NO cambia el estado de la máquina de estados.
    Solo inyecta nueva configuración.

    Raises:
        DomainException: Si no hay operación o no está RUNNING
    """
```

#### Sincronización con PLC

```python
def update_from_plc(self, plc_status: MachineStatus) -> None:
    """
    Sincroniza estado desde el PLC (heartbeat background).

    Flujo:
    1. Calcular delta de peso dispensado
    2. Actualizar current_operation.dispensed
    3. Actualizar acumuladores de sesión
    4. Detectar errores del PLC y fallar operación si es necesario

    Nota: Llamado por un servicio de background que lee el PLC periódicamente.
    """
```

#### Auditoría y Reportes

```python
def pop_events(self) -> List[FeedingEvent]:
    """
    Retorna y limpia eventos de sesión para persistencia.
    """

def get_daily_summary(self) -> Dict[str, Any]:
    """
    Genera reporte del estado actual de la sesión.

    Returns:
        {
            "session_id": UUID,
            "date": ISO datetime,
            "status": "ACTIVE" | "CLOSED",
            "total_kg": float,
            "details_by_slot": {slot: kg},
            "current_operation": {...} | None
        }
    """
```

#### Métodos Privados

```python
def _log_session_event(
    self,
    type: FeedingEventType,
    description: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registra un evento a nivel de sesión.
    """

def _initialize_slot_accumulator(self, slot: int) -> None:
    """
    Inicializa contador de slot si no existe.
    """
```

---

## 3. Entity: `FeedingOperation`

Representa una operación atómica de alimentación sobre una jaula específica. Es una **"visita"** desde START hasta STOP/COMPLETED. Tiene un ciclo de vida finito e independiente.

### 3.1 Responsabilidades

- Mantener el estado de una ejecución unitaria
- Registrar configuración aplicada (snapshot para auditoría)
- Gestionar transiciones de estado (máquina de estados)
- Acumular cantidad dispensada
- Generar eventos de operación

### 3.2 Ciclo de Vida (Máquina de Estados)

```
RUNNING → PAUSED → RUNNING → STOPPED | COMPLETED | FAILED
```

- **RUNNING**: Operación en ejecución
- **PAUSED**: Operación pausada (PLC mantiene RAM)
- **COMPLETED**: Finalizada automáticamente (meta alcanzada)
- **STOPPED**: Detenida manualmente por operador
- **FAILED**: Fallida por error del PLC

### 3.3 Atributos

```python
class FeedingOperation:
    # Identidad y relaciones
    _id: OperationId                        # UUID único de la operación
    _session_id: SessionId                  # Sesión a la que pertenece
    _cage_id: CageId                        # Jaula objetivo
    _target_slot: int                       # Slot físico usado

    # Estado de ejecución
    _status: OperationStatus                # RUNNING | PAUSED | COMPLETED | STOPPED | FAILED
    _started_at: datetime                   # Timestamp de inicio
    _ended_at: Optional[datetime]           # Timestamp de finalización

    # Configuración aplicada (snapshot inmutable)
    _applied_config: Dict[str, Any]         # Configuración enviada al PLC (JSON serializable)

    # Métricas
    _target_amount: Weight                  # Meta de alimentación
    _dispensed: Weight                      # Cantidad dispensada acumulada

    # Auditoría
    _events: List[OperationEvent]           # Log completo de eventos
    _new_events: List[OperationEvent]       # Cola de eventos nuevos (para persistencia)
```

### 3.4 Métodos de Negocio

#### Gestión de Estado

```python
def __init__(
    self,
    session_id: SessionId,
    cage_id: CageId,
    target_slot: int,
    target_amount: Weight,
    applied_config: Dict[str, Any]
) -> None:
    """
    Crea una nueva operación.
    Estado inicial: RUNNING
    """

def pause(self) -> None:
    """
    Pausa la operación.
    Precondición: status == RUNNING
    """

def resume(self) -> None:
    """
    Reanuda la operación.
    Precondición: status == PAUSED
    """

def stop(self) -> None:
    """
    Detiene manualmente la operación.
    Transición: status → STOPPED, ended_at = now
    Idempotente.
    """

def complete(self) -> None:
    """
    Finaliza automáticamente la operación (meta alcanzada).
    Transición: status → COMPLETED, ended_at = now
    Idempotente.
    """

def fail(self, error_code: str) -> None:
    """
    Marca la operación como fallida.
    Transición: status → FAILED, ended_at = now
    """
```

#### Actualización de Configuración

```python
def update_config(
    self,
    new_config: Dict[str, Any],
    changes: Dict[str, Any]
) -> None:
    """
    Actualiza la configuración aplicada (hot swap).
    Precondición: status == RUNNING
    Registra evento con diff de cambios.
    """
```

#### Sincronización

```python
def add_dispensed_amount(self, delta: Weight) -> None:
    """
    Incrementa la cantidad dispensada.
    Llamado desde el heartbeat de sincronización con PLC.
    """
```

#### Auditoría

```python
def pop_new_events(self) -> List[OperationEvent]:
    """
    Retorna y limpia eventos nuevos para persistencia.
    """

def _log_event(
    self,
    type: OperationEventType,
    description: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registra un evento de operación.
    """
```

---

## 4. Value Objects

### 4.1 Identificadores (UUID-based)

```python
@dataclass(frozen=True)
class SessionId:
    value: UUID

    @staticmethod
    def generate() -> SessionId:
        return SessionId(uuid4())

@dataclass(frozen=True)
class OperationId:
    value: UUID

    @staticmethod
    def generate() -> OperationId:
        return OperationId(uuid4())
```

### 4.2 Métricas

```python
@dataclass(frozen=True)
class Weight:
    """Peso en kilogramos."""
    _kg: float

    @staticmethod
    def zero() -> Weight:
        return Weight(0.0)

    @staticmethod
    def from_kg(kg: float) -> Weight:
        if kg < 0:
            raise ValueError("Weight cannot be negative")
        return Weight(kg)

    @property
    def as_kg(self) -> float:
        return self._kg

    @property
    def as_grams(self) -> float:
        return self._kg * 1000

    def __add__(self, other: Weight) -> Weight:
        return Weight(self._kg + other._kg)
```

### 4.3 DTOs de Configuración

```python
@dataclass(frozen=True)
class MachineConfiguration:
    """
    Configuración que se envía al PLC (Downlink).
    Estructura plana, JSON-serializable.
    """
    slot_numbers: List[int]              # Slots a activar
    target_amount_kg: float              # Meta de alimentación
    blower_speed_percentage: float       # Velocidad soplador (0-100)
    doser_speed_percentage: float        # Velocidad dosificador (0-100)
    operation_mode: str                  # "MANUAL" | "CYCLIC"
```

```python
@dataclass(frozen=True)
class MachineStatus:
    """
    Estado leído del PLC (Uplink).
    """
    total_dispensed_kg: float            # Total dispensado acumulado
    current_weight: float                # Peso actual en tolva
    motor_status: str                    # Estado del motor
    has_error: bool                      # Indica si hay error
    error_code: Optional[str]            # Código de error (si aplica)
    alarms: List[str]                    # Lista de alarmas activas
```

---

## 5. Enums

### 5.1 Estados de Sesión

```python
class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"       # Sesión operativa activa
    CLOSED = "CLOSED"       # Sesión cerrada (fin del día)
```

### 5.2 Estados de Operación

```python
class OperationStatus(str, Enum):
    RUNNING = "RUNNING"         # En ejecución
    PAUSED = "PAUSED"           # Pausada temporalmente
    COMPLETED = "COMPLETED"     # Completada automáticamente
    STOPPED = "STOPPED"         # Detenida manualmente
    FAILED = "FAILED"           # Fallida por error
```

### 5.3 Comandos del PLC

```python
class MachineCommand(str, Enum):
    PAUSE = "PAUSE"         # Congelar ejecución (mantener RAM)
    RESUME = "RESUME"       # Reanudar ejecución
    STOP = "STOP"           # Detener y resetear
```

### 5.4 Tipos de Eventos

```python
class FeedingEventType(str, Enum):
    COMMAND = "COMMAND"                 # Comando de usuario
    SYSTEM_STATUS = "SYSTEM_STATUS"     # Cambio de estado del sistema
    SYNC = "SYNC"                       # Sincronización con PLC

class OperationEventType(str, Enum):
    STARTED = "STARTED"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARAM_CHANGE = "PARAM_CHANGE"       # Cambio de parámetros en caliente
```

---

## 6. Domain Events

### 6.1 Eventos de Sesión

```python
@dataclass
class FeedingEvent:
    """Evento a nivel de sesión."""
    timestamp: datetime
    type: FeedingEventType
    description: str
    details: Dict[str, Any]
```

### 6.2 Eventos de Operación

```python
@dataclass
class OperationEvent:
    """Evento a nivel de operación."""
    timestamp: datetime
    type: OperationEventType
    description: str
    details: Dict[str, Any]
```

---

## 7. Interfaces de Dominio

### 7.1 Repositorios

```python
class IFeedingSessionRepository(Protocol):
    """Repository para FeedingSession."""

    async def save(self, session: FeedingSession) -> None:
        """Persiste una sesión (create o update)."""

    async def find_by_id(self, session_id: SessionId) -> Optional[FeedingSession]:
        """Busca sesión por ID."""

    async def find_active_by_line_id(self, line_id: LineId) -> Optional[FeedingSession]:
        """Busca sesión ACTIVE para una línea."""

    async def find_by_line_and_date(
        self,
        line_id: LineId,
        date: datetime
    ) -> Optional[FeedingSession]:
        """Busca sesión por línea y fecha."""
```

```python
class IFeedingOperationRepository(Protocol):
    """Repository para FeedingOperation."""

    async def save(self, operation: FeedingOperation) -> None:
        """Persiste una operación (create o update)."""

    async def find_by_id(self, operation_id: OperationId) -> Optional[FeedingOperation]:
        """Busca operación por ID."""

    async def find_current_by_session(
        self,
        session_id: SessionId
    ) -> Optional[FeedingOperation]:
        """
        Busca la operación actual de una sesión.
        Retorna la operación con status RUNNING o PAUSED.
        """

    async def find_all_by_session(
        self,
        session_id: SessionId
    ) -> List[FeedingOperation]:
        """Busca todas las operaciones de una sesión (historial del día)."""
```

### 7.2 Interfaz de Hardware (PLC)

```python
class IFeedingMachine(Protocol):
    """
    Puerto de comunicación con el PLC.
    Responsabilidad: Traducir comandos de dominio a protocolo Modbus/TCP.
    """

    async def send_configuration(
        self,
        line_id: LineId,
        config: MachineConfiguration
    ) -> None:
        """
        Envía configuración completa al PLC para iniciar operación.

        Escribe en registros Modbus:
        - Slots a activar
        - Velocidades de motores
        - Meta de dispensado
        - Modo de operación
        """

    async def send_command(
        self,
        line_id: LineId,
        command: MachineCommand
    ) -> None:
        """
        Envía comando discreto al PLC.

        Escribe señal booleana (bit trigger) según comando:
        - PAUSE: Congela ejecución (mantiene RAM)
        - RESUME: Reanuda ejecución
        - STOP: Detiene y resetea contexto
        """

    async def get_status(
        self,
        line_id: LineId
    ) -> MachineStatus:
        """
        Lee estado actual del PLC.

        Lee de registros Modbus:
        - Peso dispensado acumulado
        - Estado de motores
        - Alarmas activas
        - Códigos de error
        """
```

### 7.3 Interfaz de Estrategia

```python
class IFeedingStrategy(Protocol):
    """
    Factory de configuraciones del PLC.
    Responsabilidad: Traducir intención lógica a configuración física.
    """

    def get_plc_configuration(self) -> MachineConfiguration:
        """
        Genera la configuración del PLC según la estrategia.

        Returns:
            MachineConfiguration con todos los parámetros físicos.
        """
```

---

## 8. Estrategias de Alimentación

### 8.1 Estrategia Manual

```python
class ManualFeedingStrategy:
    """
    Estrategia para alimentación manual de una jaula específica.
    Mapeo directo 1:1 (una jaula, un slot).
    """

    def __init__(
        self,
        target_slot: int,
        target_amount_kg: float,
        blower_speed_percentage: float,
        doser_speed_percentage: float
    ):
        self._target_slot = target_slot
        self._target_amount_kg = target_amount_kg
        self._blower_speed = blower_speed_percentage
        self._doser_speed = doser_speed_percentage
        self._validate_parameters()

    def get_plc_configuration(self) -> MachineConfiguration:
        """
        Retorna configuración para alimentación manual.
        Un solo slot activo.
        """
        return MachineConfiguration(
            slot_numbers=[self._target_slot],
            target_amount_kg=self._target_amount_kg,
            blower_speed_percentage=self._blower_speed,
            doser_speed_percentage=self._doser_speed,
            operation_mode="MANUAL"
        )

    def _validate_parameters(self) -> None:
        if self._target_slot < 1:
            raise ValueError("Slot must be >= 1")
        if self._target_amount_kg <= 0:
            raise ValueError("Target amount must be > 0")
        if not (0 <= self._blower_speed <= 100):
            raise ValueError("Blower speed must be 0-100")
        if not (0 <= self._doser_speed <= 100):
            raise ValueError("Doser speed must be 0-100")
```

### 8.2 Estrategia Cíclica

```python
class CyclicFeedingStrategy:
    """
    Estrategia para alimentación cíclica de múltiples jaulas.
    Distribuye alimento entre varios slots en ciclos.
    """

    def __init__(
        self,
        target_slots: List[int],
        total_amount_kg: float,
        distribution_mode: str,  # "EQUAL" | "WEIGHTED"
        blower_speed_percentage: float,
        doser_speed_percentage: float,
        weights_per_slot: Optional[Dict[int, float]] = None
    ):
        self._target_slots = target_slots
        self._total_amount_kg = total_amount_kg
        self._distribution_mode = distribution_mode
        self._blower_speed = blower_speed_percentage
        self._doser_speed = doser_speed_percentage
        self._weights_per_slot = weights_per_slot or {}
        self._validate_parameters()

    def get_plc_configuration(self) -> MachineConfiguration:
        """
        Retorna configuración para alimentación cíclica.
        Múltiples slots activos.

        Nota: La lógica de distribución (ciclos, tiempos) la maneja el PLC.
        El backend solo envía la configuración inicial.
        """
        return MachineConfiguration(
            slot_numbers=self._target_slots,
            target_amount_kg=self._total_amount_kg,
            blower_speed_percentage=self._blower_speed,
            doser_speed_percentage=self._doser_speed,
            operation_mode="CYCLIC"
        )

    def _validate_parameters(self) -> None:
        if not self._target_slots:
            raise ValueError("At least one slot is required")
        if len(self._target_slots) < 2:
            raise ValueError("Cyclic mode requires at least 2 slots")
        if self._total_amount_kg <= 0:
            raise ValueError("Total amount must be > 0")
        if self._distribution_mode not in ["EQUAL", "WEIGHTED"]:
            raise ValueError("Distribution mode must be EQUAL or WEIGHTED")
        if self._distribution_mode == "WEIGHTED" and not self._weights_per_slot:
            raise ValueError("Weighted mode requires weights_per_slot")
```

---

## 9. Relaciones con Otros Agregados

### 9.1 Relación con `Cage`

- **FeedingOperation** referencia `cage_id: CageId`
- **FeedingOperation** usa `target_slot: int` (obtenido desde `Cage.slot_number`)
- La jaula conoce su slot y línea asignada (`Cage.line_id`, `Cage.slot_number`)

**Consulta necesaria en Use Case:**
```python
# Para validar que cage pertenece a la línea
cage = await cage_repository.find_by_id(cage_id)
if cage.line_id != requested_line_id:
    raise ValueError("Cage does not belong to the requested line")

# Slot físico se obtiene directamente
target_slot = cage.slot_number
```

### 9.2 Relación con `FeedingLine`

- **FeedingSession** referencia `line_id: LineId`
- La línea contiene componentes físicos (blower, doser, selector, sensor)
- **No hay relación bidireccional**: `FeedingLine` no conoce sus sesiones

**Consulta necesaria en Use Case:**
```python
# Validar que la línea existe
line = await line_repository.find_by_id(line_id)
if not line:
    raise ValueError(f"Line {line_id} not found")
```

### 9.3 Relación con `Silo`

- **No hay relación directa** en el modelo actual
- El silo se conecta físicamente al dosificador de la línea
- Futuro: Podría rastrearse consumo por silo

---

## 10. Dudas y Decisiones de Diseño

### 10.1 Decisiones Tomadas (Con Fundamento)

#### ✅ Método genérico `send_command()` en IFeedingMachine
**Decisión:** Usar un método genérico con enum `MachineCommand` en lugar de métodos específicos (`pause()`, `resume()`, `stop()`).

**Fundamento:**
- Alineado con el patrón Orchestrator → Executor
- Consistencia con `send_configuration()`
- Extensibilidad (nuevos comandos sin cambiar interfaz)
- Menor acoplamiento entre dominio e infraestructura

---

#### ✅ Update Params con Delta (merge en dominio)
**Decisión:** El use case pasa solo los valores que cambiaron (`blower_speed`, `doser_speed` como opcionales). El dominio hace el merge con valores actuales.

**Fundamento:**
- API más simple (envías solo cambios)
- Lógica de negocio (merge) en el dominio, no en application layer
- Permite validaciones específicas según parámetro

---

#### ✅ Repositorios Separados (Session y Operation)
**Decisión:** `IFeedingSessionRepository` y `IFeedingOperationRepository` son independientes.

**Fundamento:**
- Control fino de persistencia
- Operaciones se persisten inmediatamente (no al final del día)
- Session no necesita cargar todas las operations en memoria
- Consultas históricas eficientes vía repository

---

#### ✅ Eventos en Listas (no Event Sourcing puro)
**Decisión:** Los eventos se almacenan en listas dentro de los agregados y se persisten en tablas relacionales.

**Fundamento:**
- Auditoría suficiente sin complejidad de event store
- Reconstrucción de estado desde tablas (no desde eventos)
- Más simple para el equipo de desarrollo

---

#### ✅ Slot en Cage (no en Line)
**Decisión:** Cada `Cage` conoce su `slot_number` y `line_id`.

**Fundamento:**
- Simplifica asignación dinámica
- Cage es una entidad con ubicación física
- No requiere consulta adicional a través de Line

---

### 10.2 Dudas Pendientes (Sin Fundamento Claro)

#### ❓ Gestión de Day Boundary
**Pregunta:** ¿Quién es responsable de cerrar sesiones de días anteriores?

**Opciones:**
1. **Use Case de Start:** Al iniciar nueva operación, cierra sesión antigua y crea nueva
2. **Servicio de Background:** Job nocturno que cierra sesiones del día anterior
3. **Domain Service:** Servicio específico `DayBoundaryService` que coordina

**Inclinación actual:** Opción 1 (use case), pero podría generar latencia en request de start.

---

#### ❓ Auto-Completion de Operaciones
**Pregunta:** ¿Cómo detecta el sistema que una operación alcanzó su meta?

**Opciones:**
1. **Heartbeat detecta:** El servicio de sync con PLC compara `dispensed >= target` y llama `operation.complete()`
2. **PLC envía señal:** El PLC escribe un flag de "completed" que se lee en el heartbeat
3. **Híbrido:** PLC envía señal + backend valida

**Inclinación actual:** Opción 2 (PLC decide), pero requiere coordinación con equipo de hardware.

---

#### ❓ Idempotencia de `start_operation()`
**Pregunta:** Si el frontend envía doble clic en START, ¿cómo manejamos?

**Opciones:**
1. **Validación estricta:** Lanza excepción si ya hay operación activa
2. **Idempotente:** Si ya existe operación para la misma jaula, retorna su ID sin error
3. **Request ID:** El frontend envía un `request_id` único, se valida duplicación

**Inclinación actual:** Opción 1 (validación estricta), pero podría mejorar UX con opción 2.

---

#### ❓ Estrategia Cíclica: ¿Lógica en PLC o Backend?
**Pregunta:** En modo cíclico, ¿quién decide los tiempos de ciclo y distribución?

**Escenario:**
- Backend envía configuración inicial (slots, total_kg, modo)
- ¿El PLC decide cuánto tiempo alimentar cada slot?
- ¿O el backend calcula tiempos y los envía?

**Opciones:**
1. **PLC autónomo:** Backend envía config, PLC ejecuta lógica de ciclos
2. **Backend calcula:** Backend envía array de `[{slot, duration, amount}]`

**Inclinación actual:** Opción 1 (PLC autónomo), alineado con patrón Executor.

**Implicación:** Si es opción 1, `MachineConfiguration` para modo CYCLIC necesita definir qué parámetros adicionales enviar (ej. `cycle_duration_seconds`, `distribution_weights`).

---

#### ❓ Manejo de Errores del PLC
**Pregunta:** Cuando el PLC reporta error, ¿quién decide si fallar la operación?

**Opciones:**
1. **Dominio decide:** `update_from_plc()` detecta error y llama `operation.fail()`
2. **Servicio de sync decide:** El background service llama `session.handle_plc_error(status)`
3. **Casos específicos:** Algunos errores son recuperables (alarma), otros no (falla motor)

**Inclinación actual:** Opción 3 (casos específicos), pero requiere definir taxonomía de errores con equipo de hardware.

---

#### ❓ Acumuladores de Sesión: ¿Cuándo actualizar?
**Pregunta:** `_total_dispensed_kg` y `_dispensed_by_slot` se actualizan en:
1. **Heartbeat (online):** Cada sync con PLC actualiza
2. **Al cerrar operación (offline):** Solo cuando operation.stop()/complete()

**Inclinación actual:** Opción 1 (heartbeat), permite dashboards en tiempo real.

**Implicación:** Si PLC pierde conexión, los acumuladores pueden quedarse desincronizados temporalmente.

---

#### ❓ Validación de Parámetros: ¿Dominio o Strategy?
**Pregunta:** ¿Quién valida que `blower_speed` esté en 0-100?

**Opciones:**
1. **Strategy valida:** En `ManualFeedingStrategy._validate_parameters()`
2. **Value Object valida:** Crear `BlowerSpeed(value)` que valida en constructor
3. **Ambos:** Strategy valida reglas de negocio, VO valida tipo

**Inclinación actual:** Opción 1 (strategy), pero value objects mejorarían type safety.

---

### 10.3 Preguntas para el Equipo

1. **Hardware:** ¿El PLC puede enviar señal de "operación completada" o debemos calcular `dispensed >= target` en backend?

2. **Hardware:** ¿Qué códigos de error puede reportar el PLC y cuáles son recuperables vs. fatales?

3. **UX:** ¿Qué debe pasar si el usuario hace doble clic en START? ¿Error o idempotencia?

4. **Producto:** En modo cíclico, ¿cuánto control necesita el operador sobre la distribución (tiempos, pesos por slot)?

5. **Operaciones:** ¿Existe un proceso nocturno de cierre de día o esperamos que el operador cierre manualmente?

---

## 11. Próximos Pasos

1. **Validar decisiones de diseño** con equipo técnico y de producto
2. **Resolver dudas pendientes** (especialmente interacción con PLC)
3. **Definir Use Cases** en detalle (Start, Stop, Pause, Resume, Update)
4. **Especificar DTOs de Application Layer** (StartFeedingRequest, etc.)
5. **Diseñar mapeo a persistencia** (modelos SQLModel)

---

**Fin del Documento**
