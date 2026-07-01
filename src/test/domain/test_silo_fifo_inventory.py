from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.aggregates.silo import Silo
from domain.entities.silo_inventory import (
    SiloInventoryBatch,
    SiloInventoryBatchStatus,
)
from domain.value_objects import SiloName, Weight


def _batch(position: int, remaining_kg: float, reserved_kg: float = 0) -> SiloInventoryBatch:
    now = datetime.now(timezone.utc)
    return SiloInventoryBatch(
        id=uuid4(),
        silo_id=uuid4(),
        food_id=uuid4(),
        remaining_quantity_mg=round(remaining_kg * 1_000_000),
        reserved_quantity_mg=round(reserved_kg * 1_000_000),
        position=position,
        status=SiloInventoryBatchStatus.ACTIVE,
        received_at=now,
        created_by_operator_id=str(uuid4()),
        created_at=now,
        updated_at=now,
    )


def test_silo_stock_is_derived_from_loaded_inventory():
    silo = Silo(SiloName("Silo FIFO"), Weight.from_kg(1000))
    batches = [_batch(1, 300, 40), _batch(2, 200, 10)]

    silo.load_inventory(
        total_stock=Weight.from_kg(500),
        reserved_stock=Weight.from_kg(50),
        active_batches=batches,
    )

    assert silo.total_stock.as_kg == 500
    assert silo.reserved_stock.as_kg == 50
    assert silo.available_stock.as_kg == 450
    assert silo.fill_percentage == 50
    assert [batch.position for batch in silo.active_batches] == [1, 2]


def test_capacity_cannot_be_reduced_below_derived_stock():
    silo = Silo(SiloName("Silo FIFO"), Weight.from_kg(1000))
    silo.load_inventory(Weight.from_kg(500), Weight.zero(), [])

    with pytest.raises(ValueError, match="menor al stock actual"):
        silo.capacity = Weight.from_kg(499)
