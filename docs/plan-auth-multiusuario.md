# Plan de Implementacion: Autenticacion y Aislamiento de Datos por Usuario

**Fecha:** 2026-03-02
**Estado:** En progreso
**Branch:** `demo`

---

## Objetivo

Implementar autenticacion simple y aislamiento de datos por usuario para la version demo. Cada usuario solo ve y manipula sus propios recursos. No requiere seguridad robusta.

---

## Decisiones Tecnicas

| Aspecto | Decision |
|---------|----------|
| Estrategia de implementacion | En 3 fases |
| user_id | Solo en tablas raiz (11 tablas), hijas se filtran por relacion con padre |
| SystemConfig | Per-user (cambiar singleton a per-user) |
| Datos existentes | Migracion con nullable + seed script |
| Propagacion user_id | Parametro explicito en use cases y repositorios |
| JWT | PyJWT con HS256, expiracion 24h |
| Password hashing | hashlib SHA256 + salt (simple, para demo) |
| Unique constraints | Per-user (UniqueConstraint("name", "user_id")) |

---

## Tablas Raiz que Reciben `user_id`

| # | Tabla | Modelo | Notas |
|---|-------|--------|-------|
| 1 | `cages` | `CageModel` | |
| 2 | `silos` | `SiloModel` | |
| 3 | `foods` | `FoodModel` | |
| 4 | `feeding_lines` | `FeedingLineModel` | |
| 5 | `cage_groups` | `CageGroupModel` | |
| 6 | `feeding_sessions` | `FeedingSessionModel` | |
| 7 | `alerts` | `AlertModel` | |
| 8 | `scheduled_alerts` | `ScheduledAlertModel` | |
| 9 | `system_config` | `SystemConfigModel` | Cambiar PK de int(1) a user_id |
| 10 | `feedback` | `FeedbackModel` | |
| 11 | `slot_assignments` | `SlotAssignmentModel` | Tiene line_id pero necesita user_id para filtrar directo |

**Tablas hijas que NO necesitan user_id** (se filtran por padre):
- `blowers`, `dosers`, `selectors`, `sensors`, `coolers` -> via `feeding_lines.user_id`
- `cage_feedings`, `feeding_events` -> via `feeding_sessions.user_id`
- `cage_population_events`, `cage_biometry_log`, `cage_mortality_log`, `cage_config_changes_log` -> via `cages.user_id`

---

## FASE 1: Auth Core

**Estado:** Completada

### Archivos Nuevos

| Archivo | Descripcion |
|---------|-------------|
| `src/infrastructure/persistence/models/user_model.py` | Modelo SQLModel `UserModel` |
| `src/infrastructure/persistence/repositories/user_repository.py` | `UserRepository` con find_by_username, find_by_id, save |
| `src/domain/aggregates/user.py` | Aggregate `User` simple |
| `src/application/services/auth_service.py` | JWT encode/decode + password hash/verify (SHA256+salt) |
| `src/application/use_cases/auth/login_use_case.py` | `LoginUseCase` |
| `src/application/use_cases/auth/get_current_user_use_case.py` | `GetCurrentUserUseCase` (para /me) |
| `src/api/routers/auth_router.py` | `POST /api/auth/login`, `GET /api/auth/me` |
| `src/api/models/auth_models.py` | LoginRequest, LoginResponse, UserResponse |

### Archivos Existentes a Modificar

| Archivo | Cambio |
|---------|--------|
| `src/infrastructure/persistence/models/__init__.py` | Agregar `UserModel` |
| `src/domain/repositories.py` | Agregar `IUserRepository` |
| `src/domain/value_objects/identifiers.py` | Agregar `UserId` |
| `src/api/dependencies.py` | Agregar `get_current_user` dependency + factories auth |
| `src/api/routers/__init__.py` | Registrar `auth_router` |
| `alembic/env.py` | Agregar import de `UserModel` |
| `requirements.txt` | Agregar `PyJWT` |
| `.env.template` | Agregar `JWT_SECRET`, `JWT_EXPIRATION_HOURS` |

### Esquema de la tabla `users`

```
users:
  id: UUID (PK, auto-generado)
  username: str (unique, index)
  password_hash: str
  password_salt: str
  name: str
  role: str (default "admin")
  email: str | None
  created_at: datetime(tz)
```

### Endpoints de Auth

```
POST /api/auth/login
  Request:  { "username": str, "password": str }
  Response: {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": { "id", "username", "name", "role", "email" },
    "expires_in": 86400
  }
  Error 401: { "detail": "Credenciales invalidas" }

GET /api/auth/me
  Headers:  Authorization: Bearer {token}
  Response: { "id", "username", "name", "role", "email" }
  Error 401: { "detail": "Token invalido o expirado" }
```

### JWT Payload

```json
{
  "sub": "user_id (UUID string)",
  "username": "username",
  "exp": "now + 24h"
}
```

### Dependency de Auth

```python
# En dependencies.py
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    token = credentials.credentials
    payload = AuthService.decode_token(token)
    if not payload:
        raise HTTPException(401, "Token invalido o expirado")
    user_repo = UserRepository(session)
    user = await user_repo.find_by_id(UserId.from_string(payload["sub"]))
    if not user:
        raise HTTPException(401, "Usuario no encontrado")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
```

### Verificacion Fase 1

- [x] `POST /api/auth/login` con credenciales validas retorna token
- [x] `POST /api/auth/login` con credenciales invalidas retorna 401
- [x] `GET /api/auth/me` con token valido retorna datos del usuario
- [x] `GET /api/auth/me` sin token retorna 401/403
- [x] Swagger muestra candado en endpoints protegidos

---

## FASE 2: user_id en Tablas Raiz + Filtrado en Endpoints

**Estado:** Completada

### Migracion de DB

Una sola migracion que:
1. Agrega `user_id: UUID (nullable, FK -> users.id, index)` a las 11 tablas raiz
2. Cambia unique constraints de global a per-user:
   - `cages`: `UniqueConstraint("name", "user_id")`
   - `silos`: `UniqueConstraint("name", "user_id")`
   - `foods`: `UniqueConstraint("name", "user_id")`, `UniqueConstraint("code", "user_id")`
   - `feeding_lines`: `UniqueConstraint("name", "user_id")`
   - `cage_groups`: `UniqueConstraint("name", "user_id")`
3. Para `system_config`: agregar `user_id`, hacer que sea el identificador unico por usuario

### Patron de Cambio por Recurso

Para CADA recurso, modificar estas capas:

1. **Modelo SQLModel** (`*_model.py`): Agregar campo `user_id`
2. **Domain aggregate**: Agregar `_user_id: Optional[UserId]`
3. **Mapper** (`from_domain`/`to_domain`): Mapear `user_id`
4. **Repository interface** (`repositories.py`): Agregar `user_id` a metodos de lectura
5. **Repository implementation**: Agregar `WHERE user_id = :user_id`
6. **Use cases**: Recibir `user_id` y pasarlo al repositorio
7. **Router endpoints**: Inyectar `CurrentUser`, pasar `current_user.id`
8. **Dependencies.py**: Actualizar factories si es necesario

### Orden de Implementacion por Recurso

| Orden | Recurso | Endpoints | Complejidad |
|-------|---------|-----------|-------------|
| 1 | `feedback` | 1 (POST) | Baja |
| 2 | `foods` | 6 (CRUD + toggle) | Baja |
| 3 | `silos` | 5 (CRUD) | Baja-Media |
| 4 | `cages` | 16 (CRUD + sub-recursos) | Media |
| 5 | `cage_groups` | 5 (CRUD) | Baja |
| 6 | `alerts` + `scheduled_alerts` | 15 (CRUD + operaciones) | Media |
| 7 | `system_config` | 2 (GET + PATCH) | Media (cambiar singleton) |
| 8 | `feeding_lines` + `slot_assignments` | 7 (CRUD + componentes) | Media |
| 9 | `feeding_sessions` | 12+ (manual, cyclic, history) | Alta |

### Detalle: Unique Constraints a Cambiar

| Tabla | Actual | Nuevo |
|-------|--------|-------|
| `cages.name` | `unique=True` | `UniqueConstraint("name", "user_id")` |
| `silos.name` | `unique=True` | `UniqueConstraint("name", "user_id")` |
| `foods.name` | `unique=True` | `UniqueConstraint("name", "user_id")` |
| `foods.code` | `unique=True` | `UniqueConstraint("code", "user_id")` |
| `feeding_lines.name` | `unique=True` | `UniqueConstraint("name", "user_id")` |
| `cage_groups.name` | `unique=True` | `UniqueConstraint("name", "user_id")` |

### Verificacion Fase 2

- [x] Login como user1, crear cage -> OK
- [x] Login como user2, listar cages -> vacio
- [x] Login como user1, listar cages -> aparece el cage
- [x] Login como user2, crear cage con mismo nombre que user1 -> OK (unique per-user)
- [x] Intentar acceder a cage de user1 con token de user2 -> 404
- [x] Repetir para cada recurso: silos, foods, alerts, etc.

---

## FASE 3: Device Control + Seed + CORS

**Estado:** Completado

### Device Control (15 endpoints)

Los endpoints de blowers, dosers, selectors, coolers reciben un `device_id`. La validacion es:
1. Buscar device por ID -> obtener `line_id`
2. Buscar feeding_line -> verificar `user_id == current_user.id`
3. Si no coincide -> 404

**Endpoints afectados:**
- `POST /blowers/{id}/on|off|set-power`, `GET /blowers/{id}/status` (4)
- `POST /dosers/{id}/on|off|set-rate|set-speed`, `GET /dosers/{id}/status` (5)
- `POST /selectors/{id}/move|reset`, `GET /selectors/{id}/status` (3)
- `POST /coolers/{id}/on|off|set-power` (3)

### Sensor Endpoints (3 endpoints)

Ya reciben `line_id` como path parameter. Validar que la linea pertenece al usuario.
- `GET /feeding-lines/{id}/sensors/readings`
- `GET /feeding-lines/{id}/sensors`
- `PATCH /feeding-lines/{id}/sensors/{sensor_id}`

### Seed Script

**Archivo:** `scripts/seed_users.py`

```python
# Usuarios de prueba
users = [
    {"username": "demo1", "password": "demo123", "name": "Usuario Demo 1", "role": "admin", "email": "demo1@onix.com"},
    {"username": "demo2", "password": "demo123", "name": "Usuario Demo 2", "role": "admin", "email": "demo2@onix.com"},
    {"username": "demo3", "password": "demo123", "name": "Usuario Demo 3", "role": "admin", "email": "demo3@onix.com"},
]
```

El script:
1. Conecta a la DB
2. Crea los usuarios si no existen
3. Opcionalmente asigna datos existentes (sin user_id) al usuario demo1

### CORS

Agregar variable `CORS_ORIGINS` a `.env`:
```
CORS_ORIGINS=http://localhost:3000,https://tu-dominio-cloud.com
```

En `main.py`, parsear como lista y usar en `allow_origins`.

### Variables de Entorno Nuevas (totales)

```env
JWT_SECRET=una-clave-secreta-para-demo
JWT_EXPIRATION_HOURS=24
CORS_ORIGINS=http://localhost:3000
```

### Verificacion Fase 3

- [x] Device control: acceder a blower de linea de otro usuario -> 404
- [x] Seed script crea 3 usuarios correctamente
- [x] Login con demo1/demo123 funciona
- [x] CORS configurado correctamente para dominio cloud

---

## Resumen de Impacto

| Metrica | Cantidad |
|---------|----------|
| Archivos nuevos | ~10 |
| Archivos existentes modificados | ~50-60 |
| Tablas con nueva columna `user_id` | 11 |
| Endpoints que recibiran `Depends(get_current_user)` | ~90 |
| Migraciones nuevas | 2 (tabla users + user_id en tablas raiz) |
| Dependencias nuevas | 1 (PyJWT) |
| Unique constraints a cambiar | 6 |

---

## Riesgos y Mitigaciones

| Riesgo | Mitigacion |
|--------|-----------|
| Tests existentes se rompen por dependency de auth | Agregar mock de `get_current_user` en fixtures de test |
| Feeding sessions es el area mas compleja | Dejar para ultimo; el `operator_id` existente facilita la transicion |
| SystemConfig singleton -> per-user rompe el patron | Migracion cuidadosa: agregar user_id, cambiar queries |
| Unique constraints globales -> per-user | Migracion debe drop+recreate constraints |

---

## Contrato Frontend (no cambia)

| Aspecto | Comportamiento |
|---------|---------------|
| Login | `POST /api/auth/login` con `{username, password}` -> `{access_token, token_type, user, expires_in}` |
| Token | `localStorage` + header `Authorization: Bearer {token}` en cada request |
| Validacion | `GET /api/auth/me` al recargar app |
| 401 | Limpia sesion y redirige a `/login` |
| Aislamiento | Frontend confia en que backend solo retorna data del usuario autenticado |

---

## Progreso

- [x] **FASE 1:** Auth Core (modelo, JWT, login, dependency)
- [x] **FASE 2:** user_id en tablas + filtrado en endpoints
  - [x] feedback
  - [x] foods
  - [x] silos
  - [x] cages
  - [x] cage_groups
  - [x] alerts + scheduled_alerts
  - [x] system_config
  - [x] feeding_lines + slot_assignments
  - [x] feeding_sessions
- [x] **FASE 3:** Device control + seed + CORS
  - [x] Device control validation
  - [x] Sensor validation
  - [x] Seed script
  - [x] CORS configuration
