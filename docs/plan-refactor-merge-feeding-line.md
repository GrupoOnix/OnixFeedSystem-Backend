# Plan de Refactorización: Implementar merge() en FeedingLineRepository

**Fecha**: 2025-11-17  
**Versión**: 1.0  
**Estado**: Pendiente de implementación

---

## 🎯 Objetivo

Refactorizar el método `save()` de `FeedingLineRepository` para usar UPDATE en lugar de DELETE + INSERT, preservando los IDs de la línea y sus componentes cuando se actualiza. Esto evitará pérdida de datos en tablas futuras que referencien `feeding_lines.id` o IDs de componentes.

---

## 📋 Situación Actual

### Problema identificado:

**Archivo**: `src/infrastructure/persistence/repositories/feeding_line_repository.py`

**Código actual:**

```python
async def save(self, feeding_line: FeedingLine) -> None:
    existing = await self.session.get(FeedingLineModel, feeding_line.id.value)

    if existing:
        await self.session.delete(existing)  # ⚠️ PROBLEMA
        await self.session.flush()

    line_model = FeedingLineModel.from_domain(feeding_line)
    self.session.add(line_model)
```

**Consecuencias:**

- ✅ Funciona AHORA (sin FKs externas)
- ❌ Perderá datos cuando se implementen:
  - `feeding_executions` (historial de alimentaciones) → FK a `feeding_lines.id`
  - `feeding_parameters` (parámetros de alimentación) → FK a `dosers.id`
  - `cage_feeding_history` (seguimiento de jaulas) → FK a `feeding_lines.id`

---

## 🏗️ Arquitectura de Relaciones Actual

### Modelo `FeedingLineModel`:

```python
class FeedingLineModel(SQLModel, table=True):
    id: UUID (PK)
    name: str (UNIQUE)
    created_at: datetime

    # Relaciones one-to-one
    blower: BlowerModel (cascade="all, delete-orphan")
    selector: SelectorModel (cascade="all, delete-orphan")

    # Relaciones one-to-many
    dosers: List[DoserModel] (cascade="all, delete-orphan")
    sensors: List[SensorModel] (cascade="all, delete-orphan")
    slot_assignments: List[SlotAssignmentModel] (cascade="all, delete-orphan")
```

### Componentes hijos:

| Modelo                | PK         | FK a FeedingLine              | FK Externa | Cascade              |
| --------------------- | ---------- | ----------------------------- | ---------- | -------------------- |
| `BlowerModel`         | `id: UUID` | `line_id` (ON DELETE CASCADE) | -          | `all, delete-orphan` |
| `DoserModel`          | `id: UUID` | `line_id` (ON DELETE CASCADE) | `silo_id`  | `all, delete-orphan` |
| `SelectorModel`       | `id: UUID` | `line_id` (ON DELETE CASCADE) | -          | `all, delete-orphan` |
| `SensorModel`         | `id: UUID` | `line_id` (ON DELETE CASCADE) | -          | `all, delete-orphan` |
| `SlotAssignmentModel` | `id: UUID` | `line_id` (ON DELETE CASCADE) | `cage_id`  | `all, delete-orphan` |

**Nota crítica:** Todos los componentes tienen `cascade="all, delete-orphan"`, lo que significa que SQLAlchemy gestiona automáticamente la sincronización de colecciones.

---

## 🔍 Análisis de Opciones

### Opción A: `merge()` de SQLAlchemy (RECOMENDADA)

**Ventajas:**

- ✅ SQLAlchemy maneja automáticamente UPDATE vs INSERT
- ✅ Sincroniza colecciones hijas automáticamente con `cascade`
- ✅ Código simple (1 línea)
- ✅ Mantiene IDs de línea y componentes

**Desventajas:**

- ⚠️ Requiere que los modelos tengan configuración correcta de relaciones
- ⚠️ Comportamiento puede ser "mágico" (menos control explícito)

**Verificación necesaria:**

- Los modelos YA tienen `cascade="all, delete-orphan"` ✅
- Los IDs se generan en el dominio (no auto-increment) ✅

### Opción B: UPDATE manual con sincronización de colecciones

**Ventajas:**

- ✅ Control total sobre qué se actualiza
- ✅ Más explícito

**Desventajas:**

- ❌ Código muy complejo (100+ líneas)
- ❌ Duplica lógica del caso de uso
- ❌ Propenso a errores
- ❌ Difícil de mantener

**Conclusión:** Opción A es superior para este caso.

---

## 📝 Plan de Implementación

### **FASE 1: Preparación y Análisis**

#### 1.1. Verificar configuración de relaciones en modelos

**Archivos a revisar:**

- `src/infrastructure/persistence/models/feeding_line_model.py`
- `src/infrastructure/persistence/models/blower_model.py`
- `src/infrastructure/persistence/models/doser_model.py`
- `src/infrastructure/persistence/models/selector_model.py`
- `src/infrastructure/persistence/models/sensor_model.py`
- `src/infrastructure/persistence/models/slot_assignment_model.py`

**Verificar:**

- ✅ Todas las relaciones tienen `cascade="all, delete-orphan"`
- ✅ Todas las FKs tienen `ondelete="CASCADE"`
- ✅ Los IDs son UUID generados en dominio (no auto-increment)

**Estado actual:** ✅ VERIFICADO - Configuración correcta

---

#### 1.2. Entender el comportamiento de `merge()`

**Documentación de SQLAlchemy:**

`session.merge(instance)` hace lo siguiente:

1. **Si el objeto NO existe en BD** (por PK):

   - Hace INSERT del objeto y sus relaciones

2. **Si el objeto SÍ existe en BD** (por PK):
   - Hace UPDATE de los campos del objeto
   - Para relaciones con `cascade="all, delete-orphan"`:
     - Compara colecciones viejas vs nuevas por PK
     - UPDATE para elementos que existen en ambas
     - INSERT para elementos nuevos
     - DELETE para elementos que ya no están

**Ejemplo:**

```python
# Estado en BD:
# FeedingLine(id=123, dosers=[Doser(id=1), Doser(id=2)])

# Estado nuevo del agregado:
# FeedingLine(id=123, dosers=[Doser(id=1), Doser(id=3)])

# merge() hace:
# - UPDATE FeedingLine(id=123)
# - UPDATE Doser(id=1) (existe en ambos)
# - DELETE Doser(id=2) (ya no está en la colección)
# - INSERT Doser(id=3) (nuevo)
```

**Implicación crítica:** Los componentes que cambian DEBEN tener nuevos IDs (generados en dominio).

---

#### 1.3. Analizar cómo el caso de uso genera IDs

**Archivo:** `src/application/use_cases/sync_system_layout.py`

**Flujo actual:**

```python
# Cuando se actualiza una línea:
async def _update_feeding_lines(self, lines_to_update, id_map):
    for line_id, dto in lines_to_update.items():
        line = await self.line_repo.find_by_id(line_id)  # Línea existente

        # Reconstruye componentes DESDE CERO (nuevos IDs)
        blower = self._build_blower_from_model(dto.blower_config)  # Nuevo ID
        dosers = await self._build_dosers_from_model(...)  # Nuevos IDs
        selector = self._build_selector_from_model(...)  # Nuevo ID
        sensors = self._build_sensors_from_model(...)  # Nuevos IDs

        # Reemplaza componentes en el agregado
        line.update_components(blower, dosers, selector, sensors)

        # Guarda (actualmente DELETE + INSERT)
        await self.line_repo.save(line)
```

**Análisis:**

- ✅ El caso de uso genera NUEVOS IDs para componentes al actualizar
- ✅ Esto es correcto: si cambió la configuración, es un componente "diferente"
- ⚠️ Con `merge()`, los componentes viejos se eliminarán y los nuevos se insertarán
- ✅ El ID de la línea SE MANTIENE (no se regenera)

**Conclusión:** El comportamiento actual del caso de uso es COMPATIBLE con `merge()`.

---

### **FASE 2: Implementar merge() en el Repositorio**

#### 2.1. Refactorizar método `save()`

**Archivo:** `src/infrastructure/persistence/repositories/feeding_line_repository.py`

**Cambio:**

```python
# ANTES (DELETE + INSERT):
async def save(self, feeding_line: FeedingLine) -> None:
    existing = await self.session.get(FeedingLineModel, feeding_line.id.value)

    if existing:
        await self.session.delete(existing)
        await self.session.flush()

    line_model = FeedingLineModel.from_domain(feeding_line)
    self.session.add(line_model)

# DESPUÉS (merge):
async def save(self, feeding_line: FeedingLine) -> None:
    line_model = FeedingLineModel.from_domain(feeding_line)
    await self.session.merge(line_model)
```

**Explicación:**

- `merge()` detecta automáticamente si es INSERT o UPDATE por el PK
- Sincroniza colecciones hijas automáticamente gracias a `cascade`
- Mantiene el ID de la línea
- Elimina componentes viejos e inserta nuevos (por diferencia de IDs)

**Validación:** Verificar que no hay errores de sintaxis

---

#### 2.2. Eliminar código obsoleto

**Cambios:**

- ❌ Eliminar `existing = await self.session.get(...)`
- ❌ Eliminar `if existing: delete + flush`
- ✅ Mantener `FeedingLineModel.from_domain(feeding_line)`
- ✅ Cambiar `self.session.add()` por `await self.session.merge()`

---

### **FASE 3: Verificar Compatibilidad con Modelos**

#### 3.1. Verificar que `from_domain()` genera modelos correctos

**Archivo:** `src/infrastructure/persistence/models/feeding_line_model.py`

**Verificar:**

```python
@staticmethod
def from_domain(line: FeedingLine) -> "FeedingLineModel":
    line_model = FeedingLineModel(
        id=line.id.value,  # ✅ ID del agregado (se mantiene en updates)
        name=str(line.name),
        created_at=line._created_at,
    )

    # Componentes con sus IDs
    line_model.blower = BlowerModel.from_domain(line._blower, line.id.value)
    line_model.dosers = [DoserModel.from_domain(d, line.id.value) for d in line.dosers]
    line_model.selector = SelectorModel.from_domain(line._selector, line.id.value)
    line_model.sensors = [SensorModel.from_domain(s, line.id.value) for s in line._sensors]
    line_model.slot_assignments = [SlotAssignmentModel.from_domain(a, line.id.value) for a in line.get_slot_assignments()]

    return line_model
```

**Estado:** ✅ CORRECTO - Los modelos se generan con IDs del dominio

---

#### 3.2. Verificar que componentes tienen IDs únicos

**Archivos de componentes:**

Todos los componentes generan IDs en el dominio:

```python
# En domain/aggregates/feeding_line/blower.py (ejemplo)
class Blower:
    def __init__(self, ...):
        self._id = BlowerId.generate()  # ✅ UUID único
```

**Estado:** ✅ CORRECTO - Cada componente tiene ID único generado en dominio

---

### **FASE 4: Testing y Validación**

#### 4.1. Crear test de integración para UPDATE

**Archivo:** `tests/integration/test_feeding_line_repository_update.py` (nuevo)

**Casos de prueba:**

1. **Test: Actualizar nombre de línea (sin cambiar componentes)**

   ```python
   # Crear línea
   line = FeedingLine.create(...)
   await repo.save(line)
   original_id = line.id

   # Actualizar nombre
   line.name = LineName("Nuevo Nombre")
   await repo.save(line)

   # Verificar
   loaded = await repo.find_by_id(original_id)
   assert loaded.id == original_id  # ✅ ID se mantiene
   assert loaded.name == "Nuevo Nombre"
   ```

2. **Test: Agregar un doser a línea existente**

   ```python
   # Crear línea con 1 doser
   line = FeedingLine.create(..., dosers=[doser1])
   await repo.save(line)
   original_id = line.id

   # Agregar doser
   line.update_components(..., dosers=[doser1, doser2])
   await repo.save(line)

   # Verificar
   loaded = await repo.find_by_id(original_id)
   assert loaded.id == original_id  # ✅ ID se mantiene
   assert len(loaded.dosers) == 2
   ```

3. **Test: Eliminar un doser de línea existente**

   ```python
   # Crear línea con 2 dosers
   line = FeedingLine.create(..., dosers=[doser1, doser2])
   await repo.save(line)

   # Eliminar doser
   line.update_components(..., dosers=[doser1])
   await repo.save(line)

   # Verificar
   loaded = await repo.find_by_id(line.id)
   assert len(loaded.dosers) == 1

   # Verificar que doser2 fue eliminado de BD
   result = await session.execute(
       select(DoserModel).where(DoserModel.id == doser2.id.value)
   )
   assert result.scalar_one_or_none() is None  # ✅ Eliminado
   ```

4. **Test: Cambiar configuración de blower (nuevo ID)**

   ```python
   # Crear línea
   line = FeedingLine.create(..., blower=blower1)
   await repo.save(line)
   old_blower_id = blower1.id

   # Cambiar blower (nuevo ID)
   blower2 = Blower(...)  # Nuevo ID generado
   line.update_components(blower=blower2, ...)
   await repo.save(line)

   # Verificar
   loaded = await repo.find_by_id(line.id)
   assert loaded.blower.id != old_blower_id  # ✅ Nuevo blower

   # Verificar que blower1 fue eliminado
   result = await session.execute(
       select(BlowerModel).where(BlowerModel.id == old_blower_id.value)
   )
   assert result.scalar_one_or_none() is None  # ✅ Eliminado
   ```

5. **Test: Actualizar slot_assignments**

   ```python
   # Crear línea con slots [1 → cage1, 2 → cage2]
   line = FeedingLine.create(...)
   line.assign_cage_to_slot(1, cage1.id)
   line.assign_cage_to_slot(2, cage2.id)
   await repo.save(line)

   # Cambiar slots [1 → cage3, 3 → cage2]
   line.update_assignments([
       SlotAssignment(SlotNumber(1), cage3.id),
       SlotAssignment(SlotNumber(3), cage2.id)
   ])
   await repo.save(line)

   # Verificar
   loaded = await repo.find_by_id(line.id)
   assignments = loaded.get_slot_assignments()
   assert len(assignments) == 2
   assert loaded.get_cage_for_slot(1) == cage3.id
   assert loaded.get_cage_for_slot(3) == cage2.id
   ```

---

#### 4.2. Probar con caso de uso real

**Test end-to-end:**

```python
# Simular flujo completo de actualización
request = SystemLayoutModel(
    silos=[...],
    cages=[...],
    feeding_lines=[
        FeedingLineConfigModel(
            id="<UUID-EXISTENTE>",  # ⚠️ UUID real, no temporal
            line_name="Linea Actualizada",
            blower_config=...,
            dosers_config=[...],  # Agregar/quitar dosers
            selector_config=...,
            slot_assignments=[...]
        )
    ]
)

use_case = SyncSystemLayoutUseCase(...)
silos, cages, lines = await use_case.execute(request)

# Verificar que el ID de la línea se mantuvo
assert lines[0].id == UUID("<UUID-EXISTENTE>")
```

---

#### 4.3. Verificar comportamiento con transacciones

**Test de rollback:**

```python
# Crear línea
line = FeedingLine.create(...)
await repo.save(line)
await session.commit()

# Intentar actualización que falla
try:
    line.name = LineName("Nombre Duplicado")  # Viola UNIQUE constraint
    await repo.save(line)
    await session.commit()
except Exception:
    await session.rollback()

# Verificar que la línea NO cambió
loaded = await repo.find_by_id(line.id)
assert loaded.name != "Nombre Duplicado"  # ✅ Rollback funcionó
```

---

### **FASE 5: Documentación y Limpieza**

#### 5.1. Actualizar comentarios en el código

**Archivo:** `src/infrastructure/persistence/repositories/feeding_line_repository.py`

```python
async def save(self, feeding_line: FeedingLine) -> None:
    """
    Guarda o actualiza una línea de alimentación completa.

    Usa merge() de SQLAlchemy para:
    - INSERT si la línea no existe (por PK)
    - UPDATE si la línea existe (mantiene el ID)
    - Sincronizar componentes hijos automáticamente:
      - UPDATE componentes con mismo ID
      - DELETE componentes que ya no están
      - INSERT componentes nuevos

    Nota: Los componentes que cambian de configuración tienen nuevos IDs
    (generados en el dominio), por lo que se eliminan los viejos y se
    insertan los nuevos. Esto es correcto y esperado.
    """
    line_model = FeedingLineModel.from_domain(feeding_line)
    await self.session.merge(line_model)
```

---

#### 5.2. Actualizar documentación del plan de migración

**Archivo:** `docs/plan-migracion-postgresql.md`

Agregar nota en la sección de "Consideraciones Importantes":

```markdown
### Persistencia de FeedingLine

El repositorio usa `merge()` de SQLAlchemy para persistir líneas de alimentación.
Esto garantiza que:

- ✅ El ID de la línea se mantiene al actualizar
- ✅ Los componentes se sincronizan automáticamente
- ✅ Las tablas futuras que referencien `feeding_lines.id` no pierden datos

**Comportamiento:**

- Componentes que cambian de configuración tienen nuevos IDs (generados en dominio)
- SQLAlchemy elimina componentes viejos e inserta nuevos automáticamente
- Esto es correcto: un doser con diferente configuración es un "doser diferente"
```

---

#### 5.3. Crear ADR (Architecture Decision Record)

**Archivo:** `docs/adr/003-usar-merge-para-feeding-line.md` (nuevo)

```markdown
# ADR 003: Usar merge() para persistir FeedingLine

## Estado

Aceptado

## Contexto

FeedingLine es un agregado complejo con múltiples componentes hijos.
Inicialmente se usaba DELETE + INSERT para actualizaciones, pero esto
causaría pérdida de datos cuando se agreguen tablas que referencien
feeding_lines.id (ej: feeding_executions, feeding_parameters).

## Decisión

Usar `session.merge()` de SQLAlchemy en lugar de DELETE + INSERT.

## Consecuencias

### Positivas

- Mantiene el ID de la línea al actualizar
- Sincroniza componentes automáticamente
- Compatible con FKs externas futuras
- Código más simple

### Negativas

- Comportamiento menos explícito (más "mágico")
- Requiere entender cómo funciona merge() y cascade

### Notas de implementación

- Los componentes que cambian tienen nuevos IDs (generados en dominio)
- merge() elimina componentes viejos e inserta nuevos (correcto)
- Las relaciones deben tener cascade="all, delete-orphan"
```

---

## ✅ Checklist de Implementación

### Fase 1: Preparación

- [x] 1.1. Verificar configuración de relaciones en modelos
- [x] 1.2. Entender comportamiento de merge()
- [x] 1.3. Analizar cómo el caso de uso genera IDs

### Fase 2: Implementación

- [x] 2.1. Refactorizar método save() con merge()
- [x] 2.2. Eliminar código obsoleto

### Fase 3: Verificación

- [x] 3.1. Verificar que from_domain() genera modelos correctos
- [x] 3.2. Verificar que componentes tienen IDs únicos

### Fase 4: Testing

- [ ] 4.1. Crear tests de integración para UPDATE
- [ ] 4.2. Probar con caso de uso real
- [ ] 4.3. Verificar comportamiento con transacciones

### Fase 5: Documentación

- [ ] 5.1. Actualizar comentarios en el código
- [ ] 5.2. Actualizar documentación del plan de migración
- [ ] 5.3. Crear ADR

---

## 🚨 Riesgos y Mitigaciones

### Riesgo 1: merge() no sincroniza correctamente las colecciones

**Probabilidad:** Baja  
**Impacto:** Alto

**Mitigación:**

- Verificar que todas las relaciones tienen `cascade="all, delete-orphan"`
- Crear tests exhaustivos de sincronización de colecciones
- Probar con diferentes escenarios (agregar, eliminar, modificar)

### Riesgo 2: Pérdida de datos durante la transición

**Probabilidad:** Muy baja  
**Impacto:** Medio

**Mitigación:**

- Implementar en entorno de desarrollo primero
- Crear backup antes de aplicar en producción
- Probar exhaustivamente con datos reales

### Riesgo 3: Performance degradado con merge()

**Probabilidad:** Baja  
**Impacto:** Bajo

**Mitigación:**

- merge() es generalmente más eficiente que DELETE + INSERT
- Monitorear queries generadas con `echo=True`
- Optimizar si es necesario (poco probable)

---

## 📊 Resultado Esperado

Después de completar todas las fases:

✅ **ID de línea preservado** - No se pierde al actualizar  
✅ **Componentes sincronizados** - SQLAlchemy maneja automáticamente  
✅ **Compatible con FKs futuras** - feeding_executions, feeding_parameters, etc.  
✅ **Código más simple** - 1 línea en lugar de 5  
✅ **Tests exhaustivos** - Cobertura de todos los escenarios  
✅ **Documentado** - ADR y comentarios claros

---

**Próximos pasos**: Comenzar con Fase 2 (implementación de merge()).
