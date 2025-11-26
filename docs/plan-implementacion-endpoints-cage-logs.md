# Plan de Implementación: Endpoints de Logs y Eventos de Jaula

## Objetivo

Implementar 4 endpoints para gestionar y consultar eventos de jaulas:

1. Registrar Biometría
2. Registrar Mortalidad
3. Actualizar Configuración
4. Obtener Log de Actividad Unificado

---

## Decisiones de Diseño Clave

### 1. Logs NO son Entidades de Dominio

- Los logs (`BiometryLog`, `MortalityLog`, `ConfigChangeLog`) son **Value Objects inmutables**
- No tienen comportamiento de negocio, solo almacenan datos históricos
- Se crean y se consultan, nunca se modifican
- No necesitan entidades de dominio completas, solo DTOs/Models

### 2. Frontend Envía Todos los Valores

- Aunque algunos valores no cambien, el frontend siempre envía todos los campos
- Simplifica la lógica: siempre guardamos OLD y NEW en el log
- Evita confusión en el formulario del usuario
- Ejemplo: Si solo cambia el peso, igual se envía el conteo de peces

### 3. Mortalidad Acumulada NO se Persiste en Cage

- `total_mortality` se **calcula desde `cage_mortality_log`** cuando se necesita
- NO se agrega campo a la tabla `cages`
- Fuente única de verdad: el log
- Ventajas: Consistencia, auditoría, correcciones fáciles
- Se calcula con `SUM(dead_fish_count)` en el repositorio

### 4. Cada Endpoint Modifica Cage + Crea Log

- **Biometría**: ✅ Actualiza `current_fish_count` y `avg_fish_weight` + crea log
- **Mortalidad**: ❌ NO actualiza `current_fish_count`, solo crea log
- **Configuración**: ✅ Actualiza campos de config + crea log por cada cambio

---

## Arquitectura de Datos

### Tablas a Crear

```sql
-- Tabla 1: Eventos de biometría
cage_biometry_log (
    biometry_id UUID PK,
    cage_id UUID FK,
    old_fish_count INT,
    new_fish_count INT,
    old_average_weight_g DECIMAL(10,2),
    new_average_weight_g DECIMAL(10,2),
    sampled_fish_count INT,
    sampling_date DATE,
    note TEXT,
    user_id VARCHAR(50),
    created_at TIMESTAMP
)

-- Tabla 2: Eventos de mortalidad
cage_mortality_log (
    mortality_id UUID PK,
    cage_id UUID FK,
    dead_fish_count INT,
    mortality_date DATE,
    note TEXT,
    created_at TIMESTAMP
)

-- Tabla 3: Cambios de configuración
cage_config_changes_log (
    change_id UUID PK,
    cage_id UUID FK,
    field_name VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    created_at TIMESTAMP
)
```

---

## ETAPA 1: Endpoint de Biometría

**Endpoint:** `POST /api/cages/{cage_id}/biometry`

**Request Body:**

```json
{
  "fish_count": 4500,
  "average_weight_g": 550.5,
  "sampling_date": "2025-11-21",
  "note": "Muestreo realizado en sector norte"
}
```

### Tareas

#### 1.1. Value Object de Dominio (HACER PRIMERO)

**Archivo:** `src/domain/value_objects/biometry_log_entry.py`

- [x] Crear dataclass `BiometryLogEntry` (inmutable, frozen=True)
- [x] Definir todos los campos del log
- [x] Agregar factory method `create()` para crear nuevos registros

**Nota:** Es un VO inmutable, no una entidad. Solo se crea y se consulta.

#### 1.2. Modelo de Persistencia

**Archivo:** `src/infrastructure/persistence/models/biometry_log_model.py`

- [x] Crear clase `BiometryLogModel(SQLModel, table=True)`
- [x] Definir campos según schema
- [x] Definir índice en `cage_id`
- [x] Implementar método `from_domain(entry: BiometryLogEntry)`
- [x] Implementar método `to_domain() -> BiometryLogEntry`

#### 1.3. Migración de Base de Datos

- [x] Generar migración con: `alembic revision --autogenerate -m "create_cage_biometry_log_table"`
- [x] Revisar migración generada (verificar índices y foreign keys)
- [x] Aplicar migración: `alembic upgrade head`

#### 1.4. Capa de Dominio (Cage)

**Archivo:** `src/domain/aggregates/cage.py`

- [x] ~~Agregar método `update_biometry()`~~ **NO NECESARIO** - Usar métodos existentes:
  - `cage.update_fish_count(FishCount)` - Ya existe
  - `cage.update_biometry(Weight)` - Ya existe
- [x] Frontend siempre envía ambos valores, se actualizan ambos campos

#### 1.5. Repositorio

**Archivo:** `src/infrastructure/persistence/repositories/biometry_log_repository.py`

- [x] Crear interfaz `IBiometryLogRepository` en `src/domain/repositories.py`
- [x] Implementar clase `BiometryLogRepository`
- [x] Implementar método `save(log_entry: BiometryLogModel) -> None`
- [x] Implementar método `list_by_cage(cage_id: CageId, limit: int) -> List[BiometryLogModel]`

#### 1.6. DTOs

**Archivo:** `src/application/dtos/biometry_dtos.py`

- [x] Crear `RegisterBiometryRequest` dataclass
  - `fish_count: int` (siempre requerido)
  - `average_weight_g: float` (siempre requerido)
  - `sampling_date: date`
  - `note: Optional[str]`
- [x] ~~Crear `RegisterBiometryResponse`~~ **NO NECESARIO** - Endpoint retorna solo 200 OK
- [x] Crear `BiometryLogItemResponse` dataclass (para listado GET)
- [x] Crear `ListBiometryResponse` dataclass (para listado GET)

#### 1.6. Use Case

**Archivo:** `src/application/use_cases/cage/register_biometry_use_case.py`

- [x] Crear clase `RegisterBiometryUseCase`
- [x] Inyectar `ICageRepository` y `IBiometryLogRepository`
- [x] Implementar método `execute(cage_id: str, request: RegisterBiometryRequest)`
- [x] Lógica:
  1. Obtener Cage del repositorio
  2. Guardar valores OLD (snapshot antes de actualizar)
  3. Actualizar Cage usando métodos existentes
  4. Crear registro en `BiometryLog` con OLD y NEW
  5. Persistir Cage actualizado
  6. Persistir BiometryLog
  7. Retornar None (patrón transaccional: todo o nada)

**Archivo:** `src/application/use_cases/cage/list_biometry_use_case.py`

- [x] Crear clase `ListBiometryUseCase`
- [x] Implementar método `execute(cage_id: str, limit: int)`
- [x] Retornar lista de registros de biometría

#### 1.7. API Endpoint

**Archivo:** `src/api/dependencies.py`

- [x] Agregar `get_biometry_log_repo()` para inyectar repositorio
- [x] Agregar `get_register_biometry_use_case()` para inyectar use case
- [x] Agregar `get_list_biometry_use_case()` para inyectar use case
- [x] Agregar Type Aliases: `RegisterBiometryUseCaseDep`, `ListBiometryUseCaseDep`

**Archivo:** `src/api/routers/cage_router.py`

- [x] Crear endpoint `POST /api/cages/{cage_id}/biometry`
- [x] Validar request body con Pydantic (automático)
- [x] Inyectar `RegisterBiometryUseCase` con Depends
- [x] Manejar errores (404, 400, 500)
- [x] Retornar 200 OK con mensaje

**Archivo:** `src/api/routers/cage_router.py`

- [x] Crear endpoint `GET /api/cages/{cage_id}/biometry?limit=50`
- [x] Inyectar `ListBiometryUseCase` con Depends
- [x] Retornar lista de registros

#### 1.8. Testing

**Archivo:** `src/test/application/use_cases/cage/test_register_biometry_use_case.py`

- [ ] Test: Actualizar solo fish_count
- [ ] Test: Actualizar solo average_weight
- [ ] Test: Actualizar ambos
- [ ] Test: Error si no se proporciona ninguno
- [ ] Test: Error si jaula no existe
- [ ] Test: Verificar que se crea registro en log

#### 1.9. Documentación

**Archivo:** `docs/API_CAGES.md`

- [ ] Documentar endpoint POST `/api/cages/{cage_id}/biometry`
- [ ] Documentar endpoint GET `/api/cages/{cage_id}/biometry`
- [ ] Agregar ejemplos de request/response

---

## ETAPA 2: Endpoint de Mortalidad

**Endpoint:** `POST /api/cages/{cage_id}/mortality`

**Request Body:**

```json
{
  "dead_fish_count": 50,
  "mortality_date": "2025-11-21",
  "note": "Mortalidad detectada en sector sur"
}
```

### Tareas

#### 2.1. Value Object de Dominio (HACER PRIMERO)

**Archivo:** `src/domain/value_objects/mortality_log_entry.py`

- [ ] Crear dataclass `MortalityLogEntry` (inmutable, frozen=True)
- [ ] Definir todos los campos del log:
  - `mortality_id: UUID`
  - `cage_id: UUID`
  - `dead_fish_count: int`
  - `mortality_date: date`
  - `note: Optional[str]`
  - `created_at: datetime`
- [ ] Agregar factory method `create()` para crear nuevos registros
- [ ] Agregar validación: `dead_fish_count` debe ser > 0

**Nota:** Es un VO inmutable, no una entidad. Solo se crea y se consulta.

#### 2.2. Modelo de Persistencia

**Archivo:** `src/infrastructure/persistence/models/mortality_log_model.py`

- [ ] Crear clase `MortalityLogModel(SQLModel, table=True)`
- [ ] Definir campos según schema
- [ ] Definir índice en `cage_id` y `mortality_date`
- [ ] Implementar método `from_domain(entry: MortalityLogEntry)`
- [ ] Implementar método `to_domain() -> MortalityLogEntry`

#### 2.3. Migración de Base de Datos

- [ ] Generar migración con: `alembic revision --autogenerate -m "create_cage_mortality_log_table"`
- [ ] Revisar migración generada (verificar índices y foreign keys)
- [ ] Aplicar migración: `alembic upgrade head`

#### 2.4. Capa de Dominio (Cage)

**Archivo:** `src/domain/aggregates/cage.py`

- [ ] Verificar método `register_mortality(dead_count: FishCount)` existente
- [ ] Ajustar validaciones si es necesario
- [ ] **IMPORTANTE**: Asegurar que NO modifica `current_fish_count` (solo validación)

#### 2.5. Repositorio

**Archivo:** `src/infrastructure/persistence/repositories/mortality_log_repository.py`

- [ ] Crear interfaz `IMortalityLogRepository` en `src/domain/repositories.py`
- [ ] Implementar clase `MortalityLogRepository`
- [ ] Implementar método `save(log_entry: MortalityLogEntry) -> None`
- [ ] Implementar método `list_by_cage(cage_id: CageId, offset: int, limit: int) -> List[MortalityLogEntry]`
  - Con paginación (offset/limit)
  - Ordenado por `mortality_date DESC, created_at DESC`
- [ ] Implementar método `count_by_cage(cage_id: CageId) -> int`
  - Para información de paginación
- [ ] Implementar método `get_total_mortality(cage_id: CageId) -> int`
  - Calcula `SUM(dead_fish_count)` desde `cage_mortality_log`
  - Retorna 0 si no hay registros
  - Query: `SELECT COALESCE(SUM(dead_fish_count), 0) FROM cage_mortality_log WHERE cage_id = ?`

#### 2.6. DTOs

**Archivo:** `src/application/dtos/mortality_dtos.py`

- [ ] Crear `RegisterMortalityRequest` dataclass
  - `dead_fish_count: int`
  - `mortality_date: date`
  - `note: Optional[str] = None`
- [ ] ~~Crear `RegisterMortalityResponse`~~ **NO NECESARIO** - Endpoint retorna solo 200 OK
- [ ] Crear `MortalityLogItemResponse` dataclass (para listado GET)
  - `mortality_id: str`
  - `cage_id: str`
  - `dead_fish_count: int`
  - `mortality_date: str` (formato ISO)
  - `note: Optional[str]`
  - `created_at: str` (formato ISO)
- [ ] Crear `PaginatedMortalityResponse` dataclass
  - `items: List[MortalityLogItemResponse]`
  - `total: int`
  - `offset: int`
  - `limit: int`

#### 2.7. Use Case

**Archivo:** `src/application/use_cases/cage/register_mortality_use_case.py`

- [ ] Crear clase `RegisterMortalityUseCase`
- [ ] Inyectar `ICageRepository` y `IMortalityLogRepository`
- [ ] Implementar método `execute(cage_id: str, request: RegisterMortalityRequest) -> None`
- [ ] Lógica:
  1. Obtener Cage del repositorio (lanza CageNotFoundError si no existe)
  2. Validar que la jaula tenga población usando `cage.register_mortality(dead_count)`
  3. **IMPORTANTE**: NO modificar `current_fish_count` en Cage
  4. Crear `MortalityLogEntry` usando factory method `create()`
  5. Persistir registro en `cage_mortality_log` usando repositorio
  6. Retornar None (patrón transaccional: todo o nada)

**Archivo:** `src/application/use_cases/cage/list_mortality_use_case.py`

- [ ] Crear clase `ListMortalityUseCase`
- [ ] Inyectar `IMortalityLogRepository`
- [ ] Implementar método `execute(cage_id: str, offset: int, limit: int) -> PaginatedMortalityResponse`
- [ ] Lógica:
  1. Obtener lista de registros con `list_by_cage(cage_id, offset, limit)`
  2. Obtener total con `count_by_cage(cage_id)`
  3. Mapear a DTOs de respuesta
  4. Retornar respuesta paginada

#### 2.8. API Endpoint

**Archivo:** `src/api/dependencies.py`

- [ ] Agregar `get_mortality_log_repo()` para inyectar repositorio
- [ ] Agregar `get_register_mortality_use_case()` para inyectar use case
- [ ] Agregar `get_list_mortality_use_case()` para inyectar use case
- [ ] Agregar Type Aliases: `RegisterMortalityUseCaseDep`, `ListMortalityUseCaseDep`

**Archivo:** `src/api/routers/cage_router.py`

- [ ] Crear endpoint `POST /api/cages/{cage_id}/mortality`
- [ ] Validar request body con Pydantic (automático)
- [ ] Inyectar `RegisterMortalityUseCase` con Depends
- [ ] Manejar errores (404, 400, 500)
- [ ] Retornar 200 OK con mensaje
- [ ] **IMPORTANTE**: Aclarar en docstring que NO modifica `current_fish_count`

**Archivo:** `src/api/routers/cage_router.py`

- [ ] Crear endpoint `GET /api/cages/{cage_id}/mortality?offset=0&limit=50`
- [ ] Inyectar `ListMortalityUseCase` con Depends
- [ ] Validar query parameters (offset >= 0, limit > 0)
- [ ] Retornar respuesta paginada

#### 2.9. Testing

**Archivo:** `src/test/application/use_cases/cage/test_register_mortality_use_case.py`

- [ ] Test: Registrar mortalidad exitosamente
- [ ] Test: Error si jaula no existe
- [ ] Test: Error si jaula no tiene población
- [ ] Test: Error si dead_fish_count <= 0
- [ ] Test: Verificar que NO modifica current_fish_count
- [ ] Test: Verificar que se crea registro en log

#### 2.10. Documentación

**Archivo:** `docs/API_CAGES.md`

- [ ] Documentar endpoint POST `/api/cages/{cage_id}/mortality`
- [ ] Documentar endpoint GET `/api/cages/{cage_id}/mortality`
- [ ] Agregar ejemplos de request/response
- [ ] **IMPORTANTE**: Aclarar que NO modifica `current_fish_count`
- [ ] Explicar que `total_mortality` se calcula desde el log cuando se necesita

---

## ETAPA 3: Endpoint de Configuración

**Endpoint:** `PATCH /api/cages/{cage_id}/config`

**Request Body:**

```json
{
  "fcr": 1.2,
  "volume_m3": 1500,
  "max_density_kg_m3": 15.0,
  "feeding_table_id": "table-1",
  "transport_time_seconds": 120,
  "change_reason": "Ajuste por condiciones climáticas"
}
```

### Tareas

#### 3.1. Value Object de Dominio (HACER PRIMERO)

**Archivo:** `src/domain/value_objects/config_change_log_entry.py`

- [ ] Crear dataclass `ConfigChangeLogEntry` (inmutable, frozen=True)
- [ ] Definir todos los campos del log:
  - `change_id: UUID`
  - `cage_id: UUID`
  - `field_name: str`
  - `old_value: str`
  - `new_value: str`
  - `change_reason: Optional[str]`
  - `created_at: datetime`
- [ ] Agregar factory method `create()` para crear nuevos registros
- [ ] Agregar validación: `old_value` != `new_value` (solo crear log si hay cambio real)

**Nota:** Es un VO inmutable, no una entidad. Solo se crea y se consulta.

#### 3.2. Modelo de Persistencia

**Archivo:** `src/infrastructure/persistence/models/config_change_log_model.py`

- [ ] Crear clase `ConfigChangeLogModel(SQLModel, table=True)`
- [ ] Definir campos según schema
- [ ] Definir índice en `cage_id` y `created_at`
- [ ] Implementar método `from_domain(entry: ConfigChangeLogEntry)`
- [ ] Implementar método `to_domain() -> ConfigChangeLogEntry`

#### 3.3. Migración de Base de Datos

- [ ] Generar migración con: `alembic revision --autogenerate -m "create_cage_config_changes_log_table"`
- [ ] Revisar migración generada (verificar índices y foreign keys)
- [ ] Aplicar migración: `alembic upgrade head`

#### 3.4. Capa de Dominio (Cage)

**Archivo:** `src/domain/aggregates/cage.py`

- [ ] Verificar que existen métodos/propiedades para actualizar:
  - `fcr` (ya existe como propiedad)
  - `total_volume` (ya existe como propiedad)
  - `max_density` (ya existe como propiedad)
  - `feeding_table_id` (verificar si existe)
  - `transport_time` (verificar si existe)
- [ ] Agregar setters/métodos si faltan
- [ ] Verificar validaciones en cada setter

#### 3.5. Repositorio

**Archivo:** `src/infrastructure/persistence/repositories/config_change_log_repository.py`

- [ ] Crear interfaz `IConfigChangeLogRepository` en `src/domain/repositories.py`
- [ ] Implementar clase `ConfigChangeLogRepository`
- [ ] Implementar método `save_batch(log_entries: List[ConfigChangeLogEntry]) -> None`
  - Guarda múltiples cambios en una sola transacción
  - Útil cuando se actualizan varios campos a la vez
- [ ] Implementar método `list_by_cage(cage_id: CageId, offset: int, limit: int) -> List[ConfigChangeLogEntry]`
  - Con paginación (offset/limit)
  - Ordenado por `created_at DESC`
- [ ] Implementar método `count_by_cage(cage_id: CageId) -> int`
  - Para información de paginación

#### 3.6. DTOs

**Archivo:** `src/application/dtos/config_dtos.py`

- [ ] Crear `UpdateCageConfigRequest` dataclass
  - `fcr: Optional[float] = None`
  - `volume_m3: Optional[float] = None`
  - `max_density_kg_m3: Optional[float] = None`
  - `feeding_table_id: Optional[str] = None`
  - `transport_time_seconds: Optional[int] = None`
  - `change_reason: Optional[str] = None`
- [ ] ~~Crear `UpdateCageConfigResponse`~~ **NO NECESARIO** - Endpoint retorna solo 200 OK
- [ ] Crear `ConfigChangeLogItemResponse` dataclass (para listado GET)
  - `change_id: str`
  - `cage_id: str`
  - `field_name: str`
  - `old_value: str`
  - `new_value: str`
  - `change_reason: Optional[str]`
  - `created_at: str` (formato ISO)
- [ ] Crear `PaginatedConfigChangesResponse` dataclass
  - `items: List[ConfigChangeLogItemResponse]`
  - `total: int`
  - `offset: int`
  - `limit: int`

#### 3.7. Use Case

**Archivo:** `src/application/use_cases/cage/update_cage_config_use_case.py`

- [ ] Crear clase `UpdateCageConfigUseCase`
- [ ] Inyectar `ICageRepository` y `IConfigChangeLogRepository`
- [ ] Implementar método `execute(cage_id: str, request: UpdateCageConfigRequest) -> None`
- [ ] Lógica:
  1. Obtener Cage del repositorio (lanza CageNotFoundError si no existe)
  2. Crear lista vacía para almacenar cambios: `changes: List[ConfigChangeLogEntry] = []`
  3. Para cada campo en request (si no es None):
     - Obtener valor OLD del Cage
     - Si OLD != NEW:
       - Actualizar Cage usando setter correspondiente
       - Crear `ConfigChangeLogEntry` con OLD y NEW
       - Agregar a lista de cambios
  4. Si hay cambios:
     - Persistir Cage actualizado usando repositorio
     - Persistir batch de logs usando `save_batch(changes)`
  5. Retornar None (patrón transaccional: todo o nada)

**Archivo:** `src/application/use_cases/cage/list_config_changes_use_case.py`

- [ ] Crear clase `ListConfigChangesUseCase`
- [ ] Inyectar `IConfigChangeLogRepository`
- [ ] Implementar método `execute(cage_id: str, offset: int, limit: int) -> PaginatedConfigChangesResponse`
- [ ] Lógica:
  1. Obtener lista de cambios con `list_by_cage(cage_id, offset, limit)`
  2. Obtener total con `count_by_cage(cage_id)`
  3. Mapear a DTOs de respuesta
  4. Retornar respuesta paginada

#### 3.8. API Endpoint

**Archivo:** `src/api/dependencies.py`

- [ ] Agregar `get_config_change_log_repo()` para inyectar repositorio
- [ ] Agregar `get_update_cage_config_use_case()` para inyectar use case
- [ ] Agregar `get_list_config_changes_use_case()` para inyectar use case
- [ ] Agregar Type Aliases: `UpdateCageConfigUseCaseDep`, `ListConfigChangesUseCaseDep`

**Archivo:** `src/api/routers/cage_router.py`

- [ ] Crear endpoint `PATCH /api/cages/{cage_id}/config`
- [ ] Validar request body con Pydantic (automático)
- [ ] Inyectar `UpdateCageConfigUseCase` con Depends
- [ ] Manejar errores (404, 400, 500)
- [ ] Retornar 200 OK con mensaje
- [ ] **IMPORTANTE**: Solo crear logs si los valores realmente cambian

**Archivo:** `src/api/routers/cage_router.py`

- [ ] Crear endpoint `GET /api/cages/{cage_id}/config-changes?offset=0&limit=50`
- [ ] Inyectar `ListConfigChangesUseCase` con Depends
- [ ] Validar query parameters (offset >= 0, limit > 0)
- [ ] Retornar respuesta paginada

#### 3.9. Testing

**Archivo:** `src/test/application/use_cases/cage/test_update_cage_config_use_case.py`

- [ ] Test: Actualizar un solo campo
- [ ] Test: Actualizar múltiples campos
- [ ] Test: No crear log si valor no cambia (OLD == NEW)
- [ ] Test: Error si jaula no existe
- [ ] Test: Validaciones de valores (ej: fcr > 0, volume > 0)
- [ ] Test: Verificar que se crean registros en log solo para campos que cambiaron
- [ ] Test: Request vacío (todos None) no genera cambios

#### 3.10. Documentación

**Archivo:** `docs/API_CAGES.md`

- [ ] Documentar endpoint PATCH `/api/cages/{cage_id}/config`
- [ ] Documentar endpoint GET `/api/cages/{cage_id}/config-changes`
- [ ] Agregar ejemplos de request/response
- [ ] Listar campos configurables con sus validaciones
- [ ] Explicar que solo se crean logs para campos que realmente cambian

---

## ETAPA 4: Endpoint de Log Unificado

**Endpoint:** `GET /api/cages/{cage_id}/activity-log?type=all&offset=0&limit=50`

**Query Parameters:**

- `type`: `all` | `biometry` | `mortality` | `config` (default: `all`)
- `offset`: Cantidad de registros a saltar (default: 0)
- `limit`: Cantidad de registros (default: 50, max: 100)

**Response:**

```json
{
  "activities": [
    {
      "id": "uuid",
      "type": "biometry" | "mortality" | "config",
      "timestamp": "2025-11-21T10:30:00Z",
      "summary": "Descripción corta",
      "details": { /* Objeto específico por tipo */ }
    }
  ],
  "pagination": {
    "total": 150,
    "offset": 0,
    "limit": 50,
    "has_next": true,
    "has_previous": false
  }
}
```

### Tareas

#### 4.1. DTOs

**Archivo:** `src/application/dtos/activity_log_dtos.py`

- [ ] Crear `ActivityLogItemResponse` dataclass
  - `id: str`
  - `type: str` (biometry, mortality, config)
  - `timestamp: datetime`
  - `summary: str`
  - `details: dict`
- [ ] Crear `PaginatedActivityLogResponse` dataclass
  - `activities: List[ActivityLogItemResponse]`
  - `pagination: PaginationInfo`

**Nota:** Reutilizar `PaginationInfo` de otros DTOs para consistencia.

#### 4.2. Use Case

**Archivo:** `src/application/use_cases/cage/get_activity_log_use_case.py`

- [ ] Crear clase `GetActivityLogUseCase`
- [ ] Inyectar los 3 repositorios:
  - `IBiometryLogRepository`
  - `IMortalityLogRepository`
  - `IConfigChangeLogRepository`
- [ ] Implementar método `execute(cage_id: str, log_type: str, offset: int, limit: int) -> PaginatedActivityLogResponse`
- [ ] Lógica:
  1. Según `log_type`, consultar repositorios correspondientes con paginación
  2. Si `type=all`: consultar los 3 repositorios y mergear resultados
  3. Mapear cada tipo a `ActivityLogItemResponse` con formato unificado
  4. Ordenar por timestamp DESC
  5. Aplicar offset/limit al resultado mergeado
  6. Calcular total y paginación
  7. Retornar respuesta paginada
- [ ] Implementar métodos privados de mapeo:
  - `_map_biometry_to_activity(log: BiometryLogEntry) -> ActivityLogItemResponse`
  - `_map_mortality_to_activity(log: MortalityLogEntry) -> ActivityLogItemResponse`
  - `_map_config_to_activity(log: ConfigChangeLogEntry) -> ActivityLogItemResponse`

**Nota:** Operación de solo lectura, no requiere transacción.

#### 4.3. API Endpoint

**Archivo:** `src/api/dependencies.py`

- [ ] Agregar `get_activity_log_use_case()` para inyectar use case
- [ ] Agregar Type Alias: `GetActivityLogUseCaseDep`

**Archivo:** `src/api/routers/cage_router.py`

- [ ] Crear endpoint `GET /api/cages/{cage_id}/activity-log?type=all&offset=0&limit=50`
- [ ] Validar query parameters con Query (type, offset >= 0, limit entre 1-100)
- [ ] Inyectar `GetActivityLogUseCase` con Depends
- [ ] Manejar errores (404, 400, 500)
- [ ] Retornar respuesta paginada

#### 4.4. Testing

**Archivo:** `src/test/application/use_cases/cage/test_get_activity_log_use_case.py`

- [ ] Test: Obtener todos los tipos (type=all)
- [ ] Test: Filtrar por tipo específico (biometry, mortality, config)
- [ ] Test: Verificar ordenamiento por timestamp DESC
- [ ] Test: Verificar paginación funciona correctamente (offset/limit)
- [ ] Test: Verificar formato unificado de respuesta
- [ ] Test: Verificar merge correcto cuando type=all

#### 4.5. Documentación

**Archivo:** `docs/API_CAGES.md`

- [ ] Documentar endpoint GET `/api/cages/{cage_id}/activity-log`
- [ ] Documentar query parameters (type, offset, limit)
- [ ] Agregar ejemplos de response para cada tipo
- [ ] Explicar estructura unificada
- [ ] Aclarar que NO tiene user_id (sistema sin usuarios por ahora)

---

## ETAPA 5: Integración y Pruebas Finales

### Tareas

#### 5.1. Dependency Injection

**Archivo:** `src/api/dependencies.py`

- [x] Registrar `BiometryLogRepository` ✅
- [x] Registrar `MortalityLogRepository` ✅
- [x] Registrar `ConfigChangeLogRepository` ✅
- [x] Registrar todos los use cases ✅

#### 5.2. Migraciones Consolidadas

- [x] Verificar que todas las migraciones se aplican correctamente ✅
- [x] Verificar índices creados ✅
- [x] Verificar foreign keys ✅

#### 5.3. Testing de Integración

**Archivo:** `src/test/integration/test_cage_logs_endpoints.py`

- [ ] Test E2E: Registrar biometría y verificar en activity log
- [ ] Test E2E: Registrar mortalidad y verificar en activity log
- [ ] Test E2E: Actualizar config y verificar en activity log
- [ ] Test E2E: Verificar timeline unificado con múltiples eventos

#### 5.4. Documentación Final

**Archivo:** `docs/API_CAGES.md`

- [ ] Revisar y consolidar toda la documentación
- [ ] Agregar diagramas de flujo si es necesario
- [ ] Agregar ejemplos de uso completos

**Archivo:** `README_API.md`

- [ ] Actualizar con nuevos endpoints
- [ ] Agregar sección de logs y eventos

---

## Orden de Implementación Recomendado

1. ✅ **ETAPA 1** - Biometría (más complejo, establece patrón) - **COMPLETADA**
2. ✅ **ETAPA 2** - Mortalidad (similar a biometría) - **COMPLETADA**
3. ✅ **ETAPA 3** - Configuración (diferente, múltiples campos) - **COMPLETADA**
4. ⏳ **ETAPA 4** - Log Unificado (requiere las 3 anteriores) - **PENDIENTE**
5. ⏳ **ETAPA 5** - Integración y pruebas finales - **PENDIENTE**

---

## Estimación de Tiempo

| Etapa                   | Complejidad | Tiempo Estimado |
| ----------------------- | ----------- | --------------- |
| ETAPA 1 - Biometría     | Alta        | 6-8 horas       |
| ETAPA 2 - Mortalidad    | Media       | 4-5 horas       |
| ETAPA 3 - Configuración | Media-Alta  | 5-6 horas       |
| ETAPA 4 - Log Unificado | Media       | 3-4 horas       |
| ETAPA 5 - Integración   | Baja        | 2-3 horas       |
| **TOTAL**               |             | **20-26 horas** |

---

## Notas Importantes

### Validaciones Clave

- Biometría: `fish_count` y `average_weight_g` son opcionales, pero al menos uno debe estar presente
- Mortalidad: `dead_fish_count` debe ser > 0 y NO modifica `current_fish_count`
- Configuración: Solo crear log si el valor realmente cambió (OLD != NEW)
- Sin `user_id`: El sistema no maneja usuarios por ahora

### Mortalidad Acumulada

- **NO se persiste** en la tabla `cages`
- Se **calcula desde `cage_mortality_log`** usando `SUM(dead_fish_count)`
- Se incluye en la respuesta de `POST /api/cages/{cage_id}/mortality`
- Se incluye en el detalle de jaula (cuando se implemente `GET /api/cages/{cage_id}`)
- Ventajas: Fuente única de verdad, siempre consistente, fácil de auditar

### Performance

- Índices en todas las tablas de log por `(cage_id, date DESC)`
- Activity log unificado puede ser lento con muchos registros, considerar paginación
- `get_total_mortality()` es una query simple con índice, performance aceptable

### Seguridad

- Todos los endpoints validan que la jaula existe
- Sin autenticación por ahora (agregar `user_id` cuando se implemente)

### Extensibilidad

- El patrón de logs es reutilizable para otros agregados (feeding_line, silo, etc.)
- La estructura de activity log permite agregar nuevos tipos fácilmente
