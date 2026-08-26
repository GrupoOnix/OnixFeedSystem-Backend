from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from application.dtos.silo_inventory_dtos import TransferSiloStockRequest
from application.use_cases.silo import TransferSiloStockUseCase
from domain.entities.silo_inventory import (
    SiloInventoryBatch,
    SiloInventoryBatchStatus,
)


@pytest.mark.asyncio
async def test_transfer_silo_stock_maps_repository_result():
    source_silo_id = uuid4()
    destination_silo_id = uuid4()
    food_id = uuid4()
    now = datetime.now(timezone.utc)
    transferred_batch = SiloInventoryBatch(
        id=uuid4(),
        silo_id=destination_silo_id,
        food_id=food_id,
        remaining_quantity_mg=75_000_000,
        reserved_quantity_mg=0,
        position=1,
        status=SiloInventoryBatchStatus.ACTIVE,
        received_at=now,
        created_by_operator_id="operator-1",
        created_at=now,
        updated_at=now,
        food_name="Alimento A",
        food_code="A-01",
        food_provider="Proveedor",
    )
    repository = AsyncMock()
    repository.transfer_stock.return_value = [transferred_batch]
    use_case = TransferSiloStockUseCase(repository)

    response = await use_case.execute(
        str(source_silo_id),
        TransferSiloStockRequest(
            destination_silo_id=str(destination_silo_id),
            quantity_kg=75,
            operator_id="operator-1",
        ),
    )

    repository.transfer_stock.assert_awaited_once_with(
        source_silo_id,
        destination_silo_id,
        75,
        "operator-1",
    )
    assert response.source_silo_id == str(source_silo_id)
    assert response.destination_silo_id == str(destination_silo_id)
    assert response.transferred_batches[0].remaining_quantity_kg == 75
