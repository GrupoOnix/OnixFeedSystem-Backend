"""Modelos de persistencia con SQLModel."""

from .alert_model import AlertModel
from .blower_model import BlowerModel
from .cage_feeding_model import CageFeedingModel
from .cage_group_model import CageGroupModel
from .cage_model import CageModel
from .cooler_model import CoolerModel
from .doser_model import DoserModel
from .feeding_event_model import FeedingEventModel
from .feeding_line_model import FeedingLineModel
from .feeding_session_model import FeedingSessionModel
from .food_model import FoodModel
# from .operation_event_model import OperationEventModel  # REMOVED - Old feeding system
from .population_event_model import PopulationEventModel
from .scheduled_alert_model import ScheduledAlertModel
from .selector_model import SelectorModel
from .sensor_model import SensorModel
from .silo_model import SiloModel
from .slot_assignment_model import SlotAssignmentModel
from .system_config_model import SystemConfigModel

__all__ = [
    "SiloModel",
    "CageModel",
    "CageFeedingModel",
    "CageGroupModel",
    "PopulationEventModel",
    "SlotAssignmentModel",
    "FeedingLineModel",
    "BlowerModel",
    "CoolerModel",
    "DoserModel",
    "SelectorModel",
    "SensorModel",
    "FeedingSessionModel",
    "FeedingEventModel",
    # "OperationEventModel",  # REMOVED - Old feeding system
    "FoodModel",
    "AlertModel",
    "ScheduledAlertModel",
    "SystemConfigModel",
]
