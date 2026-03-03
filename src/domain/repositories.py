from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple

from domain.aggregates.alert import Alert
from domain.aggregates.feedback import Feedback
from domain.aggregates.system_config import SystemConfig
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.aggregates.food import Food
from domain.aggregates.scheduled_alert import ScheduledAlert
from domain.aggregates.silo import Silo
from domain.aggregates.user import User
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
    SessionId,
    SiloId,
    SiloName,
    UserId,
)


class IFeedingLineRepository(ABC):
    @abstractmethod
    async def save(self, feeding_line: FeedingLine) -> None: ...

    @abstractmethod
    async def find_by_id(self, line_id: LineId, user_id: UserId) -> Optional[FeedingLine]: ...

    @abstractmethod
    async def find_by_name(self, name: LineName, user_id: UserId) -> Optional[FeedingLine]: ...

    @abstractmethod
    async def get_all(self, user_id: UserId) -> list[FeedingLine]: ...

    @abstractmethod
    async def delete(self, line_id: LineId, user_id: UserId) -> None: ...


class ICageRepository(ABC):
    """Repositorio para el aggregate Cage."""

    @abstractmethod
    async def save(self, cage: Cage) -> None:
        """Guarda o actualiza una jaula."""
        ...

    @abstractmethod
    async def find_by_id(self, cage_id: CageId, user_id: UserId) -> Optional[Cage]:
        """Busca una jaula por su ID, filtrado por usuario."""
        ...

    @abstractmethod
    async def find_by_name(self, name: CageName, user_id: UserId) -> Optional[Cage]:
        """Busca una jaula por su nombre, filtrado por usuario."""
        ...

    @abstractmethod
    async def list(self, user_id: UserId) -> List[Cage]:
        """Lista todas las jaulas de un usuario."""
        ...

    @abstractmethod
    async def delete(self, cage_id: CageId, user_id: UserId) -> None:
        """Elimina una jaula del usuario."""
        ...

    @abstractmethod
    async def exists(self, cage_id: CageId, user_id: UserId) -> bool:
        """Verifica si existe una jaula con el ID dado para el usuario."""
        ...


class ICageGroupRepository(ABC):
    """Repositorio para el aggregate CageGroup."""

    @abstractmethod
    async def save(self, cage_group: CageGroup) -> None:
        """Guarda o actualiza un grupo de jaulas."""
        ...

    @abstractmethod
    async def find_by_id(self, group_id: CageGroupId, user_id: UserId) -> Optional[CageGroup]:
        """Busca un grupo por su ID, filtrado por usuario."""
        ...

    @abstractmethod
    async def find_by_name(self, name: CageGroupName, user_id: UserId) -> Optional[CageGroup]:
        """Busca un grupo por su nombre, filtrado por usuario."""
        ...

    @abstractmethod
    async def list(
        self,
        user_id: UserId,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CageGroup]:
        """
        Lista grupos de jaulas con filtros opcionales.

        Args:
            user_id: ID del usuario propietario
            search: Búsqueda en nombre, descripción o cage_ids
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación

        Returns:
            Lista de grupos ordenados por created_at DESC
        """
        ...

    @abstractmethod
    async def count(self, user_id: UserId, search: Optional[str] = None) -> int:
        """
        Cuenta total de grupos con filtros opcionales.

        Args:
            user_id: ID del usuario propietario
            search: Búsqueda en nombre, descripción o cage_ids

        Returns:
            Cantidad total de grupos
        """
        ...

    @abstractmethod
    async def delete(self, group_id: CageGroupId, user_id: UserId) -> None:
        """Elimina un grupo de jaulas del usuario."""
        ...

    @abstractmethod
    async def exists_by_name(self, name: str, user_id: UserId, exclude_id: Optional[CageGroupId] = None) -> bool:
        """
        Verifica si existe un grupo con el nombre dado.

        Args:
            name: Nombre a buscar (case-insensitive)
            user_id: ID del usuario propietario
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
    async def find_by_line_and_slot(
        self, line_id: LineId, slot_number: int, user_id: UserId
    ) -> Optional[SlotAssignment]:
        """Busca una asignación por línea y número de slot, filtrado por usuario."""
        ...

    @abstractmethod
    async def find_by_cage(self, cage_id: CageId, user_id: UserId) -> Optional[SlotAssignment]:
        """Busca la asignación de una jaula (una jaula solo puede estar en un slot), filtrado por usuario."""
        ...

    @abstractmethod
    async def find_by_line(self, line_id: LineId, user_id: UserId) -> List[SlotAssignment]:
        """Obtiene todas las asignaciones de una línea, filtrado por usuario."""
        ...

    @abstractmethod
    async def delete(self, assignment_id, user_id: UserId) -> None:
        """Elimina una asignación del usuario."""
        ...

    @abstractmethod
    async def delete_by_line(self, line_id: LineId, user_id: UserId) -> None:
        """Elimina todas las asignaciones de una línea del usuario."""
        ...

    @abstractmethod
    async def delete_by_cage(self, cage_id: CageId, user_id: UserId) -> None:
        """Elimina la asignación de una jaula del usuario."""
        ...


class ISiloRepository(ABC):
    @abstractmethod
    async def save(self, silo: Silo) -> None: ...

    @abstractmethod
    async def find_by_id(self, silo_id: SiloId, user_id: UserId) -> Optional[Silo]: ...

    @abstractmethod
    async def find_by_name(self, name: SiloName, user_id: UserId) -> Optional[Silo]: ...

    @abstractmethod
    async def get_all(self, user_id: UserId) -> List[Silo]: ...

    @abstractmethod
    async def delete(self, silo_id: SiloId, user_id: UserId) -> None: ...


class IFeedingSessionRepository(ABC):
    @abstractmethod
    async def save(self, session: FeedingSessionEntity) -> None: ...

    @abstractmethod
    async def find_by_id(self, session_id: str, user_id: UserId) -> Optional[FeedingSessionEntity]: ...

    @abstractmethod
    async def find_active_by_line(self, line_id: str, user_id: UserId) -> Optional[FeedingSessionEntity]: ...

    @abstractmethod
    async def find_today_by_line(self, line_id: str, user_id: UserId) -> Optional[FeedingSessionEntity]: ...

    @abstractmethod
    async def list_by_date_range(
        self, start: datetime, end: datetime, user_id: UserId
    ) -> List[FeedingSessionEntity]: ...


class ICageFeedingRepository(ABC):
    @abstractmethod
    async def save(self, cage_feeding: CageFeeding) -> None: ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[CageFeeding]: ...

    @abstractmethod
    async def find_by_session(self, session_id: str) -> List[CageFeeding]: ...

    @abstractmethod
    async def find_current_by_session(self, session_id: str) -> Optional[CageFeeding]: ...

    @abstractmethod
    async def get_today_dispensed_by_cage(self, cage_id: str) -> float:
        """Calcula el total de alimento dispensado a una jaula en el día actual."""
        ...

    @abstractmethod
    async def get_today_dispensed_by_cages(self, cage_ids: List[str]) -> dict[str, float]:
        """Calcula el total de alimento dispensado para múltiples jaulas en el día actual."""
        ...


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
    async def find_by_id(self, food_id: FoodId, user_id: UserId) -> Optional[Food]:
        """Busca un alimento por su ID, filtrado por usuario."""
        ...

    @abstractmethod
    async def find_by_name(self, name: FoodName, user_id: UserId) -> Optional[Food]:
        """Busca un alimento por su nombre, filtrado por usuario."""
        ...

    @abstractmethod
    async def find_by_code(self, code: str, user_id: UserId) -> Optional[Food]:
        """Busca un alimento por su código de producto, filtrado por usuario."""
        ...

    @abstractmethod
    async def get_all(self, user_id: UserId) -> List[Food]:
        """Obtiene todos los alimentos de un usuario."""
        ...

    @abstractmethod
    async def get_active(self, user_id: UserId) -> List[Food]:
        """Obtiene solo los alimentos activos de un usuario."""
        ...

    @abstractmethod
    async def delete(self, food_id: FoodId, user_id: UserId) -> None:
        """Elimina un alimento del usuario."""
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
    async def find_by_id(self, alert_id: AlertId, user_id: UserId) -> Optional[Alert]:
        """Busca una alerta por su ID, filtrado por usuario."""
        ...

    @abstractmethod
    async def list(
        self,
        user_id: UserId,
        status: Optional[List[AlertStatus]] = None,
        type: Optional[List[AlertType]] = None,
        category: Optional[List[AlertCategory]] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Alert]:
        """
        Lista alertas con filtros opcionales, filtrado por usuario.

        Args:
            user_id: ID del usuario propietario
            status: Filtrar por estados (ej: [UNREAD, READ])
            type: Filtrar por tipos (ej: [CRITICAL, WARNING])
            category: Filtrar por categorías (ej: [DEVICE, INVENTORY])
            search: Buscar en title, message, source
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación
        """
        ...

    @abstractmethod
    async def count_unread(self, user_id: UserId) -> int:
        """Cuenta la cantidad de alertas no leídas del usuario."""
        ...

    @abstractmethod
    async def mark_all_as_read(self, user_id: UserId) -> int:
        """
        Marca todas las alertas UNREAD como READ del usuario.

        Returns:
            Cantidad de alertas actualizadas.
        """
        ...

    @abstractmethod
    async def find_active_by_silo(self, silo_id: str, user_id: UserId) -> Optional[Alert]:
        """
        Busca una alerta activa (UNREAD o READ) para un silo específico del usuario.

        Útil para evitar duplicar alertas de nivel bajo.

        Args:
            silo_id: ID del silo (en formato string)
            user_id: ID del usuario propietario

        Returns:
            La alerta activa más reciente o None si no existe.
        """
        ...

    @abstractmethod
    async def find_any_by_silo(self, silo_id: str, user_id: UserId) -> Optional[Alert]:
        """
        Busca cualquier alerta para un silo del usuario (incluyendo silenciadas).

        Útil para verificar si ya existe una alerta antes de crear una nueva.

        Args:
            silo_id: ID del silo (en formato string)
            user_id: ID del usuario propietario

        Returns:
            La alerta más reciente (incluso si está silenciada) o None.
        """
        ...

    @abstractmethod
    async def list_snoozed(self, user_id: UserId, limit: int = 50, offset: int = 0) -> Tuple[List[Alert], int]:
        """
        Lista alertas actualmente silenciadas del usuario.

        Args:
            user_id: ID del usuario propietario
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación

        Returns:
            Tupla con (lista de alertas, total de alertas silenciadas)
        """
        ...

    @abstractmethod
    async def count_snoozed(self, user_id: UserId) -> int:
        """Cuenta la cantidad de alertas actualmente silenciadas del usuario."""
        ...

    @abstractmethod
    async def count_by_type(
        self,
        type: AlertType,
        user_id: UserId,
        exclude_resolved: bool = True,
        exclude_snoozed: bool = True,
    ) -> int:
        """
        Cuenta alertas por tipo del usuario.

        Args:
            type: Tipo de alerta a contar
            user_id: ID del usuario propietario
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
    async def find_by_id(self, alert_id: ScheduledAlertId, user_id: UserId) -> Optional[ScheduledAlert]:
        """Busca una alerta programada por su ID, filtrado por usuario."""
        ...

    @abstractmethod
    async def get_all(self, user_id: UserId) -> List[ScheduledAlert]:
        """Obtiene todas las alertas programadas del usuario."""
        ...

    @abstractmethod
    async def get_active(self, user_id: UserId) -> List[ScheduledAlert]:
        """Obtiene solo las alertas programadas activas del usuario."""
        ...

    @abstractmethod
    async def delete(self, alert_id: ScheduledAlertId, user_id: UserId) -> None:
        """Elimina una alerta programada del usuario."""
        ...


class IFeedbackRepository(ABC):
    """Repositorio para feedback de usuarios."""

    @abstractmethod
    async def save(self, feedback: Feedback) -> None:
        """Guarda un nuevo feedback."""
        ...


class ISystemConfigRepository(ABC):
    @abstractmethod
    async def get(self, user_id: UserId) -> SystemConfig: ...

    @abstractmethod
    async def save(self, config: SystemConfig) -> None: ...


class IUserRepository(ABC):
    """Repositorio para el aggregate User."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Guarda un nuevo usuario."""
        ...

    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Busca un usuario por su ID."""
        ...

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Busca un usuario por su username."""
        ...

    @abstractmethod
    async def get_all_user_ids(self) -> List[UserId]:
        """Obtiene los IDs de todos los usuarios registrados."""
        ...
