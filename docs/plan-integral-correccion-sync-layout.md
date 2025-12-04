# Plan Integral de Corrección: SyncSystemLayoutUseCase y Componentes

## 1. Análisis Completo del Sistema

### 1.1 Flujo Completo Request → Response

```
Frontend
   ↓ POST /system-layout
   ↓ SystemLayoutModel (Pydantic)
   ↓
Router (system_layout.py)
   ↓ use_case.execute(request)
   ↓
SyncSystemLayoutUseCase
   ├→ DeltaCalculator.calculate()  ← OK
   ├→ NameValidator.*              ← OK
   ├→ ResourceReleaser.release()   ← ❌ ROTO
   ├→ _create_*                    ← ❌ ROTO
   └→ _update_*                    ← ❌ ROTO
   ↓
Domain Layer (Repositories, Aggregates)
   ↓ (silos, cages, lines)
   ↓
ResponseMapper.to_system_layout_model()  ← ❌ ROTO
   ↓ SystemLayoutModel
   ↓
Frontend
```

### 1.2 Archivos Afectados por la Refactorización

| Archivo | Estado | Problema Principal |
|---------|--------|-------------------|
| `sync_system_layout.py` | ❌ ROTO | Usa `line.assign_cage_to_slot()` eliminado |
| `resource_releaser.py` | ❌ ROTO | Usa `line.get_slot_assignments()` eliminado |
| `response_mapper.py` | ❌ ROTO | Usa `SlotAssignment` y `line.get_slot_assignments()` eliminados |
| `delta_calculator.py` | ✅ OK | No depende de SlotAssignment |
| `name_validator.py` | ✅ OK | No depende de SlotAssignment |
| `system_layout.py` (models) | ✅ OK | Mantener para compatibilidad frontend |
| `system_layout.py` (router) | ✅ OK | No requiere cambios |
| `dependencies.py` | ✅ OK | No requiere cambios |

---

## 2. Problemas Detallados por Archivo

### 2.1 ResourceReleaser (`application/services/resource_releaser.py`)

#### Problema Actual

**Líneas 26-34:**
```python
async def _release_cages_from_line(
    line: FeedingLine,
    cage_repo: ICageRepository
) -> None:
    """Libera todas las jaulas asignadas a una línea."""
    old_assignments = line.get_slot_assignments()  # ❌ ELIMINADO
    for old_assignment in old_assignments:
        old_cage = await cage_repo.find_by_id(old_assignment.cage_id)  # ❌ SlotAssignment eliminado
        if old_cage:
            from domain.enums import CageStatus
            old_cage.status = CageStatus.AVAILABLE
            await cage_repo.save(old_cage)
            # ⚠️ Comentario dice "referencias se limpian en el repositorio" - FALSO
```

**Problemas:**
1. ❌ `line.get_slot_assignments()` fue eliminado en Fase 1
2. ❌ `old_assignment` es `SlotAssignment` que ya no existe
3. ⚠️ El código NO limpia `line_id` y `slot_number` de la cage

---

### 2.2 ResponseMapper (`api/mappers/response_mapper.py`)

#### Problema Actual

**Línea 18:**
```python
from domain.value_objects import SlotAssignment  # ❌ ELIMINADO
```

**Línea 60:**
```python
slot_assignments=[
    ResponseMapper._to_slot_assignment_model(a)
    for a in line.get_slot_assignments()  # ❌ ELIMINADO
]
```

**Líneas 114-118:**
```python
@staticmethod
def _to_slot_assignment_model(assignment: SlotAssignment) -> SlotAssignmentModel:  # ❌ SlotAssignment eliminado
    return SlotAssignmentModel(
        slot_number=assignment.slot_number.value,  # ❌ SlotNumber eliminado
        cage_id=str(assignment.cage_id)
    )
```

**Problemas:**
1. ❌ Importa `SlotAssignment` eliminado
2. ❌ Llama a `line.get_slot_assignments()` eliminado
3. ❌ Método `_to_slot_assignment_model()` usa entidades eliminadas

**Solución Correcta:**
- ✅ El mapper debe recibir TODOS los datos que necesita como parámetros
- ✅ NO debe hacer I/O (consultas a repositorio)
- ✅ Filtrar cages en memoria por `line_id`
- ✅ Mantener el mapper como transformación pura y síncrona

---

### 2.3 SyncSystemLayoutUseCase (Ya identificados)

**Problemas principales:**
1. ❌ Importa `SlotNumber`, `SlotAssignment` (línea 34)
2. ❌ Usa `line.assign_cage_to_slot()` en creación (línea 296)
3. ❌ Usa `SlotAssignment`, `line.update_assignments()` en actualización (líneas 373-394)

---

## 3. Arquitectura Correcta: Cage-Line Relationship

### 3.1 Modelo de Dominio (NUEVO)

```
┌─────────────────────┐
│   FeedingLine       │
│ - id: LineId        │
│ - name: LineName    │
│ - components        │
│ (SIN slot_assignments) │
└─────────────────────┘
         ▲
         │
         │ line_id
         │
┌─────────────────────┐
│      Cage           │
│ - id: CageId        │
│ - name: CageName    │
│ - line_id: Optional[LineId]     │ ← Referencia directa
│ - slot_number: Optional[int]    │ ← Atributo directo
│ - status: CageStatus            │
├─────────────────────┤
│ + assign_to_line(line_id, slot) │
│ + unassign_from_line()          │
└─────────────────────┘
```

### 3.2 Operaciones Clave

#### Asignar Cage a Línea
```python
# ❌ ANTES (OBSOLETO)
line.assign_cage_to_slot(slot_number, cage_id)

# ✅ AHORA (CORRECTO)
await line_repo.save(line)  # Primero guardar línea
cage.assign_to_line(line.id, slot_number)  # Asignar cage
await cage_repo.save(cage)
```

#### Desasignar Cage de Línea
```python
# ❌ ANTES (OBSOLETO)
line.remove_assignment_from_slot(slot_number)

# ✅ AHORA (CORRECTO)
cage.unassign_from_line()
cage.status = CageStatus.AVAILABLE
await cage_repo.save(cage)
```

#### Obtener Cages de una Línea
```python
# ❌ ANTES (OBSOLETO)
assignments = line.get_slot_assignments()
for assignment in assignments:
    cage = await cage_repo.find_by_id(assignment.cage_id)

# ✅ AHORA (CORRECTO)
cages = await cage_repo.find_by_line_id(line.id)
for cage in cages:
    # cage.slot_number está disponible directamente
```

---

## 4. Plan de Corrección Detallado

### FASE 1: Corregir ResourceReleaser

#### Tarea 1.1: Refactorizar `_release_cages_from_line()`

**Archivo:** `src/application/services/resource_releaser.py`

**ANTES (líneas 20-34):**
```python
@staticmethod
async def _release_cages_from_line(
    line: FeedingLine,
    cage_repo: ICageRepository
) -> None:
    """Libera todas las jaulas asignadas a una línea."""
    old_assignments = line.get_slot_assignments()  # ❌
    for old_assignment in old_assignments:
        old_cage = await cage_repo.find_by_id(old_assignment.cage_id)  # ❌
        if old_cage:
            from domain.enums import CageStatus
            old_cage.status = CageStatus.AVAILABLE
            await cage_repo.save(old_cage)
```

**DESPUÉS:**
```python
@staticmethod
async def _release_cages_from_line(
    line: FeedingLine,
    cage_repo: ICageRepository
) -> None:
    """Libera todas las jaulas asignadas a una línea."""
    # ✅ Obtener cages directamente del repositorio
    cages = await cage_repo.find_by_line_id(line.id)

    for cage in cages:
        # ✅ Usar método de dominio para desasignar
        cage.unassign_from_line()

        # ✅ Cambiar estado a AVAILABLE
        from domain.enums import CageStatus
        cage.status = CageStatus.AVAILABLE

        await cage_repo.save(cage)
```

**Cambios clave:**
1. ✅ Usar `cage_repo.find_by_line_id()` en lugar de `line.get_slot_assignments()`
2. ✅ Llamar a `cage.unassign_from_line()` para limpiar `line_id` y `slot_number`
3. ✅ Cambiar estado a `AVAILABLE`

---

### FASE 2: Corregir ResponseMapper

#### Tarea 2.1: Eliminar import obsoleto

**Archivo:** `src/api/mappers/response_mapper.py`

**Línea 18 - ELIMINAR:**
```python
from domain.value_objects import SlotAssignment  # ❌ ELIMINAR
```

#### Tarea 2.2: Refactorizar `_to_feeding_line_model()` - Filtrado en memoria

**ANTES (líneas 51-61):**
```python
@staticmethod
def _to_feeding_line_model(line: FeedingLine) -> FeedingLineConfigModel:
    return FeedingLineConfigModel(
        id=str(line.id),
        line_name=str(line.name),
        blower_config=ResponseMapper._to_blower_model(line.blower),
        sensors_config=[ResponseMapper._to_sensor_model(s) for s in line._sensors],
        dosers_config=[ResponseMapper._to_doser_model(d) for d in line.dosers],
        selector_config=ResponseMapper._to_selector_model(line.selector),
        slot_assignments=[ResponseMapper._to_slot_assignment_model(a) for a in line.get_slot_assignments()]  # ❌
    )
```

**DESPUÉS:**
```python
@staticmethod
def _to_feeding_line_model(
    line: FeedingLine,
    all_cages: List[Cage]  # ✅ Recibir todas las cages como parámetro
) -> FeedingLineConfigModel:
    # ✅ Filtrar cages que pertenecen a esta línea (en memoria)
    line_cages = [c for c in all_cages if c.line_id == line.id]

    # ✅ Ordenar por slot_number para consistencia
    line_cages_sorted = sorted(line_cages, key=lambda c: c.slot_number or 0)

    return FeedingLineConfigModel(
        id=str(line.id),
        line_name=str(line.name),
        blower_config=ResponseMapper._to_blower_model(line.blower),
        sensors_config=[ResponseMapper._to_sensor_model(s) for s in line._sensors],
        dosers_config=[ResponseMapper._to_doser_model(d) for d in line.dosers],
        selector_config=ResponseMapper._to_selector_model(line.selector),
        slot_assignments=[
            ResponseMapper._to_slot_assignment_model(cage)  # ✅ Pasar Cage directamente
            for cage in line_cages_sorted
        ]
    )
```

**Cambios clave:**
1. ✅ Recibe `all_cages: List[Cage]` como parámetro (no hace I/O)
2. ✅ Filtra en memoria las cages con `c.line_id == line.id`
3. ✅ Mantiene el método **síncrono** y **puro** (sin consultas a BD)
4. ✅ Ordena por `slot_number` para respuesta consistente

#### Tarea 2.3: Actualizar `to_system_layout_model()` para pasar cages

**ANTES:**
```python
@staticmethod
def to_system_layout_model(
    silos: List[Silo],
    cages: List[Cage],
    lines: List[FeedingLine]
) -> SystemLayoutModel:
    return SystemLayoutModel(
        silos=[ResponseMapper._to_silo_model(s) for s in silos],
        cages=[ResponseMapper._to_cage_model(c) for c in cages],
        feeding_lines=[ResponseMapper._to_feeding_line_model(line) for line in lines]  # ❌
    )
```

**DESPUÉS:**
```python
@staticmethod
def to_system_layout_model(
    silos: List[Silo],
    cages: List[Cage],
    lines: List[FeedingLine]
) -> SystemLayoutModel:
    return SystemLayoutModel(
        silos=[ResponseMapper._to_silo_model(s) for s in silos],
        cages=[ResponseMapper._to_cage_model(c) for c in cages],
        feeding_lines=[
            ResponseMapper._to_feeding_line_model(line, cages)  # ✅ Pasar todas las cages
            for line in lines
        ]
    )
```

**Cambios clave:**
1. ✅ Mantiene firma original (sin cambios para el router)
2. ✅ Pasa `cages` a `_to_feeding_line_model()` para filtrado en memoria
3. ✅ Método sigue siendo síncrono

#### Tarea 2.4: Refactorizar `_to_slot_assignment_model()`

**ANTES (líneas 113-118):**
```python
@staticmethod
def _to_slot_assignment_model(assignment: SlotAssignment) -> SlotAssignmentModel:  # ❌
    return SlotAssignmentModel(
        slot_number=assignment.slot_number.value,  # ❌
        cage_id=str(assignment.cage_id)
    )
```

**DESPUÉS:**
```python
@staticmethod
def _to_slot_assignment_model(cage: Cage) -> SlotAssignmentModel:
    """Mapea Cage a SlotAssignmentModel para compatibilidad con frontend."""
    if cage.slot_number is None:
        raise ValueError(f"Cage {cage.id} no tiene slot_number asignado")

    return SlotAssignmentModel(
        slot_number=cage.slot_number,  # ✅ Ya es int
        cage_id=str(cage.id)
    )
```

**Cambios clave:**
1. ✅ Recibe `Cage` en lugar de `SlotAssignment`
2. ✅ Usa `cage.slot_number` directamente (ya es `int`)
3. ✅ Valida que `slot_number` no sea `None`

---

### FASE 3: Corregir SyncSystemLayoutUseCase

#### Tarea 3.1: Eliminar imports obsoletos

**Archivo:** `src/application/use_cases/sync_system_layout.py`

**Línea 34 - ANTES:**
```python
from domain.value_objects import (
    LineId, LineName,
    SiloId, SiloName, Weight,
    CageId, CageName,
    BlowerName, BlowerPowerPercentage, BlowDurationInSeconds,
    DoserName, DosingRange, DosingRate,
    SelectorName, SelectorCapacity, SelectorSpeedProfile,
    SensorName,
    SlotNumber, SlotAssignment  # ❌ ELIMINAR
)
```

**Línea 34 - DESPUÉS:**
```python
from domain.value_objects import (
    LineId, LineName,
    SiloId, SiloName, Weight,
    CageId, CageName,
    BlowerName, BlowerPowerPercentage, BlowDurationInSeconds,
    DoserName, DosingRange, DosingRate,
    SelectorName, SelectorCapacity, SelectorSpeedProfile,
    SensorName
)
```

#### Tarea 3.2: Refactorizar `_create_feeding_lines()`

**ANTES (líneas 260-299):**
```python
async def _create_feeding_lines(self, lines_dtos, id_map: Dict[str, Any]) -> None:
    for dto in lines_dtos:
        # ... validaciones y creación de componentes ...

        new_line = FeedingLine.create(...)

        for slot_dto in dto.slot_assignments:
            cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
            cage = await self.cage_repo.find_by_id(cage_id)
            if cage:
                if cage.status != CageStatus.AVAILABLE:
                    raise CageNotAvailableException(...)
                cage.status = CageStatus.IN_USE
                await self.cage_repo.save(cage)

            new_line.assign_cage_to_slot(slot_dto.slot_number, cage_id)  # ❌

        await self.line_repo.save(new_line)
        id_map[dto.id] = new_line.id
```

**DESPUÉS:**
```python
async def _create_feeding_lines(self, lines_dtos, id_map: Dict[str, Any]) -> None:
    for dto in lines_dtos:
        await NameValidator.validate_unique_line_name(
            dto.line_name, exclude_id=None, repo=self.line_repo
        )

        # ✅ Validar capacidad del selector vs número de slots
        if len(dto.slot_assignments) > dto.selector_config.capacity:
            raise ValueError(
                f"La línea '{dto.line_name}' tiene {len(dto.slot_assignments)} slots "
                f"pero el selector solo tiene capacidad para {dto.selector_config.capacity}"
            )

        blower = self._build_blower_from_model(dto.blower_config)
        sensors = self._build_sensors_from_model(dto.sensors_config)
        dosers = await self._build_dosers_from_model(dto.dosers_config, id_map)
        selector = self._build_selector_from_model(dto.selector_config)

        new_line = FeedingLine.create(
            name=LineName(dto.line_name),
            blower=blower,
            dosers=dosers,
            selector=selector,
            sensors=sensors
        )

        # ✅ PASO 1: Guardar línea PRIMERO (necesitamos line_id)
        await self.line_repo.save(new_line)
        id_map[dto.id] = new_line.id

        # ✅ PASO 2: Asignar cages a la línea
        for slot_dto in dto.slot_assignments:
            # Validar que el slot_number esté en el rango válido
            if slot_dto.slot_number < 1 or slot_dto.slot_number > selector.capacity.value:
                raise ValueError(
                    f"El slot {slot_dto.slot_number} está fuera del rango válido "
                    f"(1-{selector.capacity.value}) para la línea '{dto.line_name}'"
                )

            cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
            cage = await self.cage_repo.find_by_id(cage_id)

            if not cage:
                raise ValueError(f"La jaula con ID '{slot_dto.cage_id}' no existe")

            # Validar que la jaula esté disponible
            if cage.status != CageStatus.AVAILABLE:
                raise CageNotAvailableException(
                    f"La jaula '{cage.name}' no está disponible (estado: {cage.status.value})"
                )

            # Validar que no haya otra cage en el mismo slot (slot duplicado)
            existing_cage = await self.cage_repo.find_by_line_and_slot(
                new_line.id, slot_dto.slot_number
            )
            if existing_cage:
                raise ValueError(
                    f"El slot {slot_dto.slot_number} ya está ocupado por la jaula '{existing_cage.name}'"
                )

            # ✅ Asignar cage usando método del dominio
            cage.assign_to_line(new_line.id, slot_dto.slot_number)
            cage.status = CageStatus.IN_USE
            await self.cage_repo.save(cage)
```

**Cambios clave:**
1. ✅ Validar capacidad del selector ANTES de crear
2. ✅ Guardar línea ANTES de asignar cages
3. ✅ Validar slot_number en rango válido [1, capacity]
4. ✅ Usar `cage.assign_to_line()` en lugar de método de línea
5. ✅ Validar slot duplicado con repositorio
6. ✅ Mantener gestión de estados

#### Tarea 3.3: Refactorizar `_update_feeding_lines()`

**ANTES (líneas 341-395):**
```python
async def _update_feeding_lines(self, lines_to_update, id_map: Dict[str, Any]) -> None:
    # Liberar recursos
    lines_to_release = []
    for line_id in lines_to_update.keys():
        line = await self.line_repo.find_by_id(line_id)
        if line:
            lines_to_release.append(line)

    await ResourceReleaser.release_all_from_lines(
        lines_to_release, self.silo_repo, self.cage_repo
    )

    # Reasignar recursos
    for line_id, dto in lines_to_update.items():
        line = await self.line_repo.find_by_id(line_id)
        if not line:
            continue

        # ... validaciones y actualización de componentes ...

        line.update_components(blower, dosers, selector, sensors)

        # ❌ ESTO ESTÁ MAL
        new_assignments: List[SlotAssignment] = []
        for slot_dto in dto.slot_assignments:
            cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
            # ...
            slot_number = SlotNumber(slot_dto.slot_number)  # ❌
            assignment = SlotAssignment(slot_number, cage_id)  # ❌
            new_assignments.append(assignment)

        line.update_assignments(new_assignments)  # ❌
        await self.line_repo.save(line)
```

**DESPUÉS:**
```python
async def _update_feeding_lines(self, lines_to_update, id_map: Dict[str, Any]) -> None:
    # ✅ Liberar recursos (ResourceReleaser ya actualizado en Fase 1)
    lines_to_release = []
    for line_id in lines_to_update.keys():
        line = await self.line_repo.find_by_id(line_id)
        if line:
            lines_to_release.append(line)

    await ResourceReleaser.release_all_from_lines(
        lines_to_release, self.silo_repo, self.cage_repo
    )

    # ✅ Reasignar recursos
    for line_id, dto in lines_to_update.items():
        line = await self.line_repo.find_by_id(line_id)
        if not line:
            continue

        # Validar nombre único si cambió
        if str(line.name) != dto.line_name:
            await NameValidator.validate_unique_line_name(
                dto.line_name, exclude_id=line_id, repo=self.line_repo
            )
            line.name = LineName(dto.line_name)

        # ✅ Validar capacidad del selector
        if len(dto.slot_assignments) > dto.selector_config.capacity:
            raise ValueError(
                f"La línea '{dto.line_name}' tiene {len(dto.slot_assignments)} slots "
                f"pero el selector solo tiene capacidad para {dto.selector_config.capacity}"
            )

        # Actualizar componentes
        blower = self._build_blower_from_model(dto.blower_config)
        sensors = self._build_sensors_from_model(dto.sensors_config)
        dosers = await self._build_dosers_from_model(dto.dosers_config, id_map)
        selector = self._build_selector_from_model(dto.selector_config)

        line.update_components(blower, dosers, selector, sensors)
        await self.line_repo.save(line)

        # ✅ Asignar nuevas cages (ResourceReleaser ya liberó las anteriores)
        for slot_dto in dto.slot_assignments:
            # Validar que el slot_number esté en el rango válido
            if slot_dto.slot_number < 1 or slot_dto.slot_number > selector.capacity.value:
                raise ValueError(
                    f"El slot {slot_dto.slot_number} está fuera del rango válido "
                    f"(1-{selector.capacity.value}) para la línea '{dto.line_name}'"
                )

            cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
            cage = await self.cage_repo.find_by_id(cage_id)

            if not cage:
                raise ValueError(f"La jaula con ID '{slot_dto.cage_id}' no existe")

            # Validar disponibilidad
            if cage.status != CageStatus.AVAILABLE:
                raise CageNotAvailableException(
                    f"La jaula '{cage.name}' no está disponible (estado: {cage.status.value})"
                )

            # Validar slot no duplicado
            existing_cage = await self.cage_repo.find_by_line_and_slot(
                line_id, slot_dto.slot_number
            )
            if existing_cage and existing_cage.id != cage_id:
                raise ValueError(
                    f"El slot {slot_dto.slot_number} ya está ocupado por '{existing_cage.name}'"
                )

            # ✅ Asignar usando método del dominio
            cage.assign_to_line(line_id, slot_dto.slot_number)
            cage.status = CageStatus.IN_USE
            await self.cage_repo.save(cage)
```

**Cambios clave:**
1. ✅ ResourceReleaser ya libera cages correctamente (Fase 1)
2. ✅ Validar capacidad del selector
3. ✅ Actualizar componentes primero
4. ✅ Validar slot_number en rango válido [1, capacity]
5. ✅ Asignar cages después con `cage.assign_to_line()`
6. ✅ Validaciones completas

---

## 5. Orden de Ejecución

### Secuencia Recomendada:

1. **✅ FASE 1** - Corregir ResourceReleaser
   - Tarea 1.1: Refactorizar `_release_cages_from_line()`

2. **✅ FASE 2** - Corregir ResponseMapper
   - Tarea 2.1: Eliminar import obsoleto
   - Tarea 2.2: Refactorizar `_to_feeding_line_model()` para filtrar cages en memoria
   - Tarea 2.3: Actualizar `to_system_layout_model()` para pasar cages
   - Tarea 2.4: Refactorizar `_to_slot_assignment_model()` para recibir Cage

3. **✅ FASE 3** - Corregir SyncSystemLayoutUseCase
   - Tarea 3.1: Eliminar imports obsoletos
   - Tarea 3.2: Refactorizar `_create_feeding_lines()`
   - Tarea 3.3: Refactorizar `_update_feeding_lines()`

4. **✅ TESTING** - Validación integral

**Razón del orden:**
- ResourceReleaser primero (es dependencia crítica del flujo de actualización)
- ResponseMapper en medio (no depende de otros cambios, transformación pura)
- SyncSystemLayoutUseCase al final (usa ResourceReleaser y es el componente principal)

---

## 6. Testing Integral

### 6.1 Test de Creación de Línea

```python
async def test_create_line_with_cages():
    # DADO: 2 cages disponibles
    cage1 = Cage(name=CageName("C1"))
    cage2 = Cage(name=CageName("C2"))
    await cage_repo.save(cage1)
    await cage_repo.save(cage2)

    # CUANDO: Crear línea con ambas cages
    request = SystemLayoutModel(
        silos=[...],
        cages=[
            CageConfigModel(id=str(cage1.id), name="C1"),
            CageConfigModel(id=str(cage2.id), name="C2")
        ],
        feeding_lines=[
            FeedingLineConfigModel(
                id="temp-1",
                line_name="L1",
                # ... componentes ...
                slot_assignments=[
                    SlotAssignmentModel(slot_number=1, cage_id=str(cage1.id)),
                    SlotAssignmentModel(slot_number=2, cage_id=str(cage2.id))
                ]
            )
        ]
    )

    silos, cages, lines = await use_case.execute(request)

    # ENTONCES:
    assert len(lines) == 1
    line = lines[0]

    # Verificar que las cages están asignadas
    cages_in_line = await cage_repo.find_by_line_id(line.id)
    assert len(cages_in_line) == 2

    cage1_updated = await cage_repo.find_by_id(cage1.id)
    assert cage1_updated.line_id == line.id
    assert cage1_updated.slot_number == 1
    assert cage1_updated.status == CageStatus.IN_USE

    cage2_updated = await cage_repo.find_by_id(cage2.id)
    assert cage2_updated.line_id == line.id
    assert cage2_updated.slot_number == 2
    assert cage2_updated.status == CageStatus.IN_USE
```

### 6.2 Test de Actualización de Línea

```python
async def test_update_line_change_cages():
    # DADO: Línea L1 con C1, C2 asignadas
    line = await create_line_with_cages([cage1, cage2])
    cage3 = await create_cage("C3")

    # CUANDO: Actualizar L1: quitar C2, agregar C3
    request = SystemLayoutModel(
        silos=[...],
        cages=[...],
        feeding_lines=[
            FeedingLineConfigModel(
                id=str(line.id),  # UUID real
                line_name="L1",
                # ... componentes ...
                slot_assignments=[
                    SlotAssignmentModel(slot_number=1, cage_id=str(cage1.id)),
                    SlotAssignmentModel(slot_number=2, cage_id=str(cage3.id))
                ]
            )
        ]
    )

    await use_case.execute(request)

    # ENTONCES:
    # C1 sigue asignada
    cage1_updated = await cage_repo.find_by_id(cage1.id)
    assert cage1_updated.line_id == line.id
    assert cage1_updated.status == CageStatus.IN_USE

    # C2 fue liberada
    cage2_updated = await cage_repo.find_by_id(cage2.id)
    assert cage2_updated.line_id is None
    assert cage2_updated.slot_number is None
    assert cage2_updated.status == CageStatus.AVAILABLE

    # C3 fue asignada
    cage3_updated = await cage_repo.find_by_id(cage3.id)
    assert cage3_updated.line_id == line.id
    assert cage3_updated.slot_number == 2
    assert cage3_updated.status == CageStatus.IN_USE
```

### 6.3 Test de Validaciones

```python
async def test_validation_slot_duplicado():
    # DADO: Línea L1 con C1 en slot 1
    line = await create_line_with_cage(cage1, slot=1)

    # CUANDO: Intentar asignar C2 al mismo slot
    request = SystemLayoutModel(
        # ... línea con 2 cages en slot 1 ...
    )

    # ENTONCES: Debe lanzar error
    with pytest.raises(ValueError, match="El slot 1 ya está ocupado"):
        await use_case.execute(request)

async def test_validation_capacidad_selector():
    # CUANDO: Crear línea con selector capacidad=2 y 3 cages
    request = SystemLayoutModel(
        # ... selector.capacity=2, 3 slot_assignments ...
    )

    # ENTONCES: Debe lanzar error
    with pytest.raises(ValueError, match="excede la capacidad del selector"):
        await use_case.execute(request)

async def test_validation_slot_fuera_de_rango():
    # CUANDO: Crear línea con selector capacidad=8 y slot_number=10
    request = SystemLayoutModel(
        feeding_lines=[
            FeedingLineConfigModel(
                selector_config=SelectorConfigModel(capacity=8),
                slot_assignments=[
                    SlotAssignmentModel(slot_number=10, cage_id="...")  # Fuera de rango
                ]
            )
        ]
    )

    # ENTONCES: Debe lanzar error
    with pytest.raises(ValueError, match="está fuera del rango válido"):
        await use_case.execute(request)

async def test_validation_cage_no_disponible():
    # DADO: Cage C1 en estado IN_USE (asignada a L1)
    # CUANDO: Intentar asignar C1 a L2
    # ENTONCES: Debe lanzar CageNotAvailableException
```

### 6.4 Test de ResponseMapper

```python
async def test_response_mapper_slot_assignments():
    # DADO: Línea L1 con C1 y C2 asignadas
    line = await create_line_with_cages([
        (cage1, slot=1),
        (cage2, slot=3),  # Slots no consecutivos
    ])

    # Cargar todas las cages desde BD
    all_cages = await cage_repo.list_all()

    # CUANDO: Mapear a modelo de API (método síncrono)
    model = ResponseMapper.to_system_layout_model(
        silos=[],
        cages=all_cages,  # ✅ Pasar todas las cages
        lines=[line]
    )

    # ENTONCES: slot_assignments debe tener las asignaciones correctas
    line_model = model.feeding_lines[0]
    assert len(line_model.slot_assignments) == 2

    # Ordenados por slot_number
    assert line_model.slot_assignments[0].slot_number == 1
    assert line_model.slot_assignments[0].cage_id == str(cage1.id)

    assert line_model.slot_assignments[1].slot_number == 3
    assert line_model.slot_assignments[1].cage_id == str(cage2.id)
```

---

## 7. Checklist Final

### Pre-Implementación
- [ ] Plan revisado y aprobado
- [ ] Entendimiento claro de todos los cambios
- [ ] Backup de código actual

### Implementación - Fase 1
- [ ] ResourceReleaser refactorizado
- [ ] Usa `cage_repo.find_by_line_id()`
- [ ] Llama a `cage.unassign_from_line()`
- [ ] Cambia estado a `AVAILABLE`

### Implementación - Fase 2
- [ ] ResponseMapper: import de SlotAssignment eliminado
- [ ] ResponseMapper: `_to_feeding_line_model()` recibe `all_cages` como parámetro
- [ ] ResponseMapper: Filtra cages en memoria por `line_id`
- [ ] ResponseMapper: `to_system_layout_model()` pasa `cages` al helper
- [ ] ResponseMapper: `_to_slot_assignment_model()` recibe Cage
- [ ] ResponseMapper: Método permanece síncrono (sin I/O)

### Implementación - Fase 3
- [ ] SyncSystemLayoutUseCase: imports eliminados
- [ ] `_create_feeding_lines()`: refactorizado
- [ ] `_create_feeding_lines()`: valida capacidad total del selector
- [ ] `_create_feeding_lines()`: valida slot_number en rango [1, capacity]
- [ ] `_create_feeding_lines()`: valida slot duplicado
- [ ] `_create_feeding_lines()`: usa `cage.assign_to_line()`
- [ ] `_update_feeding_lines()`: refactorizado
- [ ] `_update_feeding_lines()`: valida capacidad total del selector
- [ ] `_update_feeding_lines()`: valida slot_number en rango [1, capacity]
- [ ] `_update_feeding_lines()`: valida slot duplicado
- [ ] `_update_feeding_lines()`: usa `cage.assign_to_line()`

### Testing
- [ ] Test: Crear línea con cages - PASS
- [ ] Test: Actualizar línea - PASS
- [ ] Test: Validación slot duplicado - PASS
- [ ] Test: Validación capacidad total del selector - PASS
- [ ] Test: Validación slot_number fuera de rango - PASS
- [ ] Test: Validación cage no disponible - PASS
- [ ] Test: ResponseMapper - PASS
- [ ] Test: Eliminar línea libera cages - PASS

### Validación Final
- [ ] Código compila sin errores
- [ ] No hay referencias a SlotNumber/SlotAssignment
- [ ] Estados de Cage correctos
- [ ] BD consistente
- [ ] API funciona correctamente
- [ ] Frontend puede consumir la API

---

## 8. Archivos Modificados - Resumen

| Archivo | Cambios | Impacto |
|---------|---------|---------|
| `resource_releaser.py` | Refactorizar `_release_cages_from_line()` | ALTO |
| `response_mapper.py` | Filtrar cages en memoria, eliminar imports | ALTO |
| `sync_system_layout.py` | Refactorizar creación y actualización | CRÍTICO |
| `system_layout.py` (router) | Sin cambios | NINGUNO |
| `system_layout.py` (models) | Sin cambios | NINGUNO |
| `delta_calculator.py` | Sin cambios | NINGUNO |
| `name_validator.py` | Sin cambios | NINGUNO |
| `dependencies.py` | Sin cambios | NINGUNO |

---

## 9. Notas Importantes

1. **Frontend Compatible:** Los modelos de Pydantic (SlotAssignmentModel) se mantienen sin cambios. El frontend no requiere modificaciones.

2. **ResponseMapper Puro:** ResponseMapper permanece como transformación pura (síncrono, sin I/O). Filtra cages en memoria usando los datos que recibe como parámetros.

3. **Orden de Operaciones:** Guardar línea ANTES de asignar cages (necesitamos line_id).

4. **ResourceReleaser Crítico:** Es fundamental que funcione correctamente para que las actualizaciones liberen cages antiguas.

5. **Validaciones en Caso de Uso:** Las siguientes validaciones están en el caso de uso (no en el agregado):
   - **Capacidad total del selector**: Número de asignaciones no excede `selector.capacity`
   - **Slot_number en rango válido**: Cada slot debe estar en `[1, selector.capacity]`
   - **Slot duplicado**: No dos cages en el mismo slot (requiere repositorio para consistencia global)
   - **Cage disponible**: Estado debe ser `AVAILABLE`

6. **Estados de Cage:** Siempre sincronizar `cage.status` con las asignaciones:
   - Asignar → `IN_USE`
   - Desasignar → `AVAILABLE`

7. **Transacciones:** Todas las operaciones están dentro de la sesión de FastAPI, asegurando atomicidad.

8. **Separación de Responsabilidades:** El use case obtiene todos los datos necesarios, el mapper solo transforma. No mezclar lógica de acceso a datos en los mappers.
