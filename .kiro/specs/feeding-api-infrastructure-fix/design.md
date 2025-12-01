# Design Document: Feeding API Infrastructure Fix

## Overview

Este diseño corrige y estandariza la implementación de la infraestructura y API para los casos de uso de alimentación (feeding). El objetivo es alinear completamente el código con los patrones establecidos en `cage_router.py` y `system_layout.py`, asegurando consistencia arquitectónica en toda la aplicación.

El sistema sigue una arquitectura limpia adaptada con DDD (Domain-Driven Design):

- **Domain Layer**: Agregados, Value Objects, Interfaces (Ports)
- **Application Layer**: Use Cases, DTOs
- **Infrastructure Layer**: Repositorios (Adapters), Modelos ORM, Servicios externos
- **API Layer**: Routers, Dependencias FastAPI

## Architecture

### Capas y Responsabilidades

```
┌─────────────────────────────────────────────────────────┐
│                     API Layer                            │
│  - feeding_router.py (Endpoints REST)                   │
│  - dependencies.py (Inyección de dependencias)          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Application Layer                         │
│  - Use Cases (Start, Stop, Pause, Resume, Update)      │
│  - DTOs (Request/Response models)                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Domain Layer                            │
│  - FeedingSession (Aggregate Root)                      │
│  - FeedingEvent (Entity)                                │
│  - IFeedingSessionRepository (Port)                     │
│  - IFeedingMachine (Port)                               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Infrastructure Layer                        │
│  - FeedingSessionRepository (Adapter)                   │
│  - FeedingSessionModel, FeedingEventModel (ORM)        │
│  - PLCSimulator (Adapter)                               │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Datos

1. **Request**: Cliente HTTP → Router → Use Case
2. **Processing**: Use Case → Repository → Database
3. **Response**: Database → Repository → Use Case → Router → Cliente

## Components and Interfaces

### 1. Modelos de Persistencia

#### FeedingSessionModel

```python
class FeedingSessionModel(SQLModel, table=True):
    __tablename__ = "feeding_sessions"

    # Primary Key
    id: UUID = Field(primary_key=True)

    # Foreign Keys & Indexes
    line_id: UUID = Field(index=True, foreign_key="feeding_lines.id")

    # Temporal
    date: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Estado
    status: str = Field(index=True)  # CREATED, RUNNING, PAUSED, COMPLETED, FAILED

    # Acumuladores
    total_dispensed_kg: float = Field(default=0.0)

    # JSON Fields (PostgreSQL JSONB)
    dispensed_by_slot: Dict[str, float] = Field(
        default_factory=dict,
        sa_column=Column(JSONB)
    )
    applied_strategy_config: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )

    # Relationship
    events: List["FeedingEventModel"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

**Cambios clave**:

- Agregar `foreign_key` a `line_id`
- Agregar índice a `status`
- Usar `Relationship` de SQLModel para relación con eventos
- Usar `default_factory` en lugar de `default` para objetos mutables

#### FeedingEventModel

```python
class FeedingEventModel(SQLModel, table=True):
    __tablename__ = "feeding_events"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign Key
    session_id: UUID = Field(
        foreign_key="feeding_sessions.id",
        index=True,
        ondelete="CASCADE"
    )

    # Datos del evento
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    event_type: str = Field(max_length=50)  # COMMAND, PARAM_CHANGE, SYSTEM_STATUS, ALARM
    description: str = Field(max_length=500)
    details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    # Relationship
    session: Optional[FeedingSessionModel] = Relationship(back_populates="events")
```

**Cambios clave**:

- Usar `int` auto-incremental como PK (más eficiente para logs)
- Agregar `ondelete="CASCADE"` en foreign key
- Agregar índice a `timestamp` para consultas temporales
- Usar `Relationship` para navegación bidireccional

### 2. Repositorio

#### FeedingSessionRepository

**Patrón a seguir**: Igual que `CageRepository`

```python
class FeedingSessionRepository(IFeedingSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, feeding_session: FeedingSession) -> None:
        """
        Persiste o actualiza una sesión con sus eventos.
        Usa FLUSH en lugar de COMMIT para control transaccional.
        """
        # 1. Buscar modelo existente
        existing = await self.session.get(
            FeedingSessionModel,
            feeding_session.id.value
        )

        if existing:
            # UPDATE: Solo campos mutables
            existing.status = feeding_session.status.value
            existing.total_dispensed_kg = feeding_session.total_dispensed_kg.as_kg
            existing.dispensed_by_slot = {
                str(k): v.as_kg
                for k, v in feeding_session.dispensed_by_slot.items()
            }
            existing.applied_strategy_config = feeding_session.applied_strategy_config
        else:
            # INSERT: Crear nuevo modelo
            model = FeedingSessionModel(
                id=feeding_session.id.value,
                line_id=feeding_session.line_id.value,
                date=feeding_session.date,
                status=feeding_session.status.value,
                total_dispensed_kg=feeding_session.total_dispensed_kg.as_kg,
                dispensed_by_slot={
                    str(k): v.as_kg
                    for k, v in feeding_session.dispensed_by_slot.items()
                },
                applied_strategy_config=feeding_session.applied_strategy_config
            )
            self.session.add(model)

        # 2. Guardar eventos nuevos
        new_events = feeding_session.pop_events()
        for event in new_events:
            event_model = FeedingEventModel(
                session_id=feeding_session.id.value,
                timestamp=event.timestamp,
                event_type=event.type.value,  # Usar .value del Enum
                description=event.description,
                details=event.details
            )
            self.session.add(event_model)

        # 3. FLUSH (no commit)
        await self.session.flush()

    async def find_by_id(self, session_id: SessionId) -> Optional[FeedingSession]:
        """Busca sesión por ID."""
        model = await self.session.get(FeedingSessionModel, session_id.value)
        return self._to_domain(model) if model else None

    async def find_active_by_line_id(
        self,
        line_id: LineId
    ) -> Optional[FeedingSession]:
        """
        Busca la sesión activa más reciente de una línea.
        Activa = CREATED, RUNNING o PAUSED
        """
        query = (
            select(FeedingSessionModel)
            .where(FeedingSessionModel.line_id == line_id.value)
            .where(FeedingSessionModel.status.in_([
                SessionStatus.CREATED.value,
                SessionStatus.RUNNING.value,
                SessionStatus.PAUSED.value
            ]))
            .order_by(FeedingSessionModel.date.desc())
        )

        result = await self.session.execute(query)
        model = result.scalars().first()

        return self._to_domain(model) if model else None

    def _to_domain(self, model: FeedingSessionModel) -> FeedingSession:
        """Reconstruye el agregado desde el modelo ORM."""
        session = FeedingSession(LineId(model.line_id))

        # Restaurar identidad y estado (bypass __init__)
        session._id = SessionId(model.id)
        session._date = model.date
        session._status = SessionStatus(model.status)
        session._total_dispensed_kg = Weight.from_kg(model.total_dispensed_kg)

        # Restaurar distribución por slot
        session._dispensed_by_slot = {
            int(k): Weight.from_kg(v)
            for k, v in (model.dispensed_by_slot or {}).items()
        }

        session._applied_strategy_config = model.applied_strategy_config

        return session
```

**Cambios clave**:

- Usar `self.session.get()` en lugar de queries para búsqueda por PK
- Usar `flush()` en lugar de `commit()`
- Manejar correctamente conversión de tipos (int ↔ str en JSON)
- Usar `.value` para Enums

### 3. Router de API

#### feeding_router.py

**Patrón a seguir**: Exactamente igual que `cage_router.py`

```python
from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import Dict

from api.dependencies import (
    StartFeedingUseCaseDep,
    StopFeedingUseCaseDep,
    PauseFeedingUseCaseDep,
    ResumeFeedingUseCaseDep,
    UpdateFeedingParamsUseCaseDep
)
from application.dtos.feeding_dtos import (
    StartFeedingRequest,
    UpdateParamsRequest
)
from domain.exceptions import DomainException

router = APIRouter(prefix="/feeding", tags=["Feeding Operations"])


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_feeding(
    request: StartFeedingRequest,
    use_case: StartFeedingUseCaseDep
) -> Dict[str, str]:
    """
    Inicia una nueva sesión de alimentación en una línea.

    - **line_id**: ID de la línea de alimentación
    - **cage_id**: ID de la jaula objetivo
    - **mode**: Modo de operación (MANUAL, CYCLIC)
    - **target_amount_kg**: Meta de alimentación en kg
    - **blower_speed_percentage**: Velocidad del soplador (0-100)
    - **dosing_rate_kg_min**: Tasa de dosificación en kg/min
    """
    try:
        session_id = await use_case.execute(request)
        return {
            "session_id": str(session_id),
            "message": "Feeding session started successfully"
        }

    except ValueError as e:
        # Errores de validación (línea no existe, jaula no existe, etc.)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        # Errores de dominio (sesión ya activa, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/lines/{line_id}/stop", status_code=status.HTTP_200_OK)
async def stop_feeding(
    line_id: UUID,
    use_case: StopFeedingUseCaseDep
) -> Dict[str, str]:
    """
    Detiene la alimentación activa en una línea.

    - **line_id**: ID de la línea de alimentación
    """
    try:
        await use_case.execute(line_id)
        return {"message": "Feeding session stopped successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/lines/{line_id}/pause", status_code=status.HTTP_200_OK)
async def pause_feeding(
    line_id: UUID,
    use_case: PauseFeedingUseCaseDep
) -> Dict[str, str]:
    """
    Pausa temporalmente la alimentación en una línea.

    - **line_id**: ID de la línea de alimentación
    """
    try:
        await use_case.execute(line_id)
        return {"message": "Feeding session paused successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/lines/{line_id}/resume", status_code=status.HTTP_200_OK)
async def resume_feeding(
    line_id: UUID,
    use_case: ResumeFeedingUseCaseDep
) -> Dict[str, str]:
    """
    Reanuda una alimentación pausada en una línea.

    - **line_id**: ID de la línea de alimentación
    """
    try:
        await use_case.execute(line_id)
        return {"message": "Feeding session resumed successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.patch("/lines/{line_id}/parameters", status_code=status.HTTP_200_OK)
async def update_feeding_parameters(
    line_id: UUID,
    request: UpdateParamsRequest,
    use_case: UpdateFeedingParamsUseCaseDep
) -> Dict[str, str]:
    """
    Actualiza parámetros de alimentación en caliente (sin detener).

    - **line_id**: ID de la línea de alimentación
    - **blower_speed**: (Opcional) Nueva velocidad del soplador (0-100)
    - **dosing_rate**: (Opcional) Nueva tasa de dosificación en kg/min
    """
    try:
        # Agregar line_id al request
        request.line_id = line_id
        await use_case.execute(request)
        return {"message": "Feeding parameters updated successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
```

**Cambios clave**:

- Usar rutas RESTful: `/lines/{line_id}/stop` en lugar de `/stop/{line_id}`
- Usar mismo patrón de try-except que `cage_router`
- Documentar todos los parámetros en docstrings
- Usar códigos HTTP apropiados (201 para creación, 200 para operaciones)
- Separar ValueError (404) de DomainException (400)

### 4. Inyección de Dependencias

#### dependencies.py

**Patrón a seguir**: Estructura de `cage_router` dependencies

```python
# ============================================================================
# Dependencias de Repositorios - Feeding
# ============================================================================

async def get_feeding_session_repo(
    session: AsyncSession = Depends(get_session)
) -> FeedingSessionRepository:
    """Crea instancia del repositorio de sesiones de alimentación."""
    return FeedingSessionRepository(session)


# ============================================================================
# Servicios de Infraestructura - Feeding
# ============================================================================

# Singleton del simulador PLC (mantiene estado en memoria)
_plc_simulator_instance: Optional[PLCSimulator] = None

def get_machine_service() -> IFeedingMachine:
    """
    Retorna instancia singleton del simulador PLC.
    En producción, esto sería reemplazado por el cliente Modbus real.
    """
    global _plc_simulator_instance
    if _plc_simulator_instance is None:
        _plc_simulator_instance = PLCSimulator()
    return _plc_simulator_instance


# ============================================================================
# Dependencias de Casos de Uso - Feeding
# ============================================================================

async def get_start_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    line_repo: FeedingLineRepository = Depends(get_line_repo),
    cage_repo: CageRepository = Depends(get_cage_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> StartFeedingSessionUseCase:
    """Crea instancia del caso de uso de inicio de alimentación."""
    return StartFeedingSessionUseCase(
        session_repository=session_repo,
        line_repository=line_repo,
        cage_repository=cage_repo,
        machine_service=machine_service
    )


async def get_stop_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> StopFeedingSessionUseCase:
    """Crea instancia del caso de uso de detención de alimentación."""
    return StopFeedingSessionUseCase(
        session_repository=session_repo,
        machine_service=machine_service
    )


async def get_pause_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> PauseFeedingSessionUseCase:
    """Crea instancia del caso de uso de pausa de alimentación."""
    return PauseFeedingSessionUseCase(
        session_repository=session_repo,
        machine_service=machine_service
    )


async def get_resume_feeding_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> ResumeFeedingSessionUseCase:
    """Crea instancia del caso de uso de reanudación de alimentación."""
    return ResumeFeedingSessionUseCase(
        session_repository=session_repo,
        machine_service=machine_service
    )


async def get_update_feeding_params_use_case(
    session_repo: FeedingSessionRepository = Depends(get_feeding_session_repo),
    machine_service: IFeedingMachine = Depends(get_machine_service)
) -> UpdateFeedingParametersUseCase:
    """Crea instancia del caso de uso de actualización de parámetros."""
    return UpdateFeedingParametersUseCase(
        session_repository=session_repo,
        machine_service=machine_service
    )


# ============================================================================
# Type Aliases para Endpoints - Feeding
# ============================================================================

StartFeedingUseCaseDep = Annotated[
    StartFeedingSessionUseCase,
    Depends(get_start_feeding_use_case)
]

StopFeedingUseCaseDep = Annotated[
    StopFeedingSessionUseCase,
    Depends(get_stop_feeding_use_case)
]

PauseFeedingUseCaseDep = Annotated[
    PauseFeedingSessionUseCase,
    Depends(get_pause_feeding_use_case)
]

ResumeFeedingUseCaseDep = Annotated[
    ResumeFeedingSessionUseCase,
    Depends(get_resume_feeding_use_case)
]

UpdateFeedingParamsUseCaseDep = Annotated[
    UpdateFeedingParametersUseCase,
    Depends(get_update_feeding_params_use_case)
]
```

**Cambios clave**:

- Agrupar por secciones con comentarios claros
- Usar docstrings en todas las funciones de dependencia
- Implementar singleton correctamente para PLCSimulator
- Usar nombres consistentes con el resto del proyecto
- Mantener orden: Repositorios → Servicios → Use Cases → Type Aliases

## Data Models

### Domain Models

#### FeedingSession (Aggregate Root)

```python
class FeedingSession:
    _id: SessionId
    _line_id: LineId
    _date: datetime
    _status: SessionStatus
    _total_dispensed_kg: Weight
    _dispensed_by_slot: Dict[int, Weight]
    _applied_strategy_config: Optional[Dict[str, Any]]
    _new_events: List[FeedingEvent]
```

#### FeedingEvent (Entity)

```python
class FeedingEvent:
    timestamp: datetime
    type: FeedingEventType
    description: str
    details: Dict[str, Any]
```

### DTOs

#### StartFeedingRequest

```python
class StartFeedingRequest(BaseModel):
    line_id: UUID
    cage_id: UUID
    mode: FeedingMode
    target_amount_kg: float = Field(..., ge=0)
    blower_speed_percentage: float = Field(..., ge=0, le=100)
    dosing_rate_kg_min: float = Field(..., gt=0)
```

#### UpdateParamsRequest

```python
class UpdateParamsRequest(BaseModel):
    line_id: UUID  # Se setea desde el path parameter
    blower_speed: Optional[float] = Field(None, ge=0, le=100)
    dosing_rate: Optional[float] = Field(None, gt=0)
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property Reflection

Después de analizar los requisitos, la mayoría son requisitos de estructura de código, configuración y convenciones que no son testeables mediante property-based testing. Los requisitos testeables se enfocan en:

1. **Persistencia**: Round-trip de sesiones (guardar y recuperar debe preservar datos)
2. **Consultas**: Filtrado correcto de sesiones activas
3. **Validación**: Rangos válidos en DTOs
4. **Manejo de errores**: Mapeo correcto de excepciones a códigos HTTP
5. **Integración**: Verificación de que el sistema funciona end-to-end

La mayoría de propiedades identificadas son en realidad **ejemplos específicos** (edge cases) más que propiedades universales, dado que este spec es sobre corrección de infraestructura y no sobre lógica de negocio compleja.

### Correctness Properties

#### Property 1: Repository Round-Trip Consistency

_For any_ valid FeedingSession with events, if we save it to the repository and then retrieve it by ID, the reconstructed session should have equivalent data (same status, total dispensed, dispensed by slot, and applied config).

**Validates: Requirements 2.3**

**Rationale**: Este es un round-trip property clásico que verifica que el mapeo ORM (dominio ↔ persistencia) preserva la información. Es crítico porque cualquier pérdida de datos en este proceso causaría inconsistencias en el sistema.

#### Property 2: Active Session Filtering

_For any_ collection of FeedingSession objects with different statuses, when we query for active sessions by line_id, the result should only include sessions with status CREATED, RUNNING, or PAUSED, and they should be ordered by date in descending order.

**Validates: Requirements 2.4**

**Rationale**: Verifica que el filtrado de sesiones activas funciona correctamente independientemente de la mezcla de estados en la base de datos.

#### Property 3: DTO Validation - Target Amount

_For any_ StartFeedingRequest with target_amount_kg < 0, the Pydantic validation should raise a ValidationError.

**Validates: Requirements 6.1**

**Rationale**: Asegura que valores negativos de alimento objetivo son rechazados, previniendo datos inválidos en el sistema.

#### Property 4: DTO Validation - Blower Speed Range

_For any_ StartFeedingRequest with blower_speed_percentage outside the range [0, 100], the Pydantic validation should raise a ValidationError.

**Validates: Requirements 6.2**

**Rationale**: Asegura que la velocidad del soplador está en un rango físicamente válido (porcentaje).

#### Property 5: DTO Validation - Dosing Rate Positive

_For any_ StartFeedingRequest with dosing_rate_kg_min ≤ 0, the Pydantic validation should raise a ValidationError.

**Validates: Requirements 6.3**

**Rationale**: Asegura que la tasa de dosificación es siempre positiva, previniendo configuraciones inválidas.

#### Property 6: Optional Fields Validation

_For any_ UpdateParamsRequest with optional fields present, the validation constraints should apply only to the fields that are not None, and should use the same rules as StartFeedingRequest.

**Validates: Requirements 6.4**

**Rationale**: Verifica que las validaciones de campos opcionales funcionan correctamente cuando están presentes.

#### Property 7: Exception to HTTP Status Mapping

_For any_ endpoint, when a ValueError is raised, the HTTP response status should be 404; when a DomainException is raised, the status should be 400; when any other Exception is raised, the status should be 500.

**Validates: Requirements 3.2, 7.1, 7.2, 7.3, 7.4**

**Rationale**: Asegura consistencia en el manejo de errores a través de todos los endpoints de la API.

#### Property 8: PLC Simulator Singleton

_For any_ sequence of dependency injection calls to get_machine_service(), the returned object should be the same instance (same id() in Python).

**Validates: Requirements 4.4**

**Rationale**: Verifica que el simulador PLC mantiene su estado entre requests, lo cual es crítico para simular el comportamiento del hardware real.

### Example-Based Tests

Los siguientes son casos específicos que deben verificarse mediante tests de ejemplo:

1. **CASCADE Delete** (Req 5.3): Crear una sesión con eventos, eliminar la sesión, verificar que los eventos también se eliminaron
2. **Health Check** (Req 10.3): GET /health debe retornar 200 con {"status": "healthy"}
3. **OpenAPI Docs** (Req 8.4, 10.4): GET /docs debe retornar la página de documentación sin errores
4. **Migration Success** (Req 10.1): Ejecutar alembic upgrade head debe completar sin errores
5. **Application Startup** (Req 10.2): Iniciar la aplicación debe cargar todos los routers sin ImportError

## Error Handling

### Estrategia de Manejo de Errores

El sistema usa un enfoque de tres niveles para manejo de errores:

1. **Validación de Entrada** (API Layer)

   - FastAPI/Pydantic validan automáticamente tipos y constraints
   - Retorna 422 Unprocessable Entity para errores de validación

2. **Errores de Negocio** (Application/Domain Layer)

   - `ValueError`: Recurso no encontrado → HTTP 404
   - `DomainException`: Regla de negocio violada → HTTP 400
   - Mensajes descriptivos se propagan al cliente

3. **Errores Inesperados** (Infrastructure Layer)
   - `Exception`: Error no manejado → HTTP 500
   - Mensaje genérico para no exponer detalles internos
   - Log completo del error para debugging

### Patrón de Try-Except en Endpoints

```python
try:
    result = await use_case.execute(request)
    return {"message": "Success", "data": result}

except ValueError as e:
    # Recurso no encontrado
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(e)
    )

except DomainException as e:
    # Regla de negocio violada
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e)
    )

except Exception as e:
    # Error inesperado
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error interno del servidor: {str(e)}"
    )
```

### Manejo de Transacciones

- **Repositorios usan `flush()` no `commit()`**: El control transaccional está en el nivel de endpoint
- **FastAPI maneja commit/rollback automáticamente** a través del ciclo de vida de la sesión
- **Errores causan rollback automático**: Si una excepción escapa del endpoint, la transacción se revierte

## Testing Strategy

### Unit Tests

Los unit tests se enfocan en verificar componentes individuales:

1. **Modelos ORM**

   - Verificar que `from_domain()` y `to_domain()` funcionan correctamente
   - Verificar que las relaciones SQLAlchemy están configuradas correctamente

2. **Repositorios**

   - Verificar que `save()` maneja correctamente INSERT vs UPDATE
   - Verificar que `find_by_id()` retorna None cuando no existe
   - Verificar que `find_active_by_line_id()` filtra correctamente

3. **DTOs**

   - Verificar validaciones de Pydantic con casos válidos e inválidos
   - Verificar que campos opcionales funcionan correctamente

4. **Endpoints**
   - Verificar que cada endpoint retorna el código HTTP correcto
   - Verificar que el manejo de errores funciona según el patrón establecido

### Property-Based Tests

Los property tests verifican propiedades universales:

1. **Repository Round-Trip** (Property 1)

   - Generar sesiones aleatorias válidas
   - Guardar y recuperar
   - Verificar equivalencia

2. **Active Session Filtering** (Property 2)

   - Generar colecciones de sesiones con estados aleatorios
   - Filtrar por activas
   - Verificar que solo retorna CREATED/RUNNING/PAUSED

3. **DTO Validations** (Properties 3-6)

   - Generar valores fuera de rangos válidos
   - Verificar que Pydantic rechaza correctamente

4. **Exception Mapping** (Property 7)

   - Generar diferentes tipos de excepciones
   - Verificar que se mapean a códigos HTTP correctos

5. **Singleton Behavior** (Property 8)
   - Llamar get_machine_service() múltiples veces
   - Verificar que retorna la misma instancia

### Integration Tests

Los integration tests verifican el sistema completo:

1. **Database Migrations**

   - Ejecutar migraciones en base de datos de prueba
   - Verificar que las tablas se crean correctamente
   - Verificar que los índices y constraints existen

2. **API End-to-End**

   - Iniciar aplicación de prueba
   - Hacer requests HTTP reales a endpoints
   - Verificar respuestas completas (status, headers, body)

3. **Health Checks**
   - Verificar que /health retorna 200
   - Verificar que /docs carga correctamente

### Test Configuration

- **Framework**: pytest con pytest-asyncio
- **Database**: PostgreSQL en Docker para tests de integración
- **Property Testing**: hypothesis para Python
- **Coverage Target**: 80% para código de infraestructura

## Implementation Notes

### Orden de Implementación

1. **Modelos ORM** (FeedingSessionModel, FeedingEventModel)

   - Definir tablas con todos los campos
   - Configurar relaciones y constraints
   - Agregar métodos from_domain() y to_domain()

2. **Migración de Base de Datos**

   - Crear migración Alembic
   - Definir upgrade() y downgrade()
   - Probar en base de datos local

3. **Repositorio**

   - Implementar FeedingSessionRepository
   - Seguir patrón de CageRepository exactamente
   - Usar flush() no commit()

4. **Dependencias**

   - Actualizar dependencies.py
   - Agregar funciones de dependencia para feeding
   - Crear type aliases

5. **Router**

   - Implementar feeding_router.py
   - Seguir patrón de cage_router exactamente
   - Usar rutas RESTful

6. **Integración**
   - Registrar router en **init**.py
   - Verificar que la aplicación inicia sin errores
   - Probar endpoints manualmente

### Consideraciones de Performance

- **Índices**: line_id, date, status en feeding_sessions para consultas frecuentes
- **JSONB**: Usar JSONB en lugar de JSON para mejor performance en PostgreSQL
- **Eager Loading**: Considerar usar joinedload() si se necesitan eventos frecuentemente
- **Connection Pooling**: Configurado automáticamente por SQLAlchemy

### Consideraciones de Seguridad

- **SQL Injection**: Prevenido por uso de ORM (SQLAlchemy)
- **Validación de Entrada**: Manejada por Pydantic automáticamente
- **Error Messages**: No exponer detalles internos en errores 500
- **CORS**: Configurado en main.py (restringir en producción)

### Compatibilidad con Código Existente

- **No Breaking Changes**: Los cambios son aditivos, no modifican código existente
- **Mismo Patrón**: Sigue exactamente el patrón de cage_router y system_layout
- **Transacciones**: Compatible con el manejo transaccional existente
- **Dependencias**: No introduce nuevas dependencias externas

## Migration Script

### Alembic Migration

```python
"""create feeding sessions and events tables

Revision ID: <generated>
Revises: <previous_revision>
Create Date: <timestamp>
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '<generated>'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feeding_sessions table
    op.create_table(
        'feeding_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('line_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('total_dispensed_kg', sa.Float(), nullable=False),
        sa.Column('dispensed_by_slot', postgresql.JSONB(), nullable=False),
        sa.Column('applied_strategy_config', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['line_id'], ['feeding_lines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for feeding_sessions
    op.create_index(
        'ix_feeding_sessions_line_id',
        'feeding_sessions',
        ['line_id']
    )
    op.create_index(
        'ix_feeding_sessions_date',
        'feeding_sessions',
        ['date']
    )
    op.create_index(
        'ix_feeding_sessions_status',
        'feeding_sessions',
        ['status']
    )

    # Create feeding_events table
    op.create_table(
        'feeding_events',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ['session_id'],
            ['feeding_sessions.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for feeding_events
    op.create_index(
        'ix_feeding_events_session_id',
        'feeding_events',
        ['session_id']
    )
    op.create_index(
        'ix_feeding_events_timestamp',
        'feeding_events',
        ['timestamp']
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index('ix_feeding_events_timestamp', table_name='feeding_events')
    op.drop_index('ix_feeding_events_session_id', table_name='feeding_events')
    op.drop_table('feeding_events')

    op.drop_index('ix_feeding_sessions_status', table_name='feeding_sessions')
    op.drop_index('ix_feeding_sessions_date', table_name='feeding_sessions')
    op.drop_index('ix_feeding_sessions_line_id', table_name='feeding_sessions')
    op.drop_table('feeding_sessions')
```

## Checklist de Verificación

Antes de considerar completa la implementación, verificar:

- [ ] FeedingSessionModel tiene todos los campos y relaciones correctas
- [ ] FeedingEventModel tiene foreign key con CASCADE
- [ ] Migración Alembic se ejecuta sin errores
- [ ] FeedingSessionRepository usa flush() no commit()
- [ ] Repositorio implementa save(), find_by_id(), find_active_by_line_id()
- [ ] feeding_router.py sigue exactamente el patrón de cage_router.py
- [ ] Todos los endpoints tienen try-except con manejo de errores correcto
- [ ] dependencies.py tiene todas las funciones de dependencia
- [ ] PLCSimulator se implementa como singleton
- [ ] Router está registrado en api/routers/**init**.py
- [ ] Aplicación inicia sin errores de importación
- [ ] GET /health retorna 200
- [ ] GET /docs muestra endpoints de feeding
- [ ] Todos los endpoints responden correctamente a requests de prueba
- [ ] DTOs tienen validaciones de Pydantic correctas
- [ ] Código sigue el mismo estilo que el resto del proyecto
