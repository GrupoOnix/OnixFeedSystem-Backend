# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Feeding System API for aquaculture management. This is a FastAPI-based backend that controls automated fish feeding systems, manages feeding lines, cages, and operational feeding sessions. The system is designed with Domain-Driven Design (DDD) principles and Clean Architecture.

## Technology Stack

- **Framework**: FastAPI 0.121.0
- **Database**: PostgreSQL 18 with SQLModel/Alembic for ORM/migrations
- **Language**: Python 3.11
- **Testing**: pytest with pytest-asyncio
- **Linting**: ruff, mypy
- **Containerization**: Docker & Docker Compose

## Development Commands

### Environment Setup

**Note**: This project uses a Python virtual environment located in `.venv/` directory.

```bash
# Activate existing virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# If .venv doesn't exist, create it:
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your database credentials
```

### Docker Development

```bash
# Start all services (PostgreSQL + API)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Rebuild after code changes
docker-compose up -d --build

# Stop services
docker-compose down

# Stop and remove volumes (deletes database)
docker-compose down -v
```

### Database Migrations

```bash
# Run migrations inside Docker
docker-compose exec backend alembic upgrade head

# Create new migration (after model changes)
docker-compose exec backend alembic revision --autogenerate -m "description"

# Outside Docker (local development)
alembic upgrade head
alembic revision --autogenerate -m "description"
```

**Migration File Naming**: Alembic is configured to auto-generate filenames with format: `YYYY_MM_DD_HHMM-{revision}_{slug}.py`

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest src/test/application/use_cases/test_sync_system_layout.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src
```

**Test Configuration**: Tests are located in `src/test/`. The `pytest.ini` sets `pythonpath = src` and `testpaths = src/test`. Tests use `asyncio_mode = auto` for async test support.

### Linting & Type Checking

```bash
# Run ruff linter
ruff check src/

# Run mypy type checker
mypy src/
```

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Architecture

### Clean Architecture Layers

The codebase follows Clean Architecture with DDD:

```
src/
├── domain/              # Domain Layer (business rules, entities, value objects)
│   ├── aggregates/      # Aggregate Roots (FeedingSession, FeedingLine, Cage, Silo)
│   ├── entities/        # Domain Entities (FeedingOperation)
│   ├── value_objects/   # Value Objects (LineId, CageId, Weight, etc.)
│   ├── enums.py         # Domain enums
│   ├── repositories.py  # Repository interfaces (IFeedingLineRepository, etc.)
│   ├── interfaces.py    # Service interfaces (IFeedingMachine)
│   ├── strategies/      # Strategy pattern implementations
│   └── exceptions.py    # Domain exceptions
│
├── application/         # Application Layer (use cases, DTOs)
│   ├── use_cases/       # Use case implementations
│   │   ├── cage/        # Cage-related use cases
│   │   └── feeding/     # Feeding operation use cases
│   ├── dtos/            # Data Transfer Objects
│   └── services/        # Application services
│
├── infrastructure/      # Infrastructure Layer (persistence, external services)
│   ├── persistence/
│   │   ├── models/      # SQLModel database models
│   │   ├── repositories/ # Repository implementations
│   │   └── database.py  # Database session management
│   └── services/        # Infrastructure services (PLCSimulator)
│
├── api/                 # Presentation Layer (FastAPI routes, models)
│   ├── routers/         # API route definitions
│   ├── models/          # API request/response models
│   ├── mappers/         # Domain to API model mappers
│   └── dependencies.py  # FastAPI dependency injection
│
└── test/               # Tests (mirrors src structure)
```

### Key Architectural Patterns

1. **Dependency Injection**: All dependencies are injected via FastAPI's `Depends()` system. See `src/api/dependencies.py` for the complete DI configuration.

2. **Repository Pattern**: All data access goes through repository interfaces defined in `src/domain/repositories.py`, implemented in `src/infrastructure/persistence/repositories/`.

3. **Value Objects**: The system uses rich value objects (e.g., `LineId`, `CageId`, `Weight`, `SessionId`) instead of primitive types to enforce domain rules.

4. **Aggregate Roots**:
   - `FeedingSession`: Manages daily feeding sessions with operations
   - `FeedingLine`: Represents physical feeding lines with components (blowers, selectors, dosers)
   - `Cage`: Fish cages with population tracking and configuration
   - `Silo`: Feed storage silos

## Domain Model Key Concepts

### Feeding Operations Model (Phase 2 - Current)

The system distinguishes between:

- **FeedingSession** (Aggregate Root): Represents a daily operational session. Always starts in `ACTIVE` status. Contains accumulated totals for the day and references to the current operation.

- **FeedingOperation** (Entity): Represents a single visit to a cage (from START to STOP). Has its own lifecycle with statuses: `RUNNING`, `PAUSED`, `COMPLETED`, `STOPPED`, `FAILED`.

**Key Insight**: A session can have multiple operations throughout the day. After stopping an operation, a new one can be started in the same session. This enables feeding multiple cages or returning to the same cage multiple times per day.

### Session & Operation States

```
SessionStatus (enum):
- ACTIVE: Session is open, can contain operations
- CLOSED: Session closed at end of day

OperationStatus (enum):
- RUNNING: Operation in progress
- PAUSED: Operation temporarily paused
- COMPLETED: Finished successfully (automatic)
- STOPPED: Manually stopped by operator
- FAILED: Failed due to error
```

### Value Objects

All IDs are value objects with UUID values:
- `LineId`, `CageId`, `SiloId`, `SessionId`, `OperationId`
- `Weight`: Represents weight in kg with validation
- `CageName`, `LineName`, `SiloName`: Named entities with validation

### Feeding Strategy Pattern

The system uses the Strategy pattern for feeding configurations:
- `IFeedingStrategy` (interface): Defines strategy contract
- `ManualFeedingStrategy`: Manual operator-controlled feeding
- Returns `MachineConfiguration` DTOs for PLC communication

## Database Schema

### Key Tables

- `feeding_lines`: Physical feeding lines
- `cages`: Fish cages with population and configuration
- `silos`: Feed storage
- `slot_assignments`: Maps cages to physical slots on feeding lines
- `feeding_sessions`: Daily operational sessions
- `feeding_operations`: Individual feeding operations (visits to cages)
- `operation_events`: Detailed event log for each operation
- `feeding_events`: Session-level events
- `biometry_logs`, `mortality_logs`, `config_change_logs`: Cage tracking

### Important Relationships

- Sessions → Operations (1:N with CASCADE delete)
- Operations → OperationEvents (1:N with CASCADE delete)
- Sessions → FeedingEvents (1:N with CASCADE delete)
- FeedingLines → SlotAssignments → Cages

## Important Implementation Notes

### Repository Separation

`FeedingSessionRepository` and `FeedingOperationRepository` are separate. Operations are persisted individually, not at end of day. When loading a session, the current operation must be loaded separately:

```python
session = await session_repo.find_active_by_line_id(line_id)
if session:
    current_op = await operation_repo.find_current_by_session(session.id)
    if current_op:
        session._current_operation = current_op
```

### Event Handling

Both `FeedingSession` and `FeedingOperation` maintain event lists:
- `session.pop_events()`: Returns and clears session-level events
- `operation.pop_new_events()`: Returns only new events since last save

### Use Case Pattern

All use cases follow this structure:
1. Validate inputs (line exists, cage exists, etc.)
2. Load aggregate root from repository
3. Load related entities if needed (e.g., current operation)
4. Execute domain logic
5. Persist changes (session and/or operation)

### Dependency Injection Best Practices

When adding new use cases:
1. Define the use case class with `__init__` taking repository interfaces
2. Create factory function in `dependencies.py` (e.g., `get_*_use_case()`)
3. Create type alias using `Annotated[UseCase, Depends(get_*_use_case)]`
4. Use type alias in router endpoint signature

## API Structure

### Router Organization

- `/api/system-layout`: System configuration (sync layout, get layout)
- `/api/cages`: Cage CRUD and tracking (biometry, mortality, config)
- `/api/feeding`: Feeding operations (start, stop, pause, resume, update params)

### Common Response Patterns

- Success: Return data or `{"message": "..."}`
- Errors: Raise `HTTPException` with appropriate status code
- Use DTOs from `application/dtos/` for request/response mapping

## Migration History (Recent)

Recent migrations related to Phase 2 (FeedingOperation refactor):
- `2025_12_01_1343`: Added `feeding_operations` and `operation_events` tables
- `2025_12_03_1050`: Fixed cascade relationships

See `docs/plan-migracion-feeding-operation.md` for detailed migration plan and architecture decisions.

## Common Patterns & Conventions

### Naming Conventions

- Repository interfaces: `I{Entity}Repository` (e.g., `IFeedingLineRepository`)
- Repository implementations: `{Entity}Repository` (e.g., `FeedingLineRepository`)
- Use cases: `{Action}{Entity}UseCase` (e.g., `StartFeedingSessionUseCase`)
- Models (DB): `{Entity}Model` (e.g., `FeedingSessionModel`)
- Value Objects: PascalCase without suffix (e.g., `LineId`, `Weight`)

### Async/Await

All repository methods and use cases are async. Database sessions use `AsyncSession` from SQLAlchemy.

### Foreign Key Relationships

Use `Relationship()` from SQLModel for bidirectional relationships. CASCADE deletes are configured at both SQLAlchemy and database levels.

### Type Hints

The codebase uses comprehensive type hints. Repository interfaces use `Optional[T]` for nullable returns and `List[T]` for collections.

## Development Workflow

1. **Making Schema Changes**:
   - Modify models in `src/infrastructure/persistence/models/`
   - Generate migration: `alembic revision --autogenerate -m "description"`
   - Review generated migration file in `alembic/versions/`
   - Apply: `alembic upgrade head`

2. **Adding New Use Cases**:
   - Create use case in `src/application/use_cases/`
   - Add to `dependencies.py` with factory function
   - Create router endpoint in `src/api/routers/`
   - Add DTOs if needed in `src/application/dtos/`

3. **Adding Domain Logic**:
   - Modify aggregates in `src/domain/aggregates/`
   - Add value objects if needed in `src/domain/value_objects/`
   - Update repository interfaces in `src/domain/repositories.py`
   - Implement in `src/infrastructure/persistence/repositories/`

## Testing Strategy

Tests are located in `src/test/` mirroring the source structure. Currently, the project has integration tests for use cases. Unit tests are added as needed for critical domain logic.

When writing tests:
- Use `pytest.mark.asyncio` for async tests
- Mock external dependencies (database, PLC service)
- Test happy path and error cases
- Focus on use case behavior and domain rules

## Environment Variables

Required in `.env`:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `DB_ECHO`: SQL logging (true/false)

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `docker-compose ps`
- Check database logs: `docker-compose logs db`
- Verify environment variables in `.env`

### Migration Issues
- Rollback: `alembic downgrade -1`
- Check current version: `alembic current`
- View history: `alembic history`

### Import Errors
- Verify `PYTHONPATH` includes `src/`
- For Docker: ensure `WORKDIR /app` and code is copied correctly
- For local: activate virtual environment

## Additional Documentation

- `/docs/API_CAGES.md`: Cage management API documentation
- `/docs/comandos-alembic.md`: Alembic commands reference (Spanish)
- `/docs/Analisis-de-Requerimientos.md`: Requirements analysis
- `/docs/plan-migracion-feeding-operation.md`: Phase 2 migration plan (detailed architecture decisions)
