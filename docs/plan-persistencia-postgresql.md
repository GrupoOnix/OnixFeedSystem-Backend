# Plan de Implementación: Persistencia PostgreSQL

## Objetivo

Implementar persistencia en base de datos PostgreSQL siguiendo principios DDD, Clean Architecture y SOLID, utilizando FastAPI moderno y las mejores prácticas recomendadas por arquitectos de software.

---

## 📐 Principios Arquitectónicos

### Clean Architecture

- **Domain Layer**: Permanece puro, sin dependencias externas
- **Application Layer**: Casos de uso usan abstracciones (interfaces)
- **Infrastructure Layer**: Implementaciones concretas de persistencia
- **API Layer**: Punto de entrada HTTP, sin lógica de negocio

### DDD (Domain-Driven Design)

- **Agregados**: Persistencia atómica por agregado raíz
- **Repositorios**: Interfaces en dominio, implementaciones en infraestructura
- **Entidades**: Modelos de dominio puros, sin anotaciones ORM
- **Value Objects**: Conversión explícita en mappers

### SOLID

- **SRP**: Cada clase tiene una única responsabilidad
- **OCP**: Extensible sin modificar código existente
- **LSP**: Implementaciones intercambiables vía interfaces
- **ISP**: Interfaces específicas por agregado
- **DIP**: Dependencias hacia abstracciones

---

## 📁 Estructura de Carpetas Propuesta

```
src/
├── domain/                          # Capa de Dominio (sin cambios)
│   ├── aggregates/
│   ├── repositories.py              # Interfaces de repositorios
│   ├── value_objects.py
│   └── exceptions.py
│
├── application/                     # Capa de Aplicación
│   ├── use_cases/
│   ├── dtos.py
│   └── ports/                       # NUEVO: Abstracciones adicionales
│       └── unit_of_work.py          # Interface IUnitOfWork
│
├── infrastructure/                  # Capa de Infraestructura
│   ├── database/                    # NUEVO: Configuración de BD
│   │   ├── __init__.py
│   │   ├── connection.py            # Engine y configuración
│   │   ├── session.py               # Session factory
│   │   └── base.py                  # Base declarativa
│   │
│   ├── persistence/
│   │   ├── sqlalchemy/              # NUEVO: Implementación SQLAlchemy
│   │   │   ├── __init__.py
│   │   │   ├── models/              # Modelos ORM
│   │   │   │   ├── __init__.py
│   │   │   │   ├── silo_model.py
│   │   │   │   ├── cage_model.py
│   │   │   │   ├── feeding_line_model.py
```

│ │ │ │ ├── doser_model.py
│ │ │ │ ├── blower_model.py
│ │ │ │ └── selector_model.py
│ │ │ │
│ │ │ ├── repositories/ # Implementaciones concretas
│ │ │ │ ├── **init**.py
│ │ │ │ ├── silo_repository.py
│ │ │ │ ├── cage_repository.py
│ │ │ │ └── feeding_line_repository.py
│ │ │ │
│ │ │ ├── mappers/ # Domain ↔ ORM
│ │ │ │ ├── **init**.py
│ │ │ │ ├── silo_mapper.py
│ │ │ │ ├── cage_mapper.py
│ │ │ │ └── feeding_line_mapper.py
│ │ │ │
│ │ │ └── unit_of_work.py # Implementación UoW
│ │ │
│ │ └── mock_repositories.py # Mantener para tests
│ │
│ └── config/ # NUEVO: Configuración
│ ├── **init**.py
│ └── settings.py # Pydantic Settings
│
├── api/ # Capa de API (sin cambios mayores)
│ ├── dependencies.py # MODIFICAR: Inyección de UoW
│ ├── routers/
│ ├── models/
│ └── mappers/
│
└── main.py # MODIFICAR: Inicialización BD

```

---
```

## 📦 Fase 1: Configuración de Dependencias

### 1.1 Actualizar requirements.txt

Agregar las siguientes dependencias:

```
# ORM y Base de Datos
sqlalchemy[asyncio]>=2.0.23    # ORM moderno con soporte async
asyncpg>=0.29.0                # Driver PostgreSQL async (el más rápido)
alembic>=1.13.0                # Migraciones de BD

# Configuración
pydantic-settings>=2.1.0       # Gestión de configuración con validación
python-dotenv>=1.0.0           # Variables de entorno

# Testing (opcional, si no están)
pytest-asyncio>=0.23.0         # Tests async
testcontainers>=3.7.0          # PostgreSQL en tests (opcional)
```

### 1.2 Justificación de tecnologías

- **SQLAlchemy 2.0+**: ORM estándar de Python, soporte async nativo, type hints
- **asyncpg**: Driver más rápido para PostgreSQL, compatible con asyncio
- **Alembic**: Herramienta oficial de SQLAlchemy para migraciones
- **pydantic-settings**: Validación de configuración con type safety

---

## 📋 Fase 2: Configuración de Base de Datos

### 2.1 Crear `infrastructure/config/settings.py`

**Objetivo**: Configuración centralizada con validación

**Contenido**:

- Clase `DatabaseSettings` con pydantic-settings
- Variables de entorno: `DATABASE_URL`, `DB_ECHO`, `DB_POOL_SIZE`, etc.
- Configuración por ambiente (dev, test, prod)
- Validación automática de URLs de conexión

**Principios aplicados**:

- **SRP**: Solo configuración, sin lógica de negocio
- **OCP**: Extensible para nuevas configuraciones sin modificar existente

### 2.2 Crear `infrastructure/database/connection.py`

**Objetivo**: Gestión del engine de SQLAlchemy

**Contenido**:

- Función `create_async_engine()` con configuración optimizada
- Pool de conexiones configurado según ambiente
- Logging SQL solo en desarrollo
- Configuración de timeouts y retry logic

**Consideraciones**:

- Pool size: 5-20 conexiones según carga esperada
- Pool recycle: 3600 segundos (1 hora) para evitar conexiones stale
- Echo SQL: Solo en desarrollo para debugging

### 2.3 Crear `infrastructure/database/session.py`

**Objetivo**: Factory de sesiones async

**Contenido**:

- `AsyncSessionLocal`: Session factory configurada
- Context manager `get_async_session()` para FastAPI dependency
- Configuración `expire_on_commit=False` para evitar lazy loading issues
- Manejo automático de commit/rollback

**Patrón**: Dependency Injection compatible con FastAPI

### 2.4 Crear `infrastructure/database/base.py`

**Objetivo**: Base declarativa y convenciones

**Contenido**:

- `Base` declarativa de SQLAlchemy
- Naming conventions para constraints (PK, FK, IX, UQ)
- Mixins opcionales (timestamps, soft delete)
- Configuración de metadata

**Beneficio**: Nombres consistentes de constraints en toda la BD

---

## 🗄️ Fase 3: Modelos ORM (SQLAlchemy)

### 3.1 Principios de diseño

**Separación de responsabilidades**:

- **Modelos ORM**: Representación de tablas, anotaciones SQLAlchemy
- **Entidades de Dominio**: Lógica de negocio, reglas de validación
- **Mappers**: Conversión explícita entre ambos

**Reglas**:

- Sufijo `Model` para distinguir de entidades (ej: `SiloModel` vs `Silo`)
- Sin lógica de negocio en modelos ORM
- Relaciones mínimas, solo las necesarias para queries eficientes
- Usar tipos SQLAlchemy apropiados (UUID, Numeric, JSONB, etc.)

### 3.2 Crear `infrastructure/persistence/sqlalchemy/models/silo_model.py`

**Tabla**: `silos`

**Campos**:

- `id`: UUID (PK)
- `name`: String(100), unique, not null
- `capacity`: Numeric(10, 2), not null
- `stock_level`: Numeric(10, 2), not null, default 0
- `is_assigned`: Boolean, not null, default False
- `created_at`: DateTime(timezone=True), not null, default now()
- `updated_at`: DateTime(timezone=True), nullable

**Constraints**:

- CHECK: `capacity > 0`
- CHECK: `stock_level >= 0`
- CHECK: `stock_level <= capacity`
- UNIQUE: `name`

**Índices**:

- PK en `id`
- UNIQUE en `name`
- INDEX en `is_assigned` (para queries de silos disponibles)

### 3.3 Crear `infrastructure/persistence/sqlalchemy/models/cage_model.py`

**Tabla**: `cages`

**Campos**:

- `id`: UUID (PK)
- `name`: String(100), unique, not null
- `status`: Enum('AVAILABLE', 'IN_USE'), not null
- `created_at`: DateTime(timezone=True), not null
- `updated_at`: DateTime(timezone=True), nullable

**Constraints**:

- UNIQUE: `name`

**Índices**:

- PK en `id`
- UNIQUE en `name`
- INDEX en `status`

### 3.4 Crear `infrastructure/persistence/sqlalchemy/models/feeding_line_model.py`

**Tabla**: `feeding_lines`

**Campos**:

- `id`: UUID (PK)
- `name`: String(100), unique, not null
- `created_at`: DateTime(timezone=True), not null
- `updated_at`: DateTime(timezone=True), nullable

**Relaciones**:

- 1:1 con `blowers`
- 1:1 con `selectors`
- 1:N con `dosers`
- 1:N con `slot_assignments`

### 3.5 Crear modelos de componentes

**`blower_model.py`** - Tabla `blowers`:

- `id`: UUID (PK)
- `feeding_line_id`: UUID (FK a feeding_lines), unique, not null
- `created_at`: DateTime

**`selector_model.py`** - Tabla `selectors`:

- `id`: UUID (PK)
- `feeding_line_id`: UUID (FK a feeding_lines), unique, not null
- `created_at`: DateTime

**`doser_model.py`** - Tabla `dosers`:

- `id`: UUID (PK)
- `feeding_line_id`: UUID (FK a feeding_lines), not null
- `silo_id`: UUID (FK a silos), nullable
- `slot_number`: Integer, not null
- `created_at`: DateTime
- UNIQUE constraint en (`feeding_line_id`, `slot_number`)

### 3.6 Crear tabla de asignaciones

**Tabla**: `slot_assignments`

**Campos**:

- `id`: UUID (PK)
- `feeding_line_id`: UUID (FK), not null
- `slot_number`: Integer, not null
- `cage_id`: UUID (FK a cages), not null
- `created_at`: DateTime

**Constraints**:

- UNIQUE: (`feeding_line_id`, `slot_number`)
- UNIQUE: (`feeding_line_id`, `cage_id`) - Una jaula por línea

**Propósito**: Representa la asignación de jaulas a slots en una línea

---

## 🔄 Fase 4: Mappers (Domain ↔ ORM)

### 4.1 Principio de responsabilidad

**Objetivo**: Conversión bidireccional sin lógica de negocio

**Características**:

- Funciones puras (stateless)
- Mapeo explícito campo por campo
- Conversión de tipos (UUID ↔ str, Decimal ↔ Weight, etc.)
- Sin validaciones de negocio (eso es del dominio)

### 4.2 Crear `infrastructure/persistence/sqlalchemy/mappers/silo_mapper.py`

**Funciones**:

1. `to_domain(silo_model: SiloModel) -> Silo`

   - Convierte ORM model a entidad de dominio
   - Reconstruye value objects (SiloId, SiloName, Weight)
   - Restaura estado interno (\_id, \_is_assigned, etc.)

2. `to_orm(silo: Silo) -> SiloModel`
   - Convierte entidad de dominio a ORM model
   - Extrae valores primitivos de value objects
   - Prepara para persistencia

**Consideraciones**:

- Usar `__dict__` o setters privados para reconstruir estado interno
- Manejar conversión de tipos (UUID, Decimal, datetime)
- No crear nuevas instancias si ya existe (para updates)

### 4.3 Crear `infrastructure/persistence/sqlalchemy/mappers/cage_mapper.py`

**Funciones**:

- `to_domain(cage_model: CageModel) -> Cage`
- `to_orm(cage: Cage) -> CageModel`

**Particularidades**:

- Mapeo de enum `CageStatus`
- Conversión de value objects (CageId, CageName)

### 4.4 Crear `infrastructure/persistence/sqlalchemy/mappers/feeding_line_mapper.py`

**Funciones**:

- `to_domain(line_model: FeedingLineModel, ...) -> FeedingLine`
- `to_orm(line: FeedingLine) -> tuple[FeedingLineModel, ...]`

**Complejidad**:

- Mapeo de agregado completo con componentes anidados
- Reconstrucción de colecciones (dosers, slot_assignments)
- Manejo de relaciones 1:1 y 1:N
- Puede requerir múltiples queries para eager loading

**Estrategia**:

- Usar `selectinload()` para cargar relaciones en una query
- Mapear componentes recursivamente
- Mantener consistencia del agregado

---

## 🗂️ Fase 5: Repositorios SQLAlchemy

### 5.1 Principios de implementación

**Reglas**:

- Implementar interfaces del dominio (`ISiloRepository`, etc.)
- Usar `AsyncSession` en todos los métodos
- **NO hacer commit** - delegar al Unit of Work
- Queries optimizadas con eager loading donde sea necesario
- Manejo de errores de BD (duplicados, FK violations, etc.)

**Patrón**:

```python
class SQLAlchemySiloRepository(ISiloRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
```

### 5.2 Crear `infrastructure/persistence/sqlalchemy/repositories/silo_repository.py`

**Métodos a implementar**:

1. `async def save(self, silo: Silo) -> None`

   - Convertir a ORM con mapper
   - Verificar si existe (por ID)
   - INSERT o UPDATE según corresponda
   - `session.add()` pero NO commit

2. `async def find_by_id(self, silo_id: SiloId) -> Optional[Silo]`

   - Query por PK: `select(SiloModel).where(SiloModel.id == ...)`
   - Convertir a dominio con mapper
   - Retornar None si no existe

3. `async def find_by_name(self, name: SiloName) -> Optional[Silo]`

   - Query con filtro: `where(SiloModel.name == ...)`
   - Convertir a dominio

4. `async def get_all(self) -> List[Silo]`

   - Query simple: `select(SiloModel)`
   - Convertir lista completa a dominio

5. `async def get_next_id(self) -> SiloId`

   - Generar UUID nuevo
   - No requiere query a BD

6. `async def delete(self, silo_id: SiloId) -> None`
   - Hard delete: `delete(SiloModel).where(...)`
   - Considerar soft delete si es requerimiento

**Manejo de errores**:

- `IntegrityError` → `DomainException` (nombre duplicado)
- `NoResultFound` → retornar None
- Otros errores → propagar o wrappear

### 5.3 Crear `infrastructure/persistence/sqlalchemy/repositories/cage_repository.py`

**Implementación similar a SiloRepository**

**Particularidades**:

- Queries adicionales por status si es necesario
- Manejo de enum en filtros

### 5.4 Crear `infrastructure/persistence/sqlalchemy/repositories/feeding_line_repository.py`

**Complejidad**: Agregado con componentes anidados

**Métodos clave**:

1. `async def save(self, feeding_line: FeedingLine) -> None`

   - Guardar línea principal
   - Guardar componentes (blower, selector, dosers)
   - Guardar asignaciones de slots
   - Manejar actualizaciones (eliminar componentes viejos)
   - TODO en una transacción (sin commit)

2. `async def find_by_id(self, line_id: LineId) -> Optional[FeedingLine]`
   - Query con eager loading:
     ```python
     select(FeedingLineModel)
       .options(
         selectinload(FeedingLineModel.blower),
         selectinload(FeedingLineModel.selector),
         selectinload(FeedingLineModel.dosers),
         selectinload(FeedingLineModel.slot_assignments)
       )
       .where(...)
     ```
   - Convertir agregado completo a dominio

**Estrategia de actualización**:

- Opción 1: Delete + Insert (más simple)
- Opción 2: Merge inteligente (más eficiente)
- Recomendación: Empezar con Opción 1

---

## 🔗 Fase 6: Unit of Work Pattern

### 6.1 Crear interfaz `application/ports/unit_of_work.py`

**Objetivo**: Gestión de transacciones y acceso a repositorios

**Contenido**:

```python
class IUnitOfWork(ABC):
    silos: ISiloRepository
    cages: ICageRepository
    feeding_lines: IFeedingLineRepository

    async def __aenter__(self) -> "IUnitOfWork": ...
    async def __aexit__(self, *args) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
```

**Beneficios**:

- Transacciones atómicas
- Acceso centralizado a repositorios
- Facilita testing (mock del UoW completo)

### 6.2 Crear `infrastructure/persistence/sqlalchemy/unit_of_work.py`

**Implementación**:

```python
class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._session = self._session_factory()
        self.silos = SQLAlchemySiloRepository(self._session)
        self.cages = SQLAlchemyCageRepository(self._session)
        self.feeding_lines = SQLAlchemyFeedingLineRepository(self._session)
        return self

    async def __aexit__(self, *args):
        await self.rollback()
        await self._session.close()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
```

**Características**:

- Context manager async
- Crea repositorios con sesión compartida
- Commit/rollback explícitos
- Cierre automático de sesión

### 6.3 Integrar con FastAPI

**Crear `api/dependencies.py`**:

```python
async def get_unit_of_work() -> AsyncGenerator[IUnitOfWork, None]:
    uow = SQLAlchemyUnitOfWork(AsyncSessionLocal)
    async with uow:
        yield uow
```

**Uso en routers**:

```python
@router.post("/sync")
async def sync_layout(
    data: SystemLayoutRequest,
    uow: IUnitOfWork = Depends(get_unit_of_work)
):
    use_case = SyncSystemLayoutUseCase(uow)
    result = await use_case.execute(dto)
    await uow.commit()  # Commit explícito
    return result
```

**Ventajas**:

- Inyección de dependencias limpia
- Transacciones por request
- Rollback automático en errores

---

## 🔄 Fase 7: Migraciones con Alembic

### 7.1 Inicializar Alembic

**Comando**:

```bash
alembic init alembic
```

**Estructura generada**:

```
alembic/
├── versions/          # Migraciones
├── env.py            # Configuración de entorno
├── script.py.mako    # Template de migraciones
└── alembic.ini       # Configuración principal
```

### 7.2 Configurar `alembic/env.py`

**Modificaciones necesarias**:

1. Importar Base y modelos:

   ```python
   from infrastructure.database.base import Base
   from infrastructure.persistence.sqlalchemy.models import *
   ```

2. Configurar target_metadata:

   ```python
   target_metadata = Base.metadata
   ```

3. Habilitar async:

   ```python
   from sqlalchemy.ext.asyncio import create_async_engine

   def run_migrations_online():
       connectable = create_async_engine(...)
       # Configuración async
   ```

4. Cargar DATABASE_URL desde settings

### 7.3 Configurar `alembic.ini`

**Modificar**:

```ini
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/dbname
```

**Mejor práctica**: Usar variable de entorno

```ini
# sqlalchemy.url =
# Se carga desde env.py usando settings
```

### 7.4 Crear migraciones iniciales

**Migración 1: Tablas base**

```bash
alembic revision --autogenerate -m "create_silos_and_cages_tables"
```

Contendrá:

- Tabla `silos` con constraints
- Tabla `cages` con enum
- Índices y constraints

**Migración 2: Feeding Lines**

```bash
alembic revision --autogenerate -m "create_feeding_lines_tables"
```

Contendrá:

- Tabla `feeding_lines`
- Tablas `blowers`, `selectors`, `dosers`
- Tabla `slot_assignments`
- Foreign keys y relaciones

### 7.5 Aplicar migraciones

**Desarrollo**:

```bash
alembic upgrade head
```

**Rollback**:

```bash
alembic downgrade -1
```

**Ver historial**:

```bash
alembic history
```

### 7.6 Scripts de gestión

**Crear `scripts/init_db.py`**:

- Crear base de datos si no existe
- Ejecutar migraciones
- Seed data inicial (opcional)

**Crear `scripts/reset_db.py`**:

- Drop todas las tablas
- Recrear desde migraciones
- Útil para desarrollo

---

## 🔧 Fase 8: Actualizar Casos de Uso

### 8.1 Modificar `SyncSystemLayoutUseCase`

**Cambios necesarios**:

**Antes**:

```python
class SyncSystemLayoutUseCase:
    def __init__(
        self,
        silo_repo: ISiloRepository,
        cage_repo: ICageRepository,
        line_repo: IFeedingLineRepository
    ):
        self._silo_repo = silo_repo
        self._cage_repo = cage_repo
        self._line_repo = line_repo
```

**Después**:

```python
class SyncSystemLayoutUseCase:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def execute(self, dto: SystemLayoutDTO) -> SystemLayoutResultDTO:
        # Usar self._uow.silos, self._uow.cages, etc.
        # NO hacer commit aquí, delegar al caller
```

**Ventajas**:

- Menos parámetros en constructor
- Transaccionalidad garantizada
- Más fácil de testear

### 8.2 Actualizar routers

**Modificar `api/routers/system_layout.py`**:

```python
@router.post("/sync")
async def sync_system_layout(
    request: SystemLayoutRequest,
    uow: IUnitOfWork = Depends(get_unit_of_work)
):
    try:
        dto = SystemLayoutMapper.to_dto(request)
        use_case = SyncSystemLayoutUseCase(uow)
        result = await use_case.execute(dto)
        await uow.commit()  # Commit explícito en caso de éxito
        return SystemLayoutMapper.to_response(result)
    except DomainException as e:
        await uow.rollback()  # Rollback explícito
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await uow.rollback()
        raise HTTPException(status_code=500, detail="Internal error")
```

**Patrón**:

- Try-except para manejo de errores
- Commit explícito en éxito
- Rollback explícito en error
- Context manager cierra sesión automáticamente

### 8.3 Actualizar `main.py`

**Agregar inicialización de BD**:

```python
from infrastructure.database.connection import engine
from infrastructure.database.base import Base

@app.on_event("startup")
async def startup():
    # Verificar conexión
    async with engine.begin() as conn:
        # Opcional: crear tablas (mejor usar Alembic)
        # await conn.run_sync(Base.metadata.create_all)
        pass

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
```

**Consideraciones**:

- No crear tablas en startup (usar Alembic)
- Verificar conexión en startup
- Cerrar pool en shutdown

---

## 🧪 Fase 9: Testing

### 9.1 Estrategia de testing

**Niveles de testing**:

1. **Unit tests**: Mappers (sin BD)
2. **Integration tests**: Repositorios (con BD de prueba)
3. **E2E tests**: Casos de uso completos (con BD de prueba)

### 9.2 Configurar BD de prueba

**Opción 1: Base de datos separada**

```python
# conftest.py
@pytest.fixture(scope="session")
async def test_db():
    # Crear BD de prueba
    # Ejecutar migraciones
    yield
    # Limpiar
```

**Opción 2: TestContainers (recomendado)**

```python
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres
```

**Ventajas TestContainers**:

- Aislamiento total
- No contamina BD de desarrollo
- Reproducible en CI/CD

### 9.3 Tests de mappers

**Crear `test/infrastructure/test_mappers.py`**:

```python
def test_silo_mapper_to_domain():
    # Crear SiloModel
    # Convertir a Silo
    # Verificar campos

def test_silo_mapper_to_orm():
    # Crear Silo
    # Convertir a SiloModel
    # Verificar campos

def test_silo_mapper_roundtrip():
    # Domain → ORM → Domain
    # Verificar integridad
```

**Características**:

- No requieren BD
- Rápidos
- Verifican conversión de tipos

### 9.4 Tests de repositorios

**Crear `test/infrastructure/test_repositories.py`**:

```python
@pytest.mark.asyncio
async def test_silo_repository_save_and_find(async_session):
    repo = SQLAlchemySiloRepository(async_session)

    # Crear silo
    silo = Silo(...)
    await repo.save(silo)
    await async_session.commit()

    # Buscar
    found = await repo.find_by_id(silo.id)
    assert found is not None
    assert found.name == silo.name
```

**Fixtures necesarios**:

```python
@pytest.fixture
async def async_session(test_db):
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
```

### 9.5 Tests de casos de uso

**Modificar `test/test_sync_system_layout_use_case.py`**:

```python
@pytest.mark.asyncio
async def test_sync_system_layout_with_real_db(async_session):
    uow = SQLAlchemyUnitOfWork(lambda: async_session)

    async with uow:
        use_case = SyncSystemLayoutUseCase(uow)
        result = await use_case.execute(dto)
        await uow.commit()

    # Verificar persistencia
    async with uow:
        silos = await uow.silos.get_all()
        assert len(silos) == expected_count
```

**Ventajas**:

- Tests con BD real
- Verifican transaccionalidad
- Detectan problemas de integración

### 9.6 Configuración pytest

**Actualizar `pytest.ini` o `pyproject.toml`**:

```ini
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["src/test"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
```

---

## ⚙️ Fase 10: Configuración y Optimización

### 10.1 Variables de entorno

**Crear `.env.example`**:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/feeding_system
DB_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Crear `.env` (no commitear)**:

- Copiar de `.env.example`
- Configurar valores reales

**Actualizar `.gitignore`**:

```
.env
*.db
__pycache__/
```

### 10.2 Logging y monitoring

**Configurar logging en `main.py`**:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Logging SQL solo en desarrollo
if settings.ENVIRONMENT == "development":
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

**Métricas útiles**:

- Tiempo de queries
- Pool de conexiones (activas/idle)
- Errores de BD
- Transacciones por segundo

### 10.3 Optimizaciones de BD

**Índices recomendados**:

```sql
-- Silos
CREATE INDEX idx_silos_is_assigned ON silos(is_assigned) WHERE is_assigned = false;
CREATE INDEX idx_silos_name ON silos(name);

-- Cages
CREATE INDEX idx_cages_status ON cages(status);
CREATE INDEX idx_cages_name ON cages(name);

-- Dosers
CREATE INDEX idx_dosers_feeding_line ON dosers(feeding_line_id);
CREATE INDEX idx_dosers_silo ON dosers(silo_id);

-- Slot Assignments
CREATE INDEX idx_slot_assignments_line ON slot_assignments(feeding_line_id);
CREATE INDEX idx_slot_assignments_cage ON slot_assignments(cage_id);
```

**Connection pooling**:

- `pool_size=5`: Conexiones permanentes
- `max_overflow=10`: Conexiones adicionales bajo carga
- `pool_recycle=3600`: Reciclar cada hora
- `pool_pre_ping=True`: Verificar conexión antes de usar

### 10.4 Health checks

**Crear endpoint de salud**:

```python
@app.get("/health")
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
```

### 10.5 Documentación

**Actualizar README.md**:

- Instrucciones de setup de BD
- Variables de entorno requeridas
- Comandos de migraciones
- Troubleshooting común

**Crear `docs/database.md`**:

- Diagrama ER
- Descripción de tablas
- Índices y constraints
- Estrategias de backup

---

## 📊 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routers    │  │ Dependencies │  │   Models     │      │
│  │  (FastAPI)   │  │   (DI)       │  │  (Pydantic)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
└─────────┼──────────────────┼──────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Use Cases   │  │     DTOs     │  │  IUnitOfWork │      │
│  │              │  │              │  │  (Interface) │      │
│  └──────┬───────┘  └──────────────┘  └──────┬───────┘      │
└─────────┼──────────────────────────────────────┼──────────────┘
          │                                      │
          ▼                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Aggregates  │  │ Repositories │  │    Value     │      │
│  │  (Entities)  │  │ (Interfaces) │  │   Objects    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │ implements
                             │
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy Implementation                │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │   │
│  │  │  Models  │  │  Mappers │  │  Repositories    │   │   │
│  │  │  (ORM)   │  │          │  │  (Concrete)      │   │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │         UnitOfWork (Concrete)                │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Database Configuration                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │   │
│  │  │  Engine  │  │ Session  │  │    Settings      │   │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │    Database     │
                    └─────────────────┘
```

---

## 🎯 Orden de Implementación Recomendado

### Sprint 1: Fundamentos (Fase 1-2)

1. Actualizar `requirements.txt`
2. Crear estructura de carpetas
3. Implementar `settings.py`
4. Implementar `connection.py`
5. Implementar `session.py`
6. Implementar `base.py`
7. **Verificar**: Conexión a BD funciona

### Sprint 2: Silo (Fase 3-5)

1. Implementar `SiloModel`
2. Implementar `SiloMapper`
3. Implementar `SQLAlchemySiloRepository`
4. Crear tests de mapper
5. Crear tests de repositorio
6. **Verificar**: CRUD de Silo funciona

### Sprint 3: Cage (Fase 3-5)

1. Implementar `CageModel`
2. Implementar `CageMapper`
3. Implementar `SQLAlchemyCageRepository`
4. Crear tests
5. **Verificar**: CRUD de Cage funciona

### Sprint 4: FeedingLine (Fase 3-5)

1. Implementar modelos de componentes
2. Implementar `FeedingLineModel`
3. Implementar `FeedingLineMapper`
4. Implementar `SQLAlchemyFeedingLineRepository`
5. Crear tests
6. **Verificar**: CRUD de FeedingLine funciona

### Sprint 5: Unit of Work (Fase 6)

1. Crear interfaz `IUnitOfWork`
2. Implementar `SQLAlchemyUnitOfWork`
3. Crear `dependencies.py`
4. Actualizar casos de uso
5. Actualizar routers
6. **Verificar**: Transacciones funcionan

### Sprint 6: Migraciones (Fase 7)

1. Inicializar Alembic
2. Configurar `env.py`
3. Crear migraciones iniciales
4. Crear scripts de gestión
5. **Verificar**: Migraciones se aplican correctamente

### Sprint 7: Testing completo (Fase 9)

1. Configurar BD de prueba
2. Tests de integración
3. Tests E2E
4. **Verificar**: Todos los tests pasan

### Sprint 8: Optimización (Fase 10)

1. Configurar variables de entorno
2. Implementar logging
3. Crear índices
4. Health checks
5. Documentación
6. **Verificar**: Performance aceptable

---

## ⚠️ Consideraciones Importantes

### Separación de Responsabilidades

**Domain Layer**:

- ✅ Entidades puras sin dependencias externas
- ✅ Interfaces de repositorios
- ✅ Lógica de negocio y validaciones
- ❌ NO conoce SQLAlchemy
- ❌ NO conoce FastAPI
- ❌ NO conoce detalles de persistencia

**Infrastructure Layer**:

- ✅ Modelos ORM con anotaciones SQLAlchemy
- ✅ Implementaciones concretas de repositorios
- ✅ Mappers para conversión
- ✅ Configuración de BD
- ❌ NO contiene lógica de negocio
- ❌ NO valida reglas de dominio

**Application Layer**:

- ✅ Casos de uso orquestando dominio
- ✅ DTOs para transferencia de datos
- ✅ Usa abstracciones (IUnitOfWork)
- ❌ NO conoce detalles de persistencia
- ❌ NO conoce FastAPI

### Transaccionalidad

**Regla de oro**:

- Repositorios NO hacen commit
- Unit of Work gestiona transacciones
- Commit explícito en routers/controllers

**Ejemplo correcto**:

```python
async with uow:
    await uow.silos.save(silo)
    await uow.cages.save(cage)
    await uow.commit()  # Ambos o ninguno
```

**Ejemplo incorrecto**:

```python
await repo.save(silo)  # ❌ No hace commit
# Datos no persistidos
```

### Performance

**Eager Loading**:

- Usar `selectinload()` para relaciones 1:N
- Usar `joinedload()` para relaciones 1:1
- Evitar N+1 queries

**Índices**:

- Crear índices en columnas de búsqueda frecuente
- Índices compuestos para queries complejas
- Monitorear con `EXPLAIN ANALYZE`

**Connection Pool**:

- Ajustar según carga esperada
- Monitorear conexiones activas
- Configurar timeouts apropiados

### Testing

**Estrategia**:

- Unit tests: Rápidos, sin BD (mappers)
- Integration tests: Con BD de prueba (repositorios)
- E2E tests: Flujos completos (casos de uso)

**Aislamiento**:

- Cada test en transacción separada
- Rollback automático después de cada test
- Usar fixtures para datos de prueba

### Migraciones

**Buenas prácticas**:

- Nunca modificar migraciones aplicadas
- Crear nueva migración para cambios
- Revisar SQL generado antes de aplicar
- Mantener migraciones pequeñas y atómicas
- Documentar cambios complejos

### Seguridad

**Prevención de SQL Injection**:

- SQLAlchemy protege automáticamente
- Usar parámetros, nunca concatenar strings
- Validar inputs en capa de API

**Credenciales**:

- Nunca commitear `.env`
- Usar secrets management en producción
- Rotar credenciales regularmente

---

## 📚 Referencias y Recursos

### Documentación Oficial

**SQLAlchemy 2.0**:

- [Async ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [ORM Querying Guide](https://docs.sqlalchemy.org/en/20/orm/queryguide/)
- [Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html)

**FastAPI**:

- [SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [Async SQL Databases](https://fastapi.tiangolo.com/advanced/async-sql-databases/)
- [Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

**Alembic**:

- [Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Async Support](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)

**Pydantic**:

- [Settings Management](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Validation](https://docs.pydantic.dev/latest/concepts/validators/)

### Libros y Artículos

**Clean Architecture**:

- "Clean Architecture" - Robert C. Martin
- "Architecture Patterns with Python" - Harry Percival & Bob Gregory
  - [Cosmic Python](https://www.cosmicpython.com/)

**Domain-Driven Design**:

- "Domain-Driven Design" - Eric Evans
- "Implementing Domain-Driven Design" - Vaughn Vernon

**FastAPI Best Practices**:

- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Full Stack FastAPI Template](https://github.com/tiangolo/full-stack-fastapi-template)

### Herramientas Útiles

**Database Tools**:

- pgAdmin 4: GUI para PostgreSQL
- DBeaver: Cliente universal de BD
- psql: CLI de PostgreSQL

**Development**:

- Docker Desktop: Para contenedor PostgreSQL
- Postman/Insomnia: Testing de API
- pytest-watch: Auto-run tests

**Monitoring**:

- pg_stat_statements: Análisis de queries
- pgBadger: Análisis de logs
- Prometheus + Grafana: Métricas

---

## 🚀 Checklist de Implementación

### Fase 1-2: Configuración Base

- [ ] Actualizar `requirements.txt` con dependencias
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Crear estructura de carpetas en `infrastructure/`
- [ ] Implementar `infrastructure/config/settings.py`
- [ ] Implementar `infrastructure/database/connection.py`
- [ ] Implementar `infrastructure/database/session.py`
- [ ] Implementar `infrastructure/database/base.py`
- [ ] Crear `.env.example` y `.env`
- [ ] Verificar conexión a PostgreSQL

### Fase 3: Modelos ORM

- [ ] Implementar `SiloModel` con constraints
- [ ] Implementar `CageModel` con enum
- [ ] Implementar `FeedingLineModel`
- [ ] Implementar `BlowerModel`
- [ ] Implementar `SelectorModel`
- [ ] Implementar `DoserModel`
- [ ] Implementar tabla `slot_assignments`
- [ ] Verificar relaciones entre modelos

### Fase 4: Mappers

- [ ] Implementar `SiloMapper` (to_domain, to_orm)
- [ ] Implementar `CageMapper`
- [ ] Implementar `FeedingLineMapper`
- [ ] Tests unitarios de mappers
- [ ] Verificar conversión de value objects

### Fase 5: Repositorios

- [ ] Implementar `SQLAlchemySiloRepository`
- [ ] Implementar `SQLAlchemyCageRepository`
- [ ] Implementar `SQLAlchemyFeedingLineRepository`
- [ ] Tests de integración de repositorios
- [ ] Verificar queries con eager loading

### Fase 6: Unit of Work

- [ ] Crear interfaz `IUnitOfWork` en `application/ports/`
- [ ] Implementar `SQLAlchemyUnitOfWork`
- [ ] Crear `api/dependencies.py` con DI
- [ ] Actualizar `SyncSystemLayoutUseCase`
- [ ] Actualizar routers para usar UoW
- [ ] Verificar transaccionalidad

### Fase 7: Migraciones

- [ ] Inicializar Alembic: `alembic init alembic`
- [ ] Configurar `alembic/env.py` para async
- [ ] Configurar `alembic.ini`
- [ ] Crear migración inicial: `alembic revision --autogenerate -m "initial"`
- [ ] Revisar SQL generado
- [ ] Aplicar migraciones: `alembic upgrade head`
- [ ] Crear scripts de gestión (`init_db.py`, `reset_db.py`)

### Fase 8: Actualizar Aplicación

- [ ] Modificar casos de uso para usar UoW
- [ ] Actualizar routers con manejo de transacciones
- [ ] Actualizar `main.py` con eventos de startup/shutdown
- [ ] Verificar que API funciona con BD

### Fase 9: Testing

- [ ] Configurar BD de prueba (TestContainers o separada)
- [ ] Crear fixtures de pytest
- [ ] Tests de mappers
- [ ] Tests de repositorios con BD
- [ ] Tests E2E de casos de uso
- [ ] Verificar cobertura de tests

### Fase 10: Optimización

- [ ] Configurar variables de entorno
- [ ] Implementar logging de SQL
- [ ] Crear índices en BD
- [ ] Implementar health check endpoint
- [ ] Optimizar connection pool
- [ ] Documentar setup en README
- [ ] Crear diagrama ER en `docs/database.md`

### Verificación Final

- [ ] Todos los tests pasan
- [ ] API responde correctamente
- [ ] Datos persisten en BD
- [ ] Transacciones funcionan (rollback en errores)
- [ ] Performance aceptable
- [ ] Documentación completa
- [ ] Variables de entorno documentadas
- [ ] Migraciones aplicadas correctamente

---

## 💡 Tips y Troubleshooting

### Problemas Comunes

**Error: "asyncpg.exceptions.InvalidCatalogNameError"**

- Causa: Base de datos no existe
- Solución: Crear BD manualmente o usar script `init_db.py`

**Error: "sqlalchemy.exc.IntegrityError: duplicate key"**

- Causa: Violación de constraint UNIQUE
- Solución: Verificar lógica de negocio, manejar en capa de aplicación

**Error: "DetachedInstanceError"**

- Causa: Acceso a relación después de cerrar sesión
- Solución: Usar eager loading o `expire_on_commit=False`

**Tests lentos**

- Causa: Crear/destruir BD en cada test
- Solución: Usar transacciones con rollback, TestContainers con reuso

**N+1 Queries**

- Causa: Lazy loading de relaciones
- Solución: Usar `selectinload()` o `joinedload()`

### Mejores Prácticas

**Naming Conventions**:

```python
# Tablas: plural, snake_case
"silos", "feeding_lines", "slot_assignments"

# Columnas: snake_case
"created_at", "stock_level", "is_assigned"

# Modelos ORM: singular, PascalCase + "Model"
SiloModel, FeedingLineModel

# Entidades: singular, PascalCase
Silo, FeedingLine
```

**Manejo de Errores**:

```python
try:
    await uow.silos.save(silo)
    await uow.commit()
except IntegrityError as e:
    await uow.rollback()
    if "unique constraint" in str(e):
        raise DuplicateNameError(...)
    raise
except Exception as e:
    await uow.rollback()
    logger.error(f"Unexpected error: {e}")
    raise
```

**Logging Útil**:

```python
logger.info(f"Saving silo: {silo.name}")
logger.debug(f"Query executed: {query}")
logger.error(f"Failed to save: {error}", exc_info=True)
```

### Optimizaciones Avanzadas

**Bulk Operations**:

```python
# Insertar múltiples registros
await session.execute(
    insert(SiloModel),
    [{"name": "S1", ...}, {"name": "S2", ...}]
)
```

**Compiled Queries**:

```python
# Cache de queries compiladas
stmt = select(SiloModel).where(SiloModel.id == bindparam("silo_id"))
# Reusar stmt con diferentes parámetros
```

**Read Replicas** (futuro):

```python
# Engine para lecturas
read_engine = create_async_engine(READ_DATABASE_URL)
# Engine para escrituras
write_engine = create_async_engine(WRITE_DATABASE_URL)
```

---

## 🎓 Conclusión

Este plan proporciona una ruta clara y estructurada para implementar persistencia PostgreSQL en tu sistema de alimentación, manteniendo los principios de Clean Architecture, DDD y SOLID que ya has establecido.

### Ventajas de esta Arquitectura

1. **Mantenibilidad**: Separación clara de responsabilidades
2. **Testabilidad**: Fácil de testear con mocks o BD de prueba
3. **Escalabilidad**: Fácil agregar nuevos agregados o repositorios
4. **Flexibilidad**: Cambiar implementación de persistencia sin afectar dominio
5. **Performance**: Optimizaciones a nivel de infraestructura sin tocar lógica

### Próximos Pasos

1. **Revisar el plan** con el equipo
2. **Configurar PostgreSQL** con Docker
3. **Comenzar con Sprint 1** (fundamentos)
4. **Iterar sprint por sprint** verificando cada fase
5. **Documentar decisiones** y aprendizajes

### Soporte Continuo

A medida que implementes cada fase:

- Consulta la documentación oficial
- Revisa los ejemplos de código
- Ejecuta los tests frecuentemente
- Documenta problemas y soluciones
- Mantén el código limpio y bien estructurado

**¡Éxito con la implementación!** 🚀

---

**Documento creado**: 2024
**Versión**: 1.0
**Autor**: Plan de Arquitectura para Feeding System API
**Última actualización**: [Fecha actual]
