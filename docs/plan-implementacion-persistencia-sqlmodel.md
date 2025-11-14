# Plan de Implementación: Persistencia con SQLModel y PostgreSQL

## Contexto del Proyecto

Sistema de alimentación automatizado en acuicultura desarrollado con:

- **Arquitectura**: Clean Architecture + DDD
- **Framework**: FastAPI
- **ORM**: SQLModel
- **Base de datos**: PostgreSQL (Docker)
- **Estado actual**: Repositorios mock en memoria

## Decisiones Técnicas Clave

Estas decisiones eliminan ambigüedades del plan:

| Aspecto                   | Decisión                      | Razón                                                             |
| ------------------------- | ----------------------------- | ----------------------------------------------------------------- |
| **Driver PostgreSQL**     | `asyncpg`                     | Async nativo, mejor performance con FastAPI                       |
| **Tipo de Session**       | `AsyncSession`                | Consistente con asyncpg y FastAPI async                           |
| **Variables de entorno**  | `os.getenv()` directo         | FastAPI carga .env automáticamente                                |
| **Migraciones**           | Alembic desde el inicio       | Versionado de esquema, rollback seguro, preparado para producción |
| **BD de prueba**          | PostgreSQL temporal           | Mantiene compatibilidad con UUIDs nativos                         |
| **Timestamps**            | `datetime.utcnow()` en Python | Controlado por la aplicación                                      |
| **Dependency Injection**  | FastAPI `Depends()`           | Sistema nativo, gestión automática                                |
| **Estructura de modelos** | Un archivo por modelo         | Mejor organización y mantenibilidad                               |

## Agregados Identificados

### 1. **FeedingLine** (Agregado raíz principal)

- Entidades hijas: Blower, Doser, Selector, Sensor
- Relaciones: SlotAssignments (tabla intermedia que conecta FeedingLine con Cage mediante slots)
  - Una línea tiene N slots → Cada slot apunta a una Cage específica
  - Tabla: `slot_assignments` (line_id, slot_number, cage_id)
- Complejidad: Alta (composición de múltiples entidades)

### 2. **Cage** (Agregado independiente)

- Atributos: id, name, status, created_at
- Relaciones: Referenciado por FeedingLine (slots)

### 3. **Silo** (Agregado independiente)

- Atributos: id, name, capacity, stock_level, is_assigned, created_at
- Relaciones: Referenciado por Doser (1-a-1)

## Value Objects a Persistir

**IMPORTANTE:** Los VOs NO son tablas separadas, se "aplanan" como columnas en las tablas de sus entidades.

- **IDs**: LineId, CageId, SiloId, etc. → Se extraen como `UUID` (columna `id`)
- **Nombres**: LineName, CageName, SiloName → Se extraen como `VARCHAR(100)` (columna `name`)
- **Medidas**:
  - Weight → `BIGINT` (almacenar `_miligrams`)
  - DosingRate → `FLOAT` + `VARCHAR` (dos columnas: `value` y `unit`)
  - BlowerPowerPercentage → `FLOAT`
- **Enums**: CageStatus, SensorType → `VARCHAR` (extraer `.value`)
- **Complejos**:
  - SlotAssignment → Tabla separada `slot_assignments` (es una relación, no un atributo)
  - SelectorSpeedProfile → Dos columnas `FLOAT` (`fast_speed`, `slow_speed`)

---

## Tareas de Implementación

### Fase 1: Configuración Base de Datos

- [x] **1.1 Crear archivo de configuración de base de datos** ✅

  - Ubicación: `/src/infrastructure/persistence/database.py`
  - Crear **AsyncEngine de SQLAlchemy** con driver asyncpg para PostgreSQL
  - Configurar connection pool (pool_size=5, max_overflow=10, pool_timeout=30)
  - Implementar función `get_session()` que retorna `AsyncSession` para dependency injection
  - Gestión de variables de entorno usando `_get_required_env()` (fuerza configuración de .env)
  - Connection string: `postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}`
  - **NO implementar create_db_and_tables()** - Alembic manejará la creación de tablas
  - Conexión verificada con PostgreSQL 18

- [x] **1.2 Actualizar archivo .env.template** ✅

  - Agregar variables faltantes: DB_HOST, DB_PORT, DB_USER
  - Documentar valores por defecto para desarrollo local:
    - DB_HOST=localhost
    - DB_PORT=5432
    - DB_USER=postgres
    - DB_PASSWORD=
    - DB_NAME=feedsystemdb
  - Agregar DB_ECHO opcional

- [x] **1.3 Actualizar dependencias en requirements.txt** ✅

  - ✅ sqlmodel==0.0.27 (ya instalado)
  - ✅ asyncpg==0.30.0 (ya instalado)
  - ✅ alembic==1.13.1 (agregado a requirements.txt)
  - Pendiente: `pip install alembic` (siguiente paso)

- [x] **1.4 Configurar Alembic para migraciones** ✅

  - Inicializar Alembic: `alembic init alembic`
  - Esto crea:
    - Carpeta `/alembic/` con estructura de migraciones
    - Archivo `/alembic.ini` con configuración
    - Archivo `/alembic/env.py` (necesita configuración)

- [x] **1.5 Configurar alembic/env.py** ✅

  - Importar `DATABASE_URL` desde `database.py`
  - Importar `SQLModel.metadata` para autogenerar migraciones
  - Configurar `target_metadata = SQLModel.metadata`
  - Configurar `run_migrations_online()` para usar AsyncEngine con asyncio
  - Importar TODOS los modelos para que Alembic los detecte:
    - CageModel, SiloModel, FeedingLineModel
    - BlowerModel, DoserModel, SelectorModel, SensorModel
    - SlotAssignmentModel

- [x] **1.6 Actualizar alembic.ini** ✅

  - Comentar línea `sqlalchemy.url = ...` (usaremos la de database.py)
  - Configurar `file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s`
  - Esto genera nombres de migración legibles: `2024_01_15_1430-abc123_initial_schema.py`

### Fase 2: Modelos SQLModel - Agregados Simples

**IMPORTANTE:** Esta fase es SOLO para crear modelos de persistencia. Los repositorios se implementan en Fase 4.

- [x] **2.0 Crear estructura de carpetas** ✅

  - Crear carpeta: `/src/infrastructure/persistence/models/`
  - Crear archivo: `/src/infrastructure/persistence/models/__init__.py`
  - Crear carpeta: `/src/infrastructure/persistence/repositories/`
  - Crear archivo: `/src/infrastructure/persistence/repositories/__init__.py`

- [x] **2.1 Crear modelo SQLModel para Cage** ✅

  - Ubicación: `/src/infrastructure/persistence/models/cage_model.py`
  - Tabla: `cages`
  - Columnas:
    - `id: UUID` (PK) ← CageId.value
    - `name: str` (unique) ← CageName.value
    - `status: str` ← CageStatus.value
    - `created_at: datetime` ← usar `datetime.utcnow()` en Python
  - Implementar métodos estáticos: `to_domain(model)` y `from_domain(cage)`

- [x] **2.2 Crear modelo SQLModel para Silo** ✅
  - Ubicación: `/src/infrastructure/persistence/models/silo_model.py`
  - Tabla: `silos`
  - Columnas:
    - `id: UUID` (PK) ← SiloId.value
    - `name: str` (unique) ← SiloName.value
    - `capacity_mg: int` ← Weight.as_miligrams
    - `stock_level_mg: int` ← Weight.as_miligrams
    - `is_assigned: bool` ← bool directo
    - `created_at: datetime` ← usar `datetime.utcnow()` en Python
  - Implementar métodos estáticos: `to_domain(model)` y `from_domain(silo)`

### Fase 3: Modelos SQLModel - Agregado Complejo (FeedingLine)

- [x] **3.1 Crear modelo SQLModel para FeedingLine (tabla principal)** ✅

  - Ubicación: `/src/infrastructure/persistence/models/feeding_line_model.py`
  - Mapear LineId → UUID, LineName → str
  - Definir relaciones con entidades hijas (one-to-one, one-to-many)
  - Índice unique en name
  - Relaciones: blower (1-1), dosers (1-N), selector (1-1), sensors (1-N), slot_assignments (1-N)
  - Métodos `from_domain()` y `to_domain()` con reconstrucción completa del agregado

- [x] **3.2 Crear modelos SQLModel para entidades hijas** ✅

  - Ubicación: `/src/infrastructure/persistence/models/` (un archivo por modelo)
  - **BlowerModel** (tabla: `blowers`): ✅
    - `id: UUID` (PK), `line_id: UUID` (FK → feeding_lines)
    - `name: str`, `power_percentage: float`
    - `blow_before_seconds: int`, `blow_after_seconds: int`
  - **DoserModel** (tabla: `dosers`): ✅
    - `id: UUID` (PK), `line_id: UUID` (FK → feeding_lines)
    - `name: str`, `silo_id: UUID | None` (FK nullable → silos)
    - `dosing_rate_value: float`, `dosing_rate_unit: str`
    - `min_rate_value: float`, `max_rate_value: float`, `rate_unit: str`
  - **SelectorModel** (tabla: `selectors`): ✅
    - `id: UUID` (PK), `line_id: UUID` (FK → feeding_lines)
    - `name: str`, `capacity: int`
    - `fast_speed: float`, `slow_speed: float`
  - **SensorModel** (tabla: `sensors`): ✅
    - `id: UUID` (PK), `line_id: UUID` (FK → feeding_lines)
    - `name: str`, `sensor_type: str`
  - Todas con relación a FeedingLine mediante FK con `ondelete="CASCADE"`

- [x] **3.3 Crear modelo para SlotAssignments (tabla de relación)** ✅
  - Ubicación: `/src/infrastructure/persistence/models/slot_assignment_model.py`
  - Tabla: slot_assignments
  - Columnas: id, line_id (FK), slot_number (int), cage_id (FK)
  - FK a feeding_lines con CASCADE
  - FK a cages (referencia)
  - Implementar conversión a/desde SlotAssignment VO
  - Métodos `from_domain()` y `to_domain()`

### Fase 4: Implementación de Repositorios Reales

- [x] **4.1 Implementar CageRepository con SQLModel** ✅

  - Ubicación: `/src/infrastructure/persistence/repositories/cage_repository.py`
  - Implementar todos los métodos de `ICageRepository`:
    - `save(cage)`, `find_by_id(id)`, `find_by_name(name)`
    - `get_all()`, `delete(id)`
  - Usar `AsyncSession` de SQLAlchemy (no Session)
  - Usar `await session.execute(select(...))` para queries
  - Usar `await session.commit()` para transacciones
  - Conversión: `CageModel.from_domain()` y `model.to_domain()`

- [x] **4.2 Implementar SiloRepository con SQLModel** ✅

  - Ubicación: `/src/infrastructure/persistence/repositories/silo_repository.py`
  - Implementar todos los métodos de `ISiloRepository`:
    - `save(silo)`, `find_by_id(id)`, `find_by_name(name)`
    - `get_all()`, `delete(id)`
  - Gestión de transacciones y errores
  - Conversión entre modelos de persistencia y entidades de dominio

- [x] **4.3 Implementar FeedingLineRepository con SQLModel** ✅
  - Ubicación: `/src/infrastructure/persistence/repositories/feeding_line_repository.py`
  - Implementar todos los métodos de IFeedingLineRepository
  - Gestión de agregado completo (línea + componentes + asignaciones)
  - Eager loading con `selectinload()` para evitar N+1 queries
  - Estrategia de save: delete + recreate para actualizaciones (cascade maneja hijos)
  - Conversión entre modelos de persistencia y agregado de dominio

### Fase 5: Dependency Injection y Configuración

- [ ] **5.1 Crear módulo de dependencias (usando FastAPI Depends)**

  - Ubicación: `/src/infrastructure/persistence/dependencies.py`
  - Funciones factory para obtener instancias de repositorios
  - Usar `Depends(get_session)` para inyectar sesión de BD
  - FastAPI gestiona automáticamente el ciclo de vida de sesiones
  - **IMPORTANTE:** Usar `AsyncSession` (no `Session`)
  - Ejemplo: `def get_cage_repository(session: AsyncSession = Depends(get_session)) -> ICageRepository`

- [ ] **5.2 Actualizar main.py**

  - **NO** importar `create_db_and_tables()` (Alembic maneja esto)
  - Agregar evento de startup para verificar conexión a BD (opcional)
  - Agregar evento de shutdown para cerrar conexiones del engine
  - Configurar logging de SQLAlchemy (opcional, para debug)
  - Las tablas se crean con: `alembic upgrade head` (ejecutar antes de iniciar la app)

- [ ] **5.3 Actualizar routers para usar repositorios reales**
  - Reemplazar instancias mock por dependency injection
  - Usar `Depends(get_cage_repository)` en endpoints
  - Eliminar variables globales de repositorios mock
  - Actualizar `/src/api/routers/system_layout.py`

### Fase 6: Testing y Validación

- [ ] **6.1 Crear fixtures de testing con base de datos de prueba**

  - Ubicación: `/src/test/conftest.py` (actualizar)
  - **Decisión:** Usar PostgreSQL de prueba (no SQLite) para mantener compatibilidad con UUIDs nativos
  - Opción 1: Crear BD temporal en mismo PostgreSQL (recomendado)
  - Opción 2: Usar contenedor Docker separado para tests
  - Fixtures para crear/limpiar tablas entre tests
  - Fixtures para repositorios con BD de prueba

- [ ] **6.2 Migrar tests existentes a usar BD real**

  - Actualizar tests de repositorios mock
  - Verificar que casos de uso funcionen con persistencia real
  - Tests de conversión entre modelos de dominio y persistencia

- [ ] **6.3 Tests de integración con PostgreSQL**
  - Verificar conexión a BD en Docker
  - Tests de operaciones CRUD completas
  - Tests de transacciones y rollback
  - Tests de constraints y validaciones a nivel BD

### Fase 7: Migraciones con Alembic y Documentación

- [ ] **7.1 Crear migración inicial**

  - Asegurarse de que TODOS los modelos estén importados en `alembic/env.py`
  - Generar migración inicial: `alembic revision --autogenerate -m "initial schema"`
  - Revisar el archivo de migración generado en `/alembic/versions/`
  - Verificar que incluye todas las tablas y constraints
  - Aplicar migración: `alembic upgrade head`
  - Verificar en PostgreSQL que las tablas se crearon correctamente

- [ ] **7.2 Crear script de datos de prueba (opcional)**

  - Ubicación: `/scripts/seed_data.py`
  - Script para poblar datos de prueba usando los repositorios
  - Útil para desarrollo y demos
  - NO usar para producción

- [ ] **7.3 Actualizar documentación**
  - Actualizar README con instrucciones de setup de BD
  - Documentar workflow de migraciones con Alembic:
    - Crear migración: `alembic revision --autogenerate -m "descripción"`
    - Aplicar: `alembic upgrade head`
    - Rollback: `alembic downgrade -1`
  - Documentar estructura de tablas
  - Documentar estrategia de mapeo de value objects
  - Guía de troubleshooting común

---

## Consideraciones Técnicas

### Mapeo de Value Objects

| Value Object   | Tipo en BD        | Notas                          |
| -------------- | ----------------- | ------------------------------ |
| UUID IDs       | UUID (PostgreSQL) | Usar tipo nativo de PostgreSQL |
| Nombres (VOs)  | VARCHAR(100)      | Extraer `.value` del VO        |
| Weight         | BIGINT            | Almacenar en miligramos        |
| DosingRate     | FLOAT + VARCHAR   | Dos columnas: value y unit     |
| Enums          | VARCHAR o ENUM    | Usar `.value` del enum Python  |
| SlotAssignment | Tabla separada    | Relación many-to-many          |

### Estrategia de Transacciones

- **Agregados simples (Cage, Silo)**: Una transacción por operación
- **Agregado complejo (FeedingLine)**: Transacción que incluye:
  1. Guardar/actualizar línea
  2. Guardar/actualizar componentes (blower, dosers, selector, sensors)
  3. Guardar/actualizar slot assignments
  4. Commit o rollback completo

### Connection Pool

```python
# Configuración recomendada para desarrollo
pool_size=5          # Conexiones permanentes
max_overflow=10      # Conexiones adicionales bajo demanda
pool_timeout=30      # Timeout para obtener conexión
pool_recycle=3600    # Reciclar conexiones cada hora
```

### Variables de Entorno Requeridas

```bash
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_password
DB_NAME=feedsystemdb

# Opcional
DB_ECHO=False  # Logging de queries SQL
```

### Workflow de Alembic (Comandos Principales)

```bash
# 1. Crear nueva migración (después de cambiar modelos)
alembic revision --autogenerate -m "descripción del cambio"

# 2. Aplicar migraciones pendientes
alembic upgrade head

# 3. Ver historial de migraciones
alembic history

# 4. Ver migración actual
alembic current

# 5. Rollback a migración anterior
alembic downgrade -1

# 6. Rollback a migración específica
alembic downgrade <revision_id>

# 7. Ver SQL sin ejecutar (dry-run)
alembic upgrade head --sql
```

### Estructura de Archivos con Alembic

```
proyecto/
├── alembic/
│   ├── versions/              # Migraciones generadas
│   │   └── 2024_01_15_1430-abc123_initial_schema.py
│   ├── env.py                 # Configuración de Alembic (IMPORTANTE)
│   ├── script.py.mako         # Template para migraciones
│   └── README
├── alembic.ini                # Configuración principal
├── src/
│   └── infrastructure/
│       └── persistence/
│           ├── database.py    # AsyncEngine y get_session()
│           ├── models/        # Modelos SQLModel
│           └── repositories/  # Implementaciones
└── requirements.txt
```

---

## Orden de Implementación Recomendado

1. **Fase 1.1-1.3** → Configuración base (database.py + dependencias)
2. **Fase 1.4-1.6** → Configurar Alembic (init + env.py + alembic.ini)
3. **Fase 2** → Modelos simples (Cage, Silo)
4. **Fase 3** → Modelos complejos (FeedingLine + componentes)
5. **Fase 7.1** → Crear migración inicial y aplicar (`alembic upgrade head`)
6. **Fase 4** → Implementar repositorios (Cage, Silo, FeedingLine)
7. **Fase 5** → Dependency injection y actualización de routers
8. **Fase 6** → Testing
9. **Fase 7.2-7.3** → Scripts de datos y documentación

**IMPORTANTE:** Las tablas se crean con Alembic (Fase 7.1), NO en el código de la aplicación.

## Estimación de Esfuerzo

- **Fase 1 (completa)**: 3-4 horas (incluye setup de Alembic)
- **Fase 2**: 3-4 horas
- **Fase 3**: 4-6 horas (complejidad del agregado)
- **Fase 4**: 6-8 horas
- **Fase 5**: 2-3 horas
- **Fase 6**: 4-6 horas
- **Fase 7**: 2-3 horas

**Total estimado**: 24-34 horas

---

## Próximos Pasos

1. ✅ Revisar y aprobar este plan
2. Instalar Alembic: `pip install alembic`
3. Comenzar con Fase 1.1 (crear database.py)
4. Configurar Alembic (Fase 1.4-1.6)
5. Crear modelos SQLModel (Fase 2-3)
6. Generar y aplicar migración inicial (Fase 7.1)
7. Implementar repositorios (Fase 4)
8. Integrar con FastAPI (Fase 5)

## Notas Adicionales

- Mantener repositorios mock durante la transición (útil para tests rápidos)
- Considerar implementar patrón Unit of Work si se requiere gestión de transacciones más compleja
- Evaluar agregar índices adicionales según patrones de consulta reales
- Considerar implementar soft deletes si se requiere auditoría
