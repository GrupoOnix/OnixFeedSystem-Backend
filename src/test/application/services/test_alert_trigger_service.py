from unittest.mock import AsyncMock, MagicMock

import pytest

from application.services.alert_trigger_service import AlertTriggerService
from domain.aggregates.alert import Alert
from domain.enums import AlertCategory, AlertType
from domain.repositories import IAlertRepository


def _existing_low_silo_alert() -> Alert:
    return Alert(
        type=AlertType.WARNING,
        category=AlertCategory.INVENTORY,
        title="Nivel bajo en Silo 1",
        message="El silo está al 15.0% de capacidad (150/1000 kg)",
        source="Silo 1",
        metadata={
            "silo_id": "silo-1",
            "current_level": 150,
            "max_capacity": 1000,
            "percentage": 15.0,
        },
    )


@pytest.mark.asyncio
async def test_low_silo_alert_is_not_saved_again_when_unchanged():
    repository = MagicMock(spec=IAlertRepository)
    repository.find_any_by_silo = AsyncMock(return_value=_existing_low_silo_alert())
    repository.save = AsyncMock()
    service = AlertTriggerService(repository)

    result = await service.silo_low_level("silo-1", "Silo 1", 150, 1000, 15.0)

    assert result.created is False
    assert result.updated is False
    repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_low_silo_alert_is_updated_when_severity_changes():
    alert = _existing_low_silo_alert()
    repository = MagicMock(spec=IAlertRepository)
    repository.find_any_by_silo = AsyncMock(return_value=alert)
    repository.save = AsyncMock()
    service = AlertTriggerService(repository)

    result = await service.silo_low_level("silo-1", "Silo 1", 50, 1000, 5.0)

    assert result.updated is True
    assert alert.type == AlertType.CRITICAL
    repository.save.assert_awaited_once_with(alert)
