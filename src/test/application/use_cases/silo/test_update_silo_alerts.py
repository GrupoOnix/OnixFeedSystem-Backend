from unittest.mock import AsyncMock, MagicMock

import pytest

from application.dtos.silo_dtos import UpdateSiloRequest
from application.services.alert_trigger_service import AlertTriggerService
from application.use_cases.silo.update_silo_use_case import UpdateSiloUseCase
from domain.aggregates.silo import Silo
from domain.repositories import ISiloRepository
from domain.value_objects import SiloName, Weight


def _configured_silo(stock_kg: float) -> Silo:
    silo = Silo(SiloName("Silo 1"), Weight.from_kg(1000))
    silo.load_inventory(
        total_stock=Weight.from_kg(stock_kg),
        reserved_stock=Weight.zero(),
        active_batches=[],
    )
    return silo


@pytest.mark.asyncio
async def test_metadata_update_uses_derived_stock_for_low_level_alert():
    silo = _configured_silo(150)
    repository = MagicMock(spec=ISiloRepository)
    repository.find_by_id = AsyncMock(return_value=silo)
    repository.find_by_name = AsyncMock(return_value=None)
    repository.save = AsyncMock()
    repository.find_by_id_with_line_info = AsyncMock(return_value=(silo, [], []))
    alerts = MagicMock(spec=AlertTriggerService)
    alerts.silo_low_level = AsyncMock()
    use_case = UpdateSiloUseCase(repository, alerts)

    await use_case.execute(str(silo.id), UpdateSiloRequest(name="Silo actualizado"))

    alerts.silo_low_level.assert_awaited_once()
    assert alerts.silo_low_level.call_args.kwargs["current_level"] == 150
    assert alerts.silo_low_level.call_args.kwargs["percentage"] == 15


@pytest.mark.asyncio
async def test_metadata_update_does_not_trigger_alert_above_threshold():
    silo = _configured_silo(500)
    repository = MagicMock(spec=ISiloRepository)
    repository.find_by_id = AsyncMock(return_value=silo)
    repository.find_by_name = AsyncMock(return_value=None)
    repository.save = AsyncMock()
    repository.find_by_id_with_line_info = AsyncMock(return_value=(silo, [], []))
    alerts = MagicMock(spec=AlertTriggerService)
    alerts.silo_low_level = AsyncMock()

    await UpdateSiloUseCase(repository, alerts).execute(
        str(silo.id),
        UpdateSiloRequest(name="Silo actualizado"),
    )

    alerts.silo_low_level.assert_not_awaited()
