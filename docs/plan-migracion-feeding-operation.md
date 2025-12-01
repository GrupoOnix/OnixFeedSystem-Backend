# Plan de Migración: Introducción de FeedingOperation

**Versión:** 1.2  
**Fecha:** Diciembre 2025  
**Autor:** Equipo de Desarrollo  
**Estado:** Propuesta Técnica - Lista para Implementación

---

## 🔔 Aclaraciones Importantes

### Decisiones de Diseño Confirmadas

1. **Interfaces de Repositorios**: Ambos repositorios (`FeedingSessionRepository` y `FeedingOperationRepository`) implementan interfaces (`IFeedingSessionRepository` e `IFeedingOperationRepository`) para mantener consistencia con el patrón del proyecto.

2. **Dependency Injection**: Se usa FastAPI `Depends()` para inyectar repositorios en casos de uso. Ver sección completa de DI más abajo.

3. **Testing**: No se implementarán tests unitarios en esta fase inicial. Se validará manualmente el flujo completo. Tests se agregarán en fase posterior si es necesario.

4. **Migración de Base de Datos**: No hay datos en producción, por lo que las migraciones son libres y sin riesgo de pérdida de datos.

5. **SessionStatus**: Se cambia directamente de `CREATED, RUNNING, PAUSED, COMPLETED, FAILED` a solo `ACTIVE, CLOSED`. Los estados viejos se eliminan completamente.

6. **Repositorios Separados**: Cada entidad tiene su propio repositorio para mejor performance. Las operaciones se persisten individualmente, no al final del día.

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Estado Actual del Sistema](#estado-actual-del-sistema)
3. [Problema Identificado](#problema-identificado)
4. [Solución Propuesta](#solución-propuesta)
5. [Plan de Migración](#plan-de-migración)
6. [Checklist de Implementación](#checklist-de-implementación)

---

## 🎯 Resumen Ejecutivo

### Problema

El modelo actual de `FeedingSession` confunde dos conceptos distintos:

- **Sesión Diaria**: Contenedor de todas las operaciones del día
- **Operación Atómica**: Una visita individual a una jaula (de START a STOP)

Esto impide que el operador pueda:

- Alimentar múltiples jaulas en el mismo día
- Volver a alimentar la misma jaula varias veces
- Mantener trazabilidad detallada por visita

### Solución

Introducir la entidad `FeedingOperation` dentro del aggregate `FeedingSession`:

- **FeedingSession**: Representa el "Día Operativo" (contenedor, siempre en estado `ACTIVE`)
- **FeedingOperation**: Representa una "Visita a una Jaula" (operación atómica con su propio ciclo de vida)

---

## 📊 Estado Actual del Sistema

### Modelo de Dominio Actual

```python
# src/domain/aggregates/feeding_session.py
class FeedingSession:
    _id: SessionId
    _line_id: LineId
    _date: datetime
    _status: SessionStatus  # CREATED, RUNNING, PAUSED, COMPLETED, FAILED
    _total_dispensed_kg: Weight
    _dispensed_by_slot: Dict[int, Weight]
    _applied_strategy_config: Optional[Dict[str, Any]]
    _new_events: List[FeedingEvent]
```

### Comportamiento Actual (Problemático)

```python
# Flujo que NO funciona:

# 1. START Jaula 1
session.start(strategy_jaula_1, machine)
# → session.status = RUNNING

# 2. STOP (finalizar alimentación de Jaula 1)
session.stop(machine)
# → session.status = PAUSED  ⚠️ PROBLEMA

# 3. START Jaula 2 (FALLA)
session.start(strategy_jaula_2, machine)
# → ERROR: "There is already an active feeding session"
```

**Problema Crítico**: Después de `STOP`, no se puede iniciar una nueva operación en la misma sesión.

---

## 🔍 Problema Identificado

### Confusión Semántica

| Comando    | Significado Correcto       | Comportamiento Actual           | Problema                      |
| ---------- | -------------------------- | ------------------------------- | ----------------------------- |
| **START**  | Iniciar nueva operación    | Cambia session.status a RUNNING | ✅ Correcto                   |
| **STOP**   | Finalizar operación actual | Cambia session.status a PAUSED  | ❌ Bloquea nuevas operaciones |
| **PAUSE**  | Congelar temporalmente     | Cambia session.status a PAUSED  | ⚠️ Mismo estado que STOP      |
| **RESUME** | Descongelar                | Cambia session.status a RUNNING | ✅ Correcto                   |

### Escenario Requerido

```
DÍA 2025-11-28 (Line 1):
├─ 08:00 → START Jaula 1 (50kg)
├─ 08:30 → PAUSE
├─ 08:40 → RESUME
├─ 09:00 → STOP ✅ Fin de Operación 1
├─ 10:00 → START Jaula 2 (50kg) ❌ FALLA actualmente
├─ 11:00 → STOP ✅ Fin de Operación 2
└─ 14:00 → START Jaula 1 otra vez (30kg) ❌ FALLA actualmente

RESUMEN: Jaula 1: 80kg en 2 visitas | Jaula 2: 50kg en 1 visita
```

---

## 💡 Solución Propuesta

### Value Objects Nuevos

```python
# src/domain/value_objects.py (AGREGAR)
from dataclasses import dataclass
from uuid import UUID, uuid4

@dataclass(frozen=True)
class OperationId:
    """Value Object para identificar operaciones."""
    value: UUID

    @staticmethod
    def generate() -> 'OperationId':
        return OperationId(uuid4())

    def __str__(self) -> str:
        return str(self.value)
```

### Nuevos Enums

```python
# src/domain/enums.py (AGREGAR)

class SessionStatus(Enum):
    """Estado de la sesión diaria (contenedor)."""
    ACTIVE = "Active"      # Sesión abierta, puede tener operaciones
    CLOSED = "Closed"      # Sesión cerrada (fin del día)

class OperationStatus(Enum):
    """Estado de una operación individual."""
    RUNNING = "Running"    # Operación en curso
    PAUSED = "Paused"      # Operación congelada temporalmente
    COMPLETED = "Completed"  # Operación finalizada exitosamente
    STOPPED = "Stopped"    # Operación detenida manualmente
    FAILED = "Failed"      # Operación fallida por error

class OperationEventType(Enum):
    """Tipos de eventos específicos de operación."""
    STARTED = "Started"
    PAUSED = "Paused"
    RESUMED = "Resumed"
    PARAM_CHANGE = "ParamChange"
    COMPLETED = "Completed"
    STOPPED = "Stopped"
    FAILED = "Failed"
```

### Entidad FeedingOperation

```python
# src/domain/entities/feeding_operation.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from domain.enums import OperationStatus, OperationEventType
from domain.value_objects import CageId, Weight, OperationId

@dataclass
class OperationEvent:
    """Evento específico de una operación."""
    timestamp: datetime
    type: OperationEventType
    description: str
    details: Dict[str, Any]

class FeedingOperation:
    """
    Entity que representa una operación atómica de alimentación.
    Una "visita" a una jaula desde START hasta STOP.
    """

    def __init__(
        self,
        session_id: SessionId,
        cage_id: CageId,
        target_slot: int,
        target_amount: Weight,
        applied_config: Dict[str, Any]
    ):
        self._id: OperationId = OperationId.generate()
        self._session_id: SessionId = session_id  # Necesario para persistencia
        self._cage_id: CageId = cage_id
        self._target_slot: int = target_slot
        self._target_amount: Weight = target_amount
        self._dispensed: Weight = Weight.zero()
        self._status: OperationStatus = OperationStatus.RUNNING
        self._started_at: datetime = datetime.utcnow()
        self._ended_at: Optional[datetime] = None
        self._applied_config: Dict[str, Any] = applied_config
        self._events: List[OperationEvent] = []
        self._new_events: List[OperationEvent] = []  # Cola de eventos nuevos

        self._log_event(
            OperationEventType.STARTED,
            f"Operación iniciada en jaula {cage_id}",
            {"target_kg": target_amount.as_kg, "slot": target_slot}
        )

    # Properties
    @property
    def id(self) -> OperationId:
        return self._id

    @property
    def cage_id(self) -> CageId:
        return self._cage_id

    @property
    def target_slot(self) -> int:
        return self._target_slot

    @property
    def target_amount(self) -> Weight:
        return self._target_amount

    @property
    def dispensed(self) -> Weight:
        return self._dispensed

    @property
    def status(self) -> OperationStatus:
        return self._status

    @property
    def started_at(self) -> datetime:
        return self._started_at

    @property
    def ended_at(self) -> Optional[datetime]:
        return self._ended_at

    @property
    def applied_config(self) -> Dict[str, Any]:
        return self._applied_config.copy()

    @property
    def events(self) -> List[OperationEvent]:
        """Retorna todos los eventos (para reconstrucción desde BD)."""
        return self._events.copy()

    # Métodos de negocio
    def _log_event(self, type: OperationEventType, description: str, details: Dict[str, Any] = None):
        event = OperationEvent(
            timestamp=datetime.utcnow(),
            type=type,
            description=description,
            details=details or {}
        )
        self._events.append(event)
        self._new_events.append(event)  # También a la cola de nuevos

    def pop_new_events(self) -> List[OperationEvent]:
        """Devuelve y limpia la cola de eventos nuevos para persistir."""
        events = self._new_events.copy()
        self._new_events.clear()
        return events

    def pause(self):
        if self._status != OperationStatus.RUNNING:
            raise ValueError("Solo se puede pausar una operación RUNNING")
        self._status = OperationStatus.PAUSED
        self._log_event(OperationEventType.PAUSED, f"Pausado en {self._dispensed.as_kg}kg")

    def resume(self):
        if self._status != OperationStatus.PAUSED:
            raise ValueError("Solo se puede reanudar una operación PAUSED")
        self._status = OperationStatus.RUNNING
        self._log_event(OperationEventType.RESUMED, "Operación reanudada")

    def update_config(self, new_config: Dict[str, Any], changes: Dict[str, Any]):
        if self._status != OperationStatus.RUNNING:
            raise ValueError("Solo se pueden cambiar parámetros en RUNNING")
        self._applied_config = new_config
        self._log_event(OperationEventType.PARAM_CHANGE, "Parámetros actualizados", changes)

    def add_dispensed_amount(self, delta: Weight):
        """Incrementa la cantidad dispensada (llamado desde sync con PLC)."""
        self._dispensed += delta

    def complete(self):
        """Marca la operación como completada (fin automático)."""
        if self._status in [OperationStatus.COMPLETED, OperationStatus.STOPPED]:
            return  # Idempotente

        self._status = OperationStatus.COMPLETED
        self._ended_at = datetime.utcnow()
        self._log_event(
            OperationEventType.COMPLETED,
            f"Operación completada: {self._dispensed.as_kg}kg de {self._target_amount.as_kg}kg",
            {"dispensed": self._dispensed.as_kg, "target": self._target_amount.as_kg}
        )

    def stop(self):
        """Marca la operación como detenida manualmente."""
        if self._status in [OperationStatus.COMPLETED, OperationStatus.STOPPED]:
            return  # Idempotente

        self._status = OperationStatus.STOPPED
        self._ended_at = datetime.utcnow()
        self._log_event(
            OperationEventType.STOPPED,
            f"Operación detenida: {self._dispensed.as_kg}kg de {self._target_amount.as_kg}kg",
            {"dispensed": self._dispensed.as_kg, "target": self._target_amount.as_kg}
        )

    def fail(self, error_code: str):
        """Marca la operación como fallida."""
        self._status = OperationStatus.FAILED
        self._ended_at = datetime.utcnow()
        self._log_event(OperationEventType.FAILED, "Operación fallida", {"error_code": error_code})
```

### FeedingSession Refactorizado

```python
# src/domain/aggregates/feeding_session.py (REFACTORIZADO)

class FeedingSession:
    """
    Aggregate Root que representa una sesión operativa diaria.
    Mantiene acumuladores globales y referencia a la operación actual.
    """

    def __init__(self, line_id: LineId):
        self._id: SessionId = SessionId.generate()
        self._line_id: LineId = line_id
        self._date: datetime = datetime.utcnow()
        self._status: SessionStatus = SessionStatus.ACTIVE  # Siempre ACTIVE al crear

        # Acumuladores globales del día
        self._total_dispensed_kg: Weight = Weight.zero()
        self._dispensed_by_slot: Dict[int, Weight] = {}

        # Operación actual (la clave del cambio)
        # NO mantenemos lista completa de operaciones en memoria
        self._current_operation: Optional[FeedingOperation] = None

        # Eventos a nivel de sesión
        self._session_events: List[FeedingEvent] = []

    # Properties
    @property
    def id(self) -> SessionId:
        return self._id

    @property
    def line_id(self) -> LineId:
        return self._line_id

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def status(self) -> SessionStatus:
        return self._status

    @property
    def total_dispensed_kg(self) -> Weight:
        return self._total_dispensed_kg

    @property
    def dispensed_by_slot(self) -> Dict[int, Weight]:
        return self._dispensed_by_slot.copy()

    @property
    def current_operation(self) -> Optional[FeedingOperation]:
        return self._current_operation

    # Métodos de negocio
    async def start_operation(
        self,
        cage_id: CageId,
        target_slot: int,
        strategy: IFeedingStrategy,
        machine: IFeedingMachine
    ) -> OperationId:
        """Inicia una nueva operación de alimentación."""

        # Validar que no haya operación activa
        if self._current_operation is not None:
            if self._current_operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                raise ValueError(
                    f"Ya hay una operación activa (status: {self._current_operation.status}). "
                    "Debes hacer STOP primero."
                )

        # Obtener configuración del PLC
        config_dto = strategy.get_plc_configuration()
        config_dict = asdict(config_dto)
        config_serialized = _serialize_for_json(config_dict)

        # Crear nueva operación
        operation = FeedingOperation(
            session_id=self._id,
            cage_id=cage_id,
            target_slot=target_slot,
            target_amount=Weight.from_kg(config_dto.target_amount_kg),
            applied_config=config_serialized
        )

        # Inicializar contador de slot si no existe
        if target_slot not in self._dispensed_by_slot:
            self._dispensed_by_slot[target_slot] = Weight.zero()

        # Enviar configuración al PLC
        await machine.send_configuration(self._line_id, config_dto)

        # Registrar operación como actual
        self._current_operation = operation

        # Log a nivel de sesión
        self._log_session_event(
            FeedingEventType.COMMAND,
            f"Nueva operación iniciada en jaula {cage_id}",
            {"operation_id": str(operation.id), "target_kg": config_dto.target_amount_kg}
        )

        return operation.id

    async def stop_current_operation(self, machine: IFeedingMachine) -> None:
        """Finaliza la operación actual (cierra la visita)."""

        if self._current_operation is None:
            return  # Idempotente

        # Detener PLC
        await machine.stop(self._line_id)

        # Cerrar operación
        self._current_operation.stop()

        # Log a nivel de sesión
        self._log_session_event(
            FeedingEventType.COMMAND,
            f"Operación finalizada: {self._current_operation.dispensed.as_kg}kg",
            {"operation_id": str(self._current_operation.id)}
        )

        # Liberar slot (la sesión sigue ACTIVE)
        self._current_operation = None

    async def pause_current_operation(self, machine: IFeedingMachine) -> None:
        """Pausa temporalmente la operación actual."""

        if self._current_operation is None:
            raise ValueError("No hay operación activa para pausar")

        if self._current_operation.status != OperationStatus.RUNNING:
            raise ValueError("Solo se puede pausar una operación RUNNING")

        await machine.pause(self._line_id)
        self._current_operation.pause()

    async def resume_current_operation(self, machine: IFeedingMachine) -> None:
        """Reanuda la operación pausada."""

        if self._current_operation is None:
            raise ValueError("No hay operación para reanudar")

        if self._current_operation.status != OperationStatus.PAUSED:
            raise ValueError("Solo se puede reanudar una operación PAUSED")

        await machine.resume(self._line_id)
        self._current_operation.resume()

    async def update_current_operation_params(
        self,
        new_strategy: IFeedingStrategy,
        machine: IFeedingMachine
    ) -> None:
        """Actualiza parámetros de la operación actual en caliente."""

        if self._current_operation is None:
            raise ValueError("No hay operación activa")

        if self._current_operation.status != OperationStatus.RUNNING:
            raise ValueError("Solo se pueden cambiar parámetros en RUNNING")

        # Obtener nueva configuración
        new_config_dto = new_strategy.get_plc_configuration()
        old_config = self._current_operation.applied_config

        # Detectar cambios
        changes = {}
        if new_config_dto.blower_speed_percentage != old_config.get('blower_speed_percentage'):
            changes['blower_speed'] = {
                'from': old_config.get('blower_speed_percentage'),
                'to': new_config_dto.blower_speed_percentage
            }
        if new_config_dto.doser_speed_percentage != old_config.get('doser_speed_percentage'):
            changes['doser_speed'] = {
                'from': old_config.get('doser_speed_percentage'),
                'to': new_config_dto.doser_speed_percentage
            }

        # Aplicar
        config_dict = asdict(new_config_dto)
        config_serialized = _serialize_for_json(config_dict)

        await machine.send_configuration(self._line_id, new_config_dto)
        self._current_operation.update_config(config_serialized, changes)

    def update_from_plc(self, plc_status: MachineStatus) -> None:
        """Sincroniza estado desde el PLC (heartbeat). PENDIENTE DE IMPLEMENTACIÓN COMPLETA."""

        if self._current_operation is None:
            return

        # Calcular delta
        new_total = plc_status.total_dispensed_kg
        current_total = self._total_dispensed_kg.as_kg
        delta_kg = new_total - current_total

        if delta_kg > 0:
            delta_weight = Weight.from_kg(delta_kg)

            # Actualizar operación actual
            self._current_operation.add_dispensed_amount(delta_weight)

            # Actualizar acumuladores de sesión
            slot = self._current_operation.target_slot
            self._dispensed_by_slot[slot] += delta_weight
            self._total_dispensed_kg += delta_weight

        # Sincronizar estado (simplificado por ahora)
        if plc_status.has_error:
            if self._current_operation.status != OperationStatus.FAILED:
                self._current_operation.fail(plc_status.error_code)

    def close_session(self) -> None:
        """Cierra la sesión al final del día."""
        if self._current_operation is not None:
            raise ValueError("No se puede cerrar sesión con operación activa")

        self._status = SessionStatus.CLOSED
        self._log_session_event(FeedingEventType.SYSTEM_STATUS, "Sesión cerrada (fin del día)")

    def _log_session_event(self, type: FeedingEventType, description: str, details: Dict[str, Any] = None):
        event = FeedingEvent(
            timestamp=datetime.utcnow(),
            type=type,
            description=description,
            details=details or {}
        )
        self._session_events.append(event)

    def pop_events(self) -> List[FeedingEvent]:
        events = self._session_events.copy()
        self._session_events.clear()
        return events
```

### Modelo de Persistencia

```sql
-- Tabla: feeding_sessions (MODIFICADA)
CREATE TABLE feeding_sessions (
    id UUID PRIMARY KEY,
    line_id UUID REFERENCES feeding_lines(id),
    date TIMESTAMP,
    status VARCHAR,  -- ACTIVE, CLOSED
    total_dispensed_kg FLOAT,
    dispensed_by_slot JSONB
);

-- Tabla: feeding_operations (NUEVA)
CREATE TABLE feeding_operations (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES feeding_sessions(id) ON DELETE CASCADE,
    cage_id UUID REFERENCES cages(id),
    target_slot INTEGER,
    target_amount_kg FLOAT,
    dispensed_kg FLOAT,
    status VARCHAR,  -- RUNNING, PAUSED, COMPLETED, STOPPED, FAILED
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    applied_config JSONB
);

-- Tabla: operation_events (NUEVA)
CREATE TABLE operation_events (
    id UUID PRIMARY KEY,
    operation_id UUID REFERENCES feeding_operations(id) ON DELETE CASCADE,
    timestamp TIMESTAMP,
    type VARCHAR,
    description TEXT,
    details JSONB
);

-- Tabla: feeding_events (MODIFICADA - solo eventos de sesión)
CREATE TABLE feeding_events (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES feeding_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP,
    type VARCHAR,
    description TEXT,
    details JSONB
);
```

---

## 🚀 Plan de Migración

### Fase 1: Preparación del Dominio

#### 1.1. Crear Value Object OperationId

**Archivo**: `src/domain/value_objects.py`

Agregar al final del archivo:

```python
@dataclass(frozen=True)
class OperationId:
    """Value Object para identificar operaciones."""
    value: UUID

    @staticmethod
    def generate() -> 'OperationId':
        return OperationId(uuid4())

    def __str__(self) -> str:
        return str(self.value)
```

#### 1.2. Crear Nuevos Enums

**Archivo**: `src/domain/enums.py`

Agregar al final:

```python
class OperationStatus(Enum):
    RUNNING = "Running"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    STOPPED = "Stopped"
    FAILED = "Failed"

class OperationEventType(Enum):
    STARTED = "Started"
    PAUSED = "Paused"
    RESUMED = "Resumed"
    PARAM_CHANGE = "ParamChange"
    COMPLETED = "Completed"
    STOPPED = "Stopped"
    FAILED = "Failed"
```

Modificar `SessionStatus`:

```python
class SessionStatus(Enum):
    ACTIVE = "Active"    # Sesión abierta
    CLOSED = "Closed"    # Sesión cerrada
```

#### 1.3. Crear/Verificar Interfaces de Repositorios

**Archivo**: `src/domain/repositories.py`

**A. IFeedingOperationRepository (NUEVA)**

Agregar al final del archivo:

```python
from domain.entities.feeding_operation import FeedingOperation
from domain.value_objects import OperationId, SessionId

class IFeedingOperationRepository(ABC):
    """Interfaz del repositorio de operaciones de alimentación."""

    @abstractmethod
    async def save(self, operation: FeedingOperation) -> None:
        """Guarda o actualiza una operación."""
        pass

    @abstractmethod
    async def find_by_id(self, operation_id: OperationId) -> Optional[FeedingOperation]:
        """Busca una operación por su ID."""
        pass

    @abstractmethod
    async def find_current_by_session(self, session_id: SessionId) -> Optional[FeedingOperation]:
        """Encuentra la operación activa (RUNNING o PAUSED) de una sesión."""
        pass

    @abstractmethod
    async def find_all_by_session(self, session_id: SessionId) -> List[FeedingOperation]:
        """Obtiene todas las operaciones de una sesión (para reportes)."""
        pass
```

**B. IFeedingSessionRepository (VERIFICAR)**

Verificar que la interfaz existente tenga estos métodos:

```python
class IFeedingSessionRepository(ABC):
    """Interfaz del repositorio de sesiones de alimentación."""

    @abstractmethod
    async def save(self, session: FeedingSession) -> None:
        """Guarda o actualiza una sesión."""
        pass

    @abstractmethod
    async def find_by_id(self, session_id: SessionId) -> Optional[FeedingSession]:
        """Busca una sesión por su ID."""
        pass

    @abstractmethod
    async def find_active_by_line_id(self, line_id: LineId) -> Optional[FeedingSession]:
        """Busca la sesión activa de una línea."""
        pass
```

#### 1.4. Crear Entidad FeedingOperation

**Archivo**: `src/domain/entities/__init__.py` (crear carpeta si no existe)

```python
from .feeding_operation import FeedingOperation, OperationEvent

__all__ = ["FeedingOperation", "OperationEvent"]
```

**Archivo**: `src/domain/entities/feeding_operation.py`

Copiar la implementación completa de la sección "Solución Propuesta".

---

### Fase 2: Migración de Base de Datos

#### 2.1. Crear Modelos de Persistencia

**Archivo**: `src/infrastructure/persistence/models/feeding_operation_model.py`

```python
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .feeding_session_model import FeedingSessionModel
    from .operation_event_model import OperationEventModel

class FeedingOperationModel(SQLModel, table=True):
    __tablename__ = "feeding_operations"

    id: UUID = Field(primary_key=True)
    session_id: UUID = Field(foreign_key="feeding_sessions.id", index=True)
    cage_id: UUID = Field(foreign_key="cages.id")
    target_slot: int
    target_amount_kg: float
    dispensed_kg: float = Field(default=0.0)
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    applied_config: Dict[str, Any] = Field(sa_column=Column(JSONB))

    # Relationships
    session: "FeedingSessionModel" = Relationship(back_populates="operations")
    events: List["OperationEventModel"] = Relationship(
        back_populates="operation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

**Archivo**: `src/infrastructure/persistence/models/operation_event_model.py`

```python
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .feeding_operation_model import FeedingOperationModel

class OperationEventModel(SQLModel, table=True):
    __tablename__ = "operation_events"

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    operation_id: UUID = Field(foreign_key="feeding_operations.id", index=True)
    timestamp: datetime
    type: str
    description: str
    details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    operation: "FeedingOperationModel" = Relationship(back_populates="events")
```

#### 2.2. Actualizar FeedingSessionModel

**Archivo**: `src/infrastructure/persistence/models/feeding_session_model.py`

Agregar relationship:

```python
# Agregar al final de la clase
operations: List["FeedingOperationModel"] = Relationship(
    back_populates="session",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
```

Eliminar campo:

```python
# ELIMINAR esta línea:
applied_strategy_config: Optional[Dict[str, Any]] = Field(...)
```

#### 2.3. Crear Migración de Alembic

```bash
alembic revision --autogenerate -m "add_feeding_operations_and_operation_events"
```

Revisar y aplicar:

```bash
alembic upgrade head
```

---

### Fase 3: Refactorizar Aggregate

#### 3.1. Backup

```bash
cp src/domain/aggregates/feeding_session.py src/domain/aggregates/feeding_session.py.backup
```

#### 3.2. Reemplazar FeedingSession

Reemplazar completamente con la implementación de la sección "Solución Propuesta".

---

### Fase 4: Actualizar Repositorios

#### 4.1. FeedingSessionRepository

**Archivo**: `src/infrastructure/persistence/repositories/feeding_session_repository.py`

```python
class FeedingSessionRepository(IFeedingSessionRepository):
    def __init__(self, session: AsyncSession):
        self.db = session

    async def save(self, feeding_session: FeedingSession) -> None:
        """Guarda solo la sesión (acumuladores y estado)."""

        # Intentar recuperar modelo existente
        session_model = await self.db.get(FeedingSessionModel, feeding_session.id.value)

        if session_model:
            # UPDATE
            session_model.status = feeding_session.status.value
            session_model.total_dispensed_kg = feeding_session.total_dispensed_kg.as_kg
            session_model.dispensed_by_slot = {
                str(slot): weight.as_kg
                for slot, weight in feeding_session.dispensed_by_slot.items()
            }
        else:
            # INSERT
            session_model = FeedingSessionModel(
                id=feeding_session.id.value,
                line_id=feeding_session.line_id.value,
                date=feeding_session.date,
                status=feeding_session.status.value,
                total_dispensed_kg=feeding_session.total_dispensed_kg.as_kg,
                dispensed_by_slot={
                    str(slot): weight.as_kg
                    for slot, weight in feeding_session.dispensed_by_slot.items()
                }
            )
            self.db.add(session_model)

        # Guardar eventos de sesión
        for event in feeding_session.pop_events():
            event_model = FeedingEventModel(
                id=uuid4(),
                session_id=feeding_session.id.value,
                timestamp=event.timestamp,
                event_type=event.type.value,
                description=event.description,
                details=event.details
            )
            self.db.add(event_model)

        await self.db.flush()

    async def find_by_id(self, session_id: SessionId) -> Optional[FeedingSession]:
        result = await self.db.execute(
            select(FeedingSessionModel)
            .where(FeedingSessionModel.id == session_id.value)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_active_by_line_id(self, line_id: LineId) -> Optional[FeedingSession]:
        query = select(FeedingSessionModel).where(
            FeedingSessionModel.line_id == line_id.value,
            FeedingSessionModel.status == SessionStatus.ACTIVE.value
        ).order_by(desc(FeedingSessionModel.date))

        result = await self.db.execute(query)
        model = result.scalar_one_or_none()

        return self._to_domain(model) if model else None

    def _to_domain(self, model: FeedingSessionModel) -> FeedingSession:
        """Reconstruye el aggregate desde el modelo (sin operaciones)."""
        session = FeedingSession.__new__(FeedingSession)
        session._id = SessionId(model.id)
        session._line_id = LineId(model.line_id)
        session._date = model.date
        session._status = SessionStatus(model.status)
        session._total_dispensed_kg = Weight.from_kg(model.total_dispensed_kg)
        session._dispensed_by_slot = {
            int(slot): Weight.from_kg(kg)
            for slot, kg in (model.dispensed_by_slot or {}).items()
        }
        session._current_operation = None  # Se carga por separado
        session._session_events = []

        return session
```

#### 4.2. FeedingOperationRepository (NUEVO)

**Archivo**: `src/infrastructure/persistence/repositories/feeding_operation_repository.py`

```python
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.feeding_operation import FeedingOperation, OperationEvent
from domain.enums import OperationStatus, OperationEventType
from domain.value_objects import OperationId, CageId, Weight, SessionId
from domain.repositories import IFeedingOperationRepository
from infrastructure.persistence.models import FeedingOperationModel, OperationEventModel

class FeedingOperationRepository(IFeedingOperationRepository):
    def __init__(self, session: AsyncSession):
        self.db = session

    async def save(self, operation: FeedingOperation) -> None:
        """Guarda/actualiza una operación individual."""

        # Intentar recuperar modelo existente
        op_model = await self.db.get(FeedingOperationModel, operation.id.value)

        if op_model:
            # UPDATE
            op_model.status = operation.status.value
            op_model.dispensed_kg = operation.dispensed.as_kg
            op_model.ended_at = operation.ended_at
            op_model.applied_config = operation.applied_config
        else:
            # INSERT (nueva operación)
            op_model = FeedingOperationModel(
                id=operation.id.value,
                session_id=operation._session_id.value,  # Necesita session_id
                cage_id=operation.cage_id.value,
                target_slot=operation.target_slot,
                target_amount_kg=operation.target_amount.as_kg,
                dispensed_kg=operation.dispensed.as_kg,
                status=operation.status.value,
                started_at=operation.started_at,
                ended_at=operation.ended_at,
                applied_config=operation.applied_config
            )
            self.db.add(op_model)

        # Guardar solo eventos NUEVOS
        for event in operation.pop_new_events():
            event_model = OperationEventModel(
                id=uuid4(),
                operation_id=operation.id.value,
                timestamp=event.timestamp,
                type=event.type.value,
                description=event.description,
                details=event.details
            )
            self.db.add(event_model)

        await self.db.flush()

    async def find_by_id(self, operation_id: OperationId) -> Optional[FeedingOperation]:
        result = await self.db.execute(
            select(FeedingOperationModel)
            .where(FeedingOperationModel.id == operation_id.value)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_current_by_session(self, session_id: SessionId) -> Optional[FeedingOperation]:
        """Encuentra la operación activa (RUNNING o PAUSED) de una sesión."""
        query = select(FeedingOperationModel).where(
            FeedingOperationModel.session_id == session_id.value,
            FeedingOperationModel.status.in_([
                OperationStatus.RUNNING.value,
                OperationStatus.PAUSED.value
            ])
        ).order_by(desc(FeedingOperationModel.started_at))

        result = await self.db.execute(query)
        model = result.scalar_one_or_none()

        return self._to_domain(model) if model else None

    async def find_all_by_session(self, session_id: SessionId) -> List[FeedingOperation]:
        """Obtiene todas las operaciones de una sesión (para reportes)."""
        query = select(FeedingOperationModel).where(
            FeedingOperationModel.session_id == session_id.value
        ).order_by(FeedingOperationModel.started_at)

        result = await self.db.execute(query)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: FeedingOperationModel) -> FeedingOperation:
        """Reconstruye la operación desde el modelo."""
        operation = FeedingOperation.__new__(FeedingOperation)
        operation._id = OperationId(model.id)
        operation._session_id = SessionId(model.session_id)  # Necesario para save
        operation._cage_id = CageId(model.cage_id)
        operation._target_slot = model.target_slot
        operation._target_amount = Weight.from_kg(model.target_amount_kg)
        operation._dispensed = Weight.from_kg(model.dispensed_kg)
        operation._status = OperationStatus(model.status)
        operation._started_at = model.started_at
        operation._ended_at = model.ended_at
        operation._applied_config = model.applied_config

        # Reconstruir eventos (todos)
        operation._events = [
            OperationEvent(
                timestamp=ev.timestamp,
                type=OperationEventType(ev.type),
                description=ev.description,
                details=ev.details
            )
            for ev in model.events
        ]
        operation._new_events = []  # No hay eventos nuevos al cargar

        return operation
```

**Nota**: `FeedingOperation` necesita guardar `_session_id` internamente para poder persistirse.

---

### Fase 5: Dependency Injection

#### 5.1. Actualizar dependencies.py

**Archivo**: `src/api/dependencies.py`

Agregar al final del archivo:

```python
# ============================================================================
# Dependencias de Repositorios - AGREGAR
# ============================================================================
from infrastructure.persistence.repositories.feeding_operation_repository import FeedingOperationRepository

async def get_feeding_operation_repo(
    session: AsyncSession = Depends(get_session)
) -> FeedingOperationRepository:
    """Crea instancia del repositorio de operaciones de alimentación."""
    return FeedingOperationRepository(session)

# ============================================================================
# Dependencias de Casos de Uso - Feeding - ACTUALIZAR
# ============================================================================

async def get_start_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> StartFeedingSessionUseCase:
    """Crea instancia del caso de uso de inicio de alimentación."""
    return StartFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        line_repository=line_repo,
        cage_repository=cage_repo,
        machine_service=machine_service
    )

async def get_stop_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> StopFeedingSessionUseCase:
    """Crea instancia del caso de uso de detención de alimentación."""
    return StopFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        machine_service=machine_service
    )

async def get_pause_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> PauseFeedingSessionUseCase:
    """Crea instancia del caso de uso de pausa de alimentación."""
    return PauseFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        machine_service=machine_service
    )

async def get_resume_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> ResumeFeedingSessionUseCase:
    """Crea instancia del caso de uso de reanudación de alimentación."""
    return ResumeFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        machine_service=machine_service
    )

async def get_update_feeding_params_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> UpdateFeedingParametersUseCase:
    """Crea instancia del caso de uso de actualización de parámetros de alimentación."""
    return UpdateFeedingParametersUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        machine_service=machine_service
    )

# NUEVO - Dashboard
async def get_all_lines_dashboard_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo)
) -> GetAllLinesDashboardUseCase:
    """Crea instancia del caso de uso de dashboard de líneas."""
    return GetAllLinesDashboardUseCase(
        line_repository=line_repo,
        session_repository=session_repo,
        operation_repository=operation_repo
    )

# ============================================================================
# Type Aliases para Endpoints - Feeding - AGREGAR
# ============================================================================
GetAllLinesDashboardUseCaseDep = Annotated[
    GetAllLinesDashboardUseCase,
    Depends(get_all_lines_dashboard_use_case)
]
```

---

### Fase 6: Actualizar Casos de Uso

#### 6.1. StartFeedingUseCase

```python
class StartFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.line_repository = line_repository
        self.cage_repository = cage_repository
        self.machine_service = machine_service

    async def execute(self, request: StartFeedingRequest) -> UUID:
        # 1. Validar Línea
        line = await self.line_repository.find_by_id(LineId(request.line_id))
        if not line:
            raise ValueError(f"Line {request.line_id} not found")

        # 2. Validar Jaula y obtener Slot Físico
        cage = await self.cage_repository.find_by_id(CageId(request.cage_id))
        if not cage:
            raise ValueError(f"Cage {request.cage_id} not found")

        if cage.line_id and cage.line_id.value != request.line_id:
            raise ValueError(f"Cage does not belong to Line")

        physical_slot = await self.line_repository.get_slot_number(
            LineId(request.line_id),
            CageId(request.cage_id)
        )

        if physical_slot is None:
            raise ValueError("Cage does not have a physical slot assigned")

        # 3. Gestión de Sesión (Day Boundary)
        session = await self.session_repository.find_active_by_line_id(LineId(request.line_id))

        today = datetime.utcnow().date()

        if session:
            # Si la sesión es de ayer, cerrarla y crear nueva
            if session.date.date() < today:
                session.close_session()
                await self.session_repository.save(session)
                session = None

        # Crear nueva sesión si no existe (siempre en ACTIVE)
        if not session:
            session = FeedingSession(line_id=LineId(request.line_id))
            await self.session_repository.save(session)  # Guardar sesión nueva

        # 4. Cargar operación actual si existe
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if current_op:
            session._current_operation = current_op

        # 5. Estrategia
        strategy = ManualFeedingStrategy(
            target_slot=physical_slot,
            blower_speed=request.blower_speed_percentage,
            doser_speed=request.dosing_rate_kg_min,
            target_amount_kg=request.target_amount_kg
        )

        # 6. Iniciar Operación
        operation_id = await session.start_operation(
            cage_id=CageId(request.cage_id),
            target_slot=physical_slot,
            strategy=strategy,
            machine=self.machine_service
        )

        # 7. Persistencia (sesión + operación)
        await self.session_repository.save(session)
        await self.operation_repository.save(session.current_operation)

        return operation_id.value
```

#### 6.2. StopFeedingUseCase

```python
class StopFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))

        if not session:
            return  # Idempotente

        # Cargar operación actual
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if current_op:
            session._current_operation = current_op

        await session.stop_current_operation(self.machine_service)

        # Guardar sesión y operación
        await self.session_repository.save(session)
        if session.current_operation:  # Puede ser None después de stop
            await self.operation_repository.save(current_op)
```

#### 6.3. PauseFeedingUseCase

```python
class PauseFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))
        if not session:
            return

        # Cargar operación actual
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if current_op:
            session._current_operation = current_op

        await session.pause_current_operation(self.machine_service)

        # Guardar operación (sesión no cambia)
        await self.operation_repository.save(session.current_operation)
```

#### 6.4. ResumeFeedingUseCase

```python
class ResumeFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))
        if not session:
            raise ValueError("No active session to resume")

        # Cargar operación actual
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if current_op:
            session._current_operation = current_op

        await session.resume_current_operation(self.machine_service)

        # Guardar operación (sesión no cambia)
        await self.operation_repository.save(session.current_operation)
```

#### 5.5. UpdateFeedingParametersUseCase

```python
class UpdateFeedingParametersUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.machine_service = machine_service

    async def execute(self, request: UpdateParamsRequest) -> None:
        session = await self.session_repository.find_active_by_line_id(LineId(request.line_id))
        if not session:
            raise ValueError("No active session found")

        # Cargar operación actual
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if not current_op:
            raise ValueError("No active operation to update")

        session._current_operation = current_op

        if session.current_operation.status != OperationStatus.RUNNING:
            raise ValueError("Operation must be RUNNING to update parameters")

        # Reconstruir estrategia desde la operación actual
        current_config = session.current_operation.applied_config

        current_slot = current_config.get("slot_numbers", [None])[0]
        current_blower = current_config.get("blower_speed_percentage", 0.0)
        current_doser = current_config.get("doser_speed_percentage", 0.0)
        current_target = current_config.get("target_amount_kg", 0.0)

        # Aplicar cambios
        new_blower = request.blower_speed if request.blower_speed is not None else current_blower
        new_doser = request.dosing_rate if request.dosing_rate is not None else current_doser

        new_strategy = ManualFeedingStrategy(
            target_slot=current_slot,
            blower_speed=new_blower,
            doser_speed=new_doser,
            target_amount_kg=current_target
        )

        await session.update_current_operation_params(new_strategy, self.machine_service)

        # Guardar operación (sesión no cambia)
        await self.operation_repository.save(session.current_operation)
```

#### 5.6. GetAllLinesDashboardUseCase (NUEVO)

**Archivo**: `src/application/use_cases/feeding/get_all_lines_dashboard_use_case.py`

```python
from typing import List, Dict, Any

from domain.repositories import IFeedingSessionRepository, IFeedingLineRepository, IFeedingOperationRepository
from application.dtos.feeding_dtos import AllLinesDashboardResponse

class GetAllLinesDashboardUseCase:
    """
    Obtiene el dashboard de todas las líneas de alimentación.
    Muestra cada línea con su operación activa (si existe).
    """

    def __init__(
        self,
        line_repository: IFeedingLineRepository,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository
    ):
        self.line_repository = line_repository
        self.session_repository = session_repository
        self.operation_repository = operation_repository

    async def execute(self) -> AllLinesDashboardResponse:
        # 1. Obtener todas las líneas
        lines = await self.line_repository.find_all()

        # 2. Para cada línea, obtener su sesión activa y operación actual
        lines_data = []

        for line in lines:
            session = await self.session_repository.find_active_by_line_id(line.id)

            line_data = {
                "line_id": str(line.id.value),
                "line_name": line.name,
                "current_operation": None
            }

            if session:
                # Cargar operación actual
                current_op = await self.operation_repository.find_current_by_session(session.id)

                if current_op:
                    line_data["current_operation"] = {
                        "operation_id": str(current_op.id.value),
                        "cage_id": str(current_op.cage_id.value),
                        "target_slot": current_op.target_slot,
                        "target_kg": current_op.target_amount.as_kg,
                        "dispensed_kg": current_op.dispensed.as_kg,
                        "status": current_op.status.value,
                        "started_at": current_op.started_at.isoformat()
                    }

            lines_data.append(line_data)

        return AllLinesDashboardResponse(lines=lines_data)
```

**DTO**: `src/application/dtos/feeding_dtos.py`

```python
@dataclass
class AllLinesDashboardResponse:
    lines: List[Dict[str, Any]]
```

#### 5.7. SyncMachineStateUseCase (PENDIENTE)

**Descripción**: Proceso en segundo plano que sincroniza el estado del PLC con el dominio cada 1 segundo. Actualiza contadores de alimento y detecta fin de ciclo.

**Nota**: Se implementará en fase posterior una vez resuelto el arranque del proceso con start, stop, pause y resume.

**Sketch de implementación**:

```python
class SyncMachineStateUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        # 1. Obtener sesión activa
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))
        if not session:
            return

        # 2. Cargar operación actual
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if not current_op:
            return

        session._current_operation = current_op

        # 3. Leer estado del PLC
        plc_status = await self.machine_service.get_status(LineId(line_id))

        # 4. Sincronizar
        session.update_from_plc(plc_status)

        # 5. Guardar cambios (solo lo que cambió)
        await self.session_repository.save(session)  # Acumuladores
        await self.operation_repository.save(session.current_operation)  # Dispensed
```

---

### Fase 6: Actualizar API Endpoints

#### 6.1. Endpoints Requeridos

**Archivo**: `src/api/routes/feeding_routes.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID

router = APIRouter(prefix="/feeding", tags=["Feeding"])

# POST /feeding/start
@router.post("/start")
async def start_feeding(
    request: StartFeedingRequest,
    use_case: StartFeedingSessionUseCase = Depends()
):
    """Inicia una nueva operación de alimentación."""
    try:
        operation_id = await use_case.execute(request)
        return {
            "operation_id": str(operation_id),
            "message": "Feeding operation started successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# POST /feeding/stop
@router.post("/stop")
async def stop_feeding(
    line_id: UUID,
    use_case: StopFeedingSessionUseCase = Depends()
):
    """Detiene la operación actual de una línea."""
    await use_case.execute(line_id)
    return {"message": "Feeding operation stopped"}

# POST /feeding/pause
@router.post("/pause")
async def pause_feeding(
    line_id: UUID,
    use_case: PauseFeedingSessionUseCase = Depends()
):
    """Pausa temporalmente la operación actual."""
    try:
        await use_case.execute(line_id)
        return {"message": "Feeding operation paused"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# POST /feeding/resume
@router.post("/resume")
async def resume_feeding(
    line_id: UUID,
    use_case: ResumeFeedingSessionUseCase = Depends()
):
    """Reanuda la operación pausada."""
    try:
        await use_case.execute(line_id)
        return {"message": "Feeding operation resumed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# PUT /feeding/update-params
@router.put("/update-params")
async def update_feeding_params(
    request: UpdateParamsRequest,
    use_case: UpdateFeedingParametersUseCase = Depends()
):
    """Actualiza parámetros de la operación activa en caliente."""
    try:
        await use_case.execute(request)
        return {"message": "Parameters updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# GET /feeding/dashboard
@router.get("/dashboard")
async def get_all_lines_dashboard(
    use_case: GetAllLinesDashboardUseCase = Depends()
):
    """Obtiene el dashboard de todas las líneas con sus operaciones activas."""
    dashboard = await use_case.execute()
    return dashboard

# GET /feeding/session/{line_id}/operations (FUTURO)
# Este endpoint se implementará en fase posterior para obtener
# el historial de operaciones del día
```

---

### Fase 7: Testing

#### 7.1. Tests Unitarios del Aggregate

**Archivo**: `tests/domain/test_feeding_session_with_operations.py`

```python
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from domain.aggregates.feeding_session import FeedingSession
from domain.enums import SessionStatus, OperationStatus
from domain.value_objects import LineId, CageId, Weight

@pytest.fixture
def mock_machine():
    machine = AsyncMock()
    return machine

@pytest.fixture
def mock_strategy():
    strategy = Mock()
    strategy.get_plc_configuration.return_value = MachineConfiguration(
        mode=FeedingMode.MANUAL,
        slot_numbers=[1],
        blower_speed_percentage=50.0,
        doser_speed_percentage=30.0,
        target_amount_kg=100.0
    )
    return strategy

def test_session_starts_with_active_status():
    session = FeedingSession(line_id=LineId.generate())
    assert session.status == SessionStatus.ACTIVE

@pytest.mark.asyncio
async def test_start_operation_creates_operation(mock_machine, mock_strategy):
    session = FeedingSession(line_id=LineId.generate())
    cage_id = CageId.generate()

    operation_id = await session.start_operation(
        cage_id=cage_id,
        target_slot=1,
        strategy=mock_strategy,
        machine=mock_machine
    )

    assert session.current_operation is not None
    assert session.current_operation.cage_id == cage_id
    assert session.current_operation.status == OperationStatus.RUNNING
    assert len(session.operations) == 1

@pytest.mark.asyncio
async def test_stop_operation_closes_operation(mock_machine, mock_strategy):
    session = FeedingSession(line_id=LineId.generate())

    await session.start_operation(
        cage_id=CageId.generate(),
        target_slot=1,
        strategy=mock_strategy,
        machine=mock_machine
    )

    await session.stop_current_operation(mock_machine)

    assert session.current_operation is None
    assert session.operations[0].status == OperationStatus.STOPPED
    assert session.status == SessionStatus.ACTIVE  # Sesión sigue activa

@pytest.mark.asyncio
async def test_multiple_operations_in_same_session(mock_machine, mock_strategy):
    session = FeedingSession(line_id=LineId.generate())

    # Operación 1
    await session.start_operation(CageId.generate(), 1, mock_strategy, mock_machine)
    await session.stop_current_operation(mock_machine)

    # Operación 2
    await session.start_operation(CageId.generate(), 2, mock_strategy, mock_machine)
    await session.stop_current_operation(mock_machine)

    assert len(session.operations) == 2
    assert session.operations[0].status == OperationStatus.STOPPED
    assert session.operations[1].status == OperationStatus.STOPPED
    assert session.status == SessionStatus.ACTIVE

@pytest.mark.asyncio
async def test_pause_and_resume_operation(mock_machine, mock_strategy):
    session = FeedingSession(line_id=LineId.generate())

    await session.start_operation(CageId.generate(), 1, mock_strategy, mock_machine)

    await session.pause_current_operation(mock_machine)
    assert session.current_operation.status == OperationStatus.PAUSED

    await session.resume_current_operation(mock_machine)
    assert session.current_operation.status == OperationStatus.RUNNING

@pytest.mark.asyncio
async def test_cannot_start_operation_while_one_is_active(mock_machine, mock_strategy):
    session = FeedingSession(line_id=LineId.generate())

    await session.start_operation(CageId.generate(), 1, mock_strategy, mock_machine)

    with pytest.raises(ValueError, match="Ya hay una operación activa"):
        await session.start_operation(CageId.generate(), 2, mock_strategy, mock_machine)
```

---

## 🔧 Dependency Injection (FastAPI)

### Actualizar dependencies.py

**Archivo**: `src/api/dependencies.py`

#### A. Agregar Repositorio de Operaciones

```python
# ============================================================================
# Dependencias de Repositorios - AGREGAR
# ============================================================================
from infrastructure.persistence.repositories.feeding_operation_repository import FeedingOperationRepository

async def get_feeding_operation_repo(
    session: AsyncSession = Depends(get_session)
) -> FeedingOperationRepository:
    """Crea instancia del repositorio de operaciones de alimentación."""
    return FeedingOperationRepository(session)
```

#### B. Actualizar Casos de Uso de Feeding

Todos los casos de uso deben inyectar `operation_repo`:

```python
# ============================================================================
# Dependencias de Casos de Uso - Feeding - ACTUALIZAR
# ============================================================================

async def get_start_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> StartFeedingSessionUseCase:
    """Crea instancia del caso de uso de inicio de alimentación."""
    return StartFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        line_repository=line_repo,
        cage_repository=cage_repo,
        machine_service=machine_service
    )

async def get_stop_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> StopFeedingSessionUseCase:
    """Crea instancia del caso de uso de detención de alimentación."""
    return StopFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        machine_service=machine_service
    )

async def get_pause_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> PauseFeedingSessionUseCase:
    """Crea instancia del caso de uso de pausa de alimentación."""
    return PauseFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        machine_service=machine_service
    )

async def get_resume_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> ResumeFeedingSessionUseCase:
    """Crea instancia del caso de uso de reanudación de alimentación."""
    return ResumeFeedingSessionUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        machine_service=machine_service
    )

async def get_update_feeding_params_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo),  # NUEVO
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> UpdateFeedingParametersUseCase:
    """Crea instancia del caso de uso de actualización de parámetros de alimentación."""
    return UpdateFeedingParametersUseCase(
        session_repository=session_repo,
        operation_repository=operation_repo,  # NUEVO
        machine_service=machine_service
    )
```

#### C. Agregar Dashboard Use Case (NUEVO)

```python
# NUEVO - Dashboard
async def get_all_lines_dashboard_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    operation_repo: FeedingOperationRepository = Depends(get_feeding_operation_repo)
) -> GetAllLinesDashboardUseCase:
    """Crea instancia del caso de uso de dashboard de líneas."""
    return GetAllLinesDashboardUseCase(
        line_repository=line_repo,
        session_repository=session_repo,
        operation_repository=operation_repo
    )
```

#### D. Agregar Type Aliases para Endpoints

```python
# ============================================================================
# Type Aliases para Endpoints - Feeding - AGREGAR
# ============================================================================
GetAllLinesDashboardUseCaseDep = Annotated[
    GetAllLinesDashboardUseCase,
    Depends(get_all_lines_dashboard_use_case)
]
```

---

## ✅ Checklist de Implementación

### Fase 1: Preparación del Dominio

- [ ] Crear `OperationId` VO en `src/domain/value_objects.py`
- [ ] Crear `OperationStatus` enum en `src/domain/enums.py`
- [ ] Crear `OperationEventType` enum en `src/domain/enums.py`
- [ ] Modificar `SessionStatus` a `ACTIVE`/`CLOSED` (eliminar estados viejos: CREATED, RUNNING, PAUSED, COMPLETED, FAILED)
- [ ] Crear `IFeedingOperationRepository` en `src/domain/repositories.py`
- [ ] Verificar `IFeedingSessionRepository` en `src/domain/repositories.py` (debe tener interfaz completa)
- [ ] Crear carpeta `src/domain/entities/`
- [ ] Crear `src/domain/entities/__init__.py`
- [ ] Crear `src/domain/entities/feeding_operation.py`

### Fase 2: Base de Datos

- [ ] Crear `FeedingOperationModel`
- [ ] Crear `OperationEventModel`
- [ ] Actualizar `FeedingSessionModel` (agregar relationship, eliminar `applied_strategy_config`)
- [ ] Generar migración: `alembic revision --autogenerate`
- [ ] Aplicar migración: `alembic upgrade head`

### Fase 3: Dominio

- [ ] Backup de `feeding_session.py`
- [ ] Refactorizar `FeedingSession` completo
- [ ] Agregar solo `_current_operation` (NO lista `_operations`)
- [ ] Implementar `start_operation()` (crea operación con `session_id`)
- [ ] Implementar `stop_current_operation()`
- [ ] Implementar `pause_current_operation()`
- [ ] Implementar `resume_current_operation()`
- [ ] Implementar `update_current_operation_params()`
- [ ] Simplificar `update_from_plc()` (pendiente de completar)
- [ ] Agregar `_session_id` a `FeedingOperation.__init__()`
- [ ] Agregar `pop_new_events()` a `FeedingOperation`

### Fase 4: Repositorios

- [ ] Actualizar `FeedingSessionRepository.save()` (solo sesión)
- [ ] Actualizar `FeedingSessionRepository.find_by_id()`
- [ ] Actualizar `FeedingSessionRepository.find_active_by_line_id()`
- [ ] Actualizar `FeedingSessionRepository._to_domain()` (sin operaciones)
- [ ] Crear `FeedingOperationRepository` (nuevo archivo) con interfaz `IFeedingOperationRepository`
- [ ] Implementar `FeedingOperationRepository.save()`
- [ ] Implementar `FeedingOperationRepository.find_by_id()`
- [ ] Implementar `FeedingOperationRepository.find_current_by_session()`
- [ ] Implementar `FeedingOperationRepository.find_all_by_session()`
- [ ] Implementar `FeedingOperationRepository._to_domain()`

### Fase 5: Dependency Injection y Casos de Uso

**Dependency Injection:**

- [ ] Actualizar `dependencies.py` con `get_feeding_operation_repo()`
- [ ] Actualizar todos los `get_*_feeding_use_case()` para inyectar `operation_repo`
- [ ] Crear `get_all_lines_dashboard_use_case()`
- [ ] Agregar `GetAllLinesDashboardUseCaseDep` type alias

**Casos de Uso:**

- [ ] Actualizar `StartFeedingUseCase` (inyectar `operation_repository`, cargar operación actual, guardar ambos)
- [ ] Actualizar `StopFeedingUseCase` (inyectar `operation_repository`, cargar operación, guardar ambos)
- [ ] Actualizar `PauseFeedingSessionUseCase` (inyectar `operation_repository`, cargar operación, guardar solo operación)
- [ ] Actualizar `ResumeFeedingSessionUseCase` (inyectar `operation_repository`, cargar operación, guardar solo operación)
- [ ] Actualizar `UpdateFeedingParametersUseCase` (inyectar `operation_repository`, cargar operación, guardar solo operación)
- [ ] Crear `GetAllLinesDashboardUseCase` (inyectar `operation_repository`, cargar operación actual por sesión)

### Fase 6: API

- [ ] Actualizar `POST /feeding/start` (retornar `operation_id`)
- [ ] Actualizar `POST /feeding/stop`
- [ ] Actualizar `POST /feeding/pause`
- [ ] Actualizar `POST /feeding/resume`
- [ ] Actualizar `PUT /feeding/update-params`
- [ ] Crear `GET /feeding/dashboard` (todas las líneas)

### Fase 7: Validación Manual

- [ ] Probar flujo completo en desarrollo
- [ ] Verificar que START crea operación correctamente
- [ ] Verificar que STOP cierra operación pero sesión sigue ACTIVE
- [ ] Verificar que se puede hacer START nuevamente después de STOP
- [ ] Verificar PAUSE/RESUME
- [ ] Verificar dashboard muestra operaciones activas
- [ ] Revisar logs de eventos

**Nota**: Tests unitarios se implementarán en fase posterior si es necesario.

### Fase 8: Deployment

- [ ] Revisar logs en desarrollo
- [ ] Aplicar migración en staging
- [ ] Probar flujo completo
- [ ] Aplicar en producción
- [ ] Monitorear

---

## 🚨 Riesgos y Mitigaciones

### Riesgo 1: Sesiones Activas en Producción

**Mitigación**: Aplicar migración en horario de baja actividad. Notificar a operadores.

### Riesgo 2: Performance del Repositorio

**Mitigación**: Agregar índices en `feeding_operations.session_id`. Implementar caché.

### Riesgo 3: Sincronización con PLC

**Mitigación**: Implementar `SyncMachineStateUseCase` en fase posterior con retry logic y health checks.

---

## 🎯 Resultado Esperado

✅ **Operadores pueden**:

- Alimentar múltiples jaulas en el mismo día
- Volver a alimentar la misma jaula varias veces
- Ver dashboard con todas las líneas y operaciones activas

✅ **Sistema mantiene**:

- Trazabilidad completa por operación
- Acumuladores diarios correctos
- Sesión siempre en estado `ACTIVE` durante el día

✅ **Arquitectura limpia**:

- Separación clara entre Sesión (día) y Operación (visita)
- Value Objects correctamente aplicados
- Estados semánticamente correctos

---

**Fin del Documento**
