# Component Factory

## Propósito

`ComponentFactory` es responsable de crear instancias concretas de componentes de líneas de alimentación basándose en su tipo. Implementa el patrón Factory para permitir polimorfismo y extensibilidad sin modificar el código existente.

## Ubicación

```
src/domain/factories/component_factory.py
```

## Responsabilidades

- Crear instancias de `IBlower`, `IDoser`, `ISelector`, `ISensor`
- Seleccionar la implementación concreta según el tipo especificado
- Validar que el tipo de componente sea soportado
- Encapsular la lógica de creación de componentes

## Tipos de Componentes Soportados

### Blowers (Sopladores)

| Tipo                  | Clase    | Descripción                                |
| --------------------- | -------- | ------------------------------------------ |
| `standard` o `blower` | `Blower` | Soplador estándar con configuración básica |

**Parámetros de creación:**

- `name`: Nombre del soplador
- `non_feeding_power`: Potencia en modo no-alimentación (0-100%)
- `blow_before_time`: Tiempo de soplado antes de alimentar (segundos)
- `blow_after_time`: Tiempo de soplado después de alimentar (segundos)

### Dosers (Dosificadores)

| Tipo                 | Clase   | Descripción          |
| -------------------- | ------- | -------------------- |
| `standard` o `doser` | `Doser` | Dosificador estándar |

**Parámetros de creación:**

- `name`: Nombre del dosificador
- `assigned_silo_id`: ID del silo asignado
- `dosing_range`: Rango de dosificación (min/max)
- `current_rate`: Tasa actual de dosificación

**Tipos futuros** (preparados para extensión):

- `VariDoser`: Dosificador de velocidad variable
- `PulseDoser`: Dosificador por pulsos
- `ScrewDoser`: Dosificador de tornillo

### Selectors (Selectoras)

| Tipo                    | Clase      | Descripción        |
| ----------------------- | ---------- | ------------------ |
| `standard` o `selector` | `Selector` | Selectora estándar |

**Parámetros de creación:**

- `name`: Nombre de la selectora
- `capacity`: Capacidad (número de slots)
- `speed_profile`: Perfil de velocidades (rápida/lenta)

### Sensors (Sensores)

| Tipo            | Clase    | Descripción     |
| --------------- | -------- | --------------- |
| Todos los tipos | `Sensor` | Sensor genérico |

**Tipos de sensor:**

- `TEMPERATURE`: Sensor de temperatura
- `PRESSURE`: Sensor de presión
- `FLOW`: Sensor de flujo

**Parámetros de creación:**

- `name`: Nombre del sensor
- `sensor_type`: Tipo de sensor (enum `SensorType`)

## Uso

### Desde el Caso de Uso

```python
from domain.factories import ComponentFactory

factory = ComponentFactory()

# Crear blower
blower = factory.create_blower(
    blower_type="standard",
    name=BlowerName("Soplador 1"),
    non_feeding_power=BlowerPowerPercentage(50.0),
    blow_before_time=BlowDurationInSeconds(5),
    blow_after_time=BlowDurationInSeconds(3)
)

# Crear doser
doser = factory.create_doser(
    doser_type="standard",
    name=DoserName("Dosificador 1"),
    assigned_silo_id=silo_id,
    dosing_range=DosingRange(min_rate=10.0, max_rate=100.0),
    current_rate=DosingRate(50.0)
)

# Crear selector
selector = factory.create_selector(
    selector_type="standard",
    name=SelectorName("Selectora 1"),
    capacity=SelectorCapacity(4),
    speed_profile=SelectorSpeedProfile(
        fast_speed=BlowerPowerPercentage(80.0),
        slow_speed=BlowerPowerPercentage(20.0)
    )
)

# Crear sensor
sensor = factory.create_sensor(
    sensor_type=SensorType.TEMPERATURE,
    name=SensorName("Sensor Temp 1")
)
```

## Extensibilidad

### Agregar un Nuevo Tipo de Dosificador

Para agregar un nuevo tipo de dosificador (ej: `VariDoser`):

1. **Crear la clase** que implemente `IDoser`:

```python
# src/domain/aggregates/feeding_line/vari_doser.py
from domain.interfaces import IDoser

class VariDoser(IDoser):
    def __init__(self, name, assigned_silo_id, dosing_range, current_rate):
        # Implementación específica
        pass

    def calibrate(self, calibration_data):
        # Lógica de calibración específica para VariDoser
        pass
```

2. **Actualizar el Factory**:

```python
# src/domain/factories/component_factory.py
from ..aggregates.feeding_line.vari_doser import VariDoser

@staticmethod
def create_doser(doser_type, name, assigned_silo_id, dosing_range, current_rate):
    doser_type_lower = doser_type.lower()

    if doser_type_lower in ["standard", "doser"]:
        return Doser(...)

    elif doser_type_lower == "varidoser":
        return VariDoser(
            name=name,
            assigned_silo_id=assigned_silo_id,
            dosing_range=dosing_range,
            current_rate=current_rate
        )

    raise ValueError(f"Tipo de doser no soportado: '{doser_type}'")
```

3. **Listo**: El resto del sistema funciona sin cambios.

## Manejo de Errores

El factory lanza `ValueError` cuando se solicita un tipo no soportado:

```python
try:
    blower = factory.create_blower(
        blower_type="turbo",  # Tipo no soportado
        ...
    )
except ValueError as e:
    # "Tipo de blower no soportado: 'turbo'"
    print(e)
```

## Principios de Diseño

- **Open/Closed Principle**: Abierto para extensión (nuevos tipos), cerrado para modificación (caso de uso no cambia)
- **Dependency Inversion**: El caso de uso depende de interfaces (`IBlower`, `IDoser`), no de implementaciones concretas
- **Single Responsibility**: El factory solo se encarga de crear componentes
- **Factory Pattern**: Encapsula la lógica de creación y selección de implementaciones

## Notas Técnicas

- El factory es stateless (sin estado), todos los métodos son `@staticmethod`
- Los tipos de componentes son case-insensitive (`"Standard"` = `"standard"`)
- El factory normaliza tipos comunes (ej: `"blower"` → `"standard"`)
- Cada método del factory retorna la interfaz correspondiente, no la clase concreta
