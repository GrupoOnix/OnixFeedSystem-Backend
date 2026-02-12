# Onboarding: Sistema de Alimentacion

> **Documento para desarrolladores que se integran al equipo de backend**
> 
> **Nota importante**: El sistema de alimentacion actual sera modificado o reemplazado en su totalidad. Este documento describe el estado actual para facilitar la comprension antes de los cambios.

---

## 1. Vision General del Proyecto

Este backend controla un **sistema automatizado de alimentacion para acuicultura**. El sistema gestiona:

- **Lineas de alimentacion** (FeedingLine): Infraestructura fisica con sopladores, dosificadores, selectores y sensores
- **Jaulas** (Cage): Donde estan los peces, con seguimiento de poblacion y biomasa
- **Silos**: Almacenamiento de alimento
- **Sesiones de alimentacion** (FeedingSession): Operaciones diarias de alimentacion

### Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| Framework | FastAPI 0.121.0 |
| Base de datos | PostgreSQL 18 |
| ORM | SQLModel + Alembic |
| Python | 3.11 |
| Testing | pytest + pytest-asyncio |
| Linting | ruff, mypy |

---

## 2. Arquitectura del Sistema

El proyecto sigue **Clean Architecture + DDD (Domain-Driven Design)**:

```
src/
├── domain/              # Capa de Dominio (reglas de negocio puras)
│   ├── aggregates/      # Aggregate Roots
│   ├── entities/        # Entidades de dominio
│   ├── value_objects/   # Value Objects (IDs tipados, Weight, etc.)
│   ├── strategies/      # Patron Strategy para modos de alimentacion
│   ├── repositories.py  # Interfaces de repositorios
│   ├── interfaces.py    # Interfaces de servicios externos (IFeedingMachine)
│   └── enums.py         # Enumeraciones del dominio
│
├── application/         # Capa de Aplicacion (casos de uso)
│   ├── use_cases/       # Implementacion de casos de uso
│   └── dtos/            # Data Transfer Objects
│
├── infrastructure/      # Capa de Infraestructura (implementaciones)
│   ├── persistence/     # Repositorios, modelos de BD
│   └── services/        # Servicios externos (PLCSimulator)
│
└── api/                 # Capa de Presentacion (FastAPI)
    ├── routers/         # Endpoints REST
    ├── models/          # Request/Response models
    └── dependencies.py  # Inyeccion de dependencias
```

### Principio de Dependencias

```
API → Application → Domain ← Infrastructure
         ↓              ↓
      (usa)        (implementa interfaces)
```

El dominio NO depende de nada externo. Infrastructure implementa las interfaces definidas en el dominio.

---

## 3. Sistema de Alimentacion - Componentes Principales

### 3.1 Modelo de Dominio

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FeedingLine (Aggregate)                      │
│  Representa una linea fisica de alimentacion                        │
├─────────────────────────────────────────────────────────────────────┤
│  Componentes:                                                       │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌───────────┐ │
│  │ Blower  │→ │ Cooler  │→ │  Doser   │→ │Selector│→ │  Jaulas   │ │
│  │(soplador)  │(enfriador) │(dosificador) │(distribuidor)│ (1-N)  │ │
│  └─────────┘  └─────────┘  └──────────┘  └────────┘  └───────────┘ │
│                                                                     │
│  + Sensors (temperatura, presion, flujo)                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Sesiones y Operaciones

El sistema usa un **modelo de dos niveles**:

```
┌──────────────────────────────────────────────────────────────┐
│              FeedingSession (Aggregate Root)                  │
│  Sesion operativa diaria - contenedor de operaciones         │
├──────────────────────────────────────────────────────────────┤
│  - session_id: SessionId                                     │
│  - line_id: LineId                                           │
│  - date: datetime                                            │
│  - status: ACTIVE | CLOSED                                   │
│  - total_dispensed_kg: Weight (acumulador del dia)          │
│  - current_operation: FeedingOperation (0..1)               │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ contiene N operaciones en el dia
                              ▼
┌──────────────────────────────────────────────────────────────┐
│              FeedingOperation (Entity)                        │
│  Una "visita" a una jaula (desde START hasta STOP)           │
├──────────────────────────────────────────────────────────────┤
│  - operation_id: OperationId                                 │
│  - session_id: SessionId (FK)                                │
│  - cage_id: CageId                                           │
│  - target_slot: int                                          │
│  - target_amount: Weight                                     │
│  - dispensed: Weight                                         │
│  - status: RUNNING | PAUSED | COMPLETED | STOPPED | FAILED   │
│  - started_at, ended_at: datetime                            │
│  - applied_config: Dict (configuracion enviada al PLC)       │
│  - events: List[OperationEvent] (historial de la operacion)  │
└──────────────────────────────────────────────────────────────┘
```

**Concepto clave**: Una sesion puede tener multiples operaciones durante el dia. Despues de hacer STOP en una operacion, se puede iniciar otra en la misma sesion (alimentar otra jaula o volver a la misma).

### 3.3 Estados y Transiciones

#### SessionStatus (Sesion)
```
ACTIVE ──────────────────────────→ CLOSED
       (cierre al final del dia)
```

#### OperationStatus (Operacion)
```
         ┌──────────┐
         │ RUNNING  │◄──────────┐
         └────┬─────┘           │
              │                 │
    ┌─────────┼─────────┐       │
    ▼         ▼         ▼       │
┌───────┐ ┌───────┐ ┌───────┐   │
│PAUSED │ │STOPPED│ │FAILED │   │
└───┬───┘ └───────┘ └───────┘   │
    │                           │
    └───────────────────────────┘
          (resume)
```

---

## 4. Flujo de una Operacion de Alimentacion

### 4.1 Inicio (Start)

```
Usuario                API                UseCase              Domain              PLC
   │                    │                    │                    │                  │
   │  POST /feeding/start                    │                    │                  │
   │  {line_id, cage_id,│                    │                    │                  │
   │   mode, target_kg} │                    │                    │                  │
   │───────────────────►│                    │                    │                  │
   │                    │  execute(request)  │                    │                  │
   │                    │───────────────────►│                    │                  │
   │                    │                    │  1. Validar linea  │                  │
   │                    │                    │  2. Validar jaula  │                  │
   │                    │                    │  3. Resolver slot  │                  │
   │                    │                    │─────────────────────────────────────► │
   │                    │                    │                    │                  │
   │                    │                    │  4. Buscar/crear sesion              │
   │                    │                    │───────────────────►│                  │
   │                    │                    │                    │                  │
   │                    │                    │  5. Crear estrategia (Manual)        │
   │                    │                    │───────────────────►│                  │
   │                    │                    │                    │                  │
   │                    │                    │  6. session.start_operation()        │
   │                    │                    │───────────────────►│                  │
   │                    │                    │                    │  send_config()  │
   │                    │                    │                    │────────────────►│
   │                    │                    │                    │                  │
   │                    │                    │  7. Persistir sesion + operacion     │
   │                    │                    │─────────────────────────────────────► │
   │                    │                    │                    │                  │
   │                    │  {session_id}      │                    │                  │
   │◄───────────────────│◄───────────────────│                    │                  │
```

### 4.2 Archivo: `src/application/use_cases/feeding/start_feeding_use_case.py`

```python
class StartFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        machine_service: IFeedingMachine   # <-- Interface al PLC
    ):
        # ...

    async def execute(self, request: StartFeedingRequest) -> UUID:
        # 1. Validar Linea
        line = await self.line_repository.find_by_id(LineId(request.line_id))
        
        # 2. Validar Jaula y obtener Slot Fisico
        cage = await self.cage_repository.find_by_id(CageId(request.cage_id))
        physical_slot = await self.line_repository.get_slot_number(...)
        
        # 3. Gestion de Sesion (Day Boundary)
        session = await self.session_repository.find_active_by_line_id(...)
        # Si es de ayer, cerrar y crear nueva
        
        # 4. Crear estrategia
        strategy = ManualFeedingStrategy(
            target_slot=physical_slot,
            blower_speed=request.blower_speed_percentage,
            doser_speed=request.dosing_rate_kg_min,
            target_amount_kg=request.target_amount_kg
        )
        
        # 5. Iniciar operacion (delega al dominio)
        operation_id = await session.start_operation(
            cage_id=cage_id,
            target_slot=physical_slot,
            strategy=strategy,
            machine=self.machine_service  # Inyeccion de la interface
        )
        
        # 6. Persistir
        await self.session_repository.save(session)
        await self.operation_repository.save(session.current_operation)
        
        return operation_id.value
```

---

## 5. Patron Strategy para Modos de Alimentacion

El sistema soporta diferentes modos de alimentacion mediante el patron Strategy:

```
┌─────────────────────────┐
│   IFeedingStrategy      │  (Interface)
├─────────────────────────┤
│ get_plc_configuration() │ → MachineConfiguration
└───────────┬─────────────┘
            │
    ┌───────┴───────┬─────────────────┐
    ▼               ▼                 ▼
┌────────────┐ ┌────────────┐ ┌──────────────┐
│  Manual    │ │  Cyclic    │ │ Programmed   │
│  Strategy  │ │  Strategy  │ │  Strategy    │
└────────────┘ └────────────┘ └──────────────┘
  (actual)       (futuro)       (futuro)
```

### ManualFeedingStrategy (src/domain/strategies/manual.py)

El operador controla manualmente todos los parametros:

```python
class ManualFeedingStrategy(IFeedingStrategy):
    def __init__(self, target_slot: int, blower_speed: float, 
                 doser_speed: float, target_amount_kg: float):
        self.target_slot = target_slot
        self.blower_speed = blower_speed
        self.doser_speed = doser_speed
        self.target_amount_kg = target_amount_kg

    def get_plc_configuration(self) -> MachineConfiguration:
        return MachineConfiguration(
            feeding_mode=FeedingMode.MANUAL,
            target_slot=self.target_slot,
            blower_speed_percentage=self.blower_speed,
            doser_speed_percentage=self.doser_speed,
            target_amount_kg=self.target_amount_kg
        )
```

---

## 6. Comunicacion con Hardware (IFeedingMachine)

### 6.1 Interface del Puerto

```python
# src/domain/interfaces.py

class IFeedingMachine(ABC):
    """Puerto para comunicacion con hardware de alimentacion."""
    
    @abstractmethod
    async def send_configuration(self, line_id: LineId, config: MachineConfiguration) -> None:
        """Envia configuracion completa al PLC."""
        pass

    @abstractmethod
    async def get_status(self, line_id: LineId) -> MachineStatus:
        """Lee estado actual de la maquina (polling frecuente)."""
        pass

    @abstractmethod
    async def pause(self, line_id: LineId) -> None:
        """Pausa la operacion."""
        pass

    @abstractmethod
    async def resume(self, line_id: LineId) -> None:
        """Reanuda desde pausa."""
        pass

    @abstractmethod
    async def stop(self, line_id: LineId) -> None:
        """Detiene totalmente y resetea."""
        pass

    # Control individual de dispositivos
    async def set_blower_power(self, command: BlowerCommand) -> None: ...
    async def set_doser_rate(self, command: DoserCommand) -> None: ...
    async def move_selector(self, command: SelectorCommand) -> None: ...
    async def set_cooler_power(self, command: CoolerCommand) -> None: ...
    async def get_sensor_readings(self, line_id: LineId) -> SensorReadings: ...
```

### 6.2 Implementacion Actual: PLCSimulator

```python
# src/infrastructure/services/plc_simulator.py

class PLCSimulator(IFeedingMachine):
    """Simulador de PLC para desarrollo y testing."""
    
    async def send_configuration(self, line_id: LineId, config: MachineConfiguration) -> None:
        # Simula envio de configuracion
        self._configs[line_id] = config
        
    async def get_status(self, line_id: LineId) -> MachineStatus:
        # Retorna estado simulado
        return MachineStatus(
            is_running=True,
            total_dispensed_kg=self._simulated_dispensed,
            # ...
        )
```

**En produccion**, se implementaria un `PLCModbusClient` que use pymodbus u otro protocolo industrial.

---

## 7. API Endpoints de Alimentacion

### Router: `src/api/routers/feeding_router.py`

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/feeding/start` | Inicia sesion/operacion de alimentacion |
| POST | `/feeding/lines/{line_id}/stop` | Detiene operacion activa |
| POST | `/feeding/lines/{line_id}/pause` | Pausa operacion |
| POST | `/feeding/lines/{line_id}/resume` | Reanuda operacion pausada |
| PATCH | `/feeding/lines/{line_id}/parameters` | Actualiza parametros en caliente |

### Request de Inicio

```python
class StartFeedingRequest(BaseModel):
    line_id: UUID
    cage_id: UUID
    mode: FeedingMode = FeedingMode.MANUAL
    target_amount_kg: float
    blower_speed_percentage: float  # 0-100
    dosing_rate_kg_min: float
```

---

## 8. Inyeccion de Dependencias

### Archivo: `src/api/dependencies.py`

Todas las dependencias se configuran aca usando `Depends()` de FastAPI:

```python
# Repositorios
def get_feeding_session_repository(session: DbSessionDep) -> IFeedingSessionRepository:
    return FeedingSessionRepository(session)

def get_feeding_operation_repository(session: DbSessionDep) -> IFeedingOperationRepository:
    return FeedingOperationRepository(session)

# Servicios
def get_feeding_machine() -> IFeedingMachine:
    return PLCSimulator()  # En prod seria PLCModbusClient

# Use Cases
def get_start_feeding_use_case(
    session_repo: Annotated[IFeedingSessionRepository, Depends(get_feeding_session_repository)],
    operation_repo: Annotated[IFeedingOperationRepository, Depends(get_feeding_operation_repository)],
    line_repo: Annotated[IFeedingLineRepository, Depends(get_feeding_line_repository)],
    cage_repo: Annotated[ICageRepository, Depends(get_cage_repository)],
    machine: Annotated[IFeedingMachine, Depends(get_feeding_machine)]
) -> StartFeedingSessionUseCase:
    return StartFeedingSessionUseCase(session_repo, operation_repo, line_repo, cage_repo, machine)

# Type alias para uso en routers
StartFeedingUseCaseDep = Annotated[StartFeedingSessionUseCase, Depends(get_start_feeding_use_case)]
```

---

## 9. Persistencia

### Modelos de Base de Datos

```
┌──────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│ feeding_sessions │────<│feeding_operations │────<│ operation_events │
├──────────────────┤     ├───────────────────┤     ├──────────────────┤
│ id (PK)          │     │ id (PK)           │     │ id (PK)          │
│ line_id (FK)     │     │ session_id (FK)   │     │ operation_id (FK)│
│ date             │     │ cage_id (FK)      │     │ timestamp        │
│ status           │     │ target_slot       │     │ type             │
│ total_dispensed  │     │ target_amount     │     │ description      │
│ dispensed_by_slot│     │ dispensed         │     │ details (JSON)   │
│ created_at       │     │ status            │     └──────────────────┘
│ updated_at       │     │ started_at        │
└──────────────────┘     │ ended_at          │
                         │ applied_config    │
                         └───────────────────┘

Relaciones con CASCADE DELETE:
- Session → Operations (eliminar sesion elimina operaciones)
- Operation → Events (eliminar operacion elimina eventos)
```

### Repositorios

Los repositorios traducen entre modelos de BD y entidades de dominio:

```python
# src/infrastructure/persistence/repositories/feeding_session_repository.py

class FeedingSessionRepository(IFeedingSessionRepository):
    async def find_active_by_line_id(self, line_id: LineId) -> Optional[FeedingSession]:
        # Query con SQLModel
        stmt = select(FeedingSessionModel).where(
            FeedingSessionModel.line_id == line_id.value,
            FeedingSessionModel.status == SessionStatus.ACTIVE
        )
        result = await self.session.exec(stmt)
        model = result.first()
        
        if model:
            return self._to_domain(model)  # Mapeo a entidad de dominio
        return None
```

---

## 10. Archivos Clave para el Area de Alimentacion

### Dominio (logica de negocio)
| Archivo | Descripcion |
|---------|-------------|
| `src/domain/aggregates/feeding_session.py` | **Aggregate Root** - Sesion diaria |
| `src/domain/entities/feeding_operation.py` | Entidad - Operacion individual |
| `src/domain/aggregates/feeding_line/` | Componentes de linea (Blower, Doser, Selector, etc.) |
| `src/domain/strategies/base.py` | Interface IFeedingStrategy |
| `src/domain/strategies/manual.py` | Estrategia manual |
| `src/domain/interfaces.py` | Interface IFeedingMachine |
| `src/domain/enums.py` | SessionStatus, OperationStatus, FeedingMode |
| `src/domain/repositories.py` | Interfaces de repositorios |

### Aplicacion (casos de uso)
| Archivo | Descripcion |
|---------|-------------|
| `src/application/use_cases/feeding/start_feeding_use_case.py` | Iniciar alimentacion |
| `src/application/use_cases/feeding/stop_feeding_use_case.py` | Detener alimentacion |
| `src/application/use_cases/feeding/control_feeding_use_case.py` | Pausar/Reanudar |
| `src/application/use_cases/feeding/update_feeding_use_case.py` | Actualizar parametros |
| `src/application/dtos/feeding_dtos.py` | DTOs de request/response |

### Infraestructura
| Archivo | Descripcion |
|---------|-------------|
| `src/infrastructure/services/plc_simulator.py` | Simulador de PLC |
| `src/infrastructure/persistence/models/feeding_session_model.py` | Modelo BD sesion |
| `src/infrastructure/persistence/models/feeding_operation_model.py` | Modelo BD operacion |
| `src/infrastructure/persistence/repositories/feeding_session_repository.py` | Repo sesiones |
| `src/infrastructure/persistence/repositories/feeding_operation_repository.py` | Repo operaciones |

### API
| Archivo | Descripcion |
|---------|-------------|
| `src/api/routers/feeding_router.py` | Endpoints REST |
| `src/api/dependencies.py` | Inyeccion de dependencias |

---

## 11. Comandos de Desarrollo

```bash
# Activar entorno virtual
source .venv/bin/activate

# Iniciar servicios (PostgreSQL + API)
docker-compose up -d

# Ver logs del backend
docker-compose logs -f backend

# Ejecutar tests
pytest

# Tests especificos de feeding
pytest src/test/application/use_cases/feeding/

# Linting
ruff check src/

# Type checking
mypy src/

# Migraciones
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic revision --autogenerate -m "descripcion"
```

---

## 12. Proximos Pasos para el Nuevo Desarrollador

1. **Configurar entorno local** siguiendo las instrucciones en `CLAUDE.md`

2. **Ejecutar la aplicacion** y probar los endpoints en http://localhost:8000/docs

3. **Leer los archivos clave** en el orden sugerido:
   - `src/domain/enums.py` (entender estados)
   - `src/domain/aggregates/feeding_session.py` (logica principal)
   - `src/domain/entities/feeding_operation.py` (operacion individual)
   - `src/application/use_cases/feeding/start_feeding_use_case.py` (flujo completo)

4. **Ejecutar tests existentes** para entender el comportamiento esperado

5. **Revisar documentacion adicional** en `/docs/`:
   - `plan-migracion-feeding-operation.md` - Decisiones de arquitectura
   - `API_CAGES.md` - API de jaulas (relacionado)

---

## 13. Consideraciones para el Reemplazo del Sistema

Al ser un sistema que sera modificado/reemplazado, ten en cuenta:

1. **Interfaces bien definidas**: El sistema usa interfaces (`IFeedingMachine`, `IFeedingStrategy`, repositorios) que facilitan el reemplazo de implementaciones

2. **Separacion de capas**: La logica de dominio esta aislada, permitiendo cambiar la infraestructura sin afectar reglas de negocio

3. **Patron Strategy**: Agregar nuevos modos de alimentacion solo requiere crear nuevas estrategias

4. **Persistencia separada**: Los modelos de BD estan desacoplados de las entidades de dominio

5. **Simulador de PLC**: Permite desarrollo sin hardware real, facilitando testing

---

*Documento generado: Febrero 2026*
*Ultima actualizacion del sistema: Fase 2 (FeedingOperation refactor)*
