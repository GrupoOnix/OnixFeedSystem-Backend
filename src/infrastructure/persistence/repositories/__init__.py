"""Implementaciones de repositorios con SQLModel."""

from .alert_repository import AlertRepository
from .biometry_log_repository import BiometryLogRepository
from .cage_feeding_repository import CageFeedingRepository
from .cage_group_repository import CageGroupRepository
from .cage_repository import CageRepository
from .config_change_log_repository import ConfigChangeLogRepository
from .feeding_event_repository import FeedingEventRepository
from .feeding_line_repository import FeedingLineRepository
from .feeding_session_repository import FeedingSessionRepository
from .food_repository import FoodRepository
from .mortality_log_repository import MortalityLogRepository
from .population_event_repository import PopulationEventRepository
from .scheduled_alert_repository import ScheduledAlertRepository
from .silo_repository import SiloRepository
from .slot_assignment_repository import SlotAssignmentRepository
from .system_config_repository import SystemConfigRepository

__all__ = [
    "SiloRepository",
    "CageRepository",
    "CageFeedingRepository",
    "CageGroupRepository",
    "PopulationEventRepository",
    "SlotAssignmentRepository",
    "FeedingLineRepository",
    "FeedingSessionRepository",
    "FeedingEventRepository",
    "FoodRepository",
    "AlertRepository",
    "ScheduledAlertRepository",
    "BiometryLogRepository",
    "MortalityLogRepository",
    "ConfigChangeLogRepository",
    "SystemConfigRepository",
]
