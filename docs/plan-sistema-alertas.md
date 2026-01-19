# Plan de Implementación: Sistema de Alertas

## Resumen Ejecutivo

Este documento detalla el plan de implementación del sistema de alertas para el backend de OnixFeedSystem. El sistema permitirá crear, gestionar y programar alertas relacionadas con dispositivos, inventario, alimentación y mantenimiento.

---

## 1. Arquitectura Propuesta

### 1.1 Estructura de Archivos

```
src/
├── domain/
│   ├── aggregates/
│   │   ├── alert.py                    # Aggregate Root: Alert
│   │   └── scheduled_alert.py          # Aggregate Root: ScheduledAlert
│   ├── value_objects/
│   │   └── alert_ids.py                # AlertId, ScheduledAlertId
│   ├── enums.py                        # + AlertType, AlertStatus, AlertCategory, ScheduledAlertFrequency
│   └── repositories.py                 # + IAlertRepository, IScheduledAlertRepository
│
├── application/
│   ├── use_cases/
│   │   └── alerts/
│   │       ├── __init__.py
│   │       ├── list_alerts_use_case.py
│   │       ├── get_unread_count_use_case.py
│   │       ├── update_alert_use_case.py
│   │       ├── mark_alert_read_use_case.py
│   │       ├── mark_all_alerts_read_use_case.py
│   │       ├── create_alert_use_case.py          # Interno (para triggers)
│   │       ├── list_scheduled_alerts_use_case.py
│   │       ├── create_scheduled_alert_use_case.py
│   │       ├── update_scheduled_alert_use_case.py
│   │       ├── delete_scheduled_alert_use_case.py
│   │       └── toggle_scheduled_alert_use_case.py
│   └── dtos/
│       └── alert_dtos.py
│
├── infrastructure/
│   ├── persistence/
│   │   ├── models/
│   │   │   ├── alert_model.py
│   │   │   └── scheduled_alert_model.py
│   │   └── repositories/
│   │       ├── alert_repository.py
│   │       └── scheduled_alert_repository.py
│   └── services/
│       └── alert_scheduler_service.py    # Job para alertas programadas
│
├── api/
│   └── routers/
│       └── alerts_router.py
│
└── alembic/
    └── versions/
        └── YYYY_MM_DD_HHMM-xxx_create_alerts_tables.py
```

---

## 2. Capa de Dominio

### 2.1 Enums (agregar a `src/domain/enums.py`)

```python
class AlertType(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    SUCCESS = "SUCCESS"

class AlertStatus(Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"

class AlertCategory(Enum):
    SYSTEM = "SYSTEM"
    DEVICE = "DEVICE"
    FEEDING = "FEEDING"
    INVENTORY = "INVENTORY"
    MAINTENANCE = "MAINTENANCE"
    CONNECTION = "CONNECTION"

class ScheduledAlertFrequency(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM_DAYS = "CUSTOM_DAYS"
```

### 2.2 Value Objects (`src/domain/value_objects/alert_ids.py`)

```python
@dataclass(frozen=True)
class AlertId:
    value: UUID
    
    @classmethod
    def generate(cls) -> "AlertId":
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, id_str: str) -> "AlertId":
        return cls(UUID(id_str))

@dataclass(frozen=True)
class ScheduledAlertId:
    value: UUID
    
    @classmethod
    def generate(cls) -> "ScheduledAlertId":
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, id_str: str) -> "ScheduledAlertId":
        return cls(UUID(id_str))
```

### 2.3 Aggregate Root: Alert (`src/domain/aggregates/alert.py`)

```python
class Alert:
    """Aggregate Root que representa una alerta del sistema."""
    
    def __init__(
        self,
        type: AlertType,
        category: AlertCategory,
        title: str,
        message: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._id: AlertId = AlertId.generate()
        self._type: AlertType = type
        self._status: AlertStatus = AlertStatus.UNREAD
        self._category: AlertCategory = category
        self._title: str = title
        self._message: str = message
        self._source: Optional[str] = source
        self._timestamp: datetime = datetime.utcnow()
        self._read_at: Optional[datetime] = None
        self._resolved_at: Optional[datetime] = None
        self._resolved_by: Optional[str] = None
        self._metadata: Dict[str, Any] = metadata or {}

    # Properties (getters)
    @property
    def id(self) -> AlertId: ...
    @property
    def type(self) -> AlertType: ...
    # ... etc

    # Métodos de negocio
    def mark_as_read(self) -> None:
        """Marca la alerta como leída."""
        if self._status == AlertStatus.UNREAD:
            self._status = AlertStatus.READ
            self._read_at = datetime.utcnow()

    def resolve(self, resolved_by: Optional[str] = None) -> None:
        """Resuelve la alerta."""
        if self._status in [AlertStatus.UNREAD, AlertStatus.READ]:
            self._status = AlertStatus.RESOLVED
            self._resolved_at = datetime.utcnow()
            self._resolved_by = resolved_by
            if self._read_at is None:
                self._read_at = self._resolved_at

    def archive(self) -> None:
        """Archiva la alerta."""
        self._status = AlertStatus.ARCHIVED
```

### 2.4 Aggregate Root: ScheduledAlert (`src/domain/aggregates/scheduled_alert.py`)

```python
class ScheduledAlert:
    """Aggregate Root que representa una alerta programada."""
    
    def __init__(
        self,
        title: str,
        message: str,
        type: AlertType,
        category: AlertCategory,
        frequency: ScheduledAlertFrequency,
        next_trigger_date: datetime,
        days_before_warning: int = 0,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        custom_days_interval: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._id: ScheduledAlertId = ScheduledAlertId.generate()
        self._title: str = title
        self._message: str = message
        self._type: AlertType = type
        self._category: AlertCategory = category
        self._frequency: ScheduledAlertFrequency = frequency
        self._next_trigger_date: datetime = next_trigger_date
        self._days_before_warning: int = days_before_warning
        self._is_active: bool = True
        self._device_id: Optional[str] = device_id
        self._device_name: Optional[str] = device_name
        self._custom_days_interval: Optional[int] = custom_days_interval
        self._metadata: Dict[str, Any] = metadata or {}
        self._created_at: datetime = datetime.utcnow()
        self._last_triggered_at: Optional[datetime] = None

    # Métodos de negocio
    def should_trigger(self, now: datetime) -> bool:
        """Determina si la alerta debe dispararse."""
        if not self._is_active:
            return False
        
        trigger_date = self._next_trigger_date - timedelta(days=self._days_before_warning)
        
        if now >= trigger_date:
            if self._last_triggered_at is None:
                return True
            return self._last_triggered_at < trigger_date
        
        return False

    def mark_triggered(self) -> None:
        """Marca la alerta como disparada y calcula la siguiente fecha."""
        self._last_triggered_at = datetime.utcnow()
        self._next_trigger_date = self._calculate_next_date()

    def _calculate_next_date(self) -> datetime:
        """Calcula la próxima fecha de disparo según la frecuencia."""
        base = self._next_trigger_date
        
        if self._frequency == ScheduledAlertFrequency.DAILY:
            return base + timedelta(days=1)
        elif self._frequency == ScheduledAlertFrequency.WEEKLY:
            return base + timedelta(weeks=1)
        elif self._frequency == ScheduledAlertFrequency.MONTHLY:
            # Siguiente mes, mismo día
            month = base.month + 1
            year = base.year
            if month > 12:
                month = 1
                year += 1
            return base.replace(year=year, month=month)
        elif self._frequency == ScheduledAlertFrequency.CUSTOM_DAYS:
            return base + timedelta(days=self._custom_days_interval or 1)
        
        return base

    def toggle_active(self) -> bool:
        """Activa/desactiva la alerta programada."""
        self._is_active = not self._is_active
        return self._is_active

    def update(
        self,
        title: Optional[str] = None,
        message: Optional[str] = None,
        type: Optional[AlertType] = None,
        frequency: Optional[ScheduledAlertFrequency] = None,
        next_trigger_date: Optional[datetime] = None,
        days_before_warning: Optional[int] = None,
        custom_days_interval: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Actualiza los campos de la alerta programada."""
        if title is not None:
            self._title = title
        # ... etc
```

### 2.5 Interfaces de Repositorio (agregar a `src/domain/repositories.py`)

```python
class IAlertRepository(ABC):
    """Repositorio para alertas."""

    @abstractmethod
    async def save(self, alert: Alert) -> None: ...

    @abstractmethod
    async def find_by_id(self, alert_id: AlertId) -> Optional[Alert]: ...

    @abstractmethod
    async def list(
        self,
        status: Optional[List[AlertStatus]] = None,
        type: Optional[List[AlertType]] = None,
        category: Optional[List[AlertCategory]] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Alert]: ...

    @abstractmethod
    async def count_unread(self) -> int: ...

    @abstractmethod
    async def mark_all_as_read(self) -> int:
        """Marca todas las alertas UNREAD como READ. Retorna cantidad actualizada."""
        ...


class IScheduledAlertRepository(ABC):
    """Repositorio para alertas programadas."""

    @abstractmethod
    async def save(self, scheduled_alert: ScheduledAlert) -> None: ...

    @abstractmethod
    async def find_by_id(self, alert_id: ScheduledAlertId) -> Optional[ScheduledAlert]: ...

    @abstractmethod
    async def get_all(self) -> List[ScheduledAlert]: ...

    @abstractmethod
    async def get_active(self) -> List[ScheduledAlert]: ...

    @abstractmethod
    async def delete(self, alert_id: ScheduledAlertId) -> None: ...
```

---

## 3. Capa de Infraestructura

### 3.1 Modelos de Base de Datos

**`src/infrastructure/persistence/models/alert_model.py`**

```python
class AlertModel(SQLModel, table=True):
    __tablename__ = "alerts"

    id: UUID = Field(primary_key=True)
    type: str = Field(index=True)          # AlertType.value
    status: str = Field(index=True)        # AlertStatus.value
    category: str = Field(index=True)      # AlertCategory.value
    title: str = Field(max_length=200)
    message: str
    source: Optional[str] = Field(default=None, max_length=200)
    timestamp: datetime = Field(index=True)
    read_at: Optional[datetime] = Field(default=None)
    resolved_at: Optional[datetime] = Field(default=None)
    resolved_by: Optional[str] = Field(default=None, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    @staticmethod
    def from_domain(alert: Alert) -> "AlertModel": ...
    
    def to_domain(self) -> Alert: ...
```

**`src/infrastructure/persistence/models/scheduled_alert_model.py`**

```python
class ScheduledAlertModel(SQLModel, table=True):
    __tablename__ = "scheduled_alerts"

    id: UUID = Field(primary_key=True)
    title: str = Field(max_length=200)
    message: str
    type: str                              # AlertType.value
    category: str                          # AlertCategory.value
    frequency: str                         # ScheduledAlertFrequency.value
    next_trigger_date: datetime = Field(index=True)
    days_before_warning: int = Field(default=0)
    is_active: bool = Field(default=True, index=True)
    device_id: Optional[str] = Field(default=None, max_length=100)
    device_name: Optional[str] = Field(default=None, max_length=200)
    custom_days_interval: Optional[int] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    created_at: datetime
    last_triggered_at: Optional[datetime] = Field(default=None)

    @staticmethod
    def from_domain(sa: ScheduledAlert) -> "ScheduledAlertModel": ...
    
    def to_domain(self) -> ScheduledAlert: ...
```

### 3.2 Migración Alembic

```python
# alembic/versions/YYYY_MM_DD_HHMM-xxx_create_alerts_tables.py

def upgrade() -> None:
    # Tabla alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('source', sa.String(200), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=True),
        sa.Column('metadata', JSONB(), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_type', 'alerts', ['type'])
    op.create_index('ix_alerts_status', 'alerts', ['status'])
    op.create_index('ix_alerts_category', 'alerts', ['category'])
    op.create_index('ix_alerts_timestamp', 'alerts', ['timestamp'])
    
    # Tabla scheduled_alerts
    op.create_table(
        'scheduled_alerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('next_trigger_date', sa.DateTime(), nullable=False),
        sa.Column('days_before_warning', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('device_name', sa.String(200), nullable=True),
        sa.Column('custom_days_interval', sa.Integer(), nullable=True),
        sa.Column('metadata', JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduled_alerts_next_trigger_date', 'scheduled_alerts', ['next_trigger_date'])
    op.create_index('ix_scheduled_alerts_is_active', 'scheduled_alerts', ['is_active'])

def downgrade() -> None:
    op.drop_table('scheduled_alerts')
    op.drop_table('alerts')
```

---

## 4. Capa de Aplicación

### 4.1 DTOs (`src/application/dtos/alert_dtos.py`)

```python
@dataclass
class AlertResponse:
    id: str
    type: str
    status: str
    category: str
    title: str
    message: str
    source: Optional[str]
    timestamp: datetime
    read_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class ListAlertsRequest:
    status: Optional[List[str]] = None      # ["UNREAD", "READ"]
    type: Optional[List[str]] = None        # ["CRITICAL", "WARNING"]
    category: Optional[List[str]] = None    # ["DEVICE", "FEEDING"]
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0

@dataclass
class ListAlertsResponse:
    alerts: List[AlertResponse]
    total: int

@dataclass
class UnreadCountResponse:
    count: int

@dataclass
class UpdateAlertRequest:
    status: Optional[str] = None
    resolved_by: Optional[str] = None

@dataclass
class CreateScheduledAlertRequest:
    title: str
    message: str
    type: str
    category: str
    frequency: str
    next_trigger_date: datetime
    days_before_warning: int = 0
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    custom_days_interval: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ScheduledAlertResponse:
    id: str
    title: str
    message: str
    type: str
    category: str
    frequency: str
    next_trigger_date: datetime
    days_before_warning: int
    is_active: bool
    device_id: Optional[str]
    device_name: Optional[str]
    custom_days_interval: Optional[int]
    metadata: Dict[str, Any]
    created_at: datetime
    last_triggered_at: Optional[datetime]

@dataclass
class UpdateScheduledAlertRequest:
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None
    frequency: Optional[str] = None
    next_trigger_date: Optional[datetime] = None
    days_before_warning: Optional[int] = None
    custom_days_interval: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
```

### 4.2 Casos de Uso Principales

**`list_alerts_use_case.py`**
```python
class ListAlertsUseCase:
    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, request: ListAlertsRequest) -> ListAlertsResponse:
        # Convertir strings a enums
        status_list = [AlertStatus(s) for s in request.status] if request.status else None
        type_list = [AlertType(t) for t in request.type] if request.type else None
        category_list = [AlertCategory(c) for c in request.category] if request.category else None
        
        alerts = await self._alert_repo.list(
            status=status_list,
            type=type_list,
            category=category_list,
            search=request.search,
            limit=request.limit,
            offset=request.offset
        )
        
        return ListAlertsResponse(
            alerts=[self._to_response(a) for a in alerts],
            total=len(alerts)  # TODO: implementar count separado para paginación real
        )
```

**`create_alert_use_case.py`** (uso interno para triggers)
```python
class CreateAlertUseCase:
    """Caso de uso interno para crear alertas desde triggers del sistema."""
    
    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(
        self,
        type: AlertType,
        category: AlertCategory,
        title: str,
        message: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertId:
        alert = Alert(
            type=type,
            category=category,
            title=title,
            message=message,
            source=source,
            metadata=metadata
        )
        
        await self._alert_repo.save(alert)
        return alert.id
```

---

## 5. Capa de API

### 5.1 Router (`src/api/routers/alerts_router.py`)

```python
router = APIRouter(prefix="/alerts", tags=["Alerts"])

# ============================================================================
# Alertas
# ============================================================================

@router.get("", response_model=ListAlertsResponse)
async def list_alerts(
    use_case: ListAlertsUseCaseDep,
    status: Optional[str] = Query(None, description="Filtrar por status (comma-separated)"),
    type: Optional[str] = Query(None, description="Filtrar por tipo (comma-separated)"),
    category: Optional[str] = Query(None, description="Filtrar por categoría (comma-separated)"),
    search: Optional[str] = Query(None, description="Buscar en title, message, source"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> ListAlertsResponse:
    """Lista alertas con filtros y paginación."""
    request = ListAlertsRequest(
        status=status.split(",") if status else None,
        type=type.split(",") if type else None,
        category=category.split(",") if category else None,
        search=search,
        limit=limit,
        offset=offset
    )
    return await use_case.execute(request)

@router.get("/unread/count", response_model=UnreadCountResponse)
async def get_unread_count(use_case: GetUnreadCountUseCaseDep) -> UnreadCountResponse:
    """Obtiene el contador de alertas no leídas (para navbar)."""
    return await use_case.execute()

@router.patch("/{alert_id}")
async def update_alert(
    alert_id: str,
    request: UpdateAlertRequest,
    use_case: UpdateAlertUseCaseDep
) -> AlertResponse:
    """Actualiza una alerta (status, resolved_by)."""
    return await use_case.execute(alert_id, request)

@router.post("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    use_case: MarkAlertReadUseCaseDep
) -> dict:
    """Marca una alerta como leída."""
    await use_case.execute(alert_id)
    return {"message": "Alerta marcada como leída"}

@router.patch("/read-all")
async def mark_all_read(use_case: MarkAllAlertsReadUseCaseDep) -> dict:
    """Marca todas las alertas como leídas."""
    count = await use_case.execute()
    return {"message": f"{count} alertas marcadas como leídas"}

# ============================================================================
# Alertas Programadas
# ============================================================================

@router.get("/scheduled", response_model=List[ScheduledAlertResponse])
async def list_scheduled_alerts(
    use_case: ListScheduledAlertsUseCaseDep
) -> List[ScheduledAlertResponse]:
    """Lista todas las alertas programadas."""
    return await use_case.execute()

@router.post("/scheduled", response_model=ScheduledAlertResponse, status_code=201)
async def create_scheduled_alert(
    request: CreateScheduledAlertRequest,
    use_case: CreateScheduledAlertUseCaseDep
) -> ScheduledAlertResponse:
    """Crea una nueva alerta programada."""
    return await use_case.execute(request)

@router.patch("/scheduled/{alert_id}", response_model=ScheduledAlertResponse)
async def update_scheduled_alert(
    alert_id: str,
    request: UpdateScheduledAlertRequest,
    use_case: UpdateScheduledAlertUseCaseDep
) -> ScheduledAlertResponse:
    """Actualiza una alerta programada."""
    return await use_case.execute(alert_id, request)

@router.delete("/scheduled/{alert_id}")
async def delete_scheduled_alert(
    alert_id: str,
    use_case: DeleteScheduledAlertUseCaseDep
) -> dict:
    """Elimina una alerta programada."""
    await use_case.execute(alert_id)
    return {"message": "Alerta programada eliminada"}

@router.patch("/scheduled/{alert_id}/toggle")
async def toggle_scheduled_alert(
    alert_id: str,
    use_case: ToggleScheduledAlertUseCaseDep
) -> dict:
    """Activa/desactiva una alerta programada."""
    is_active = await use_case.execute(alert_id)
    return {"is_active": is_active}
```

---

## 6. Servicio de Scheduler

### 6.1 AlertSchedulerService (`src/infrastructure/services/alert_scheduler_service.py`)

```python
class AlertSchedulerService:
    """
    Servicio que verifica y dispara alertas programadas.
    Diseñado para ejecutarse cada 60 segundos via background task.
    """
    
    def __init__(
        self,
        scheduled_alert_repo: IScheduledAlertRepository,
        alert_repo: IAlertRepository
    ):
        self._scheduled_alert_repo = scheduled_alert_repo
        self._alert_repo = alert_repo

    async def check_and_trigger_alerts(self) -> int:
        """
        Verifica alertas programadas y crea alertas cuando corresponde.
        Retorna cantidad de alertas disparadas.
        """
        now = datetime.utcnow()
        triggered_count = 0
        
        scheduled_alerts = await self._scheduled_alert_repo.get_active()
        
        for sa in scheduled_alerts:
            if sa.should_trigger(now):
                # Crear alerta
                alert = Alert(
                    type=sa.type,
                    category=AlertCategory.MAINTENANCE,  # Programadas siempre son MAINTENANCE
                    title=sa.title,
                    message=sa.message,
                    source=sa.device_name,
                    metadata={
                        "scheduled_alert_id": str(sa.id),
                        "maintenance_date": sa.next_trigger_date.isoformat(),
                        **(sa.metadata or {})
                    }
                )
                await self._alert_repo.save(alert)
                
                # Marcar como disparada (actualiza next_trigger_date)
                sa.mark_triggered()
                await self._scheduled_alert_repo.save(sa)
                
                triggered_count += 1
        
        return triggered_count
```

### 6.2 Background Task (FastAPI Lifespan)

```python
# En main.py o startup
from contextlib import asynccontextmanager
import asyncio

async def scheduled_alerts_job():
    """Job que corre cada 60 segundos."""
    while True:
        try:
            async with get_session_context() as session:
                scheduled_repo = ScheduledAlertRepository(session)
                alert_repo = AlertRepository(session)
                service = AlertSchedulerService(scheduled_repo, alert_repo)
                
                count = await service.check_and_trigger_alerts()
                if count > 0:
                    logger.info(f"Alertas programadas disparadas: {count}")
                    
                await session.commit()
        except Exception as e:
            logger.error(f"Error en scheduled_alerts_job: {e}")
        
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(scheduled_alerts_job())
    yield
    # Shutdown
    task.cancel()
```

---

## 7. Triggers para Crear Alertas

### 7.1 Servicio de Triggers (`src/application/services/alert_trigger_service.py`)

```python
class AlertTriggerService:
    """
    Servicio centralizado para disparar alertas desde diferentes partes del sistema.
    Otros use cases pueden inyectar este servicio para crear alertas.
    
    NOTA: Todos los mensajes están en español.
    """
    
    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    # =========================================================================
    # TRIGGERS PRIORITARIOS (Fase 1)
    # =========================================================================

    async def silo_low_level(
        self,
        silo_id: str,
        silo_name: str,
        current_level: float,
        max_capacity: float,
        percentage: float
    ) -> AlertId:
        """Nivel bajo de silo."""
        alert_type = AlertType.CRITICAL if percentage < 10 else AlertType.WARNING
        return await self._create_alert(
            type=alert_type,
            category=AlertCategory.INVENTORY,
            title=f"Nivel bajo en {silo_name}",
            message=f"El silo está al {percentage:.1f}% de capacidad ({current_level:.0f}/{max_capacity:.0f} kg)",
            source=silo_name,
            metadata={
                "silo_id": silo_id,
                "current_level": current_level,
                "max_capacity": max_capacity,
                "percentage": percentage
            }
        )

    async def sensor_out_of_range(
        self,
        sensor_id: str,
        sensor_name: str,
        line_id: str,
        current_value: float,
        normal_range: Tuple[float, float],
        unit: str
    ) -> AlertId:
        """Sensor fuera de rango."""
        return await self._create_alert(
            type=AlertType.WARNING,
            category=AlertCategory.DEVICE,
            title=f"Sensor fuera de rango: {sensor_name}",
            message=f"Valor actual: {current_value} {unit}. Rango normal: {normal_range[0]}-{normal_range[1]} {unit}",
            source=f"{sensor_name} - Línea {line_id}",
            metadata={
                "sensor_id": sensor_id,
                "line_id": line_id,
                "current_value": current_value,
                "normal_range": list(normal_range),
                "unit": unit
            }
        )

    async def device_incomplete_config(
        self,
        device_id: str,
        device_type: str,  # "Blower", "Doser", "Selector"
        device_name: str,
        line_id: str,
        line_name: str,
        missing_fields: List[str]
    ) -> AlertId:
        """Dispositivo con configuración incompleta o incorrecta."""
        missing_str = ", ".join(missing_fields)
        return await self._create_alert(
            type=AlertType.WARNING,
            category=AlertCategory.DEVICE,
            title=f"Configuración incompleta: {device_name}",
            message=f"El {device_type.lower()} tiene campos sin configurar: {missing_str}",
            source=f"{device_name} - {line_name}",
            metadata={
                "device_id": device_id,
                "device_type": device_type,
                "line_id": line_id,
                "line_name": line_name,
                "missing_fields": missing_fields
            }
        )

    # =========================================================================
    # TRIGGERS FUTUROS (para implementar después)
    # =========================================================================

    async def device_error(
        self,
        device_id: str,
        device_name: str,
        line_id: str,
        error_code: str,
        error_message: str
    ) -> AlertId:
        """Dispositivo reporta error. (FUTURO - requiere comunicación PLC)"""
        return await self._create_alert(
            type=AlertType.CRITICAL,
            category=AlertCategory.DEVICE,
            title=f"Error en {device_name}",
            message=error_message,
            source=f"{device_name} - Línea {line_id}",
            metadata={
                "device_id": device_id,
                "line_id": line_id,
                "error_code": error_code
            }
        )

    async def connection_lost(
        self,
        device_id: str,
        device_name: str,
        line_id: str,
        last_seen: datetime
    ) -> AlertId:
        """Sin heartbeat de dispositivo. (FUTURO - requiere monitoreo de conexión)"""
        return await self._create_alert(
            type=AlertType.WARNING,
            category=AlertCategory.CONNECTION,
            title=f"Sin conexión: {device_name}",
            message=f"No se recibe señal del dispositivo desde {last_seen.strftime('%Y-%m-%d %H:%M:%S')}",
            source=f"{device_name} - Línea {line_id}",
            metadata={
                "device_id": device_id,
                "line_id": line_id,
                "last_seen": last_seen.isoformat()
            }
        )

    async def feeding_operation_failed(
        self,
        operation_id: str,
        line_id: str,
        cage_id: str,
        reason: str,
        amount_dispensed: float,
        amount_target: float
    ) -> AlertId:
        """Operación de feeding falla. (FUTURO - requiere detección de fallos)"""
        return await self._create_alert(
            type=AlertType.CRITICAL,
            category=AlertCategory.FEEDING,
            title="Fallo en operación de alimentación",
            message=f"La operación falló: {reason}. Dispensado: {amount_dispensed:.1f}kg de {amount_target:.1f}kg objetivo",
            source=f"Línea {line_id}",
            metadata={
                "operation_id": operation_id,
                "line_id": line_id,
                "cage_id": cage_id,
                "reason": reason,
                "amount_dispensed": amount_dispensed,
                "amount_target": amount_target
            }
        )

    # =========================================================================
    # MÉTODO INTERNO
    # =========================================================================

    async def _create_alert(
        self,
        type: AlertType,
        category: AlertCategory,
        title: str,
        message: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertId:
        alert = Alert(
            type=type,
            category=category,
            title=title,
            message=message,
            source=source,
            metadata=metadata
        )
        await self._alert_repo.save(alert)
        return alert.id
```

---

## 8. Orden de Implementación

### Fase 1: Fundamentos (Prioridad Alta)
1. Agregar enums a `domain/enums.py`
2. Crear value objects `AlertId`, `ScheduledAlertId`
3. Crear aggregate `Alert`
4. Crear modelo `AlertModel`
5. Crear migración para tabla `alerts`
6. Crear `AlertRepository`
7. Agregar interfaz `IAlertRepository` a `repositories.py`

### Fase 2: API de Alertas
8. Crear DTOs de alertas
9. Crear casos de uso:
   - `ListAlertsUseCase`
   - `GetUnreadCountUseCase`
   - `UpdateAlertUseCase`
   - `MarkAlertReadUseCase`
   - `MarkAllAlertsReadUseCase`
10. Crear router `/alerts`
11. Configurar dependencies.py

### Fase 3: Alertas Programadas
12. Crear aggregate `ScheduledAlert`
13. Crear modelo `ScheduledAlertModel`
14. Crear migración para tabla `scheduled_alerts`
15. Crear `ScheduledAlertRepository`
16. Crear casos de uso de alertas programadas
17. Agregar endpoints `/alerts/scheduled`

### Fase 4: Scheduler y Triggers
18. Crear `AlertSchedulerService`
19. Configurar background task en lifespan (usando asyncio)
20. Crear `AlertTriggerService` con triggers prioritarios:
    - `silo_low_level` - Nivel bajo de silo
    - `sensor_out_of_range` - Sensor fuera de rango
    - `device_incomplete_config` - Dispositivo con configuración incompleta
21. (FUTURO) Integrar triggers en use cases existentes cuando sea posible

### Fase 5: Testing
22. Tests unitarios para aggregates
23. Tests de integración para use cases
24. Tests de API para endpoints

---

## 9. Decisiones Tomadas

| Aspecto | Decisión |
|---------|----------|
| **Paginación** | Simple por ahora (sin `total_count` separado). Se agrega después si es necesario |
| **Campo `resolved_by`** | String opcional. Se vinculará a sistema de usuarios cuando exista |
| **Retención de alertas** | Sin política por ahora. Las alertas se mantienen indefinidamente |
| **Triggers prioritarios** | `silo_low_level`, `sensor_out_of_range`, `device_incomplete_config` |
| **Idioma** | Español para todos los mensajes de alerta |
| **Scheduler** | asyncio con lifespan de FastAPI (simple y sin dependencias externas) |

---

## 10. Estimación de Archivos

| Archivo | Líneas Aprox. |
|---------|---------------|
| `domain/enums.py` (modificación) | +25 |
| `domain/value_objects/alert_ids.py` | ~40 |
| `domain/aggregates/alert.py` | ~120 |
| `domain/aggregates/scheduled_alert.py` | ~180 |
| `domain/repositories.py` (modificación) | +40 |
| `infrastructure/persistence/models/alert_model.py` | ~80 |
| `infrastructure/persistence/models/scheduled_alert_model.py` | ~100 |
| `infrastructure/persistence/repositories/alert_repository.py` | ~120 |
| `infrastructure/persistence/repositories/scheduled_alert_repository.py` | ~80 |
| `application/dtos/alert_dtos.py` | ~100 |
| `application/use_cases/alerts/*.py` (10 archivos) | ~400 |
| `application/services/alert_trigger_service.py` | ~150 |
| `infrastructure/services/alert_scheduler_service.py` | ~60 |
| `api/routers/alerts_router.py` | ~150 |
| `api/dependencies.py` (modificación) | +100 |
| Migración Alembic | ~60 |
| **Total aproximado** | **~1,800 líneas** |
