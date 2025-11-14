# Plan de Migración: De Clases Concretas a Abstracciones en SyncSystemLayoutUseCase

**Fecha**: 2025-11-14  
**Versión**: 1.0  
**Estado**: Pendiente de implementación

---

## 🎯 Objetivo

Migrar el caso de uso `SyncSystemLayoutUseCase` y sus servicios para que dependan de las interfaces (`IBlower`, `IDoser`, `ISelector`, `ISensor`) en lugar de las clases concretas (`Blower`, `Doser`, `Selector`, `Sensor`).

## 📋 Contexto

Actualmente el caso de uso instancia directamente las clases concretas:

- `Blower` → debe usar `IBlower`
- `Doser` → debe usar `IDoser`
- `Selector` → debe usar `ISelector`
- `Sensor` → debe usar `ISensor`

Esto es necesario porque en producción habrá múltiples implementaciones:

- **Dosers**: `VariDoser`, `PulseDoser`, `ScrewDoser` (todos implementan `IDoser`)
- **Blowers**: Potencialmente diferentes tipos de sopladores
- **Selectors**: Potencialmente diferentes tipos de selectoras
- **Sensors**: Diferentes tipos de sensores

El polimorfismo permitirá que cada implementación tenga su propia lógica de calibración y operación, mientras el caso de uso trabaja con la abstracción.

---

## 🔍 Análisis de Dependencias

### Archivos afectados

1. **Caso de uso principal**:

   - `src/application/use_cases/sync_system_layout.py`

2. **Servicios de aplicación**:

   - `src/application/services/resource_releaser.py`
   - `src/application/services/delta_calculator.py`
   - `src/application/services/name_validator.py` (no afectado)

3. **DTOs** (potencialmente):

   - `src/application/dtos.py` (necesita campo `component_type` para identificar implementación)

4. **Mappers**:

   - `src/application/mappers.py` (debe mapear desde interfaces)

5. **Capa API** (fuera de alcance por ahora):
   - `src/api/endpoints/system_layout.py`

### Métodos que instancian clases concretas

En `SyncSystemLayoutUseCase`:

- `_build_blower_from_dto()` → instancia `Blower`
- `_build_sensors_from_dto()` → instancia `Sensor`
- `_build_dosers_from_dto()` → instancia `Doser`
- `_build_selector_from_dto()` → instancia `Selector`

---

## 📝 Plan de Migración (Paso a Paso)

### **FASE 1: Preparación de Infraestructura**

#### 1.1. Crear Factory Pattern para Componentes

**Archivo**: `src/domain/factories/component_factory.py`

**Responsabilidad**: Crear instancias concretas basándose en el tipo de componente.

**Contenido**:

```python
class ComponentFactory:
    @staticmethod
    def create_blower(blower_type: str, ...) -> IBlower:
        # Por ahora solo Blower, luego VariBlower, etc.

    @staticmethod
    def create_doser(doser_type: str, ...) -> IDoser:
        # VariDoser, PulseDoser, ScrewDoser

    @staticmethod
    def create_selector(selector_type: str, ...) -> ISelector:
        # Por ahora solo Selector

    @staticmethod
    def create_sensor(sensor_type: SensorType, ...) -> ISensor:
        # Por ahora solo Sensor
```

**Razón**: Centralizar la lógica de creación y permitir extensibilidad sin modificar el caso de uso.

---

#### 1.2. Actualizar DTOs con Campo `component_type`

**Archivo**: `src/application/dtos.py`

**Cambios**:

- `BlowerConfigDTO` → agregar campo `blower_type: str = "standard"`
- `DoserConfigDTO` → ya tiene `doser_type: str` ✅
- `SelectorConfigDTO` → agregar campo `selector_type: str = "standard"`
- `SensorConfigDTO` → ya tiene `sensor_type: str` ✅

**Razón**: El DTO debe indicar qué implementación concreta crear.

---

### **FASE 2: Refactorización del Caso de Uso**

#### 2.1. Inyectar ComponentFactory en el Constructor

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Cambio**:

```python
def __init__(self,
             line_repo: IFeedingLineRepository,
             silo_repo: ISiloRepository,
             cage_repo: ICageRepository,
             component_factory: ComponentFactory):  # ← NUEVO
    self.line_repo = line_repo
    self.silo_repo = silo_repo
    self.cage_repo = cage_repo
    self.component_factory = component_factory  # ← NUEVO
```

**Razón**: Inversión de dependencias (el caso de uso no debe conocer implementaciones concretas).

---

#### 2.2. Refactorizar Métodos `_build_*_from_dto()`

**Cambios en cada método**:

**Antes**:

```python
def _build_blower_from_dto(self, dto: BlowerConfigDTO) -> Blower:
    return Blower(...)  # ← Clase concreta
```

**Después**:

```python
def _build_blower_from_dto(self, dto: BlowerConfigDTO) -> IBlower:
    return self.component_factory.create_blower(
        blower_type=dto.blower_type,
        name=BlowerName(dto.name),
        ...
    )  # ← Interfaz
```

**Aplicar a**:

- `_build_blower_from_dto()` → retorna `IBlower`
- `_build_sensors_from_dto()` → retorna `List[ISensor]`
- `_build_dosers_from_dto()` → retorna `List[IDoser]`
- `_build_selector_from_dto()` → retorna `ISelector`

**Razón**: El caso de uso trabaja con abstracciones, no con implementaciones.

---

#### 2.3. Actualizar Imports

**Eliminar**:

```python
from domain.aggregates.feeding_line.blower import Blower
from domain.aggregates.feeding_line.doser import Doser
from domain.aggregates.feeding_line.selector import Selector
from domain.aggregates.feeding_line.sensor import Sensor
```

**Agregar**:

```python
from domain.interfaces import IBlower, IDoser, ISelector, ISensor
from domain.factories import ComponentFactory
```

---

### **FASE 3: Actualización de Servicios**

#### 3.1. ResourceReleaser

**Archivo**: `src/application/services/resource_releaser.py`

**Cambio**: Ya usa `line.dosers` que retorna `Tuple[IDoser, ...]` ✅

**Acción**: Verificar que no haya referencias a clases concretas.

---

#### 3.2. DeltaCalculator

**Archivo**: `src/application/services/delta_calculator.py`

**Cambio**: No instancia componentes, solo calcula diferencias ✅

**Acción**: Sin cambios necesarios.

---

### **FASE 4: Actualización de Mappers**

#### 4.1. DomainToDTOMapper

**Archivo**: `src/application/mappers.py`

**Cambio**: Los métodos deben trabajar con interfaces:

**Antes**:

```python
def blower_to_dto(blower: Blower) -> BlowerConfigDTO:
```

**Después**:

```python
def blower_to_dto(blower: IBlower) -> BlowerConfigDTO:
    return BlowerConfigDTO(
        name=str(blower.name),
        blower_type=blower.__class__.__name__.lower(),  # ← Detectar tipo
        ...
    )
```

**Aplicar a**:

- `blower_to_dto(blower: IBlower)`
- `doser_to_dto(doser: IDoser)`
- `selector_to_dto(selector: ISelector)`
- `sensor_to_dto(sensor: ISensor)`

**Razón**: Los mappers deben trabajar con abstracciones y detectar el tipo concreto para el DTO.

---

### **FASE 5: Testing**

#### 5.1. Actualizar Tests Existentes

**Archivos**:

- `src/test/application/use_cases/test_sync_*.py`

**Cambios**:

- Inyectar `ComponentFactory` en el caso de uso
- Verificar que los tests sigan pasando
- Agregar tests para diferentes tipos de componentes (cuando existan)

---

#### 5.2. Crear Tests para ComponentFactory

**Archivo**: `src/test/domain/factories/test_component_factory.py`

**Casos de prueba**:

- Crear cada tipo de componente
- Validar que retornan la interfaz correcta
- Validar que lanzan error si el tipo es inválido

---

### **FASE 6: Documentación**

#### 6.1. Actualizar Documentación del Caso de Uso

**Archivo**: `docs/03-casos-de-uso/UC-01-sincronizar-trazado-sistema.md`

**Agregar sección**: "Tipos de Componentes Soportados"

---

#### 6.2. Documentar ComponentFactory

**Archivo**: `docs/02-dominio/factories.md` (nuevo)

**Contenido**:

- Propósito del factory
- Tipos de componentes soportados
- Cómo agregar nuevos tipos

---

## ✅ Checklist de Implementación

### Fase 1: Preparación

- [ ] Crear `src/domain/factories/__init__.py`
- [ ] Crear `src/domain/factories/component_factory.py`
- [ ] Actualizar `BlowerConfigDTO` con `blower_type`
- [ ] Actualizar `SelectorConfigDTO` con `selector_type`

### Fase 2: Caso de Uso

- [ ] Inyectar `ComponentFactory` en constructor
- [ ] Refactorizar `_build_blower_from_dto()`
- [ ] Refactorizar `_build_sensors_from_dto()`
- [ ] Refactorizar `_build_dosers_from_dto()`
- [ ] Refactorizar `_build_selector_from_dto()`
- [ ] Actualizar imports

### Fase 3: Servicios

- [ ] Verificar `ResourceReleaser`
- [ ] Verificar `DeltaCalculator`

### Fase 4: Mappers

- [ ] Actualizar `blower_to_dto()`
- [ ] Actualizar `doser_to_dto()`
- [ ] Actualizar `selector_to_dto()`
- [ ] Actualizar `sensor_to_dto()`

### Fase 5: Testing

- [ ] Actualizar tests existentes
- [ ] Crear tests para `ComponentFactory`
- [ ] Ejecutar suite completa de tests

### Fase 6: Documentación

- [ ] Actualizar UC-01
- [ ] Crear documentación de factories

---

## 🚨 Consideraciones Importantes

### 1. Compatibilidad hacia atrás

- Mantener `Blower`, `Doser`, `Selector`, `Sensor` como implementaciones por defecto
- El factory debe usar estas clases cuando `component_type` sea `"standard"` o no esté especificado

### 2. Extensibilidad futura

- Cuando se agreguen `VariDoser`, `PulseDoser`, etc., solo se modifica el factory
- El caso de uso NO cambia

### 3. Capa API (fuera de alcance)

- La capa API debe enviar el campo `component_type` en los DTOs
- Esto se abordará en una migración posterior

### 4. Persistencia

- Los repositorios ya trabajan con interfaces (`FeedingLine` almacena `IDoser`, no `Doser`)
- No requiere cambios en la capa de infraestructura

---

## 📊 Impacto Estimado

| Componente    | Archivos Afectados | Complejidad | Riesgo |
| ------------- | ------------------ | ----------- | ------ |
| Factory       | 1 nuevo            | Baja        | Bajo   |
| DTOs          | 1 modificado       | Baja        | Bajo   |
| Caso de Uso   | 1 modificado       | Media       | Medio  |
| Mappers       | 1 modificado       | Media       | Medio  |
| Tests         | 5-10 modificados   | Media       | Bajo   |
| Documentación | 2 archivos         | Baja        | Bajo   |

**Tiempo estimado**: 4-6 horas de desarrollo + 2 horas de testing

---

## 🎯 Resultado Esperado

Después de la migración:

1. ✅ El caso de uso depende de abstracciones (`IBlower`, `IDoser`, etc.)
2. ✅ La creación de componentes está centralizada en `ComponentFactory`
3. ✅ Es fácil agregar nuevos tipos de componentes sin modificar el caso de uso
4. ✅ Se mantiene compatibilidad con las implementaciones actuales
5. ✅ El código sigue los principios SOLID (especialmente Dependency Inversion)

---

**Próximos pasos**: Implementar Fase 1 y validar con tests antes de continuar.
