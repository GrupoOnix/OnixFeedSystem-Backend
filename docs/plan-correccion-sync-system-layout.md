# Plan de Corrección: SyncSystemLayoutUseCase

## 1. Análisis de Situación Actual

### 1.1 Contexto
`SyncSystemLayoutUseCase` es el **caso de uso más crítico del sistema**. Maneja la sincronización completa del canvas de trazado (frontend) con la base de datos en una sola operación transaccional.

**Funcionalidad:**
- Calcula diferencias (delta) entre estado del canvas y BD
- Ejecuta creaciones, actualizaciones y eliminaciones
- Mapea IDs temporales a IDs reales
- Valida todas las reglas de negocio (FA1-FA7)

### 1.2 Problemas Identificados

#### ❌ PROBLEMA 1: Imports Obsoletos (CRÍTICO)

**Ubicación:** Líneas 13, 34

```python
# Línea 13
from api.models.system_layout import SlotAssignmentModel  # ⚠️ Modelo antiguo

# Línea 34
from domain.value_objects import (
    # ... otros imports ...
    SlotNumber, SlotAssignment  # ❌ ELIMINADOS en Fase 1
)
```

**Impacto:**
- El código no compila
- `SlotNumber` y `SlotAssignment` fueron eliminados en Fase 1 (tarea 1.3)

---

#### ❌ PROBLEMA 2: Método Eliminado en Creación de Líneas (CRÍTICO)

**Ubicación:** Líneas 280-296 (`_create_feeding_lines()`)

```python
for slot_dto in dto.slot_assignments:
    cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)

    cage = await self.cage_repo.find_by_id(cage_id)
    if cage:
        if cage.status != CageStatus.AVAILABLE:
            raise CageNotAvailableException(...)
        cage.status = CageStatus.IN_USE
        await self.cage_repo.save(cage)

    new_line.assign_cage_to_slot(slot_dto.slot_number, cage_id)  # ❌ NO EXISTE
```

**Impacto:**
- `FeedingLine.assign_cage_to_slot()` fue eliminado en Fase 1 (tarea 1.2)
- La asignación de cages a líneas ya no funciona

---

#### ❌ PROBLEMA 3: Métodos Eliminados en Actualización de Líneas (CRÍTICO)

**Ubicación:** Líneas 373-394 (`_update_feeding_lines()`)

```python
new_assignments: List[SlotAssignment] = []  # ❌ SlotAssignment eliminado
for slot_dto in dto.slot_assignments:
    cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)

    cage = await self.cage_repo.find_by_id(cage_id)
    if cage:
        if cage.status != CageStatus.AVAILABLE:
            raise CageNotAvailableException(...)
        cage.status = CageStatus.IN_USE
        await self.cage_repo.save(cage)

    slot_number = SlotNumber(slot_dto.slot_number)  # ❌ SlotNumber eliminado
    assignment = SlotAssignment(slot_number, cage_id)  # ❌ SlotAssignment eliminado
    new_assignments.append(assignment)

line.update_assignments(new_assignments)  # ❌ Método eliminado
await self.line_repo.save(line)
```

**Impacto:**
- `SlotAssignment` ya no existe como entidad
- `FeedingLine.update_assignments()` fue eliminado en Fase 1
- Actualización de líneas completamente rota

---

### 1.3 Cambio Arquitectural: Antes vs Después

#### Arquitectura ANTIGUA (obsoleta)
```
┌─────────────────┐
│  FeedingLine    │
├─────────────────┤
│ - id            │
│ - name          │
│ - components    │
│ - slot_assignments: Dict[int, SlotAssignment]  ← Diccionario interno
└─────────────────┘
         │ contiene
         ▼
┌─────────────────┐
│ SlotAssignment  │  ← Entidad intermedia
├─────────────────┤
│ - slot_number   │
│ - cage_id       │
└─────────────────┘
         │ referencia
         ▼
┌─────────────────┐
│     Cage        │
├─────────────────┤
│ - id            │
│ - name          │
│ (sin line_id)   │  ← No sabe a qué línea pertenece
└─────────────────┘
```

**Características:**
- Relación unidireccional: FeedingLine → Cage
- Entidad intermedia SlotAssignment
- Cage independiente, sin conocimiento de su línea
- Tabla `slot_assignments` en BD

#### Arquitectura NUEVA (refactorizada)
```
┌─────────────────┐
│  FeedingLine    │
├─────────────────┤
│ - id            │
│ - name          │
│ - components    │
│ (sin slots)     │  ← Ya no gestiona slots
└─────────────────┘
         ▲
         │ pertenece a
         │
┌─────────────────┐
│     Cage        │
├─────────────────┤
│ - id            │
│ - name          │
│ - line_id       │  ← Referencia directa a línea
│ - slot_number   │  ← Atributo directo
├─────────────────┤
│ + assign_to_line(line_id, slot_number)    │
│ + unassign_from_line()                    │
└─────────────────┘
```

**Características:**
- Relación bidireccional: Cage conoce su línea
- Sin entidad intermedia
- Cage autoreferencial
- Columnas `line_id` y `slot_number` directamente en tabla `cages`

---

## 2. Plan de Corrección

### Fase 1: Eliminar Referencias Obsoletas

#### ✅ Tarea 1.1: Eliminar imports de dominio obsoletos

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
    SlotNumber, SlotAssignment  # ❌ ELIMINAR ESTO
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

#### ⚠️ Tarea 1.2: Verificar modelo de API (no modificar aún)

**Archivo:** `src/api/models/system_layout.py`

**Acción:** Revisar pero NO modificar `SlotAssignmentModel` en esta fase.

**Razón:** El frontend sigue usando este modelo. Cambios en API requieren coordinación con frontend.

---

### Fase 2: Refactorizar Creación de Líneas

#### ✅ Tarea 2.1: Refactorizar `_create_feeding_lines()`

**Archivo:** `src/application/use_cases/sync_system_layout.py`
**Ubicación:** Líneas 260-299

**ANTES (lógica incorrecta):**
```python
async def _create_feeding_lines(self, lines_dtos, id_map: Dict[str, Any]) -> None:
    for dto in lines_dtos:
        await NameValidator.validate_unique_line_name(...)

        blower = self._build_blower_from_model(dto.blower_config)
        sensors = self._build_sensors_from_model(dto.sensors_config)
        dosers = await self._build_dosers_from_model(dto.dosers_config, id_map)
        selector = self._build_selector_from_model(dto.selector_config)

        new_line = FeedingLine.create(...)

        # ❌ ESTO ESTÁ MAL
        for slot_dto in dto.slot_assignments:
            cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
            cage = await self.cage_repo.find_by_id(cage_id)
            if cage:
                if cage.status != CageStatus.AVAILABLE:
                    raise CageNotAvailableException(...)
                cage.status = CageStatus.IN_USE
                await self.cage_repo.save(cage)

            new_line.assign_cage_to_slot(slot_dto.slot_number, cage_id)  # ❌ NO EXISTE

        await self.line_repo.save(new_line)
        id_map[dto.id] = new_line.id
```

**DESPUÉS (lógica correcta):**
```python
async def _create_feeding_lines(self, lines_dtos, id_map: Dict[str, Any]) -> None:
    for dto in lines_dtos:
        await NameValidator.validate_unique_line_name(
            dto.line_name, exclude_id=None, repo=self.line_repo
        )

        # Validar capacidad del selector vs número de slots
        if len(dto.slot_assignments) > dto.selector_config.capacity:
            raise ValueError(
                f"La línea '{dto.line_name}' tiene {len(dto.slot_assignments)} slots asignados "
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

        # ✅ GUARDAR LÍNEA PRIMERO (necesitamos line_id)
        await self.line_repo.save(new_line)
        id_map[dto.id] = new_line.id

        # ✅ ASIGNAR CAGES A LA LÍNEA (nuevo enfoque)
        for slot_dto in dto.slot_assignments:
            cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
            cage = await self.cage_repo.find_by_id(cage_id)

            if not cage:
                raise ValueError(f"La jaula con ID '{slot_dto.cage_id}' no existe")

            # Validar que la jaula esté disponible
            if cage.status != CageStatus.AVAILABLE:
                raise CageNotAvailableException(
                    f"La jaula '{cage.name}' no está disponible (estado: {cage.status.value})"
                )

            # Validar que no haya otra cage en el mismo slot
            existing_cage = await self.cage_repo.find_by_line_and_slot(
                new_line.id, slot_dto.slot_number
            )
            if existing_cage:
                raise ValueError(
                    f"El slot {slot_dto.slot_number} ya está ocupado por la jaula '{existing_cage.name}'"
                )

            # ✅ ASIGNAR usando método del dominio Cage
            cage.assign_to_line(new_line.id, slot_dto.slot_number)
            cage.status = CageStatus.IN_USE
            await self.cage_repo.save(cage)
```

**Cambios clave:**
1. ✅ Validar capacidad del selector ANTES de crear la línea
2. ✅ Guardar línea ANTES de asignar cages (necesitamos `new_line.id`)
3. ✅ Usar `cage.assign_to_line(line_id, slot_number)` en lugar de método de línea
4. ✅ Validar slot duplicado con `cage_repo.find_by_line_and_slot()`
5. ✅ Mantener gestión de estados de Cage

---

### Fase 3: Refactorizar Actualización de Líneas

#### ✅ Tarea 3.1: Refactorizar `_update_feeding_lines()`

**Archivo:** `src/application/use_cases/sync_system_layout.py`
**Ubicación:** Líneas 341-395

**ANTES (lógica incorrecta):**
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

        if str(line.name) != dto.line_name:
            await NameValidator.validate_unique_line_name(...)
            line.name = LineName(dto.line_name)

        blower = self._build_blower_from_model(dto.blower_config)
        sensors = self._build_sensors_from_model(dto.sensors_config)
        dosers = await self._build_dosers_from_model(dto.dosers_config, id_map)
        selector = self._build_selector_from_model(dto.selector_config)

        line.update_components(blower, dosers, selector, sensors)

        # ❌ ESTO ESTÁ MAL
        new_assignments: List[SlotAssignment] = []
        for slot_dto in dto.slot_assignments:
            cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
            cage = await self.cage_repo.find_by_id(cage_id)
            if cage:
                if cage.status != CageStatus.AVAILABLE:
                    raise CageNotAvailableException(...)
                cage.status = CageStatus.IN_USE
                await self.cage_repo.save(cage)

            slot_number = SlotNumber(slot_dto.slot_number)  # ❌
            assignment = SlotAssignment(slot_number, cage_id)  # ❌
            new_assignments.append(assignment)

        line.update_assignments(new_assignments)  # ❌ NO EXISTE
        await self.line_repo.save(line)
```

**DESPUÉS (lógica correcta):**
```python
async def _update_feeding_lines(self, lines_to_update, id_map: Dict[str, Any]) -> None:
    # Nota: ResourceReleaser ya debería manejar la desasignación de cages
    # Si no lo hace, se agregará en Tarea 3.2

    # Liberar recursos (silos y cages)
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

        # Validar nombre único si cambió
        if str(line.name) != dto.line_name:
            await NameValidator.validate_unique_line_name(
                dto.line_name, exclude_id=line_id, repo=self.line_repo
            )
            line.name = LineName(dto.line_name)

        # Validar capacidad del selector
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

        # ✅ ASIGNAR CAGES (nuevo enfoque)
        for slot_dto in dto.slot_assignments:
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

            # ✅ ASIGNAR usando método del dominio
            cage.assign_to_line(line_id, slot_dto.slot_number)
            cage.status = CageStatus.IN_USE
            await self.cage_repo.save(cage)
```

**Cambios clave:**
1. ✅ Confiar en `ResourceReleaser` para desasignar cages
2. ✅ Validar capacidad del selector
3. ✅ Actualizar componentes primero, guardar línea
4. ✅ Asignar cages después con `cage.assign_to_line()`
5. ✅ Validaciones de slot duplicado y disponibilidad

---

### Fase 4: Actualizar ResourceReleaser

#### ✅ Tarea 4.1: Verificar y actualizar `ResourceReleaser`

**Archivo:** `src/application/services/resource_releaser.py` (asumo que existe)

**Verificar que el método `release_all_from_lines()` desasigne correctamente las cages.**

**Si el código actual hace algo como esto:**
```python
# ❌ ANTIGUO (probablemente)
for line in lines:
    line.clear_slot_assignments()  # Método que ya no existe
```

**Debe cambiarse a:**
```python
# ✅ NUEVO
async def release_all_from_lines(
    lines: List[FeedingLine],
    silo_repo: ISiloRepository,
    cage_repo: ICageRepository
) -> None:
    """Libera silos y cages asignados a las líneas."""

    for line in lines:
        # Liberar silos de los dosers
        for doser in line.dosers:
            silo = await silo_repo.find_by_id(doser.assigned_silo_id)
            if silo:
                silo.release_from_doser()
                await silo_repo.save(silo)

        # ✅ Liberar cages asignadas a esta línea
        cages = await cage_repo.find_by_line_id(line.id)
        for cage in cages:
            cage.unassign_from_line()
            cage.status = CageStatus.AVAILABLE
            await cage_repo.save(cage)
```

**Nota:** Si `ResourceReleaser` no existe o no desasigna cages, integrar esta lógica directamente en `_update_feeding_lines()` antes de reasignar.

---

## 3. Validaciones Críticas

### Validación 1: Slot Duplicado

**Estrategia ANTIGUA:**
```python
# Validación en FeedingLine
if slot_number in line._slot_assignments:
    raise ValueError("Slot ya asignado")
```

**Estrategia NUEVA:**
```python
# Validación consultando repositorio
existing_cage = await self.cage_repo.find_by_line_and_slot(line_id, slot_number)
if existing_cage:
    raise ValueError(f"El slot {slot_number} ya está ocupado por '{existing_cage.name}'")
```

### Validación 2: Capacidad del Selector

**Ubicación:** En el caso de uso, ANTES de asignar cages.

```python
if len(dto.slot_assignments) > selector.capacity.value:
    raise ValueError(
        f"La línea '{dto.line_name}' excede la capacidad del selector "
        f"({selector.capacity.value})"
    )
```

### Validación 3: Cage Disponible

**Mantener validación actual:**
```python
if cage.status != CageStatus.AVAILABLE:
    raise CageNotAvailableException(
        f"La jaula '{cage.name}' no está disponible (estado: {cage.status.value})"
    )
```

---

## 4. Orden de Ejecución

### Secuencia Recomendada:

1. **✅ Fase 1, Tarea 1.1** - Eliminar imports obsoletos
2. **✅ Fase 4, Tarea 4.1** - Actualizar ResourceReleaser (si es necesario)
3. **✅ Fase 2, Tarea 2.1** - Refactorizar `_create_feeding_lines()`
4. **✅ Fase 3, Tarea 3.1** - Refactorizar `_update_feeding_lines()`
5. **✅ Testing Manual** - Verificar funcionalidad completa

**Razón del orden:**
- Eliminar imports primero para que el código compile
- Actualizar ResourceReleaser antes de update (dependencia)
- Create antes que update (más simple, menos casos edge)

---

## 5. Testing y Validación

### Casos de Prueba Críticos:

#### Test 1: Crear línea con cages
```
DADO: 2 cages disponibles (C1, C2)
CUANDO: Crear línea L1 con C1 en slot 1, C2 en slot 2
ENTONCES:
  - L1 existe con componentes
  - C1.line_id = L1.id, C1.slot_number = 1, C1.status = IN_USE
  - C2.line_id = L1.id, C2.slot_number = 2, C2.status = IN_USE
```

#### Test 2: Actualizar línea cambiando slots
```
DADO: Línea L1 con C1 en slot 1, C2 en slot 2
CUANDO: Actualizar L1: C1 en slot 2, C3 en slot 1
ENTONCES:
  - C1.slot_number = 2
  - C2.line_id = NULL, C2.status = AVAILABLE (liberada)
  - C3.line_id = L1.id, C3.slot_number = 1, C3.status = IN_USE
```

#### Test 3: Eliminar línea
```
DADO: Línea L1 con C1, C2 asignadas
CUANDO: Eliminar L1
ENTONCES:
  - L1 no existe
  - C1.line_id = NULL, C1.status = AVAILABLE
  - C2.line_id = NULL, C2.status = AVAILABLE
```

#### Test 4: Validación de slot duplicado
```
DADO: Línea L1 con C1 en slot 1
CUANDO: Intentar asignar C2 a slot 1 de L1
ENTONCES: ValueError("El slot 1 ya está ocupado por 'C1'")
```

#### Test 5: Validación de capacidad
```
DADO: Selector con capacidad = 2
CUANDO: Crear línea con 3 cages asignadas
ENTONCES: ValueError("... excede la capacidad del selector (2)")
```

---

## 6. Riesgos y Mitigaciones

### Riesgo 1: Transacciones Incompletas
**Problema:** Si falla a mitad de asignación, BD queda inconsistente.

**Mitigación:**
- FastAPI + SQLAlchemy usan transacciones automáticas en `get_session()`
- Rollback automático en caso de excepción
- **Verificar:** Que todas las operaciones estén dentro de la misma sesión

### Riesgo 2: Orden de Operaciones
**Problema:** Guardar línea antes de asignar cages puede causar problemas.

**Mitigación:**
- Es el orden correcto (necesitamos line_id)
- La transacción asegura atomicidad
- Tests verifican comportamiento correcto

### Riesgo 3: ResourceReleaser No Actualizado
**Problema:** Si ResourceReleaser no desasigna cages, quedarán asignadas después de update.

**Mitigación:**
- Revisar implementación de ResourceReleaser (Tarea 4.1)
- Si no existe, implementar lógica directamente en el caso de uso
- Tests verifican liberación correcta

### Riesgo 4: Frontend Rompiendo
**Problema:** Cambios en API (SlotAssignmentModel) pueden romper frontend.

**Mitigación:**
- **NO modificar API en esta fase**
- Mantener `SlotAssignmentModel` compatible
- Cambios en API requieren coordinación con equipo frontend

---

## 7. Checklist de Validación Final

### Pre-Implementación
- [ ] Plan revisado y aprobado
- [ ] Backup de BD creado (si es producción)
- [ ] ResourceReleaser revisado

### Durante Implementación
- [ ] Imports obsoletos eliminados
- [ ] Código compila sin errores
- [ ] ResourceReleaser actualizado (si necesario)
- [ ] `_create_feeding_lines()` refactorizado
- [ ] `_update_feeding_lines()` refactorizado
- [ ] Validaciones implementadas

### Post-Implementación
- [ ] Test 1: Crear línea con cages - PASS
- [ ] Test 2: Actualizar línea - PASS
- [ ] Test 3: Eliminar línea - PASS
- [ ] Test 4: Validación slot duplicado - PASS
- [ ] Test 5: Validación capacidad - PASS
- [ ] No hay regresiones en funcionalidad existente
- [ ] Estados de Cage correctos (AVAILABLE/IN_USE)
- [ ] BD consistente después de operaciones

---

## 8. Notas Importantes

1. **No tocar FeedingLine:** El agregado ya fue refactorizado en Fase 1. No agregar métodos de slots.

2. **Responsabilidad de Cage:** Es responsabilidad de `Cage` saber a qué línea pertenece y en qué slot.

3. **Caso de uso orquesta:** `SyncSystemLayoutUseCase` orquesta, pero lógica de negocio está en agregados.

4. **API compatible:** Mantener `SlotAssignmentModel` en API por compatibilidad con frontend.

5. **Validaciones en caso de uso:** Algunas validaciones (capacidad, slot duplicado) se hacen en el caso de uso porque requieren consultas al repositorio.

6. **Estados de Cage:** Siempre actualizar `cage.status` al asignar/desasignar:
   - `AVAILABLE` cuando no está asignada
   - `IN_USE` cuando está asignada a una línea

---

## 9. Próximos Pasos Después de Esta Corrección

Una vez completado este plan:

1. **Revisar otros casos de uso** que puedan usar SlotAssignment
2. **Actualizar GetSystemLayoutUseCase** si es necesario
3. **Coordinar con frontend** para actualizar API (si aplica)
4. **Documentar cambios** en documentación de casos de uso
5. **Crear tests automatizados** para prevenir regresiones
