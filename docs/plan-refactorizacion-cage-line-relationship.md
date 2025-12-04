# Plan de Refactorización: Relación Cage-Line Directa

**Versión:** 1.0
**Fecha:** Diciembre 2025
**Objetivo:** Simplificar la relación entre Cage y FeedingLine eliminando la entidad intermedia SlotAssignment y estableciendo una relación directa 1:N.

---

## 📋 Resumen Ejecutivo

### Problema Actual

La relación entre `Cage` y `FeedingLine` está implementada a través de una entidad intermedia `SlotAssignment` que complica innecesariamente la arquitectura. Esta entidad mantiene la asignación de jaulas a slots en líneas de alimentación, pero añade complejidad a queries, repositorios y casos de uso.

### Solución Propuesta

Convertir la relación en una asociación directa 1:N donde:
- Una `FeedingLine` tiene muchas `Cages`
- Una `Cage` pertenece opcionalmente a una `FeedingLine` y tiene un `slot_number`
- Los atributos `line_id` y `slot_number` pasan a ser propiedades directas de `Cage`

### Beneficios Esperados

1. **Simplicidad arquitectural**: Elimina una entidad y sus repositorios asociados
2. **Claridad conceptual**: La relación es directa y obvia
3. **Performance mejorado**: No requiere JOINs con tabla intermedia
4. **Código más mantenible**: Menos capas de abstracción
5. **Queries simplificadas**: Acceso directo por `cage.line_id` y `cage.slot_number`

---

## 🎯 Decisiones de Diseño

### Comportamiento CASCADE Definido

1. **Doser → Silo**: `SET NULL` (silo queda libre al borrar doser)
2. **FeedingOperation → Cage**: `SET NULL` (operaciones históricas se mantienen sin jaula)
3. **FeedingLine → Cage**: `SET NULL` (jaulas quedan sin línea al borrar línea)
4. **Cage → Logs (Biometry, Mortality, Config)**: `CASCADE` (logs se borran con la jaula)

### Campos Nuevos en Cage

- `line_id`: UUID opcional (FK a feeding_lines.id)
- `slot_number`: Entero opcional (1-based, representa la ranura física en la línea)

---

## 📐 Fases de Implementación

---

## Fase 1: Refactorizar el Dominio

**Objetivo:** Modificar las entidades de dominio para reflejar la nueva estructura de relación directa entre Cage y FeedingLine.

### Tareas

#### 1.1. Modificar el Aggregate Cage

**Archivo:** `src/domain/aggregates/cage.py`

**Cambios requeridos:**

1. Agregar atributo privado `_line_id` de tipo `Optional[LineId]` al constructor
2. Agregar atributo privado `_slot_number` de tipo `Optional[int]` al constructor
3. Crear property público `line_id` que retorne el valor de `_line_id`
4. Crear property público `slot_number` que retorne el valor de `_slot_number`
5. Crear método de negocio `assign_to_line(line_id: LineId, slot_number: int)` que:
   - Valide que `slot_number` sea mayor o igual a 1
   - Asigne ambos valores a los atributos privados
6. Crear método de negocio `unassign_from_line()` que:
   - Establezca ambos atributos privados en `None`
7. Actualizar el método `__init__` para aceptar estos nuevos parámetros opcionales

#### 1.2. Modificar el Aggregate FeedingLine

**Archivo:** `src/domain/aggregates/feeding_line/feeding_line.py`

**Cambios requeridos:**

1. Eliminar completamente el atributo `_slot_assignments` (lista de SlotAssignment)
2. Eliminar todos los métodos relacionados con gestión de slot assignments:
   - Método para agregar assignments
   - Método para eliminar assignments
   - Método para obtener assignments
   - Método para actualizar assignments
3. Eliminar el import de `SlotAssignment` del archivo
4. Mantener el resto de la funcionalidad del aggregate intacta

**Justificación:** Las asignaciones ahora se gestionan directamente en Cage y se consultan mediante el repositorio cuando sea necesario.

#### 1.3. Eliminar Value Object SlotAssignment

**Archivo:** `src/domain/value_objects/structural.py`

**Cambios requeridos:**

1. Eliminar completamente la clase `SlotAssignment` del archivo
2. Mantener la clase `SlotNumber` si existe y se usa en otros contextos
3. Si el archivo queda vacío o solo con `SlotNumber`, evaluar si mantenerlo o moverlo

#### 1.4. Actualizar exports de Value Objects

**Archivo:** `src/domain/value_objects/__init__.py`

**Cambios requeridos:**

1. Eliminar `SlotAssignment` de la lista de exports (`__all__`)
2. Verificar que no se exporte desde otros módulos
3. Mantener el resto de exports intactos

#### 1.5. Actualizar interfaz de repositorio ICageRepository

**Archivo:** `src/domain/repositories.py`

**Cambios requeridos:**

1. Agregar método abstracto `find_by_line_and_slot` que:
   - Acepte `line_id: LineId` y `slot_number: int`
   - Retorne `Optional[Cage]`
   - Permita buscar una jaula por su línea y número de slot
2. Agregar método abstracto `find_by_line_id` que:
   - Acepte `line_id: LineId`
   - Retorne `List[Cage]`
   - Permita obtener todas las jaulas de una línea específica

#### 1.6. Actualizar interfaz de repositorio IFeedingLineRepository

**Archivo:** `src/domain/repositories.py`

**Cambios requeridos:**

1. Eliminar completamente el método `get_slot_number` (ya no es necesario)
2. Eliminar cualquier otro método relacionado con SlotAssignment
3. Mantener los métodos de CRUD básicos del repositorio

---

## Fase 2: Ajustar Modelos de Persistencia

**Objetivo:** Modificar los modelos SQLModel para reflejar la nueva estructura de base de datos y eliminar la tabla intermedia.

### Tareas

#### 2.1. Modificar CageModel

**Archivo:** `src/infrastructure/persistence/models/cage_model.py`

**Cambios requeridos:**

1. Agregar campo `line_id` de tipo `Optional[UUID]`:
   - Definir como Foreign Key a `feeding_lines.id`
   - Configurar `ondelete="SET NULL"` (jaula sobrevive si se borra línea)
   - Agregar índice con `index=True`
   - Establecer como nullable con `default=None`

2. Agregar campo `slot_number` de tipo `Optional[int]`:
   - Establecer como nullable con `default=None`
   - Sin validaciones a nivel de base de datos (se manejan en dominio)

3. Agregar relationship `feeding_line`:
   - Tipo: `Optional["FeedingLineModel"]`
   - Configurar `back_populates="cages"`
   - Sin cascade delete (jaulas no se borran con la línea)

4. Actualizar método `from_domain`:
   - Mapear `cage.line_id.value` si existe, sino `None`
   - Mapear `cage.slot_number` directamente

5. Actualizar método `to_domain`:
   - Reconstruir `LineId` desde `line_id` si existe
   - Pasar `slot_number` directamente al constructor de Cage

#### 2.2. Modificar FeedingLineModel

**Archivo:** `src/infrastructure/persistence/models/feeding_line_model.py`

**Cambios requeridos:**

1. Eliminar completamente el relationship `slot_assignments`
2. Agregar nuevo relationship `cages`:
   - Tipo: `List["CageModel"]`
   - Configurar `back_populates="feeding_line"`
   - Usar `sa_relationship_kwargs={"cascade": "save-update"}` (NO delete-orphan)

3. Actualizar método `from_domain`:
   - Eliminar toda la lógica de conversión de slot_assignments
   - No mapear cages desde línea (se manejan independientemente)

4. Actualizar método `to_domain`:
   - Eliminar reconstrucción de slot_assignments
   - No cargar cages en la línea (se consultan por repositorio si es necesario)

5. Eliminar imports relacionados con SlotAssignmentModel

#### 2.3. Eliminar SlotAssignmentModel

**Archivo:** `src/infrastructure/persistence/models/slot_assignment_model.py`

**Acción:** Eliminar completamente el archivo.

#### 2.4. Actualizar exports de modelos

**Archivo:** `src/infrastructure/persistence/models/__init__.py`

**Cambios requeridos:**

1. Eliminar import de `SlotAssignmentModel`
2. Eliminar `SlotAssignmentModel` de la lista `__all__`
3. Mantener todos los demás exports intactos

#### 2.5. Corregir CASCADE en FeedingOperationModel

**Archivo:** `src/infrastructure/persistence/models/feeding_operation_model.py`

**Cambios requeridos:**

1. Modificar el campo `cage_id`:
   - Agregar `ondelete="SET NULL"` al Foreign Key
   - Cambiar tipo a `Optional[UUID]` para permitir NULL
   - Actualizar validaciones si es necesario

**Justificación:** Las operaciones históricas deben mantenerse aunque se borre la jaula.

#### 2.6. Corregir CASCADE en DoserModel

**Archivo:** `src/infrastructure/persistence/models/doser_model.py`

**Cambios requeridos:**

1. Modificar el campo `silo_id`:
   - Agregar `ondelete="SET NULL"` al Foreign Key
   - Ya es `Optional[UUID]`, verificar que sea consistente

**Justificación:** El silo queda libre si se borra el doser.

#### 2.7. Agregar CASCADE en logs de Cage

**Archivos a modificar:**
- `src/infrastructure/persistence/models/biometry_log_model.py`
- `src/infrastructure/persistence/models/mortality_log_model.py`
- `src/infrastructure/persistence/models/config_change_log_model.py`

**Cambios requeridos en cada archivo:**

1. Modificar el campo `cage_id`:
   - Agregar `ondelete="CASCADE"` al Foreign Key
   - Mantener `nullable=False` (logs requieren jaula)

**Justificación:** Si se borra una jaula, todo su historial debe borrarse.

#### 2.8. Agregar relationships en logs de Cage (opcional)

**Archivos:** Los mismos tres archivos de logs mencionados arriba

**Cambios opcionales:**

1. Agregar relationship hacia `CageModel` en cada modelo de log
2. Configurar `back_populates` si se desea navegación bidireccional
3. Usar TYPE_CHECKING para evitar imports circulares

**Nota:** Este paso es opcional, solo si se desea navegación ORM desde logs hacia cages.

---

## Fase 3: Actualizar Repositorios

**Objetivo:** Modificar las implementaciones de repositorios para trabajar con la nueva estructura de datos.

### Tareas

#### 3.1. Actualizar CageRepository

**Archivo:** `src/infrastructure/persistence/repositories/cage_repository.py`

**Cambios requeridos:**

1. Implementar método `find_by_line_and_slot`:
   - Construir query SQL con WHERE para `line_id` y `slot_number`
   - Ejecutar query de forma asíncrona
   - Convertir resultado a entidad de dominio Cage
   - Retornar Optional[Cage]

2. Implementar método `find_by_line_id`:
   - Construir query SQL con WHERE para `line_id`
   - Ejecutar query de forma asíncrona
   - Convertir todos los resultados a entidades de dominio
   - Retornar List[Cage]

3. Actualizar método `save`:
   - Asegurar que mapea correctamente `line_id` y `slot_number` del dominio al modelo
   - Manejar casos donde estos valores sean None

4. Actualizar método `_to_domain`:
   - Reconstruir correctamente LineId desde el modelo
   - Pasar slot_number al constructor de Cage

#### 3.2. Actualizar FeedingLineRepository

**Archivo:** `src/infrastructure/persistence/repositories/feeding_line_repository.py`

**Cambios requeridos:**

1. Eliminar completamente el método `get_slot_number` (ya no existe en interfaz)

2. Eliminar cualquier lógica relacionada con:
   - Carga de slot_assignments
   - Guardado de slot_assignments
   - Conversión de slot_assignments

3. Actualizar método `save`:
   - Eliminar lógica de persistencia de slot_assignments
   - No intentar guardar asignaciones

4. Actualizar método `_to_domain`:
   - Eliminar reconstrucción de slot_assignments
   - Retornar FeedingLine sin asignaciones

**Justificación:** Las asignaciones ahora son parte de Cage y se gestionan por CageRepository.

#### 3.3. Eliminar SlotAssignmentRepository (si existe)

**Ubicación potencial:** `src/infrastructure/persistence/repositories/`

**Acción:**
1. Buscar si existe un archivo de repositorio para SlotAssignment
2. Si existe, eliminarlo completamente
3. Eliminar su import/export de `__init__.py` en la carpeta repositories

---

## Fase 4: Actualizar Casos de Uso

**Objetivo:** Refactorizar los casos de uso que dependen de SlotAssignment para usar la nueva estructura directa.

### Tareas

#### 4.1. Identificar casos de uso afectados

**Acción:**

1. Buscar en `src/application/use_cases/` todos los archivos que:
   - Importen SlotAssignment
   - Usen métodos de FeedingLineRepository relacionados con slots
   - Llamen a `get_slot_number` o similares

2. Crear lista completa de archivos afectados para revisión sistemática

#### 4.2. Actualizar StartFeedingSessionUseCase

**Archivo:** `src/application/use_cases/feeding/start_feeding_use_case.py`

**Cambios requeridos:**

1. Eliminar import de SlotAssignment
2. Modificar lógica de obtención de slot físico:
   - En lugar de llamar a `line_repository.get_slot_number(line_id, cage_id)`
   - Usar directamente `cage.slot_number` después de cargar la cage
   - Validar que la cage tenga slot_number antes de proceder

3. Actualizar validaciones:
   - Verificar que `cage.line_id` coincida con el `line_id` del request
   - Verificar que `cage.slot_number` no sea None
   - Lanzar error descriptivo si la cage no está asignada a ninguna línea

#### 4.3. Actualizar SyncSystemLayoutUseCase

**Archivo:** `src/application/use_cases/sync_system_layout.py`

**Cambios requeridos:**

1. Eliminar toda la lógica de sincronización de SlotAssignments
2. Modificar para sincronizar directamente:
   - Actualizar `cage.line_id` y `cage.slot_number` basándose en el payload recibido
   - Usar método `cage.assign_to_line(line_id, slot_number)` del dominio

3. Actualizar lógica de desasignación:
   - Usar método `cage.unassign_from_line()` cuando corresponda

4. Simplificar el flujo eliminando la capa intermedia de assignments

#### 4.4. Actualizar GetSystemLayoutUseCase

**Archivo:** `src/application/use_cases/get_system_layout.py`

**Cambios requeridos:**

1. Modificar consulta de asignaciones:
   - En lugar de consultar SlotAssignments por separado
   - Cargar cages con `cage_repository.find_by_line_id(line_id)`
   - Usar directamente `cage.slot_number` para el mapeo

2. Actualizar construcción del DTO de respuesta:
   - Mapear directamente desde los atributos de Cage
   - Eliminar conversiones intermedias de SlotAssignment

#### 4.5. Actualizar cualquier otro caso de uso afectado

**Proceso:**

1. Para cada caso de uso identificado en 4.1:
   - Eliminar imports de SlotAssignment
   - Reemplazar lógica de consulta de assignments con acceso directo a cage.line_id/slot_number
   - Actualizar validaciones según corresponda
   - Simplificar flujos eliminando la capa intermedia

2. Documentar los cambios realizados en cada archivo

---

## Fase 5: Generar y Aplicar Migración de Base de Datos

**Objetivo:** Crear una migración que transfiera los datos existentes de la tabla intermedia a los nuevos campos en cages, y luego eliminar la tabla antigua.

### Tareas

#### 5.1. Crear backup de la base de datos

**Acción:**

1. Generar dump completo de la base de datos actual:
   - Usar comando PostgreSQL `pg_dump`
   - Guardar en ubicación segura con timestamp
   - Verificar que el backup sea restaurable

**Justificación:** Seguridad ante cualquier problema durante la migración.

#### 5.2. Generar migración automática con Alembic

**Comando:**
```
alembic revision --autogenerate -m "refactor_cage_line_direct_relationship"
```

**Acción posterior:**

1. Localizar archivo de migración generado en `alembic/versions/`
2. Revisar que Alembic haya detectado:
   - Adición de columnas `line_id` y `slot_number` a tabla `cages`
   - Creación de FK de `line_id` hacia `feeding_lines.id`
   - Eliminación de tabla `slot_assignments`

#### 5.3. Editar migración para incluir migración de datos

**Archivo:** El archivo de migración generado en `alembic/versions/`

**Cambios requeridos:**

1. Modificar la función `upgrade()` para agregar pasos intermedios:
   - **Paso 1:** Agregar columnas `line_id` y `slot_number` como nullable a `cages`
   - **Paso 2:** Migrar datos de `slot_assignments` a `cages` con UPDATE query
   - **Paso 3:** Agregar FK constraint de `line_id` hacia `feeding_lines.id`
   - **Paso 4:** Eliminar tabla `slot_assignments`

2. En el paso de migración de datos (Paso 2), escribir SQL que:
   - Haga UPDATE de tabla `cages`
   - Use JOIN con `slot_assignments` para obtener `line_id` y `slot_number`
   - Establezca los valores correspondientes en cada cage

3. Verificar que el orden de operaciones sea correcto para evitar violaciones de FK

#### 5.4. Revisar y validar migración

**Acciones:**

1. Leer completamente el archivo de migración generado
2. Verificar SQL sintácticamente correcto
3. Confirmar que la función `downgrade()` también está implementada correctamente
4. Verificar que todos los índices se creen correctamente
5. Confirmar configuración de CASCADE en FKs

#### 5.5. Aplicar migración en ambiente de desarrollo

**Comando:**
```
alembic upgrade head
```

**Verificaciones post-migración:**

1. Confirmar que la migración se ejecutó sin errores
2. Verificar que tabla `slot_assignments` ya no existe
3. Verificar que tabla `cages` tiene nuevas columnas
4. Ejecutar query manual para confirmar que datos se migraron correctamente:
   - Contar cages con `line_id` NOT NULL
   - Comparar con cantidad original de slot_assignments
5. Verificar que FKs y constraints están aplicados

#### 5.6. Validar integridad de datos

**Acciones:**

1. Ejecutar queries de validación:
   - Verificar que no hay cages con `slot_number` sin `line_id`
   - Verificar que no hay `slot_number` duplicados en la misma `line_id`
   - Confirmar que todas las FKs apuntan a registros existentes

2. Probar operaciones CRUD:
   - Crear nueva cage con línea asignada
   - Actualizar cage cambiando de línea
   - Eliminar cage y verificar que logs se eliminan (CASCADE)
   - Eliminar línea y verificar que cages quedan con `line_id` NULL

---

## Fase 6: Corregir Imports y TYPE_CHECKING

**Objetivo:** Optimizar imports en todos los modelos de persistencia para evitar importaciones innecesarias en runtime y usar TYPE_CHECKING apropiadamente.

### Tareas

#### 6.1. Refactorizar imports en modelos de componentes

**Archivos a modificar:**
- `blower_model.py`
- `doser_model.py`
- `selector_model.py`
- `sensor_model.py`

**Cambios en cada archivo:**

1. Agregar bloque TYPE_CHECKING al inicio del archivo
2. Mover imports de tipos de dominio que solo se usan en anotaciones a TYPE_CHECKING:
   - Clases de dominio (Blower, Doser, etc.)
   - Interfaces (IBlower, IDoser, etc.)
   - Value Objects usados solo en tipos de retorno

3. Mantener fuera de TYPE_CHECKING:
   - Value Objects necesarios en runtime para `from_domain()` y `to_domain()`
   - Enums necesarios para conversiones

4. Importar FeedingLineModel con comillas dentro del Relationship

#### 6.2. Refactorizar imports en CageModel

**Archivo:** `src/infrastructure/persistence/models/cage_model.py`

**Cambios:**

1. Crear bloque TYPE_CHECKING
2. Mover imports de dominio que no se usan en runtime a TYPE_CHECKING
3. Mantener Value Objects necesarios para conversiones fuera de TYPE_CHECKING
4. Importar FeedingLineModel con comillas en el Relationship

#### 6.3. Refactorizar imports en SiloModel

**Archivo:** `src/infrastructure/persistence/models/silo_model.py`

**Cambios:**

1. Evaluar si necesita TYPE_CHECKING (actualmente no tiene relationships)
2. Si no tiene referencias a otros modelos, dejar imports como están
3. Documentar decisión

#### 6.4. Verificar imports en modelos de logs

**Archivos:**
- `biometry_log_model.py`
- `mortality_log_model.py`
- `config_change_log_model.py`

**Acciones:**

1. Verificar que usan TYPE_CHECKING para CageModel si agregaron relationship
2. Verificar que imports de Value Objects están fuera de TYPE_CHECKING
3. Mantener imports necesarios para conversiones

#### 6.5. Validar que no hay imports circulares

**Acción:**

1. Ejecutar script de validación de imports (si existe)
2. Intentar importar cada modelo individualmente en Python REPL
3. Verificar que no hay errores de import circular
4. Documentar estructura de dependencias si es necesario

---

## Fase 7: Actualizar Documentación y Validación Final

**Objetivo:** Actualizar toda la documentación afectada y realizar pruebas de validación completas del sistema refactorizado.

### Tareas

#### 7.1. Actualizar documentación técnica

**Archivos a actualizar:**

1. `CLAUDE.md`:
   - Actualizar sección de "Domain Model Key Concepts"
   - Documentar nueva relación directa Cage-Line
   - Eliminar referencias a SlotAssignment
   - Actualizar ejemplos de uso de repositorios

2. `docs/feeding_domain_classes_detailed.md` y `docs/feeding_domain_classes_simple.md`:
   - Actualizar diagramas de clases
   - Eliminar SlotAssignment de diagramas
   - Agregar line_id y slot_number a Cage
   - Actualizar relaciones

3. Cualquier otro archivo de documentación que mencione SlotAssignment

#### 7.2. Actualizar diagramas arquitecturales

**Archivos potenciales:**
- Diagramas en `docs/` que muestren relaciones entre entidades

**Acciones:**

1. Identificar todos los diagramas que incluyan SlotAssignment
2. Actualizar para mostrar relación directa
3. Regenerar imágenes si es necesario
4. Verificar consistencia con la implementación

#### 7.3. Ejecutar suite completa de tests

**Acción:**

1. Ejecutar todos los tests existentes:
   - Tests unitarios de dominio
   - Tests de integración de repositorios
   - Tests de casos de uso
   - Tests de endpoints API

2. Identificar tests que fallan debido a la refactorización

3. Actualizar o eliminar tests obsoletos:
   - Tests específicos de SlotAssignment
   - Tests que usaban métodos eliminados de repositorios

4. Verificar que todos los tests pasen después de las actualizaciones

#### 7.4. Pruebas manuales de funcionalidad

**Escenarios a probar:**

1. **Sincronización de layout del sistema:**
   - Enviar payload con asignaciones de cages a líneas
   - Verificar que cages se asignan correctamente con line_id y slot_number
   - Verificar respuesta del endpoint

2. **Inicio de sesión de alimentación:**
   - Iniciar feeding con una cage asignada a línea
   - Verificar que se usa correctamente el slot_number de la cage
   - Verificar que operación se crea exitosamente

3. **Consulta de layout:**
   - Obtener layout del sistema
   - Verificar que response incluye cages con sus slots
   - Verificar estructura del JSON de respuesta

4. **Gestión de cages:**
   - Crear cage sin línea asignada
   - Asignar cage a línea posteriormente
   - Cambiar cage de línea
   - Desasignar cage de línea
   - Eliminar cage y verificar CASCADE en logs

5. **Eliminación de línea:**
   - Eliminar línea con cages asignadas
   - Verificar que cages quedan con line_id NULL
   - Verificar que no se borran las cages

#### 7.5. Validar performance de queries

**Acciones:**

1. Ejecutar queries de obtención de cages por línea
2. Medir tiempos de respuesta
3. Comparar con performance anterior (si se tiene baseline)
4. Verificar que índices están siendo utilizados correctamente
5. Analizar planes de ejecución con EXPLAIN ANALYZE en PostgreSQL

#### 7.6. Actualizar checklist de implementación

**Archivo:** `docs/plan-migracion-feeding-operation.md` (si contiene referencias)

**Acciones:**

1. Revisar documento existente
2. Actualizar referencias a SlotAssignment si existen
3. Marcar como completada esta refactorización
4. Documentar lecciones aprendidas

#### 7.7. Crear registro de cambios

**Crear nuevo archivo:** `docs/changelog-cage-line-refactor.md`

**Contenido:**

1. Fecha de implementación
2. Resumen de cambios realizados
3. Archivos modificados y eliminados
4. Breaking changes en la API (si los hay)
5. Instrucciones para desarrolladores sobre cómo adaptar código existente
6. Issues conocidos o limitaciones temporales

---

## 📊 Criterios de Aceptación

### Dominio

- [ ] Cage tiene propiedades line_id y slot_number
- [ ] Cage tiene métodos assign_to_line() y unassign_from_line()
- [ ] FeedingLine NO contiene lista de slot_assignments
- [ ] SlotAssignment NO existe como Value Object
- [ ] Interfaces de repositorios actualizadas correctamente

### Modelos de Persistencia

- [ ] CageModel tiene campos line_id y slot_number
- [ ] CageModel tiene FK correcta hacia FeedingLine con SET NULL
- [ ] FeedingLineModel tiene relationship hacia cages
- [ ] SlotAssignmentModel NO existe
- [ ] Todos los CASCADE configurados correctamente según decisiones
- [ ] TYPE_CHECKING usado apropiadamente en todos los modelos

### Base de Datos

- [ ] Tabla slot_assignments eliminada
- [ ] Tabla cages tiene columnas line_id y slot_number
- [ ] FK de cages.line_id apunta a feeding_lines.id con SET NULL
- [ ] Datos migrados correctamente desde slot_assignments
- [ ] Índices creados en line_id
- [ ] No hay registros huérfanos o inconsistentes

### Repositorios

- [ ] CageRepository implementa find_by_line_and_slot()
- [ ] CageRepository implementa find_by_line_id()
- [ ] FeedingLineRepository NO tiene métodos de slot_assignment
- [ ] Todos los métodos save() funcionan correctamente

### Casos de Uso

- [ ] StartFeedingSessionUseCase usa cage.slot_number directamente
- [ ] SyncSystemLayoutUseCase asigna correctamente cages a líneas
- [ ] GetSystemLayoutUseCase retorna información correcta
- [ ] Ningún caso de uso importa o usa SlotAssignment

### Tests y Validación

- [ ] Todos los tests unitarios pasan
- [ ] Todos los tests de integración pasan
- [ ] Pruebas manuales de flujos principales exitosas
- [ ] Performance de queries es aceptable
- [ ] No hay imports circulares

### Documentación

- [ ] CLAUDE.md actualizado
- [ ] Diagramas de dominio actualizados
- [ ] Changelog creado
- [ ] Comentarios en código actualizados

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Pérdida de datos durante migración

**Mitigación:**
- Crear backup completo antes de migración
- Validar migración en ambiente de desarrollo primero
- Incluir queries de validación post-migración
- Implementar función downgrade() funcional

### Riesgo 2: Breaking changes en API

**Mitigación:**
- Revisar todos los endpoints que retornan información de cages
- Actualizar contratos de API si es necesario
- Documentar cambios en responses
- Comunicar cambios a consumidores de la API

### Riesgo 3: Queries N+1 en casos de uso

**Mitigación:**
- Usar eager loading en relaciones cuando sea necesario
- Implementar métodos de repositorio optimizados
- Medir performance antes y después
- Agregar índices apropiados

### Riesgo 4: Tests obsoletos que fallan

**Mitigación:**
- Identificar tests afectados tempranamente
- Actualizar tests en paralelo con código de producción
- No dejar tests comentados o deshabilitados
- Agregar nuevos tests para funcionalidad refactorizada

---

## 📅 Estimación de Tiempo

- **Fase 1 (Dominio):** 1-2 horas
- **Fase 2 (Modelos):** 2-3 horas
- **Fase 3 (Repositorios):** 1-2 horas
- **Fase 4 (Casos de Uso):** 2-3 horas
- **Fase 5 (Migración BD):** 2-3 horas
- **Fase 6 (Imports):** 1 hora
- **Fase 7 (Documentación y Validación):** 2-3 horas

**Total estimado:** 11-17 horas de trabajo enfocado

---

## ✅ Orden de Ejecución Recomendado

1. Realizar Fase 1 completa (Dominio)
2. Realizar Fase 2 completa (Modelos)
3. Realizar Fase 3 completa (Repositorios)
4. Realizar Fase 4 completa (Casos de Uso)
5. Crear backup de BD antes de Fase 5
6. Realizar Fase 5 completa (Migración BD)
7. Realizar Fase 6 completa (Imports)
8. Realizar Fase 7 completa (Validación)

**No saltar entre fases.** Completar cada fase antes de continuar a la siguiente para mantener consistencia y detectar problemas tempranamente.

---

**Fin del Plan de Refactorización**
