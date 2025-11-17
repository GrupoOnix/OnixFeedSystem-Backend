# Plan de Migración: Uso de Abstracciones y Eliminación de DTOs Redundantes

**Fecha**: 2025-11-14  
**Versión**: 4.0  
**Estado**: Pendiente de implementación

---

## 🎯 Objetivo

Refactorizar el sistema para que:

1. El caso de uso `SyncSystemLayoutUseCase` dependa de abstracciones (`IBlower`, `IDoser`, `ISelector`, `ISensor`)
2. Eliminar la capa DTO redundante (mapeo 1:1 sin lógica)
3. Usar directamente Pydantic Models como entrada del caso de uso
4. Caso de uso retorna entidades (dominio puro)
5. API convierte entidades a Pydantic para respuesta
6. Implementar polimorfismo con `ComponentFactory`

---

## 📋 Problemas Identificados

### 1. Dependencia de Clases Concretas

El caso de uso instancia directamente:

- `Blower`, `Doser`, `Selector`, `Sensor` (clases concretas)
- Debería usar: `IBlower`, `IDoser`, `ISelector`, `ISensor` (interfaces)

### 2. Capa DTO Redundante

```
Pydantic Model → DTO (mapeo 1:1 sin lógica) → Caso de Uso
```

Los DTOs son copias exactas de los Pydantic Models sin agregar valor.

### 3. Falta de Polimorfismo

No se pueden agregar nuevos tipos de componentes (`VariDoser`, `PulseDoser`, `ScrewDoser`) sin modificar el caso de uso.

---

## 🏗️ Arquitectura Objetivo

### Flujo Correcto

```
Request:  Pydantic → Caso de Uso (construye entidades usando Factory) → Repositorio
Response: Repositorio → Entidades → Caso de Uso → API/ResponseMapper → Pydantic
```

### Responsabilidades por Capa

| Capa            | Responsabilidad                                                      |
| --------------- | -------------------------------------------------------------------- |
| **API**         | Validación entrada (Pydantic), Serialización salida (ResponseMapper) |
| **Application** | Orquestación + Construcción de entidades (UseCase + Factory)         |
| **Domain**      | Lógica de negocio, Reglas de dominio, Factory de componentes         |

---

## 📝 Plan de Migración (Paso a Paso)

### **FASE 1: Preparación de Infraestructura** ✅

#### 1.1. Crear ComponentFactory ✅

**Archivo**: `src/domain/factories/component_factory.py`

**Estado**: Completado

**Contenido**:

- Factory con métodos para crear `IBlower`, `IDoser`, `ISelector`, `ISensor`
- Soporta tipos actuales: `Blower`, `Doser`, `Selector`, `Sensor`
- Preparado para extensión: `VariDoser`, `PulseDoser`, `ScrewDoser`

---

#### 1.2. Actualizar Pydantic Models con Campos de Tipo ✅

**Archivo**: `src/api/models/system_layout.py`

**Estado**: Completado

**Cambios**:

- ✅ `BlowerConfigModel` → tiene `blower_type: str`
- ✅ `DoserConfigModel` → tiene `doser_type: str`
- ✅ `SelectorConfigModel` → tiene `selector_type: str`
- ✅ `SensorConfigModel` → tiene `sensor_type: str`

---

### **FASE 2: Crear ResponseMapper en API**

#### 2.1. Crear ResponseMapper

**Archivo**: `src/api/mappers/response_mapper.py` (nuevo)

**Responsabilidad**: Convertir Entidades de Dominio a Pydantic Models para respuesta

**Métodos principales**:

```python
class ResponseMapper:
    @staticmethod
    def to_system_layout_model(
        silos: List[Silo],
        cages: List[Cage],
        lines: List[FeedingLine]
    ) -> SystemLayoutModel:
        return SystemLayoutModel(
            silos=[ResponseMapper._to_silo_model(s) for s in silos],
            cages=[ResponseMapper._to_cage_model(c) for c in cages],
            feeding_lines=[ResponseMapper._to_feeding_line_model(l) for l in lines]
        )

    @staticmethod
    def _to_silo_model(silo: Silo) -> SiloConfigModel:
        return SiloConfigModel(
            id=str(silo.id),
            name=str(silo.name),
            capacity=silo.capacity.as_kg
        )

    @staticmethod
    def _to_cage_model(cage: Cage) -> CageConfigModel:
        return CageConfigModel(
            id=str(cage.id),
            name=str(cage.name)
        )

    @staticmethod
    def _to_feeding_line_model(line: FeedingLine) -> FeedingLineConfigModel:
        return FeedingLineConfigModel(
            id=str(line.id),
            line_name=str(line.name),
            blower_config=ResponseMapper._to_blower_model(line.blower),
            sensors_config=[ResponseMapper._to_sensor_model(s) for s in line._sensors],
            dosers_config=[ResponseMapper._to_doser_model(d) for d in line.dosers],
            selector_config=ResponseMapper._to_selector_model(line.selector),
            slot_assignments=[ResponseMapper._to_slot_assignment_model(a) for a in line.get_slot_assignments()]
        )

    @staticmethod
    def _to_blower_model(blower: IBlower) -> BlowerConfigModel:
        return BlowerConfigModel(
            id=str(blower.id),
            name=str(blower.name),
            blower_type=blower.__class__.__name__.lower(),
            non_feeding_power=blower.non_feeding_power.value,
            blow_before_time=blower.blow_before_feeding_time.value,
            blow_after_time=blower.blow_after_feeding_time.value
        )

    @staticmethod
    def _to_sensor_model(sensor: ISensor) -> SensorConfigModel:
        return SensorConfigModel(
            id=str(sensor.id),
            name=str(sensor.name),
            sensor_type=sensor.sensor_type.name
        )

    @staticmethod
    def _to_doser_model(doser: IDoser) -> DoserConfigModel:
        return DoserConfigModel(
            id=str(doser.id),
            name=str(doser.name),
            assigned_silo_id=str(doser.assigned_silo_id),
            doser_type=doser.doser_type,
            min_rate=doser.dosing_range.min_rate,
            max_rate=doser.dosing_range.max_rate,
            current_rate=doser.current_rate.value
        )

    @staticmethod
    def _to_selector_model(selector: ISelector) -> SelectorConfigModel:
        return SelectorConfigModel(
            id=str(selector.id),
            name=str(selector.name),
            selector_type=selector.__class__.__name__.lower(),
            capacity=selector.capacity.value,
            fast_speed=selector.speed_profile.fast_speed.value,
            slow_speed=selector.speed_profile.slow_speed.value
        )

    @staticmethod
    def _to_slot_assignment_model(assignment: SlotAssignment) -> SlotAssignmentModel:
        return SlotAssignmentModel(
            slot_number=assignment.slot_number.value,
            cage_id=str(assignment.cage_id)
        )
```

**Notas**:

- Detecta tipo concreto usando `__class__.__name__`
- Convierte Value Objects a tipos primitivos
- Pertenece a la capa API (correcto según Clean Architecture)

---

#### 2.2. Actualizar `__init__.py` de API Mappers

**Archivo**: `src/api/mappers/__init__.py`

**Contenido**:

```python
from .response_mapper import ResponseMapper

__all__ = ['ResponseMapper']
```

---

### **FASE 3: Refactorizar Caso de Uso**

#### 3.1. Inyectar ComponentFactory en el Constructor

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Antes**:

```python
def __init__(self,
             line_repo: IFeedingLineRepository,
             silo_repo: ISiloRepository,
             cage_repo: ICageRepository):
    self.line_repo = line_repo
    self.silo_repo = silo_repo
    self.cage_repo = cage_repo
```

**Después**:

```python
def __init__(self,
             line_repo: IFeedingLineRepository,
             silo_repo: ISiloRepository,
             cage_repo: ICageRepository,
             component_factory: ComponentFactory):
    self.line_repo = line_repo
    self.silo_repo = silo_repo
    self.cage_repo = cage_repo
    self.component_factory = component_factory
```

---

#### 3.2. Cambiar Firma del Método `execute()`

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Antes**:

```python
async def execute(self, request: SystemLayoutDTO) -> SystemLayoutDTO:
```

**Después**:

```python
async def execute(self, request: SystemLayoutModel) -> tuple[List[Silo], List[Cage], List[FeedingLine]]:
```

**Razón**:

- Recibe Pydantic (entrada validada)
- Retorna entidades (dominio puro, sin conocer Pydantic)

---

#### 3.3. Refactorizar Métodos `_build_*_from_dto()` para Usar Factory

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Cambios en cada método**:

**Antes** (`_build_blower_from_dto`):

```python
def _build_blower_from_dto(self, dto: BlowerConfigDTO) -> Blower:
    name = BlowerName(dto.name)
    non_feeding_power = BlowerPowerPercentage(dto.non_feeding_power)
    blow_before_time = BlowDurationInSeconds(dto.blow_before_time)
    blow_after_time = BlowDurationInSeconds(dto.blow_after_time)

    return Blower(
        name=name,
        non_feeding_power=non_feeding_power,
        blow_before_time=blow_before_time,
        blow_after_time=blow_after_time
    )
```

**Después**:

```python
def _build_blower_from_model(self, model: BlowerConfigModel) -> IBlower:
    name = BlowerName(model.name)
    non_feeding_power = BlowerPowerPercentage(model.non_feeding_power)
    blow_before_time = BlowDurationInSeconds(model.blow_before_time)
    blow_after_time = BlowDurationInSeconds(model.blow_after_time)

    return self.component_factory.create_blower(
        blower_type=model.blower_type,
        name=name,
        non_feeding_power=non_feeding_power,
        blow_before_time=blow_before_time,
        blow_after_time=blow_after_time
    )
```

**Aplicar cambios similares a**:

- `_build_blower_from_dto()` → `_build_blower_from_model()` (retorna `IBlower`)
- `_build_sensors_from_dto()` → `_build_sensors_from_model()` (retorna `List[ISensor]`)
- `_build_dosers_from_dto()` → `_build_dosers_from_model()` (retorna `List[IDoser]`)
- `_build_selector_from_dto()` → `_build_selector_from_model()` (retorna `ISelector`)

---

#### 3.4. Actualizar Imports

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Eliminar**:

```python
from application.dtos import (
    SystemLayoutDTO,
    SiloConfigDTO,
    CageConfigDTO,
    FeedingLineConfigDTO,
    BlowerConfigDTO,
    SensorConfigDTO,
    DoserConfigDTO,
    SelectorConfigDTO,
    SlotAssignmentDTO
)
from application.mappers import DomainToDTOMapper
from domain.aggregates.feeding_line.blower import Blower
from domain.aggregates.feeding_line.doser import Doser
from domain.aggregates.feeding_line.selector import Selector
from domain.aggregates.feeding_line.sensor import Sensor
```

**Agregar**:

```python
from typing import List, Tuple
from api.models.system_layout import (
    SystemLayoutModel,
    SiloConfigModel,
    CageConfigModel,
    FeedingLineConfigModel,
    BlowerConfigModel,
    SensorConfigModel,
    DoserConfigModel,
    SelectorConfigModel,
    SlotAssignmentModel
)
from domain.interfaces import IBlower, IDoser, ISelector, ISensor
from domain.factories import ComponentFactory
```

---

#### 3.5. Refactorizar `_rebuild_layout()`

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Antes**:

```python
async def _rebuild_layout(self) -> SystemLayoutDTO:
    all_silos = await self.silo_repo.get_all()
    all_cages = await self.cage_repo.get_all()
    all_lines = await self.line_repo.get_all()

    silos_dtos = [
        DomainToDTOMapper.silo_to_dto(silo)
        for silo in all_silos
    ]

    cages_dtos = [
        DomainToDTOMapper.cage_to_dto(cage)
        for cage in all_cages
    ]

    lines_dtos = [
        DomainToDTOMapper.feeding_line_to_dto(line)
        for line in all_lines
    ]

    return SystemLayoutDTO(
        silos=silos_dtos,
        cages=cages_dtos,
        feeding_lines=lines_dtos
    )
```

**Después**:

```python
async def _rebuild_layout(self) -> Tuple[List[Silo], List[Cage], List[FeedingLine]]:
    all_silos = await self.silo_repo.get_all()
    all_cages = await self.cage_repo.get_all()
    all_lines = await self.line_repo.get_all()

    return (all_silos, all_cages, all_lines)
```

**Razón**: Retorna entidades puras, sin conversión (dominio puro)

---

### **FASE 4: Refactorizar DeltaCalculator**

#### 4.1. Cambiar para Trabajar con Tipos Genéricos (Duck Typing)

**Archivo**: `src/application/services/delta_calculator.py`

**Razón**: `DeltaCalculator` está en la capa de aplicación y NO debe importar Pydantic Models (capa API). Usamos duck typing para acceder a atributos sin dependencia de tipos concretos.

**Antes**:

```python
from application.dtos import SystemLayoutDTO, SiloConfigDTO, ...

@staticmethod
async def calculate(
    request: SystemLayoutDTO,
    line_repo: IFeedingLineRepository,
    silo_repo: ISiloRepository,
    cage_repo: ICageRepository
) -> Delta:
```

**Después**:

```python
from typing import Any

@staticmethod
async def calculate(
    request: Any,  # Acepta cualquier objeto con atributos silos, cages, feeding_lines
    line_repo: IFeedingLineRepository,
    silo_repo: ISiloRepository,
    cage_repo: ICageRepository
) -> Delta:
    # Accede a atributos por nombre (duck typing)
    for silo in request.silos:
        if DeltaCalculator._is_uuid(silo.id):
            ...
```

**Cambios en Delta**:

```python
@dataclass
class Delta:
    silos_to_create: List[Any]      # Objetos con atributos id, name, capacity
    silos_to_update: Dict[SiloId, Any]
    silos_to_delete: Set[SiloId]

    cages_to_create: List[Any]      # Objetos con atributos id, name
    cages_to_update: Dict[CageId, Any]
    cages_to_delete: Set[CageId]

    lines_to_create: List[Any]      # Objetos con atributos id, line_name, etc.
    lines_to_update: Dict[LineId, Any]
    lines_to_delete: Set[LineId]
```

**Nota**: El código funciona igual, solo cambian los tipos. `DeltaCalculator` accede a atributos como `item.id`, `item.name`, etc., sin importar el tipo concreto. Esto mantiene la capa de aplicación independiente de la capa API.

---

### **FASE 5: Refactorizar Capa API**

#### 5.1. Actualizar Router

**Archivo**: `src/api/routers/system_layout.py`

**Antes**:

```python
async def save_system_layout(request: SystemLayoutModel) -> SystemLayoutModel:
    # 1. Pydantic → DTO
    app_dto = SystemLayoutMapper.to_app_dto(request)

    # 2. Ejecutar caso de uso
    result_dto = await use_case.execute(app_dto)

    # 3. DTO → Pydantic
    api_response = SystemLayoutMapper.to_api_model(result_dto)

    return api_response
```

**Después**:

```python
async def save_system_layout(request: SystemLayoutModel) -> SystemLayoutModel:
    # 1. Obtener instancia del caso de uso con Factory
    use_case = get_sync_system_layout_use_case()

    # 2. Ejecutar caso de uso (recibe Pydantic, retorna entidades)
    silos, cages, lines = await use_case.execute(request)

    # 3. Convertir entidades a Pydantic
    response = ResponseMapper.to_system_layout_model(silos, cages, lines)

    return response
```

---

#### 5.2. Actualizar Dependency Injection

**Archivo**: `src/api/routers/system_layout.py`

**Antes**:

```python
def get_sync_system_layout_use_case() -> SyncSystemLayoutUseCase:
    return SyncSystemLayoutUseCase(
        line_repo=_line_repo,
        silo_repo=_silo_repo,
        cage_repo=_cage_repo
    )
```

**Después**:

```python
def get_sync_system_layout_use_case() -> SyncSystemLayoutUseCase:
    return SyncSystemLayoutUseCase(
        line_repo=_line_repo,
        silo_repo=_silo_repo,
        cage_repo=_cage_repo,
        component_factory=ComponentFactory()
    )
```

---

#### 5.3. Actualizar Imports

**Archivo**: `src/api/routers/system_layout.py`

**Eliminar**:

```python
from api.mappers import SystemLayoutMapper
```

**Agregar**:

```python
from api.mappers import ResponseMapper
from domain.factories import ComponentFactory
```

---

### **FASE 6: Limpieza de Archivos Obsoletos**

#### 6.1. Eliminar DTOs

**Archivo**: `src/application/dtos.py`

**Acción**: Eliminar completamente

**Razón**: Redundantes, Pydantic Models son suficientes

---

#### 6.2. Eliminar Mapper de API (entrada)

**Archivo**: `src/api/mappers/system_layout_mapper.py`

**Acción**: Eliminar completamente

**Razón**: Ya no hay conversión Pydantic → DTO (entrada directa)

---

#### 6.3. Eliminar Mapper de Dominio a DTO

**Archivo**: `src/application/mappers/domain_to_dto_mapper.py`

**Acción**: Eliminar completamente

**Razón**: Reemplazado por `ResponseMapper` en API

---

#### 6.4. Eliminar Carpeta de Mappers de Application (si está vacía)

**Carpeta**: `src/application/mappers/`

**Acción**: Eliminar si no contiene otros archivos

---

### **FASE 7: Testing**

#### 7.1. Actualizar Tests del Caso de Uso

**Archivos**: `src/test/application/use_cases/test_sync_*.py`

**Cambios**:

- Usar Pydantic Models en lugar de DTOs
- Inyectar `ComponentFactory` en el caso de uso
- Verificar que retorna tupla de entidades
- Verificar que usa interfaces (`IBlower`, `IDoser`, etc.)

---

#### 7.2. Crear Tests para ComponentFactory

**Archivo**: `src/test/domain/factories/test_component_factory.py` (nuevo)

**Casos de prueba**:

- Creación de cada tipo de componente
- Validación de tipos soportados
- Error cuando el tipo es inválido
- Verificar que retorna interfaces correctas

---

#### 7.3. Crear Tests para ResponseMapper

**Archivo**: `src/test/api/mappers/test_response_mapper.py` (nuevo)

**Casos de prueba**:

- Conversión de entidades a Pydantic Models
- Detección correcta de tipos de componentes
- Serialización de Value Objects

---

#### 7.4. Actualizar Tests de API

**Archivos**: `src/test/api/routers/test_system_layout.py`

**Cambios**:

- Eliminar tests del mapper de entrada (ya no existe)
- Verificar que el endpoint usa `ResponseMapper`

---

### **FASE 8: Documentación**

#### 8.1. Actualizar Documentación del Caso de Uso

**Archivo**: `docs/03-casos-de-uso/UC-01-sincronizar-trazado-sistema.md`

**Agregar**:

- Sección sobre tipos de componentes soportados
- Explicación del uso de `ComponentFactory`
- Diagrama de flujo actualizado (sin DTOs)
- Explicación de que retorna entidades

---

#### 8.2. Documentar ComponentFactory

**Archivo**: `docs/02-dominio/factories.md` (nuevo)

**Contenido**:

- Propósito del factory
- Tipos de componentes soportados
- Cómo agregar nuevos tipos (extensibilidad)
- Ejemplos de uso

---

#### 8.3. Actualizar Arquitectura General

**Archivo**: `docs/README.md`

**Cambios**:

- Actualizar diagrama de capas (eliminar capa DTO)
- Documentar flujo simplificado
- Explicar por qué se eliminaron los DTOs
- Documentar `ResponseMapper` en API

---

## ✅ Checklist de Implementación

### Fase 1: Preparación ✅

- [x] 1.1. Crear `ComponentFactory`
- [x] 1.2. Actualizar Pydantic Models con campos de tipo

### Fase 2: ResponseMapper

- [ ] 2.1. Crear `ResponseMapper` en API
- [ ] 2.2. Actualizar `__init__.py` de API mappers

### Fase 3: Caso de Uso

- [ ] 3.1. Inyectar `ComponentFactory` en constructor
- [ ] 3.2. Cambiar firma de `execute()` (retorna entidades)
- [ ] 3.3. Refactorizar métodos `_build_*` para usar Factory
- [ ] 3.4. Actualizar imports
- [ ] 3.5. Refactorizar `_rebuild_layout()` (retorna entidades)

### Fase 4: DeltaCalculator

- [ ] 4.1. Cambiar para trabajar con Pydantic Models

### Fase 5: Capa API

- [ ] 5.1. Actualizar router (usar ResponseMapper)
- [ ] 5.2. Actualizar dependency injection
- [ ] 5.3. Actualizar imports

### Fase 6: Limpieza

- [ ] 6.1. Eliminar `application/dtos.py`
- [ ] 6.2. Eliminar `api/mappers/system_layout_mapper.py`
- [ ] 6.3. Eliminar `application/mappers/domain_to_dto_mapper.py`
- [ ] 6.4. Eliminar carpeta `application/mappers/` (si vacía)

### Fase 7: Testing

- [ ] 7.1. Actualizar tests del caso de uso
- [ ] 7.2. Crear tests para `ComponentFactory`
- [ ] 7.3. Crear tests para `ResponseMapper`
- [ ] 7.4. Actualizar tests de API

### Fase 8: Documentación

- [ ] 8.1. Actualizar UC-01
- [ ] 8.2. Documentar `ComponentFactory`
- [ ] 8.3. Actualizar arquitectura general

---

## 🚨 Consideraciones Importantes

### 1. Clean Architecture Respetada ✅

**Caso de uso NO conoce Pydantic para salida**:

- Recibe Pydantic (entrada validada - aceptable)
- Retorna entidades (dominio puro)
- API convierte entidades a Pydantic (responsabilidad correcta)

**DeltaCalculator NO depende de tipos de API**:

- Usa `Any` (duck typing) para no importar Pydantic Models
- Accede a atributos por nombre sin dependencia de tipos concretos
- Mantiene la capa de aplicación independiente de la capa API

### 2. Separación de Responsabilidades

- **API**: Validación entrada + Serialización salida
- **Application**: Orquestación + Construcción (sin conocer tipos de API)
- **Domain**: Lógica de negocio pura

### 3. Extensibilidad Futura

Cuando se agreguen `VariDoser`, `PulseDoser`, etc.:

- Solo modificar `ComponentFactory`
- `ResponseMapper` detecta tipo automáticamente (`__class__.__name__`)
- El resto del sistema no cambia

### 4. Testing

- Caso de uso retorna entidades (fácil de testear)
- `ResponseMapper` testeable independientemente
- Sin acoplamiento entre capas

---

## 📊 Impacto Estimado

| Componente     | Archivos Nuevos | Archivos Modificados | Archivos Eliminados | Complejidad |
| -------------- | --------------- | -------------------- | ------------------- | ----------- |
| Factories      | 0               | 0                    | 0                   | - ✅        |
| ResponseMapper | 1               | 1                    | 0                   | Media       |
| Caso de Uso    | 0               | 1                    | 0                   | Media       |
| Servicios      | 0               | 1                    | 0                   | Baja        |
| API            | 0               | 1                    | 1                   | Baja        |
| DTOs           | 0               | 0                    | 1                   | Baja        |
| Mappers        | 0               | 0                    | 2                   | Baja        |
| Tests          | 2               | 5-10                 | 0                   | Media       |
| Docs           | 2               | 2                    | 0                   | Baja        |
| **TOTAL**      | **5**           | **11-16**            | **4**               | **Media**   |

**Tiempo estimado**: 10-12 horas de desarrollo + 3-4 horas de testing

---

## 🎯 Resultado Esperado

Después de la migración:

1. ✅ Caso de uso depende de abstracciones (`IBlower`, `IDoser`, etc.)
2. ✅ Eliminada capa DTO redundante
3. ✅ Clean Architecture respetada (caso de uso retorna entidades)
4. ✅ Fácil agregar nuevos tipos de componentes (polimorfismo)
5. ✅ Separación clara de responsabilidades
6. ✅ Código más testeable y mantenible

---

## 🔄 Diagrama de Flujo Final

```
┌─────────────────────────────────────────────────────────────┐
│                         REQUEST                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Pydantic Model  │ (API Layer - Validación)
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Use Case       │ (Application Layer)
                    │  - Orquestación  │
                    │  - Usa Factory   │
                    │  - Crea entidades│
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    Entidades     │ (Domain Layer)
                    │  (Silo, Cage,    │
                    │  FeedingLine con │
                    │  IBlower, IDoser)│
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Repositorios   │ (Infrastructure)
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    Entidades     │ (Domain Layer)
                    │   (resultado)    │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Use Case       │ (Application Layer)
                    │  - Retorna       │
                    │    entidades     │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ ResponseMapper   │ (API Layer)
                    │  - Entidades →   │
                    │    Pydantic      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Pydantic Model  │ (API Layer - Serialización)
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         RESPONSE                             │
└─────────────────────────────────────────────────────────────┘
```

---

**Próximos pasos**: Implementar Fase 2 (crear ResponseMapper) y validar con tests.
