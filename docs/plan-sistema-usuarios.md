# Plan de implementación: Sistema de usuarios y autenticación

> Estado: planificado  
> Objetivo: agregar autenticación por token JWT y auditoría de usuario en el backend, sin multi-tenencia.

---

## 1. Resumen de decisiones

| Tema | Decisión |
|------|----------|
| Login | `username` + `password` |
| Token | JWT con PyJWT, expira en **24 horas**, sin refresh tokens |
| Password hashing | `bcrypt` directo |
| Roles | `user` y `admin`; `adminOnix` es **superadmin** (`is_superadmin=True`) |
| `operator_id` en sesiones | UUID del usuario autenticado, guardado como string |
| Nombre visible en frontend | Respuestas incluyen `operator_name` |
| `operator_id` en request body | **Se elimina**; se obtiene del token |
| Admin por defecto | `adminOnix` / `OnixServicios`, creado al iniciar la app |
| `ActivityLogEntry.actor` | `username` (legible para auditoría) |
| `Alert.resolved_by` | `username` |
| Health/root | Abiertos sin token |
| CORS | No se modifica |
| Multi-tenencia | No. Recursos compartidos entre usuarios autenticados |

### Dependencias a agregar

```text
PyJWT==2.10.1
bcrypt==4.2.0
```

### Variables de entorno a agregar

```env
JWT_SECRET_KEY=cambia-esto-en-produccion
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 2. Fases de implementación

### Fase 0 — Revertir migración errónea

**Objetivo:** eliminar las columnas `user_id` agregadas por la migración `720a03b05d34_add_user_id_to_11_root_tables.py`.

**Archivo a crear:**
- Nueva migración Alembic `revert_user_id_from_root_tables.py`

**Tablas a limpiar:**
- `alerts`
- `cage_groups`
- `cages`
- `feedback`
- `feeding_lines`
- `feeding_sessions`
- `foods`
- `scheduled_alerts`
- `silos`
- `slot_assignments`
- `system_config`

**Nota:** el campo `operator_id` de `feeding_sessions` **no** se toca, ya que se reutilizará para auditoría.

---

### Fase 1 — Fundamentos de autenticación

#### Dominio

| Archivo | Contenido |
|---------|-----------|
| `src/domain/aggregates/user.py` | `UserRole` enum y aggregate `User` |
| `src/domain/value_objects/identifiers.py` | `UserId` |
| `src/domain/repositories.py` | `IUserRepository` |
| `src/domain/exceptions.py` | `InvalidCredentialsError`, `UserInactiveError`, `UserAlreadyExistsError`, `InsufficientPermissionsError` |

#### Infraestructura

| Archivo | Contenido |
|---------|-----------|
| `src/infrastructure/persistence/models/user_model.py` | `UserModel` (SQLModel) |
| `src/infrastructure/persistence/repositories/user_repository.py` | `UserRepository` |
| `src/infrastructure/security/password_service.py` | Hashing y verificación con bcrypt |
| `src/infrastructure/security/token_service.py` | Creación y decodificación de JWT |
| `src/infrastructure/security/jwt_config.py` | Lectura de variables JWT desde `.env` |
| Migración Alembic | Crear tabla `users` |

#### Aplicación

| Archivo | Contenido |
|---------|-----------|
| `src/application/dtos/auth_dtos.py` | `LoginRequest`, `LoginResponse`, `UserResponse`, `RegisterUserRequest`, `ChangePasswordRequest` |
| `src/application/use_cases/auth/authenticate_user_use_case.py` | Login |
| `src/application/use_cases/auth/register_user_use_case.py` | Crear usuario |
| `src/application/use_cases/auth/change_password_use_case.py` | Cambiar contraseña propia |
| `src/application/use_cases/auth/get_current_user_use_case.py` | Obtener usuario desde token |
| `src/application/use_cases/users/list_users_use_case.py` | Listar usuarios |
| `src/application/use_cases/users/update_user_status_use_case.py` | Activar/desactivar usuario |
| `src/application/use_cases/users/update_user_role_use_case.py` | Cambiar rol |
| `src/application/use_cases/users/reset_user_password_use_case.py` | Resetear contraseña |

---

### Fase 2 — API de autenticación y gestión de usuarios

#### Router de autenticación

**Archivo:** `src/api/routers/auth_router.py`

| Método | Endpoint | Descripción | Permiso |
|--------|----------|-------------|---------|
| POST | `/api/auth/login` | Devuelve access token | Público |
| GET | `/api/auth/me` | Devuelve usuario actual | Autenticado |
| PATCH | `/api/auth/me/password` | Cambiar contraseña propia | Autenticado |

#### Router de usuarios

**Archivo:** `src/api/routers/users_router.py`

| Método | Endpoint | Descripción | Permiso |
|--------|----------|-------------|---------|
| POST | `/api/users` | Crear usuario | Admin o superadmin |
| GET | `/api/users` | Listar usuarios | Admin o superadmin |
| PATCH | `/api/users/{id}/status` | Activar/desactivar usuario | Admin (solo `user`) / superadmin (todos) |
| PATCH | `/api/users/{id}/role` | Cambiar rol de usuario | Superadmin |
| PATCH | `/api/users/{id}/password` | Resetear contraseña | Superadmin |

#### Modelos y registro

- `src/api/models/auth_models.py`
- `src/api/models/user_models.py`
- Registrar routers en `src/api/routers/__init__.py`

---

### Fase 3 — Dependencias de seguridad en FastAPI

**Archivo:** `src/api/dependencies.py`

Dependencias a crear:
- `get_current_user`
- `get_current_admin_user`
- `get_current_superadmin_user`

Type aliases a exportar:
- `CurrentUserDep`
- `CurrentAdminUserDep`
- `CurrentSuperAdminUserDep`

---

### Fase 4 — Proteger endpoints existentes

Inyectar `current_user: CurrentUserDep` en todos los routers existentes:

- `src/api/routers/cage_router.py`
- `src/api/routers/cage_group_router.py`
- `src/api/routers/silo_router.py`
- `src/api/routers/food_router.py`
- `src/api/routers/feeding_line_router.py`
- `src/api/routers/feeding_router.py`
- `src/api/routers/sensor_router.py`
- `src/api/routers/device_control_router.py`
- `src/api/routers/alerts_router.py`
- `src/api/routers/feedback_router.py`
- `src/api/routers/system_config_router.py`
- `src/api/routers/system_layout.py`

En esta fase solo se agrega autenticación. No se modifica lógica de negocio.

---

### Fase 5 — Auditoría en operaciones de alimentación

**Objetivo:** registrar quién inicia, pausa, reanuda y cancela cada alimentación.

#### Cambios en modelos de API

- `src/api/models/feeding_models.py`
  - Eliminar `operator_id` de `ManualFeedingRequest`
  - Eliminar `operator_id` de `CyclicFeedingRequest`
  - Agregar `operator_name` a `SessionHistoryItem`
  - Agregar `operator_name` a `SessionHistoryDetail`

#### Cambios en routers

- `src/api/routers/feeding_router.py`
  - Pasar `current_user.id` y `current_user.full_name` a los use cases

#### Cambios en DTOs de aplicación

- Ajustar request DTOs para no recibir `operator_id`

#### Cambios en use cases

- `src/application/use_cases/feeding/start_manual_feeding_use_case.py`
- `src/application/use_cases/feeding/start_cyclic_feeding_use_case.py`
- `src/application/use_cases/feeding/control_feeding_use_cases.py` (pause, resume, cancel, update_cage_mode)

Reglas:
- `FeedingSession.operator_id` = `str(current_user.id)`
- `FeedingEvent.data["operator_id"]` = `str(current_user.id)`
- `ActivityLogEntry.actor` = `current_user.username`
- Respuestas incluyen `operator_name` para mostrar en frontend

---

### Fase 6 — Auditoría en otras acciones

#### ActivityLog

Llenar `ActivityLogEntry.actor` con `current_user.username` en use cases de:

- Jaulas (`cage`):
  - Set population
  - Register mortality
  - Update biometry
  - Harvest
  - Adjust population
  - Update cage config
- Grupos de jaulas (`cage_group`)

#### Alertas

- Llenar `Alert.resolved_by` con `current_user.username` en use cases de alertas.
- Opcional: agregar `read_by` y `snoozed_by` si se requiere auditoría completa de alertas.

---

### Fase 7 — Admin por defecto

**Objetivo:** garantizar que exista un superadmin al iniciar la aplicación.

#### Archivos

- `src/infrastructure/services/default_admin_service.py`
  - Función `seed_default_admin_if_needed(session)`
  - Verifica si existe `adminOnix`
  - Si no existe, lo crea con:
    - `role = "admin"`
    - `is_superadmin = True`
    - `password = OnixServicios`
    - `is_active = True`

- `src/infrastructure/services/background_tasks.py`
  - Llamar a `seed_default_admin_if_needed` dentro del `lifespan_with_scheduler`

---

### Fase 8 — Tests

#### Tests nuevos

| Archivo | Cobertura |
|---------|-----------|
| `src/test/domain/test_user.py` | Creación, roles, validaciones de `User` |
| `src/test/api/test_auth_router.py` | Login exitoso/fallido, token inválido, `/me` |
| `src/test/api/test_users_router.py` | CRUD de usuarios, permisos de admin/superadmin |
| `src/test/api/test_auth_required.py` | Endpoints protegidos rechazan peticiones sin token |

#### Tests a ajustar

- `src/test/api/conftest.py`
  - Agregar fixture `auth_headers` que genere un token de prueba
- Tests de API e integración existentes
  - Inyectar autenticación en las peticiones

#### Calidad

- `ruff check src/`
- `mypy src/`
- `pytest`

---

### Fase 9 — Documentación

| Archivo | Cambio |
|---------|--------|
| `.env.template` | Agregar variables JWT |
| `README.md` | Documentar endpoints de auth y flujo de login |
| `AGENTS.md` | Actualizar si se agregan comandos o convenciones nuevas |

---

## 3. Modelo de permisos

| Rol | Permisos |
|-----|----------|
| `user` | Operar el sistema (alimentaciones, consultar estados, cambiar configuraciones operativas). No puede crear ni gestionar usuarios. |
| `admin` | Todo lo de `user`, más crear/listar/desactivar usuarios con rol `user`. Puede cambiar su propia contraseña. |
| `superadmin` | Todo lo de `admin`, más crear/modificar/desactivar otros admins, cambiar roles y resetear contraseñas de cualquier usuario. |

**Nota:** solo `adminOnix` se crea como superadmin por defecto. El superadmin puede crear más superadmins si es necesario.

---

## 4. Notas de implementación

- El `operator_id` en `FeedingSession` y `FeedingEvent` se guarda como string para no modificar el esquema actual. El valor es `str(user.id)`.
- Las respuestas de historial de alimentación deben hacer join con `users` para devolver `operator_name`.
- `ActivityLogEntry.actor` y `Alert.resolved_by` guardan `username` directamente para facilitar la lectura humana.
- La migración errónea `720a03b05d34` debe revertirse antes de crear la tabla `users` para evitar conflictos.

---

## 5. Próximos pasos

1. Ejecutar **Fase 0**: revertir migración errónea.
2. Ejecutar **Fase 1**: crear fundamentos de autenticación.
3. Continuar con fases siguientes en orden.
