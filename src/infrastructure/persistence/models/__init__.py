"""Modelos de persistencia con SQLModel."""

from .activity_log_model import ActivityLogModel
from .alert_model import AlertModel
from .biometry_log_model import BiometryLogModel
from .cage_group_activity_log_model import CageGroupActivityLogModel
from .blower_model import BlowerModel
from .cage_feeding_model import CageFeedingModel
from .cage_group_model import CageGroupModel
from .cage_model import CageModel
from .config_change_log_model import ConfigChangeLogModel
from .cooler_model import CoolerModel
from .doser_model import DoserModel
from .doser_calibration_model import DoserCalibrationModel
from .doser_silo_model import DoserSiloModel
from .feedback_model import FeedbackModel
from .feeding_event_model import FeedingEventModel
from .feeding_execution_job_model import FeedingExecutionJobModel
from .feeding_line_model import FeedingLineModel
from .feeding_session_model import FeedingSessionModel
from .food_model import FoodModel
from .last_selected_feeding_mode_model import LastSelectedFeedingModeModel
from .last_valid_cyclic_feeding_config_model import LastValidCyclicFeedingConfigModel
from .last_valid_manual_feeding_config_model import LastValidManualFeedingConfigModel
from .mortality_log_model import MortalityLogModel

# from .operation_event_model import OperationEventModel  # REMOVED - Old feeding system
from .population_event_model import PopulationEventModel
from .scheduled_alert_model import ScheduledAlertModel
from .scheduled_feeding_plan_model import ScheduledFeedingPlanModel
from .scheduled_feeding_run_model import ScheduledFeedingRunModel
from .selector_model import SelectorModel
from .sensor_model import SensorModel
from .silo_model import SiloModel
from .silo_inventory_model import (
    FeedingBatchConsumptionModel,
    SiloInventoryBatchModel,
    SiloInventoryMovementModel,
    SiloStockReservationModel,
)
from .slot_assignment_model import SlotAssignmentModel
from .system_config_model import SystemConfigModel
from .user_model import UserModel

__all__ = [
    "ActivityLogModel",
    "AlertModel",
    "BiometryLogModel",
    "CageGroupActivityLogModel",
    "SiloModel",
    "SiloInventoryBatchModel",
    "SiloInventoryMovementModel",
    "SiloStockReservationModel",
    "FeedingBatchConsumptionModel",
    "CageModel",
    "CageFeedingModel",
    "CageGroupModel",
    "ConfigChangeLogModel",
    "PopulationEventModel",
    "SlotAssignmentModel",
    "FeedingLineModel",
    "BlowerModel",
    "CoolerModel",
    "DoserModel",
    "DoserCalibrationModel",
    "DoserSiloModel",
    "SelectorModel",
    "SensorModel",
    "FeedingSessionModel",
    "FeedingEventModel",
    "FeedingExecutionJobModel",
    "LastValidManualFeedingConfigModel",
    "LastValidCyclicFeedingConfigModel",
    "LastSelectedFeedingModeModel",
    "FeedbackModel",
    "FoodModel",
    "MortalityLogModel",
    # "OperationEventModel",  # REMOVED - Old feeding system
    "ScheduledAlertModel",
    "ScheduledFeedingPlanModel",
    "ScheduledFeedingRunModel",
    "SystemConfigModel",
    "UserModel",
]
