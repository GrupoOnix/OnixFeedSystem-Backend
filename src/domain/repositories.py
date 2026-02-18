from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple

from domain.aggregates.alert import Alert
from domain.aggregates.system_config import SystemConfig
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.aggregates.food import Food
from domain.aggregates.scheduled_alert import ScheduledAlert
from domain.aggregates.silo import Silo
from domain.entities.cage_feeding import CageFeeding
from domain.entities.feeding_event import FeedingEvent, FeedingEventType
from domain.entities.feeding_session import FeedingSession as FeedingSessionEntity
from domain.entities.population_event import PopulationEvent
from domain.entities.slot_assignment import SlotAssignment
from domain.enums import AlertCategory, AlertStatus, AlertType, PopulationEventType

from .aggregates.feeding_line.feeding_line import FeedingLine
from .value_objects import (
    AlertId,
    BiometryLogEntry,
    CageGroupId,
    CageGroupName,
    CageId,
    CageName,
    ConfigChangeLogEntry,
    FoodId,
    FoodName,
    LineId,
    LineName,
    MortalityLogEntry,
    ScheduledAlertId,
    SiloId,
    SiloName,
)


class IFeedingLineRepository(ABC):
    @abstractmethod
    async def save(self, feeding_line: FeedingLine) -> None: ...

    @abstractmethod
    async def find_by_id(self, line_id: LineId) -> Optional[FeedingLine]: ...

    @abstractmethod
    async def find_by_name(self, name: LineName) -> Optional[FeedingLine]: ...

    @abstractmethod
    async def get_all(self) -> list[FeedingLine]: ...

    @abstractmethod
    async def delete(self, line_id: LineId) -> None: ...


class ICageRepository(ABC):
    """Repositorio para el aggregate Cage."""

    @abstractmethod
    async def save(self, cage: Cage) -> None:
        """Guarda o actualiza una jaula."""
        ...

    @abstractmethod
    async def find_by_id(self, cage_id: CageId) -> Optional[Cage]:
        """Busca una jaula por su ID."""
        ...

    @abstractmethod
    async def find_by_name(self, name: CageName) -> Optional[Cage]:
        """Busca una jaula por su nombre."""
        ...

    @abstractmethod
    async def list(self) -> List[Cage]:
        """Lista todas las jaulas."""
        ...

    @abstractmethod
    async def delete(self, cage_id: CageId) -> None:
        """Elimina una jaula."""
        ...

    @abstractmethod
    async def exists(self, cage_id: CageId) -> bool:
        """Verifica si existe una jaula con el ID dado."""
        ...


class ICageGroupRepository(ABC):
    """Repositorio para el aggregate CageGroup."""

    @abstractmethod
    async def save(self, cage_group: CageGroup) -> None:
        """Guarda o actualiza un grupo de jaulas."""
        ...

    @abstractmethod
    async def find_by_id(self, group_id: CageGroupId) -> Optional[CageGroup]:
        """Busca un grupo por su ID."""
        ...

    @abstractmethod
    async def find_by_name(self, name: CageGroupName) -> Optional[CageGroup]:
        """Busca un grupo por su nombre."""
        ...

    @abstractmethod
    async def list(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CageGroup]:
        """
        Lista grupos de jaulas con filtros opcionales.

        Args:
            search: Búsqueda en nombre, descripción o cage_ids
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación

        Returns:
            Lista de grupos ordenados por created_at DESC
        """
        ...

    @abstractmethod
    async def count(self, search: Optional[str] = None) -> int:
        """
        Cuenta total de grupos con filtros opcionales.

        Args:
            search: Búsqueda en nombre, descripción o cage_ids

        Returns:
            Cantidad total de grupos
        """
        ...

    @abstractmethod
    async def delete(self, group_id: CageGroupId) -> None:
        """Elimina un grupo de jaulas."""
        ...

    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: Optional[CageGroupId] = None) -> bool:
        """
        Verifica si existe un grupo con el nombre dado.

        Args:
            name: Nombre a buscar (case-insensitive)
            exclude_id: ID de grupo a excluir (útil para updates)

        Returns:
            True si existe un grupo con ese nombre, False en caso contrario
        """
        ...


class IPopulationEventRepository(ABC):
    """Repositorio para eventos de población de jaulas."""

    @abstractmethod
    async def save(self, event: PopulationEvent) -> None:
        """Guarda un evento de población."""
        ...

    @abstractmethod
    async def list_by_cage(
        self,
        cage_id: CageId,
        event_types: Optional[List[PopulationEventType]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PopulationEvent]:
        """
        Lista eventos de población de una jaula.

        Args:
            cage_id: ID de la jaula
            event_types: Filtro opcional por tipos de evento
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación

        Returns:
            Lista de eventos ordenados por fecha DESC
        """
        ...

    @abstractmethod
    async def count_by_cage(
        self,
        cage_id: CageId,
        event_types: Optional[List[PopulationEventType]] = None,
    ) -> int:
        """Cuenta eventos de una jaula, opcionalmente filtrados por tipo."""
        ...


class ISlotAssignmentRepository(ABC):
    """Repositorio para asignaciones de jaulas a slots de líneas."""

    @abstractmethod
    async def save(self, assignment: SlotAssignment) -> None:
        """Guarda o actualiza una asignación."""
        ...

    @abstractmethod
    async def find_by_line_and_slot(self, line_id: LineId, slot_number: int) -> Optional[SlotAssignment]:
        """Busca una asignación por línea y número de slot."""
        ...

    @abstractmethod
    async def find_by_cage(self, cage_id: CageId) -> Optional[SlotAssignment]:
        """Busca la asignación de una jaula (una jaula solo puede estar en un slot)."""
        ...

    @abstractmethod
    async def find_by_line(self, line_id: LineId) -> List[SlotAssignment]:
        """Obtiene todas las asignaciones de una línea."""
        ...

    @abstractmethod
    async def delete(self, assignment_id) -> None:
        """Elimina una asignación."""
        ...

    @abstractmethod
    async def delete_by_line(self, line_id: LineId) -> None:
        """Elimina todas las asignaciones de una línea."""
        ...

    @abstractmethod
    async def delete_by_cage(self, cage_id: CageId) -> None:
        """Elimina la asignación de una jaula."""
        ...


class ISiloRepository(ABC):
    @abstractmethod
    async def save(self, silo: Silo) -> None: ...

    @abstractmethod
    async def find_by_id(self, silo_id: SiloId) -> Optional[Silo]: ...

    @abstractmethod
    async def find_by_name(self, name: SiloName) -> Optional[Silo]: ...

    @abstractmethod
    async def get_all(self) -> List[Silo]: ...

    @abstractmethod
    async def delete(self, silo_id: SiloId) -> None: ...


class IFeedingSessionRepository(ABC):
    @abstractmethod
    async def save(self, session: FeedingSessionEntity) -> None: ...

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[FeedingSessionEntity]: ...

    @abstractmethod
    async def find_active_by_line(self, line_id: str) -> Optional[FeedingSessionEntity]: ...

    @abstractmethod
    async def find_today_by_line(self, line_id: str) -> Optional[FeedingSessionEntity]: ...

    @abstractmethod
    async def list_by_date_range(self, start: datetime, end: datetime) -> List[FeedingSessionEntity]: ...


class ICageFeedingRepository(ABC):
    @abstractmethod
    async def save(self, cage_feeding: CageFeeding) -> None: ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[CageFeeding]: ...

    @abstractmethod
    async def find_by_session(self, session_id: str) -> List[CageFeeding]: ...

    @abstractmethod
    async def find_current_by_session(self, session_id: str) -> Optional[CageFeeding]: ...


class IFeedingEventRepository(ABC):
    @abstractmethod
    async def save(self, event: FeedingEvent) -> None: ...

    @abstractmethod
    async def save_many(self, events: List[FeedingEvent]) -> None: ...

    @abstractmethod
    async def find_by_session(self, session_id: str) -> List[FeedingEvent]: ...

    @abstractmethod
    async def find_by_type(self, session_id: str, event_type: FeedingEventType) -> List[FeedingEvent]: ...


class IBiometryLogRepository(ABC):
    """Repositorio para logs de biometría de jaulas."""

    @abstractmethod
    async def save(self, log_entry: BiometryLogEntry) -> None:
        """Guarda un registro de biometría."""
        ...

    @abstractmethod
    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List[BiometryLogEntry]:
        """Lista registros de biometría de una jaula, ordenados por fecha DESC."""
        ...

    @abstractmethod
    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de biometría de una jaula."""
        ...


class IMortalityLogRepository(ABC):
    """Repositorio para logs de mortalidad de jaulas."""

    @abstractmethod
    async def save(self, log_entry: MortalityLogEntry) -> None:
        """Guarda un registro de mortalidad."""
        ...

    @abstractmethod
    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List[MortalityLogEntry]:
        """Lista registros de mortalidad de una jaula, ordenados por fecha DESC."""
        ...

    @abstractmethod
    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de mortalidad de una jaula."""
        ...

    @abstractmethod
    async def get_total_mortality(self, cage_id: CageId) -> int:
        """Calcula la mortalidad acumulada total de una jaula."""
        ...


class IConfigChangeLogRepository(ABC):
    """Repositorio para logs de cambios de configuración de jaulas."""

    @abstractmethod
    async def save_batch(self, log_entries: List[ConfigChangeLogEntry]) -> None:
        """Guarda múltiples registros de cambios en una sola transacción."""
        ...

    @abstractmethod
    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List[ConfigChangeLogEntry]:
        """Lista registros de cambios de configuración de una jaula, ordenados por fecha DESC."""
        ...

    @abstractmethod
    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de cambios de configuración de una jaula."""
        ...


class IFoodRepository(ABC):
    """Interfaz del repositorio de alimentos."""

    @abstractmethod
    async def save(self, food: Food) -> None:
        """Guarda o actualiza un alimento."""
        ...

    @abstractmethod
    async def find_by_id(self, food_id: FoodId) -> Optional[Food]:
        """Busca un alimento por su ID."""
        ...

    @abstractmethod
    async def find_by_name(self, name: FoodName) -> Optional[Food]:
        """Busca un alimento por su nombre."""
        ...

    @abstractmethod
    async def find_by_code(self, code: str) -> Optional[Food]:
        """Busca un alimento por su código de producto."""
        ...

    @abstractmethod
    async def get_all(self) -> List[Food]:
        """Obtiene todos los alimentos."""
        ...

    @abstractmethod
    async def get_active(self) -> List[Food]:
        """Obtiene solo los alimentos activos."""
        ...

    @abstractmethod
    async def delete(self, food_id: FoodId) -> None:
        """Elimina un alimento."""
        ...


# ============================================================================
# Repositorios de Alertas
# ============================================================================


class IAlertRepository(ABC):
    """Repositorio para alertas del sistema."""

    @abstractmethod
    async def save(self, alert: Alert) -> None:
        """Guarda o actualiza una alerta."""
        ...

    @abstractmethod
    async def find_by_id(self, alert_id: AlertId) -> Optional[Alert]:
        """Busca una alerta por su ID."""
        ...

    @abstractmethod
    async def list(
        self,
        status: Optional[List[AlertStatus]] = None,
        type: Optional[List[AlertType]] = None,
        category: Optional[List[AlertCategory]] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Alert]:
        """
        Lista alertas con filtros opcionales.

        Args:
            status: Filtrar por estados (ej: [UNREAD, READ])
            type: Filtrar por tipos (ej: [CRITICAL, WARNING])
            category: Filtrar por categorías (ej: [DEVICE, INVENTORY])
            search: Buscar en title, message, source
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación
        """
        ...

    @abstractmethod
    async def count_unread(self) -> int:
        """Cuenta la cantidad de alertas no leídas."""
        ...

    @abstractmethod
    async def mark_all_as_read(self) -> int:
        """
        Marca todas las alertas UNREAD como READ.

        Returns:
            Cantidad de alertas actualizadas.
        """
        ...

    @abstractmethod
    async def find_active_by_silo(self, silo_id: str) -> Optional[Alert]:
        """
        Busca una alerta activa (UNREAD o READ) para un silo específico.

        Útil para evitar duplicar alertas de nivel bajo.

        Args:
            silo_id: ID del silo (en formato string)

        Returns:
            La alerta activa más reciente o None si no existe.
        """
        ...

    @abstractmethod
    async def find_any_by_silo(self, silo_id: str) -> Optional[Alert]:
        """
        Busca cualquier alerta para un silo (incluyendo silenciadas).

        Útil para verificar si ya existe una alerta antes de crear una nueva.

        Args:
            silo_id: ID del silo (en formato string)

        Returns:
            La alerta más reciente (incluso si está silenciada) o None.
        """
        ...

    @abstractmethod
    async def list_snoozed(self, limit: int = 50, offset: int = 0) -> Tuple[List[Alert], int]:
        """
        Lista alertas actualmente silenciadas.

        Args:
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación

        Returns:
            Tupla con (lista de alertas, total de alertas silenciadas)
        """
        ...

    @abstractmethod
    async def count_snoozed(self) -> int:
        """Cuenta la cantidad de alertas actualmente silenciadas."""
        ...

    @abstractmethod
    async def count_by_type(
        self,
        type: AlertType,
        exclude_resolved: bool = True,
        exclude_snoozed: bool = True,
    ) -> int:
        """
        Cuenta alertas por tipo.

        Args:
            type: Tipo de alerta a contar
            exclude_resolved: Excluir alertas resueltas
            exclude_snoozed: Excluir alertas silenciadas

        Returns:
            Cantidad de alertas del tipo especificado
        """
        ...


class IScheduledAlertRepository(ABC):
    """Repositorio para alertas programadas."""

    @abstractmethod
    async def save(self, scheduled_alert: ScheduledAlert) -> None:
        """Guarda o actualiza una alerta programada."""
        ...

    @abstractmethod
    async def find_by_id(self, alert_id: ScheduledAlertId) -> Optional[ScheduledAlert]:
        """Busca una alerta programada por su ID."""
        ...

    @abstractmethod
    async def get_all(self) -> List[ScheduledAlert]:
        """Obtiene todas las alertas programadas."""
        ...

    @abstractmethod
    async def get_active(self) -> List[ScheduledAlert]:
        """Obtiene solo las alertas programadas activas."""
        ...

    @abstractmethod
    async def delete(self, alert_id: ScheduledAlertId) -> None:
        """Elimina una alerta programada."""
        ...


class ISystemConfigRepository(ABC):

    @abstractmethod
    async def get(self) -> SystemConfig:
        ...

    @abstractmethod
    async def save(self, config: SystemConfig) -> None:
        ...
