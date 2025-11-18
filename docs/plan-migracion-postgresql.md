# Plan de Migración: De Repositorios Mock a PostgreSQL con Unit of Work

**Fecha**: 2025-11-17  
**Versión**: 1.0  
**Estado**: Pendiente de implementación

---

## 🎯 Objetivo

Migrar el sistema de repositorios mock (en memoria) a repositorios PostgreSQL reales, implementando el patrón Unit of Work para garantizar transaccionalidad y consistencia de datos.

---

## 📋 Situación Actual

**Problemas identificados:**

1. ❌ Repositorios mock guardan en memoria (se pierde al reiniciar)
2. ❌ Cada repositorio SQL hace `commit()` individual
3. ❌ Sin transaccionalidad: si falla a mitad de operación, BD se corrompe
4. ❌ Router acoplado a repositorios mock globales
5. ❌ Sin inyección de dependencias de FastAPI
6. ❌ Endpoint `/reset` usa variables globales

**Estado actual del código:**

- ✅ Modelos SQLModel creados
- ✅ Repositorios SQL implementados
- ✅ AsyncEngine y AsyncSession configurados
- ❌ Repositorios hacen commit individual
- ❌ Router usa repos mock

---

## 🏗️ Arquitectura Objetivo

### Flujo Transaccional

```
Request → FastAPI DI
    ↓
get_session() abre transacción
    ↓
Crea repositorios (misma session)
    ↓
Crea caso de uso con repositorios
    ↓
Endpoint ejecuta caso de uso
    ↓
Caso de uso opera (sin commits)
    ↓
Si OK → session.commit() ✅
Si Error → session.rollback() ✅
```

### Estructura de Dependencias

```
Session (FastAPI DI)
    ↓
Repositorios (reciben session)
    ↓
Caso de Uso (recibe repositorios)
    ↓
Endpoint (recibe caso de uso)
```

---

## 📝 Plan de Implementación

### **FASE 1: Implementar Unit of Work en Session**

#### 1.1. Actualizar `get_session()` para manejar transacciones

**Archivo**: `src/infrastructure/persistence/database.py`

**Cambio**:

```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador de sesiones (Unit of Work) para DI en FastAPI.

    Maneja automáticamente commit/rollback para toda la transacción:
    - Si el endpoint termina sin errores → commit
    - Si hay excepción → rollback
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Validación**: Verificar que no hay errores de sintaxis

---

### **FASE 2: Remover Commits de Repositorios**

#### 2.1. Actualizar `SiloRepository`

**Archivo**: `src/infrastructure/persistence/repositories/silo_repository.py`

**Cambios**:

- Eliminar `await self.session.commit()` de `save()`
- Eliminar `await self.session.commit()` de `delete()`

**Razón**: La session manejará el commit al final de la transacción completa

---

#### 2.2. Actualizar `CageRepository`

**Archivo**: `src/infrastructure/persistence/repositories/cage_repository.py`

**Cambios**:

- Eliminar `await self.session.commit()` de `save()`
- Eliminar `await self.session.commit()` de `delete()`

---

#### 2.3. Actualizar `FeedingLineRepository`

**Archivo**: `src/infrastructure/persistence/repositories/feeding_line_repository.py`

**Cambios**:

- Eliminar `await self.session.commit()` de `save()`
- Eliminar `await self.session.commit()` de `delete()`

---

### **FASE 3: Crear Sistema de Inyección de Dependencias**

#### 3.1. Crear archivo de dependencias

**Archivo**: `src/api/dependencies.py` (nuevo)

**Contenido**:

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.database import get_session
from infrastructure.persistence.repositories import (
    SiloRepository,
    CageRepository,
    FeedingLineRepository
)
from application.use_cases import (
    SyncSystemLayoutUseCase,
    GetSystemLayoutUseCase
)
from domain.factories import ComponentFactory

# Dependencias de repositorios
async def get_silo_repo(
    session: AsyncSession = Depends(get_session)
) -> SiloRepository:
    return SiloRepository(session)

async def get_cage_repo(
    session: AsyncSession = Depends(get_session)
) -> CageRepository:
    return CageRepository(session)

async def get_line_repo(
    session: AsyncSession = Depends(get_session)
) -> FeedingLineRepository:
    return FeedingLineRepository(session)

def get_component_factory() -> ComponentFactory:
    return ComponentFactory()

# Dependencias de casos de uso
async def get_sync_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    silo_repo: SiloRepository = Depends(get_silo_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    factory: ComponentFactory = Depends(get_component_factory)
) -> SyncSystemLayoutUseCase:
    return SyncSystemLayoutUseCase(
        line_repo=line_repo,
        silo_repo=silo_repo,
        cage_repo=cage_repo,
        component_factory=factory
    )

async def get_get_use_case(
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    silo_repo: SiloRepository = Depends(get_silo_repo),
    cage_repo: CageRepository = Depends(get_cage_repo)
) -> GetSystemLayoutUseCase:
    return GetSystemLayoutUseCase(
        line_repo=line_repo,
        silo_repo=silo_repo,
        cage_repo=cage_repo
    )

# Type aliases para endpoints
SyncUseCaseDep = Annotated[SyncSystemLayoutUseCase, Depends(get_sync_use_case)]
GetUseCaseDep = Annotated[GetSystemLayoutUseCase, Depends(get_get_use_case)]
```

---

### **FASE 4: Refactorizar Router**

#### 4.1. Actualizar imports del router

**Archivo**: `src/api/routers/system_layout.py`

**Eliminar**:

```python
from infrastructure.persistence.mock_repositories import (
    MockFeedingLineRepository,
    MockSiloRepository,
    MockCageRepository
)

# Variables globales
_line_repo = MockFeedingLineRepository()
_silo_repo = MockSiloRepository()
_cage_repo = MockCageRepository()

def get_sync_system_layout_use_case() -> SyncSystemLayoutUseCase:
    ...
```

**Agregar**:

```python
from api.dependencies import SyncUseCaseDep, GetUseCaseDep
```

---

#### 4.2. Refactorizar endpoint `POST /`

**Archivo**: `src/api/routers/system_layout.py`

**Antes**:

```python
async def save_system_layout(request: SystemLayoutModel) -> SystemLayoutModel:
    use_case = get_sync_system_layout_use_case()
    silos, cages, lines = await use_case.execute(request)
    response = ResponseMapper.to_system_layout_model(silos, cages, lines)
    return response
```

**Después**:

```python
async def save_system_layout(
    request: SystemLayoutModel,
    use_case: SyncUseCaseDep
) -> SystemLayoutModel:
    silos, cages, lines = await use_case.execute(request)
    return ResponseMapper.to_system_layout_model(silos, cages, lines)
```

---

#### 4.3. Refactorizar endpoint `GET /export`

**Archivo**: `src/api/routers/system_layout.py`

**Antes**:

```python
async def export_system() -> SystemLayoutModel:
    use_case = get_get_system_layout_use_case()
    silos, cages, lines = await use_case.execute()
    response = ResponseMapper.to_system_layout_model(silos, cages, lines)
    return response
```

**Después**:

```python
async def export_system(use_case: GetUseCaseDep) -> SystemLayoutModel:
    silos, cages, lines = await use_case.execute()
    return ResponseMapper.to_system_layout_model(silos, cages, lines)
```

---

#### 4.4. Eliminar endpoints auxiliares de testing

**Archivo**: `src/api/routers/system_layout.py`

**Eliminar**:

- Endpoint `GET /status` (usa repos mock globales)
- Endpoint `DELETE /reset` (usa variables globales)

**Razón**: Estos endpoints eran para testing con repos mock. Con BD real no son necesarios.

**Alternativa**: Crear endpoints de health check si es necesario:

```python
@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
```

---

### **FASE 5: Testing y Validación**

#### 5.1. Verificar conexión a BD

**Test manual**:

```bash
# Conectar a PostgreSQL
psql -h localhost -U postgres -d feeding_system

# Listar tablas
\dt

# Verificar estructura
\d silos
\d cages
\d feeding_lines
```

---

#### 5.2. Probar endpoint POST con datos simples

**Request**:

```json
{
  "silos": [{ "id": "temp-1", "name": "Silo Test", "capacity": 1000.0 }],
  "cages": [],
  "feeding_lines": []
}
```

**Validar**:

- ✅ Datos guardados en BD
- ✅ Response con UUID real
- ✅ No errores en logs

---

#### 5.3. Probar rollback en caso de error

**Test**: Enviar request con nombre duplicado

**Validar**:

- ✅ Error 400 retornado
- ✅ BD sin cambios (rollback exitoso)
- ✅ No datos corruptos

---

#### 5.4. Probar endpoint GET /export

**Validar**:

- ✅ Retorna datos guardados
- ✅ IDs correctos
- ✅ Relaciones intactas

---

#### 5.5. Actualizar tests unitarios

**Archivos**: `src/test/application/use_cases/test_*.py`

**Cambios**:

- Usar repositorios SQL con session de test
- Configurar BD de test (SQLite in-memory o PostgreSQL test)
- Mockear session si es necesario

---

### **FASE 6: Limpieza y Documentación**

#### 6.1. Eliminar archivos obsoletos

**Eliminar**:

- `src/infrastructure/persistence/mock_repositories.py`

**Razón**: Ya no se usan repositorios mock

---

#### 6.2. Actualizar documentación

**Archivo**: `docs/README.md`

**Agregar sección**: "Configuración de Base de Datos"

**Contenido**:

- Variables de entorno requeridas
- Cómo ejecutar migraciones
- Cómo resetear BD de desarrollo

---

#### 6.3. Crear script de setup

**Archivo**: `scripts/setup_db.sh` (nuevo)

**Contenido**:

```bash
#!/bin/bash
# Script para configurar BD de desarrollo

echo "Aplicando migraciones..."
alembic upgrade head

echo "Base de datos lista!"
```

---

### **FASE 7: Configuración de Producción**

#### 7.1. Configurar manejo de shutdown

**Archivo**: `src/main.py`

**Agregar**:

```python
from infrastructure.persistence.database import close_db_connection

@app.on_event("shutdown")
async def shutdown():
    await close_db_connection()
```

---

#### 7.2. Configurar pool de conexiones para producción

**Archivo**: `src/infrastructure/persistence/database.py`

**Ajustar según carga esperada**:

```python
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Desactivar en producción
    pool_size=20,  # Ajustar según carga
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

---

#### 7.3. Configurar logging de BD

**Archivo**: `src/infrastructure/persistence/database.py`

**Agregar**:

```python
import logging

logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.WARNING)  # Solo warnings y errors
```

---

## ✅ Checklist de Implementación

### Fase 1: Unit of Work

- [x] 1.1. Actualizar `get_session()` con commit/rollback

### Fase 2: Repositorios

- [x] 2.1. Remover commits de `SiloRepository`
- [x] 2.2. Remover commits de `CageRepository`
- [x] 2.3. Remover commits de `FeedingLineRepository`

### Fase 3: Inyección de Dependencias

- [x] 3.1. Crear `api/dependencies.py`

### Fase 4: Router

- [x] 4.1. Actualizar imports
- [x] 4.2. Refactorizar `POST /`
- [x] 4.3. Refactorizar `GET /export`
- [x] 4.4. Eliminar endpoints de testing

### Fase 5: Testing

- [ ] 5.1. Verificar conexión a BD
- [ ] 5.2. Probar POST con datos simples
- [ ] 5.3. Probar rollback en error
- [ ] 5.4. Probar GET /export
- [ ] 5.5. Actualizar tests unitarios

### Fase 6: Limpieza

- [ ] 6.1. Eliminar `mock_repositories.py`
- [ ] 6.2. Actualizar documentación
- [ ] 6.3. Crear script de setup

### Fase 7: Producción

- [ ] 7.1. Configurar shutdown handler
- [ ] 7.2. Ajustar pool de conexiones
- [ ] 7.3. Configurar logging

---

## 🚨 Consideraciones Importantes

### 1. Backup antes de migrar

Hacer backup de datos mock si hay algo importante (probablemente no, pero por si acaso)

### 2. Testing exhaustivo

Probar especialmente:

- Creación de líneas completas con componentes
- Actualización de entidades existentes
- Eliminación en cascada
- Rollback en errores

### 3. Manejo de errores

El router ya tiene manejo de excepciones, pero verificar que capture todos los casos:

- `DomainException` → 400
- `ValueError` → 400
- `SQLAlchemyError` → 500
- Otros → 500

### 4. Performance

Con BD real, considerar:

- Índices en columnas frecuentemente consultadas
- Eager loading vs lazy loading
- Paginación si hay muchos registros

### 5. Migraciones

- Nunca editar migraciones aplicadas
- Siempre crear nueva migración para cambios
- Probar migraciones en entorno de desarrollo primero

---

## 📊 Resultado Esperado

Después de completar todas las fases:

✅ **Transaccionalidad garantizada** - Commit/rollback automático
✅ **BD PostgreSQL real** - Datos persistentes
✅ **Inyección de dependencias** - Router limpio y desacoplado
✅ **Sin corrupción de datos** - Rollback en errores
✅ **Listo para producción** - Pool configurado, logging, shutdown
✅ **Migraciones versionadas** - Alembic configurado
✅ **Tests actualizados** - Funcionan con BD real

---

**Próximos pasos**: Comenzar con Fase 1 (actualizar `get_session()`).
