"""Casos de uso para el sistema de alertas."""

from .create_alert_use_case import CreateAlertUseCase

# Alertas programadas
from .create_scheduled_alert_use_case import CreateScheduledAlertUseCase
from .delete_scheduled_alert_use_case import DeleteScheduledAlertUseCase
from .get_alert_counts_use_case import GetAlertCountsUseCase
from .get_snoozed_count_use_case import GetSnoozedCountUseCase
from .get_unread_count_use_case import GetUnreadCountUseCase
from .list_alerts_use_case import ListAlertsUseCase
from .list_scheduled_alerts_use_case import ListScheduledAlertsUseCase
from .list_snoozed_alerts_use_case import ListSnoozedAlertsUseCase
from .mark_alert_read_use_case import MarkAlertReadUseCase
from .mark_all_alerts_read_use_case import MarkAllAlertsReadUseCase
from .snooze_alert_use_case import SnoozeAlertUseCase
from .toggle_scheduled_alert_use_case import ToggleScheduledAlertUseCase
from .unsnooze_alert_use_case import UnsnoozeAlertUseCase
from .update_alert_use_case import UpdateAlertUseCase
from .update_scheduled_alert_use_case import UpdateScheduledAlertUseCase

__all__ = [
    # Alertas
    "ListAlertsUseCase",
    "GetUnreadCountUseCase",
    "UpdateAlertUseCase",
    "MarkAlertReadUseCase",
    "MarkAllAlertsReadUseCase",
    "SnoozeAlertUseCase",
    "UnsnoozeAlertUseCase",
    "CreateAlertUseCase",
    "ListSnoozedAlertsUseCase",
    "GetAlertCountsUseCase",
    "GetSnoozedCountUseCase",
    # Alertas programadas
    "ListScheduledAlertsUseCase",
    "CreateScheduledAlertUseCase",
    "UpdateScheduledAlertUseCase",
    "DeleteScheduledAlertUseCase",
    "ToggleScheduledAlertUseCase",
]
