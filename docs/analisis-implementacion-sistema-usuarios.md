# Análisis de la implementación del Sistema de Usuarios y Autenticación

> Fecha: 2026-07-01  
> Estado: plan implementado al 100%  
> Este documento recoge observaciones y deuda técnica detectada para abordar en una iteración posterior.

---

## Resumen ejecutivo

La implementación del plan de sistema de usuarios y autenticación está **sólida y alineada con el plan**. Se completaron las 9 fases, los tests pasan y la arquitectura respeta Clean Architecture. Sin embargo, existen algunos puntos de deuda técnica y mejoras de seguridad que conviene atender antes de considerar el sistema listo para producción.

---

## 🔴 Críticas / Deuda técnica importante

### 1. `alembic/env.py` no importa todos los modelos

Hoy `env.py` solo importa una parte de los modelos activos. Faltan, entre otros:

- `CageGroupModel`
- `ActivityLogModel`
- `AlertModel`
- `ScheduledAlertModel`
- `FeedbackModel`
- `FoodModel`
- `DoserSiloModel`
- `PopulationEventModel`
- `SlotAssignmentModel`
- `LastSelectedFeedingModeModel`
- `LastValidCyclicFeedingConfigModel`
- `LastValidManualFeedingConfigModel`

**Riesgo:** si en el futuro se ejecuta `alembic revision --autogenerate`, Alembic comparará contra un metadata incompleto y podría generar migraciones que **eliminen tablas existentes** o dupliquen índices.

**Evidencia:** al generar la migración de `cage_group_activity_log`, autogenerate detectó cambios ajenos (`users_username_key`, FKs de `slot_assignments`, etc.).

**Sugerencia:** importar todos los modelos activos en `env.py`, o importar el módulo `src.infrastructure.persistence.models` completo.

---

### 2. Credenciales del admin por defecto hardcodeadas en código

`src/infrastructure/services/default_admin_service.py` define:

```python
DEFAULT_ADMIN_USERNAME = "adminOnix"
DEFAULT_ADMIN_PASSWORD = "OnixServicios"
```

**Riesgo:** es fácil olvidar cambiarlas en producción y cualquier persona con acceso al repo conoce las credenciales iniciales.

**Sugerencia:** permitir sobreescribir mediante variables de entorno:

```python
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "adminOnix")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "OnixServicios")
```

Actualizar `.env.template`, `README.md` y `AGENTS.md` para documentar estas variables.

---

### 3. Posible race condition al crear el admin por defecto

`seed_default_admin_if_needed` ejecuta `find_by_username` y luego `save` en dos pasos. Si se levanta la app con varios workers de Uvicorn (`--workers 4`), varios workers pueden ejecutar el lifespan simultáneamente, ver que el admin no existe e intentar crearlo todos.

**Riesgo:** el segundo `save` fallará por el unique constraint de `username`. Aunque se captura la excepción en `lifespan_with_scheduler`, genera ruido en los logs y no es idempotente.

**Sugerencia:** capturar `IntegrityError` en el servicio y tratarlo como "ya existe", o usar `ON CONFLICT DO NOTHING` / upsert.

---

### 4. CORS abierto (`allow_origins=["*"]`)

El `main.py` configura CORS con `allow_origins=["*"]`. Aunque el plan indica no modificar CORS, esto es un riesgo de seguridad en producción.

**Sugerencia:**
- Documentar claramente que debe restringirse antes de deployar.
- Idealmente, leer los origins permitidos desde `.env`.

---

## 🟡 Observaciones medias

### 5. `test_auth_required.py` no prueba tokens inválidos o expirados

El test cubre muy bien el caso "sin token", pero no token malformado, token expirado o firma inválida. Sería bueno agregar un par de casos para robustecer la cobertura.

**Sugerencia:** agregar tests como:

- Header `Authorization: Bearer invalid_token` → 401
- Token con firma inválida → 401
- Token expirado → 401

---

### 6. Migración `create_users_table` vs modelo `UserModel`

La migración `08b43ca26a82_create_users_table.py` crea un índice no único sobre `username` (`unique=False`) y un `UniqueConstraint` aparte, mientras que el modelo `UserModel` define `Field(unique=True, index=True)`.

**Riesgo:** funciona, pero genera diferencias en autogenerate y puede confundir al equipo.

**Sugerencia:** alinear la migración con el modelo, o regenerar la migración con autogenerate una vez que `env.py` importe todos los modelos.

---

### 7. No hay rate limiting en `/api/auth/login`

El endpoint de login está expuesto a ataques de fuerza bruta.

**Sugerencia:**
- Agregar rate limiting por IP y/o por username (por ejemplo, con `slowapi`).
- O implementar bloqueo temporal tras varios intentos fallidos.

---

### 8. `ActivityLogEntry` está fuertemente acoplado a `cage_id`

Para soportar logs de grupos de jaulas fue necesario crear un VO separado (`CageGroupActivityLogEntry`). Esto es correcto, pero si en el futuro se agregan más logs no-jaula (silos, líneas, etc.) habrá que seguir creando VOs similares.

**Sugerencia a futuro:** considerar hacer `cage_id` opcional en `ActivityLogEntry` y usar `source_entity_type`/`source_entity_id` de forma más explícita para entidades no-jaula.

---

## 🟢 Lo que está bien

- **Arquitectura limpia:** las capas están separadas; los use cases reciben interfaces, no implementaciones concretas.
- **Auditoría consistente:** `operator_id` se obtiene del token, `operator_name` aparece en el historial y `actor = username` en logs de actividad.
- **Permisos bien implementados:** uso correcto de `CurrentAdminUserDep` y `CurrentSuperAdminUserDep`.
- **Tests:** buena cobertura de auth, endpoints protegidos, users y dominio.
- **Documentación:** README quedó claro con ejemplos de curl y roles.
- **Migraciones:** se creó y aplicó correctamente la tabla de logs de grupos.

---

## Recomendaciones de prioridad

| Prioridad | Tarea | Archivos afectados |
|-----------|-------|--------------------|
| Alta | Completar imports de modelos en `alembic/env.py` | `alembic/env.py` |
| Alta | Evitar hardcodear credenciales del admin por defecto | `src/infrastructure/services/default_admin_service.py`, `.env.template`, `README.md`, `AGENTS.md` |
| Alta | Hacer idempotente el seed del admin (manejar race condition) | `src/infrastructure/services/default_admin_service.py` |
| Media | Restringir CORS en producción | `src/main.py`, `.env.template` |
| Media | Agregar tests de token inválido/expirado | `src/test/api/test_auth_required.py` |
| Media | Alinear migración de `users` con el modelo | `alembic/versions/2026_07_01_1540-08b43ca26a82_create_users_table.py` |
| Baja | Rate limiting en login | `src/api/routers/auth_router.py` |
| Baja | Generalizar `ActivityLogEntry` para entidades no-jaula | `src/domain/value_objects/activity_log_entry.py` |
