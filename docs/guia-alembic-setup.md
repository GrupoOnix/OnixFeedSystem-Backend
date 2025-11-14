# Guía de Configuración de Alembic con SQLModel y AsyncPG

## ¿Por qué Alembic desde el inicio?

✅ Versionado de esquema de BD  
✅ Rollback seguro de cambios  
✅ Historial de migraciones  
✅ Trabajo en equipo ordenado  
✅ Deploy a producción controlado  
✅ Autogenera migraciones desde modelos SQLModel

---

## Paso 1: Instalar Alembic

```bash
pip install alembic
```

Agregar a `requirements.txt`:

```
alembic==1.13.1
```

---

## Paso 2: Inicializar Alembic

```bash
# Desde la raíz del proyecto
alembic init alembic
```

Esto crea:

```
proyecto/
├── alembic/
│   ├── versions/          # Aquí se guardan las migraciones
│   ├── env.py            # Configuración principal (IMPORTANTE)
│   ├── script.py.mako    # Template para migraciones
│   └── README
└── alembic.ini           # Configuración de Alembic
```

---

## Paso 3: Configurar `alembic.ini`

Editar `/alembic.ini`:

### 3.1 Comentar la línea de sqlalchemy.url

```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
# ↑ Comentar esta línea (usaremos la URL de database.py)
```

### 3.2 Configurar formato de nombres de migración

Buscar la línea `file_template` y cambiarla:

```ini
# Antes:
# file_template = %%(rev)s_%%(slug)s

# Después (nombres más legibles):
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
```

Esto genera nombres como: `2024_01_15_1430-abc123def456_initial_schema.py`

---

## Paso 4: Configurar `alembic/env.py`

Este es el archivo MÁS IMPORTANTE. Aquí le decimos a Alembic:

- Dónde está la URL de la BD
- Qué modelos debe detectar
- Cómo usar AsyncEngine

### 4.1 Importar dependencias necesarias

Al inicio del archivo, agregar:

```python
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# IMPORTANTE: Agregar src al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar SQLModel para acceder a metadata
from sqlmodel import SQLModel

# Importar DATABASE_URL desde tu database.py
from src.infrastructure.persistence.database import DATABASE_URL

# CRÍTICO: Importar TODOS los modelos para que Alembic los detecte
from src.infrastructure.persistence.models.cage_model import CageModel
from src.infrastructure.persistence.models.silo_model import SiloModel
from src.infrastructure.persistence.models.feeding_line_model import FeedingLineModel
from src.infrastructure.persistence.models.blower_model import BlowerModel
from src.infrastructure.persistence.models.doser_model import DoserModel
from src.infrastructure.persistence.models.selector_model import SelectorModel
from src.infrastructure.persistence.models.sensor_model import SensorModel
from src.infrastructure.persistence.models.slot_assignment_model import SlotAssignmentModel
```

### 4.2 Configurar target_metadata

Buscar la línea `target_metadata = None` y cambiarla:

```python
# Antes:
# target_metadata = None

# Después:
target_metadata = SQLModel.metadata
```

### 4.3 Configurar la URL de conexión

Buscar la función `run_migrations_offline()` y modificar:

```python
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL  # ← Usar nuestra URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
```

### 4.4 Configurar run_migrations_online para async

Reemplazar completamente la función `run_migrations_online()`:

```python
def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support."""

    # Configuración para async engine
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_run_migrations(connection: Connection) -> None:
        await connection.run_sync(do_migrations)

    def do_migrations(connection: Connection) -> None:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await do_run_migrations(connection)

        await connectable.dispose()

    asyncio.run(run_async_migrations())


# Ejecutar migraciones
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## Paso 5: Verificar Configuración

### 5.1 Verificar que PostgreSQL está corriendo

```bash
docker ps
# Debe mostrar el contenedor feedsystemdb corriendo en puerto 5432
```

### 5.2 Verificar variables de entorno

Asegurarse de que `.env` tiene:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_password
DB_NAME=feedsystemdb
```

### 5.3 Probar conexión de Alembic

```bash
alembic current
# Si no hay error, la configuración es correcta
```

---

## Paso 6: Crear Migración Inicial

Una vez que tengas TODOS los modelos SQLModel creados:

```bash
# Generar migración automáticamente
alembic revision --autogenerate -m "initial schema"
```

Esto crea un archivo en `/alembic/versions/` como:

```
2024_01_15_1430-abc123def456_initial_schema.py
```

### 6.1 Revisar la migración generada

**IMPORTANTE:** Siempre revisar el archivo generado antes de aplicarlo.

```python
# Ejemplo de lo que Alembic genera:
def upgrade() -> None:
    # ### commands auto generated by Alembic ###
    op.create_table('cages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    # ... más tablas
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic ###
    op.drop_table('cages')
    # ... más drops
    # ### end Alembic commands ###
```

---

## Paso 7: Aplicar Migración

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head
```

Salida esperada:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> abc123def456, initial schema
```

### 7.1 Verificar en PostgreSQL

```bash
# Conectar a PostgreSQL
docker exec -it feedsystemdb psql -U postgres -d feedsystemdb

# Ver tablas creadas
\dt

# Debe mostrar:
# cages
# silos
# feeding_lines
# blowers
# dosers
# selectors
# sensors
# slot_assignments
# alembic_version (tabla de control de Alembic)
```

---

## Workflow de Desarrollo con Alembic

### Cuando modificas un modelo:

```bash
# 1. Editar modelo SQLModel (ej: agregar columna a CageModel)
# 2. Generar migración
alembic revision --autogenerate -m "add fish_count to cages"

# 3. Revisar migración generada en /alembic/versions/

# 4. Aplicar migración
alembic upgrade head

# 5. Si algo sale mal, hacer rollback
alembic downgrade -1
```

### Comandos útiles:

```bash
# Ver historial de migraciones
alembic history

# Ver migración actual
alembic current

# Rollback a migración específica
alembic downgrade <revision_id>

# Ver SQL sin ejecutar (dry-run)
alembic upgrade head --sql

# Rollback completo (volver a inicio)
alembic downgrade base
```

---

## Troubleshooting

### Error: "Can't locate revision identified by 'head'"

**Causa:** No hay migraciones creadas aún.  
**Solución:** Crear migración inicial con `alembic revision --autogenerate -m "initial"`

### Error: "Target database is not up to date"

**Causa:** Hay migraciones pendientes.  
**Solución:** `alembic upgrade head`

### Error: "No module named 'src'"

**Causa:** Alembic no encuentra tus módulos.  
**Solución:** Verificar que agregaste `sys.path.insert(0, ...)` en `env.py`

### Error: "Table 'X' already exists"

**Causa:** Intentas crear tablas que ya existen.  
**Solución:**

1. Opción 1: Borrar BD y recrear desde cero
2. Opción 2: Marcar migración como aplicada sin ejecutarla:
   ```bash
   alembic stamp head
   ```

### Alembic no detecta cambios en modelos

**Causa:** Los modelos no están importados en `env.py`.  
**Solución:** Importar TODOS los modelos explícitamente en `alembic/env.py`

---

## Estructura Final

```
proyecto/
├── alembic/
│   ├── versions/
│   │   └── 2024_01_15_1430-abc123_initial_schema.py
│   ├── env.py                 # ✅ Configurado
│   └── script.py.mako
├── alembic.ini                # ✅ Configurado
├── src/
│   └── infrastructure/
│       └── persistence/
│           ├── database.py    # DATABASE_URL exportada
│           └── models/        # Todos los modelos SQLModel
├── .env                       # Variables de BD
└── requirements.txt           # alembic incluido
```

---

## Checklist de Configuración

- [ ] Alembic instalado (`pip install alembic`)
- [ ] `alembic init alembic` ejecutado
- [ ] `alembic.ini` configurado (URL comentada, file_template)
- [ ] `alembic/env.py` configurado:
  - [ ] Imports de SQLModel y DATABASE_URL
  - [ ] Imports de TODOS los modelos
  - [ ] `target_metadata = SQLModel.metadata`
  - [ ] `run_migrations_online()` con async support
- [ ] PostgreSQL corriendo en Docker
- [ ] Variables de entorno en `.env`
- [ ] Modelos SQLModel creados
- [ ] Migración inicial generada (`alembic revision --autogenerate`)
- [ ] Migración aplicada (`alembic upgrade head`)
- [ ] Tablas verificadas en PostgreSQL

---

## Próximo Paso

Una vez configurado Alembic, continuar con la implementación de repositorios (Fase 4 del plan).

**Las tablas ya están creadas por Alembic, NO necesitas `create_all()` en tu código.**
