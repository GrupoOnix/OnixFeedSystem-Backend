# Plan de Implementación: Componente Cooler

> **¡Hola, Claude Code del futuro!** 👋  
> Este documento contiene el plan completo para integrar el componente Cooler al sistema de alimentación.  
> El plan fue diseñado considerando la arquitectura DDD y Clean Architecture existente.  
> Sigue las fases en orden y todo saldrá bien. ¡Buena suerte! 🚀

---

## 1. Análisis del Contexto Actual

### Estructura de Componentes Existentes

**Componentes actuales en FeedingLine:**
- **Blower**: Soplador con control de potencia (power_percentage, current_power_percentage) y tiempos de soplado
- **Doser**: Dosificador con tasa de dosificación y rango operativo
- **Selector**: Selector con capacidad de slots y posición actual
- **Sensor**: Sensores de temperatura, presión y flujo

**Ubicación del Cooler en el flujo físico:**
```
Blower → [Cooler] → Doser → Selector → Jaula
```

### Propósito del Cooler

El Cooler enfría el aire entre el Blower y el Doser para proteger el alimento y evitar que el calor generado por el flujo de aire dañe la calidad del pellet.

**Características clave:**
- **Opcional**: No todas las líneas lo tienen instalado (existen otros métodos de enfriado)
- **Estado**: ON/OFF (encendido/apagado)
- **Potencia**: Porcentaje de enfriamiento (0-100%)
- **Simple**: De momento solo tiene campos básicos, sin integración automática con sensores

---

## 2. Diseño del Componente Cooler

### 2.1 Campos y Propiedades

**Campos básicos (implementar ahora):**
- `id`: UUID (CoolerId)
- `name`: string (CoolerName)
- `is_on`: boolean (estado on/off)
- `cooling_power_percentage`: float (0-100) - Potencia de enfriamiento
- `created_at`: datetime

**Campos opcionales futuros (NO implementar ahora):**
- `target_temperature`: Temperatura objetivo (requiere integración con sensores)
- `current_temperature`: Temperatura actual (requiere lectura en tiempo real)
- `min_power`, `max_power`: Rango operativo si se necesita validación

### 2.2 Decisiones de Diseño

#### ¿Por qué Optional?

El Cooler es `Optional[ICooler]` en FeedingLine porque:
- No todas las líneas lo tienen instalado
- Existen otros métodos de enfriado de aire (refrigeración pasiva, etc.)
- La validación FA1 (InsufficientComponentsException) NO debe requerir cooler obligatoriamente

#### Relación con Blower

El Cooler es independiente del Blower pero trabaja en conjunto:
- Blower genera flujo de aire a presión
- Cooler enfría ese flujo antes de llegar al Doser
- En PLC real, pueden tener control coordinado (e.g., aumentar enfriamiento si blower aumenta potencia)

#### Integración con Sensores

**No se implementa ahora**, pero el diseño lo permite en el futuro:
- Sensores de temperatura pueden leer temperatura pre-cooler y post-cooler
- Lógica de control automático: ajustar `cooling_power_percentage` según temperatura objetivo
- Esto requeriría agregar `target_temperature` y lógica en estrategias de alimentación

---

## 3. Capa de Dominio

### 3.1 Value Objects a Crear

#### Archivo: `src/domain/value_objects/feeding_specs.py`

**Agregar al archivo existente:**

```python
class CoolerPowerPercentage:
    """
    Value Object: Potencia de enfriamiento del cooler (0-100%).
    """
    def __init__(self, value: float):
        if not (0 <= value <= 100):
            raise ValueError(
                f"La potencia de enfriamiento debe estar entre 0 y 100. Recibido: {value}"
            )
        self._value = value
    
    @property
    def value(self) -> float:
        return self._value
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CoolerPowerPercentage):
            return False
        return self._value == other._value
    
    def __str__(self) -> str:
        return f"{self._value}%"
    
    def __repr__(self) -> str:
        return f"CoolerPowerPercentage({self._value})"
```

#### Archivo: `src/domain/value_objects/identifiers.py`

**Agregar:**

```python
class CoolerId(BaseIdentifier):
    """Identificador único de un Cooler."""
    pass
```

#### Archivo: `src/domain/value_objects/names.py`

**Agregar:**

```python
class CoolerName(BaseName):
    """Nombre de un Cooler (max 100 caracteres, no vacío)."""
    pass
```

#### Archivo: `src/domain/value_objects/__init__.py`

**Actualizar exports:**

```python
from .identifiers import (
    # ... existentes
    CoolerId,  # NUEVO
)

from .names import (
    # ... existentes
    CoolerName,  # NUEVO
)

from .feeding_specs import (
    # ... existentes
    CoolerPowerPercentage,  # NUEVO
)

__all__ = [
    # ... existentes
    "CoolerId",
    "CoolerName",
    "CoolerPowerPercentage",
]
```

### 3.2 Interfaz ICooler

#### Archivo: `src/domain/interfaces.py`

**Agregar al final del archivo:**

```python
class ICooler(ABC):
    """
    Interfaz de dominio para un Cooler (enfriador de aire).
    
    El cooler se ubica entre el Blower y el Doser, enfriando el aire
    para evitar que el calor dañe la calidad del alimento.
    """
    
    @property
    @abstractmethod
    def id(self) -> CoolerId: ...
    
    @property
    @abstractmethod
    def name(self) -> CoolerName: ...
    
    @name.setter
    @abstractmethod
    def name(self, name: CoolerName) -> None: ...
    
    @property
    @abstractmethod
    def is_on(self) -> bool: ...
    
    @is_on.setter
    @abstractmethod
    def is_on(self, value: bool) -> None: ...
    
    @property
    @abstractmethod
    def cooling_power_percentage(self) -> CoolerPowerPercentage: ...
    
    @cooling_power_percentage.setter
    @abstractmethod
    def cooling_power_percentage(self, power: CoolerPowerPercentage) -> None: ...
    
    @property
    @abstractmethod
    def created_at(self) -> datetime: ...
    
    # -----------------
    # Métodos de Comportamiento (Reglas de Negocio)
    # -----------------
    
    @abstractmethod
    def validate_power_is_safe(self, power: CoolerPowerPercentage) -> bool:
        """
        Valida que la potencia de enfriamiento sea segura.
        
        En el futuro puede incluir lógicas más complejas (e.g., validar
        contra temperatura ambiente, estado del blower, etc.).
        """
        ...
```

**No olvides agregar imports:**

```python
from .value_objects import (
    # ... existentes
    CoolerId,
    CoolerName,
    CoolerPowerPercentage,
)
```

### 3.3 Entidad Cooler

#### Archivo nuevo: `src/domain/aggregates/feeding_line/cooler.py`

```python
"""
Entidad de dominio: Cooler (Enfriador de Aire)

El cooler es un componente opcional de la línea de alimentación que enfría
el aire entre el Blower y el Doser para proteger la calidad del alimento.
"""

from datetime import datetime

from domain.interfaces import ICooler
from domain.value_objects import (
    CoolerId,
    CoolerName,
    CoolerPowerPercentage,
)


class Cooler(ICooler):
    """
    Enfriador de aire para línea de alimentación.
    
    El cooler reduce la temperatura del aire generado por el blower
    antes de que llegue al dosificador, protegiendo así el alimento.
    
    Atributos:
        - id: Identificador único del cooler
        - name: Nombre descriptivo
        - is_on: Estado encendido/apagado
        - cooling_power_percentage: Potencia de enfriamiento (0-100%)
        - created_at: Timestamp de creación
    """
    
    def __init__(
        self,
        name: CoolerName,
        cooling_power_percentage: CoolerPowerPercentage,
        is_on: bool = False,
    ):
        """
        Crea una nueva instancia de Cooler.
        
        Args:
            name: Nombre del cooler
            cooling_power_percentage: Potencia de enfriamiento inicial
            is_on: Estado inicial (por defecto apagado)
        """
        self._id = CoolerId.generate()
        self._name = name
        self._is_on = is_on
        self._cooling_power_percentage = cooling_power_percentage
        self._created_at = datetime.utcnow()
    
    # -----------------
    # Properties
    # -----------------
    
    @property
    def id(self) -> CoolerId:
        return self._id
    
    @property
    def name(self) -> CoolerName:
        return self._name
    
    @name.setter
    def name(self, name: CoolerName) -> None:
        self._name = name
    
    @property
    def is_on(self) -> bool:
        return self._is_on
    
    @is_on.setter
    def is_on(self, value: bool) -> None:
        self._is_on = value
    
    @property
    def cooling_power_percentage(self) -> CoolerPowerPercentage:
        return self._cooling_power_percentage
    
    @cooling_power_percentage.setter
    def cooling_power_percentage(self, power: CoolerPowerPercentage) -> None:
        """
        Actualiza la potencia de enfriamiento.
        
        Valida que la potencia sea segura antes de asignar.
        
        Raises:
            ValueError: Si la potencia no es válida
        """
        if not self.validate_power_is_safe(power):
            raise ValueError(
                f"La potencia {power} no es segura para este cooler"
            )
        self._cooling_power_percentage = power
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    # -----------------
    # Métodos de Comportamiento
    # -----------------
    
    def validate_power_is_safe(self, power: CoolerPowerPercentage) -> bool:
        """
        Valida que la potencia de enfriamiento sea segura.
        
        Por ahora, solo valida que sea una instancia correcta de CoolerPowerPercentage.
        En el futuro puede incluir lógicas más complejas.
        
        Args:
            power: Potencia a validar
            
        Returns:
            True si la potencia es segura, False en caso contrario
        """
        return isinstance(power, CoolerPowerPercentage)
    
    def turn_on(self) -> None:
        """Enciende el cooler."""
        self._is_on = True
    
    def turn_off(self) -> None:
        """Apaga el cooler."""
        self._is_on = False
```

### 3.4 Actualizar FeedingLine

#### Archivo: `src/domain/aggregates/feeding_line/feeding_line.py`

**Cambios a realizar:**

1. **Agregar import:**

```python
from ...interfaces import IBlower, IDoser, ISelector, ISensor, ICooler  # Agregar ICooler
```

2. **Agregar propiedad privada en `__init__`:**

```python
def __init__(self, name: LineName):
    self._id = LineId.generate()
    self._name = name
    self._blower: Optional[IBlower] = None
    self._dosers: Tuple[IDoser, ...] = ()
    self._selector: Optional[ISelector] = None
    self._sensors: Tuple[ISensor, ...] = ()
    self._cooler: Optional[ICooler] = None  # NUEVO
    self._created_at = datetime.utcnow()
```

3. **Actualizar método `create()`:**

```python
@classmethod
def create(cls,
           name: LineName,
           blower: IBlower,
           dosers: List[IDoser],
           selector: ISelector,
           sensors: List[ISensor] = [],
           cooler: Optional[ICooler] = None  # NUEVO
           ) -> 'FeedingLine':
    
    # Regla FA1: Validar composición mínima
    if not blower:
        raise InsufficientComponentsException("Se requiere un Blower.")
    if not dosers or len(dosers) == 0:
        raise InsufficientComponentsException("Se requiere al menos un Doser.")
    if not selector:
        raise InsufficientComponentsException("Se requiere un Selector.")
    # NOTA: Cooler es OPCIONAL, no se valida aquí

    # Regla FA7: Validar sensores únicos por tipo
    cls._validate_unique_sensor_types(sensors or [])

    # Creamos la instancia
    line = cls(name)
    
    # Asignamos los componentes
    line._blower = blower
    line._dosers = tuple(dosers)
    line._selector = selector
    line._sensors = tuple(sensors or [])
    line._cooler = cooler  # NUEVO
    
    return line
```

4. **Agregar property para cooler:**

```python
@property
def cooler(self) -> Optional[ICooler]:
    """
    Cooler opcional de la línea.
    
    El cooler enfría el aire entre el blower y el doser.
    No todas las líneas lo tienen instalado.
    """
    return self._cooler
```

5. **Actualizar método `update_components()`:**

```python
def update_components(self, 
                     blower: IBlower, 
                     dosers: List[IDoser], 
                     selector: ISelector, 
                     sensors: Optional[List[ISensor]] = None,
                     cooler: Optional[ICooler] = None) -> None:  # NUEVO parámetro

    # Reutilizar validación FA1: Composición mínima
    if not blower:
        raise InsufficientComponentsException("Se requiere un Blower.")
    if not dosers or len(dosers) == 0:
        raise InsufficientComponentsException("Se requiere al menos un Doser.")
    if not selector:
        raise InsufficientComponentsException("Se requiere un Selector.")
    
    # Reutilizar validación FA7: Sensores únicos por tipo
    self._validate_unique_sensor_types(sensors or [])
    
    # Asignar los nuevos componentes
    self._blower = blower
    self._dosers = tuple(dosers)
    self._selector = selector
    self._sensors = tuple(sensors or [])
    self._cooler = cooler  # NUEVO
```

---

## 4. Capa de Infraestructura

### 4.1 Modelo de Persistencia

#### Archivo nuevo: `src/infrastructure/persistence/models/cooler_model.py`

```python
"""Modelo de persistencia para Cooler."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from domain.value_objects import (
    CoolerId,
    CoolerName,
    CoolerPowerPercentage,
)

if TYPE_CHECKING:
    from domain.aggregates.feeding_line.cooler import Cooler
    from domain.interfaces import ICooler


class CoolerModel(SQLModel, table=True):
    __tablename__ = "coolers"

    id: UUID = Field(primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    is_on: bool = Field(default=False)
    cooling_power_percentage: float

    feeding_line: "FeedingLineModel" = Relationship(back_populates="cooler")

    @staticmethod
    def from_domain(cooler: "ICooler", line_id: UUID) -> "CoolerModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return CoolerModel(
            id=cooler.id.value,
            line_id=line_id,
            name=str(cooler.name),
            is_on=cooler.is_on,
            cooling_power_percentage=cooler.cooling_power_percentage.value,
        )

    def to_domain(self) -> "Cooler":
        """Convierte modelo de persistencia a entidad de dominio."""
        # Import local para evitar circular imports
        from domain.aggregates.feeding_line.cooler import Cooler

        cooler = Cooler(
            name=CoolerName(self.name),
            cooling_power_percentage=CoolerPowerPercentage(
                self.cooling_power_percentage
            ),
            is_on=self.is_on,
        )
        cooler._id = CoolerId(self.id)
        return cooler
```

### 4.2 Actualizar FeedingLineModel

#### Archivo: `src/infrastructure/persistence/models/feeding_line_model.py`

**Cambios:**

1. **Agregar relación en la clase:**

```python
class FeedingLineModel(SQLModel, table=True):
    __tablename__ = "feeding_lines"

    # ... campos existentes
    
    cooler: Optional["CoolerModel"] = Relationship(  # NUEVO
        back_populates="feeding_line",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
```

2. **Actualizar método `from_domain()`:**

```python
@staticmethod
def from_domain(line: FeedingLine) -> "FeedingLineModel":
    """Convierte entidad de dominio a modelo de persistencia."""
    from .blower_model import BlowerModel
    from .doser_model import DoserModel
    from .selector_model import SelectorModel
    from .sensor_model import SensorModel
    from .cooler_model import CoolerModel  # NUEVO

    line_model = FeedingLineModel(
        id=line.id.value,
        name=str(line.name),
        created_at=line._created_at,
    )

    if line._blower:
        line_model.blower = BlowerModel.from_domain(line._blower, line.id.value)

    line_model.dosers = [
        DoserModel.from_domain(doser, line.id.value) for doser in line.dosers
    ]

    if line._selector:
        line_model.selector = SelectorModel.from_domain(
            line._selector, line.id.value
        )

    line_model.sensors = [
        SensorModel.from_domain(sensor, line.id.value) for sensor in line._sensors
    ]
    
    # NUEVO: Persistir cooler si existe
    if line._cooler:
        line_model.cooler = CoolerModel.from_domain(line._cooler, line.id.value)

    return line_model
```

3. **Actualizar método `to_domain()`:**

```python
def to_domain(self) -> FeedingLine:
    """Convierte modelo de persistencia a entidad de dominio."""
    from domain.aggregates.feeding_line.blower import Blower
    from domain.aggregates.feeding_line.doser import Doser
    from domain.aggregates.feeding_line.selector import Selector
    from domain.aggregates.feeding_line.sensor import Sensor
    from domain.aggregates.feeding_line.cooler import Cooler  # NUEVO

    if not self.blower or not self.selector:
        raise ValueError(
            "FeedingLine debe tener blower y selector para reconstruir el dominio"
        )

    blower_domain = self.blower.to_domain()
    dosers_domain = [doser.to_domain() for doser in self.dosers]
    selector_domain = self.selector.to_domain()
    sensors_domain = [sensor.to_domain() for sensor in self.sensors]
    cooler_domain = self.cooler.to_domain() if self.cooler else None  # NUEVO

    line = FeedingLine.create(
        name=LineName(self.name),
        blower=blower_domain,
        dosers=dosers_domain,
        selector=selector_domain,
        sensors=sensors_domain,
        cooler=cooler_domain,  # NUEVO
    )

    line._id = LineId(self.id)
    line._created_at = self.created_at

    return line
```

### 4.3 Migración de Base de Datos

**Generar migración con Alembic:**

```bash
# Desde el contenedor Docker:
docker-compose exec backend alembic revision --autogenerate -m "add cooler to feeding lines"

# O localmente (con .venv activado):
alembic revision --autogenerate -m "add cooler to feeding lines"
```

**Verificar y ajustar el archivo de migración generado:**

El archivo debería verse similar a:

```python
"""add cooler to feeding lines

Revision ID: {hash}
Revises: 897baf33d221
Create Date: {timestamp}
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "{hash}"
down_revision: Union[str, Sequence[str], None] = "897baf33d221"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "coolers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("line_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_on", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cooling_power_percentage", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["line_id"], 
            ["feeding_lines.id"], 
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("coolers")
```

**Ejecutar migración:**

```bash
# Desde Docker:
docker-compose exec backend alembic upgrade head

# O localmente:
alembic upgrade head
```

---

## 5. Capa de Aplicación

### 5.1 DTOs para Comunicación PLC

#### Archivo: `src/domain/dtos/machine_io_v2.py`

**Actualizar `MachineConfiguration`:**

```python
@dataclass(frozen=True)
class MachineConfiguration:
    start_command: bool
    mode: FeedingMode
    slot_numbers: List[int]
    blower_speed_percentage: float
    doser_speed_percentage: float
    target_amount_kg: float
    batch_amount_kg: float = 0.0
    pause_time_seconds: int = 0
    
    # NUEVO: Campos para Cooler
    cooler_enabled: bool = False
    cooler_power_percentage: float = 0.0

    def __post_init__(self):
        if not self.slot_numbers:
            raise ValueError("La configuración debe tener al menos un slot objetivo.")
```

**Actualizar `MachineStatus`:**

```python
@dataclass(frozen=True)
class MachineStatus:
    is_running: bool
    is_paused: bool
    current_mode: FeedingMode
    total_dispensed_kg: float
    current_flow_rate: float
    current_slot_number: int
    current_list_index: int
    current_cycle_index: int
    total_cycles_configured: int
    has_error: bool = False
    error_code: Optional[int] = None
    
    # NUEVO: Estado del Cooler
    cooler_is_on: bool = False
    cooler_power: float = 0.0
```

### 5.2 Actualizar PLCSimulator

#### Archivo: `src/infrastructure/services/plc_simulator.py`

**1. Agregar CoolerState:**

```python
@dataclass
class CoolerState:
    """Estado simulado de un cooler"""
    state: ComponentState = ComponentState.OFF
    is_on: bool = False
    cooling_power_percentage: float = 0.0
    uptime_seconds: float = 0.0

    def update(self, delta_seconds: float) -> None:
        """Actualiza el estado del cooler"""
        if self.is_on:
            self.uptime_seconds += delta_seconds
            # El cooler opera a potencia constante (sin transiciones)
            # En implementación real podría tener rampa de enfriamiento
```

**2. Actualizar LineState:**

```python
@dataclass
class LineState:
    """Estado completo de una línea de alimentación"""
    
    line_id: str
    is_running: bool = False
    is_paused: bool = False
    mode: FeedingMode = FeedingMode.MANUAL

    # Configuración actual
    slot_list: List[int] = field(default_factory=list)
    current_slot_index: int = 0
    target_amount_kg: float = 0.0
    batch_amount_kg: float = 0.0

    # Componentes
    blower: BlowerState = field(default_factory=BlowerState)
    doser: DoserState = field(default_factory=DoserState)
    selector: SelectorState = field(default_factory=SelectorState)
    cooler: Optional[CoolerState] = None  # NUEVO: Cooler opcional

    # ... resto de campos
    
    def update_all_components(self, delta_seconds: float) -> None:
        """Actualiza todos los componentes de la línea"""
        self.blower.update(delta_seconds)
        self.doser.update(delta_seconds)
        self.selector.update(delta_seconds)
        
        # NUEVO: Actualizar cooler si existe
        if self.cooler:
            self.cooler.update(delta_seconds)
```

**3. Actualizar método `send_configuration()`:**

```python
async def send_configuration(
    self, line_id: LineId, config: MachineConfiguration
) -> None:
    """Envía configuración al PLC simulado."""
    state = self._get_or_create_state(line_id)

    await asyncio.sleep(0.05)

    if config.start_command:
        # ... configuración existente de blower, doser, selector
        
        # NUEVO: Configurar cooler si está habilitado
        if config.cooler_enabled:
            if state.cooler is None:
                state.cooler = CoolerState()
            
            state.cooler.state = ComponentState.RUNNING
            state.cooler.is_on = True
            state.cooler.cooling_power_percentage = config.cooler_power_percentage
        else:
            # Si el cooler está deshabilitado, apagarlo
            if state.cooler:
                state.cooler.state = ComponentState.OFF
                state.cooler.is_on = False
        
        # ... resto del código
```

**4. Actualizar método `get_status()`:**

```python
async def get_status(self, line_id: LineId) -> MachineStatus:
    """Obtiene el estado actual del PLC simulado."""
    state = self._get_or_create_state(line_id)

    await asyncio.sleep(0.02)

    # ... actualización de componentes existente
    
    # NUEVO: Obtener estado del cooler
    cooler_is_on = state.cooler.is_on if state.cooler else False
    cooler_power = (
        state.cooler.cooling_power_percentage if state.cooler else 0.0
    )

    return MachineStatus(
        is_running=state.is_running,
        is_paused=state.is_paused,
        current_mode=state.mode,
        total_dispensed_kg=round(state.doser.total_dispensed_kg, 3),
        current_flow_rate=round(state.doser.current_flow_rate_kg_per_hour, 2),
        current_slot_number=state.selector.current_slot,
        current_list_index=state.current_slot_index,
        current_cycle_index=state.current_cycle,
        total_cycles_configured=state.total_cycles,
        has_error=state.simulate_error,
        error_code=state.error_code,
        # NUEVO: Estado del cooler
        cooler_is_on=cooler_is_on,
        cooler_power=cooler_power,
    )
```

**5. Actualizar método `stop()`:**

```python
async def stop(self, line_id: LineId) -> None:
    """Detiene completamente la operación."""
    state = self._get_or_create_state(line_id)

    await asyncio.sleep(0.05)

    final_dispensed = state.doser.total_dispensed_kg

    state.is_running = False
    state.is_paused = False

    # Detener todos los componentes
    state.blower.state = ComponentState.OFF
    state.blower.target_speed_percentage = 0.0
    state.blower.current_speed_percentage = 0.0

    state.doser.state = ComponentState.OFF
    state.doser.target_speed_percentage = 0.0
    state.doser.current_speed_percentage = 0.0

    state.selector.state = ComponentState.OFF
    
    # NUEVO: Detener cooler si existe
    if state.cooler:
        state.cooler.state = ComponentState.OFF
        state.cooler.is_on = False

    self._log_action(
        line_id, "STOPPED (Hard)", f"Final dispensed: {final_dispensed:.2f}kg"
    )
```

---

## 6. Capa de API

### 6.1 API Models

Si tienes un archivo de modelos API para FeedingLine (por ejemplo `src/api/models/feeding_line_models.py`), actualízalo. Si no existe, agrégalo a los modelos existentes.

```python
from typing import Optional
from pydantic import BaseModel, Field


class CoolerCreateRequest(BaseModel):
    """Request para crear un Cooler."""
    name: str = Field(..., max_length=100)
    cooling_power_percentage: float = Field(..., ge=0, le=100)
    is_on: bool = False


class CoolerResponse(BaseModel):
    """Response con datos de un Cooler."""
    id: str
    name: str
    is_on: bool
    cooling_power_percentage: float


class FeedingLineResponse(BaseModel):
    """Response con datos completos de una FeedingLine."""
    id: str
    name: str
    # ... campos existentes (blower, dosers, selector, sensors)
    cooler: Optional[CoolerResponse] = None  # NUEVO
```

### 6.2 Actualizar Endpoints

#### Endpoint: POST /system-layout/sync

**Archivo:** `src/api/routers/system_layout_router.py` (o donde esté definido)

**Request payload debe aceptar cooler opcional:**

```python
class SyncLayoutRequest(BaseModel):
    lines: List[LineData]

class LineData(BaseModel):
    name: str
    blower: BlowerData
    dosers: List[DoserData]
    selector: SelectorData
    sensors: Optional[List[SensorData]] = []
    cooler: Optional[CoolerData] = None  # NUEVO
```

**CoolerData schema:**

```python
class CoolerData(BaseModel):
    name: str
    cooling_power_percentage: float = Field(ge=0, le=100)
    is_on: bool = False
```

**En el use case `SyncSystemLayoutUseCase`:**

Al construir la línea de dominio, pasar el cooler si existe:

```python
# Construir cooler si viene en los datos
cooler_domain = None
if line_data.cooler:
    cooler_domain = Cooler(
        name=CoolerName(line_data.cooler.name),
        cooling_power_percentage=CoolerPowerPercentage(
            line_data.cooler.cooling_power_percentage
        ),
        is_on=line_data.cooler.is_on
    )

# Crear la línea con todos los componentes
line = FeedingLine.create(
    name=LineName(line_data.name),
    blower=blower_domain,
    dosers=dosers_domain,
    selector=selector_domain,
    sensors=sensors_domain,
    cooler=cooler_domain  # NUEVO
)
```

#### Endpoint: GET /feeding-lines/{line_id}

**Actualizar el mapper/response para incluir cooler:**

```python
def map_feeding_line_to_response(line: FeedingLine) -> FeedingLineResponse:
    # ... mapeo existente
    
    # NUEVO: Mapear cooler si existe
    cooler_response = None
    if line.cooler:
        cooler_response = CoolerResponse(
            id=str(line.cooler.id),
            name=str(line.cooler.name),
            is_on=line.cooler.is_on,
            cooling_power_percentage=line.cooler.cooling_power_percentage.value
        )
    
    return FeedingLineResponse(
        # ... campos existentes
        cooler=cooler_response
    )
```

---

## 7. Testing

### 7.1 Unit Tests de Dominio

#### Archivo: `src/test/domain/aggregates/feeding_line/test_cooler.py`

```python
"""Tests unitarios para la entidad Cooler."""

import pytest
from datetime import datetime

from domain.aggregates.feeding_line.cooler import Cooler
from domain.value_objects import CoolerName, CoolerPowerPercentage


class TestCoolerCreation:
    """Tests de creación de Cooler."""
    
    def test_create_cooler_with_valid_data(self):
        """Debe crear un Cooler con datos válidos."""
        cooler = Cooler(
            name=CoolerName("Cooler Principal"),
            cooling_power_percentage=CoolerPowerPercentage(75.0),
            is_on=True
        )
        
        assert cooler.id is not None
        assert str(cooler.name) == "Cooler Principal"
        assert cooler.is_on is True
        assert cooler.cooling_power_percentage.value == 75.0
        assert isinstance(cooler.created_at, datetime)
    
    def test_cooler_defaults_to_off(self):
        """Debe crear un Cooler apagado por defecto."""
        cooler = Cooler(
            name=CoolerName("Cooler Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0)
        )
        
        assert cooler.is_on is False


class TestCoolerPowerValidation:
    """Tests de validación de potencia."""
    
    def test_valid_power_percentage(self):
        """Debe aceptar potencias válidas (0-100)."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(0.0)
        )
        assert cooler.cooling_power_percentage.value == 0.0
        
        cooler.cooling_power_percentage = CoolerPowerPercentage(100.0)
        assert cooler.cooling_power_percentage.value == 100.0
    
    def test_invalid_power_percentage_below_zero(self):
        """Debe rechazar potencias negativas."""
        with pytest.raises(ValueError):
            CoolerPowerPercentage(-10.0)
    
    def test_invalid_power_percentage_above_100(self):
        """Debe rechazar potencias mayores a 100."""
        with pytest.raises(ValueError):
            CoolerPowerPercentage(150.0)


class TestCoolerBehavior:
    """Tests de comportamiento del Cooler."""
    
    def test_turn_on(self):
        """Debe encender el cooler."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=False
        )
        
        cooler.turn_on()
        assert cooler.is_on is True
    
    def test_turn_off(self):
        """Debe apagar el cooler."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=True
        )
        
        cooler.turn_off()
        assert cooler.is_on is False
    
    def test_validate_power_is_safe(self):
        """Debe validar que la potencia sea segura."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0)
        )
        
        assert cooler.validate_power_is_safe(CoolerPowerPercentage(75.0)) is True
```

#### Archivo: `src/test/domain/aggregates/feeding_line/test_feeding_line.py`

**Agregar tests para FeedingLine con Cooler:**

```python
class TestFeedingLineWithCooler:
    """Tests de FeedingLine con Cooler opcional."""
    
    def test_create_feeding_line_with_cooler(self):
        """Debe crear una FeedingLine con Cooler."""
        # Arrange
        cooler = Cooler(
            name=CoolerName("Cooler 1"),
            cooling_power_percentage=CoolerPowerPercentage(80.0)
        )
        
        # Act
        line = FeedingLine.create(
            name=LineName("Línea 1"),
            blower=mock_blower,
            dosers=[mock_doser],
            selector=mock_selector,
            cooler=cooler
        )
        
        # Assert
        assert line.cooler is not None
        assert str(line.cooler.name) == "Cooler 1"
        assert line.cooler.cooling_power_percentage.value == 80.0
    
    def test_create_feeding_line_without_cooler(self):
        """Debe crear una FeedingLine sin Cooler (None)."""
        # Act
        line = FeedingLine.create(
            name=LineName("Línea Sin Cooler"),
            blower=mock_blower,
            dosers=[mock_doser],
            selector=mock_selector
            # cooler no se pasa
        )
        
        # Assert
        assert line.cooler is None
    
    def test_update_components_with_cooler(self):
        """Debe actualizar componentes incluyendo el Cooler."""
        # Arrange
        line = FeedingLine.create(
            name=LineName("Línea 1"),
            blower=mock_blower,
            dosers=[mock_doser],
            selector=mock_selector
        )
        
        new_cooler = Cooler(
            name=CoolerName("Nuevo Cooler"),
            cooling_power_percentage=CoolerPowerPercentage(90.0)
        )
        
        # Act
        line.update_components(
            blower=mock_blower,
            dosers=[mock_doser],
            selector=mock_selector,
            cooler=new_cooler
        )
        
        # Assert
        assert line.cooler is not None
        assert str(line.cooler.name) == "Nuevo Cooler"
```

### 7.2 Integration Tests

#### Archivo: `src/test/infrastructure/persistence/repositories/test_feeding_line_repository.py`

**Agregar tests de persistencia:**

```python
@pytest.mark.asyncio
async def test_save_feeding_line_with_cooler(session):
    """Debe persistir y recuperar FeedingLine con Cooler."""
    # Arrange
    cooler = Cooler(
        name=CoolerName("Cooler Test"),
        cooling_power_percentage=CoolerPowerPercentage(85.0),
        is_on=True
    )
    
    line = FeedingLine.create(
        name=LineName("Línea con Cooler"),
        blower=mock_blower,
        dosers=[mock_doser],
        selector=mock_selector,
        cooler=cooler
    )
    
    repo = FeedingLineRepository(session)
    
    # Act
    await repo.save(line)
    retrieved_line = await repo.find_by_id(line.id)
    
    # Assert
    assert retrieved_line is not None
    assert retrieved_line.cooler is not None
    assert str(retrieved_line.cooler.name) == "Cooler Test"
    assert retrieved_line.cooler.cooling_power_percentage.value == 85.0
    assert retrieved_line.cooler.is_on is True


@pytest.mark.asyncio
async def test_save_feeding_line_without_cooler(session):
    """Debe persistir FeedingLine sin Cooler (NULL en BD)."""
    # Arrange
    line = FeedingLine.create(
        name=LineName("Línea sin Cooler"),
        blower=mock_blower,
        dosers=[mock_doser],
        selector=mock_selector
        # No se pasa cooler
    )
    
    repo = FeedingLineRepository(session)
    
    # Act
    await repo.save(line)
    retrieved_line = await repo.find_by_id(line.id)
    
    # Assert
    assert retrieved_line is not None
    assert retrieved_line.cooler is None
```

### 7.3 API Tests

Actualizar tests del endpoint `sync-system-layout`:

```python
@pytest.mark.asyncio
async def test_sync_layout_with_cooler(client):
    """Debe sincronizar layout con Cooler en una línea."""
    payload = {
        "lines": [
            {
                "name": "Línea 1",
                "blower": {...},
                "dosers": [...],
                "selector": {...},
                "cooler": {
                    "name": "Cooler Principal",
                    "cooling_power_percentage": 75.0,
                    "is_on": false
                }
            }
        ]
    }
    
    response = await client.post("/system-layout/sync", json=payload)
    
    assert response.status_code == 200
    # Verificar que el cooler fue persistido
```

---

## 8. Orden de Implementación

Sigue estas fases **en orden estricto** para evitar errores de compilación y dependencias:

### Fase 1: Dominio (Core Business Logic)

1. ✅ **Value Objects**
   - `src/domain/value_objects/feeding_specs.py`: Agregar `CoolerPowerPercentage`
   - `src/domain/value_objects/identifiers.py`: Agregar `CoolerId`
   - `src/domain/value_objects/names.py`: Agregar `CoolerName`
   - `src/domain/value_objects/__init__.py`: Actualizar exports

2. ✅ **Interfaz**
   - `src/domain/interfaces.py`: Agregar `ICooler` interface

3. ✅ **Entidad**
   - `src/domain/aggregates/feeding_line/cooler.py`: Implementar `Cooler`

4. ✅ **Actualizar FeedingLine**
   - `src/domain/aggregates/feeding_line/feeding_line.py`: Agregar soporte para cooler opcional

5. ✅ **Tests unitarios de dominio**
   - `src/test/domain/aggregates/feeding_line/test_cooler.py`
   - Actualizar `test_feeding_line.py`

### Fase 2: Infraestructura (Persistencia)

6. ✅ **Modelo de persistencia**
   - `src/infrastructure/persistence/models/cooler_model.py`: Crear modelo

7. ✅ **Actualizar FeedingLineModel**
   - `src/infrastructure/persistence/models/feeding_line_model.py`: Agregar relación con cooler

8. ✅ **Migración de base de datos**
   - Generar: `alembic revision --autogenerate -m "add cooler to feeding lines"`
   - Revisar el archivo generado
   - Ejecutar: `alembic upgrade head`

9. ✅ **Tests de integración (persistencia)**
   - Actualizar `test_feeding_line_repository.py`

### Fase 3: DTOs y Servicios PLC

10. ✅ **DTOs de comunicación PLC**
    - `src/domain/dtos/machine_io_v2.py`: Actualizar `MachineConfiguration` y `MachineStatus`

11. ✅ **PLCSimulator**
    - `src/infrastructure/services/plc_simulator.py`: Agregar `CoolerState` y actualizar métodos

### Fase 4: API y Presentación

12. ✅ **API Models**
    - Crear/actualizar modelos API para incluir cooler

13. ✅ **Endpoints**
    - Actualizar `sync-system-layout` para aceptar cooler
    - Actualizar respuestas de GET para incluir cooler

14. ✅ **Tests de API**
    - Actualizar tests de endpoints

### Fase 5: Documentación

15. ✅ **Actualizar documentación**
    - `CLAUDE.md`: Agregar Cooler a lista de componentes
    - Crear este documento `PLAN_IMPLEMENTACION_COOLER.md` ✨

---

## 9. Impacto en Sistema Existente

### 9.1 Cambios Breaking

**NO hay breaking changes** porque:
- ✅ Cooler es opcional en FeedingLine
- ✅ Endpoints existentes siguen funcionando sin cooler
- ✅ Modelos de base de datos son extensibles (cooler_id nullable)
- ✅ DTOs PLC tienen valores por defecto (`cooler_enabled=False`)

### 9.2 Backwards Compatibility

- ✅ Líneas existentes en BD no tendrán cooler (NULL permitido)
- ✅ `FeedingLine.create()` acepta `cooler=None` por defecto
- ✅ API responses incluyen `cooler: Optional[CoolerResponse]`
- ✅ Request payloads aceptan `cooler: Optional[CoolerData]`

### 9.3 Migraciones de Datos

**No se requiere migración de datos** porque:
- La tabla `coolers` se crea vacía
- Las líneas existentes no tienen coolers asociados (comportamiento esperado)
- No hay valores por defecto obligatorios

---

## 10. Preguntas Pendientes (Para el Implementador)

Antes de implementar, considera estas preguntas:

### 10.1 Integración con Sensores

**¿El cooler tendrá integración con sensores de temperatura desde el inicio?**

- **Opción A (Simple)**: No, solo control manual de on/off y potencia
  - ✅ Implementar como está en este plan
  
- **Opción B (Automático)**: Sí, ajustar potencia según temperatura objetivo
  - Agregar campos: `target_temperature`, `current_temperature`
  - Crear lógica en estrategias de alimentación
  - Integrar con sensores existentes de temperatura

### 10.2 Control en Tiempo Real

**¿Se requiere endpoint específico para controlar el cooler durante operaciones?**

- **Opción A**: No, se configura en sync-system-layout y no cambia durante operación
  - ✅ No agregar endpoints adicionales
  
- **Opción B**: Sí, operador puede ajustar potencia en tiempo real
  - Crear endpoint: `PATCH /feeding-lines/{line_id}/cooler`
  - Persistir cambios en tiempo real
  - Enviar comando al PLC vía `IFeedingMachine`

### 10.3 Semántica de `cooling_power_percentage`

**¿Qué representa exactamente este campo?**

- **Opción A**: Potencia del compresor/refrigerador (0-100% de capacidad)
- **Opción B**: Velocidad de ventilación del sistema de enfriamiento
- **Opción C**: Target de reducción de temperatura (% de enfriamiento deseado)

**Impacto**: Afecta validaciones y documentación del campo.

### 10.4 Límites Operativos

**¿Hay restricciones de seguridad?**

- **Ejemplo 1**: No operar cooler si temperatura ambiente > 40°C
- **Ejemplo 2**: Potencia mínima del 30% cuando blower está encendido
- **Ejemplo 3**: Cooler debe encenderse X segundos antes del blower

Si existen restricciones, agregarlas en `validate_power_is_safe()`.

---

## 11. Notas Finales para el Implementador

### Consejos

1. **Sigue el orden de fases**: No saltes pasos, las dependencias están ordenadas
2. **Tests first (opcional)**: Puedes escribir tests antes de implementar (TDD)
3. **Commits incrementales**: Haz commits por fase completada
4. **Revisa las migraciones**: Alembic autogenera, pero siempre revisa el SQL
5. **Ejecuta tests frecuentemente**: `pytest -v` después de cada fase

### Checklist de Validación

Después de implementar, verifica:

- [ ] Tests unitarios pasan: `pytest src/test/domain/`
- [ ] Tests de integración pasan: `pytest src/test/infrastructure/`
- [ ] Tests de API pasan: `pytest src/test/api/`
- [ ] Migraciones aplicadas: `alembic current`
- [ ] No hay imports circulares: `python -m src.main`
- [ ] Linter pasa: `ruff check src/`
- [ ] Type checker pasa: `mypy src/`
- [ ] API docs actualizadas: http://localhost:8000/docs

### Recursos Útiles

- **Patrón existente**: Revisa `Blower` como referencia (estructura similar)
- **Migraciones**: `docs/comandos-alembic.md`
- **DDD patterns**: `docs/plan-migracion-feeding-operation.md`

---

## 12. Resumen Ejecutivo

| Aspecto | Detalle |
|---------|---------|
| **Complejidad** | Media-Baja (similar a agregar Blower o Selector) |
| **Riesgo** | Bajo (cambios no invasivos, opcional) |
| **Breaking Changes** | Ninguno |
| **Backwards Compatible** | Sí |
| **Tests** | Completo (unit, integration, API) |
| **Documentación** | Actualizar CLAUDE.md y docs de API |

**Campos implementados:**
- `id`, `name`, `is_on`, `cooling_power_percentage`, `created_at`

**Campos futuros (no implementar ahora):**
- `target_temperature`, `current_temperature`, `min_power`, `max_power`

---

**¡Buena suerte con la implementación!** 🚀

Si tienes dudas, consulta este documento o revisa los componentes existentes (Blower, Doser, Selector) como referencia.

---

**Última actualización**: 2026-01-15  
**Autor**: Claude Code (Sesión de Planning)  
**Revisado por**: Pendiente
