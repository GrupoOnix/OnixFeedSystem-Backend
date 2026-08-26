from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from domain.entities.silo_inventory import SiloInventoryMovementType
from infrastructure.persistence.repositories.silo_inventory_repository import SiloInventoryRepository


def _repository_for_create(*, batches, result):
    session = MagicMock()
    session.flush = AsyncMock()
    repository = SiloInventoryRepository(session)
    repository._lock_silo = AsyncMock(return_value=SimpleNamespace(capacity_mg=1_000_000_000))
    repository._require_active_food = AsyncMock()
    repository.get_summary = AsyncMock(return_value=SimpleNamespace(total_stock_mg=100_000_000))
    repository._active_models = AsyncMock(return_value=batches)
    repository._add_movement = MagicMock()
    repository.get_batch = AsyncMock(return_value=result)
    return repository, session


@pytest.mark.asyncio
async def test_create_batch_consolidates_only_with_the_top_batch_of_the_same_food():
    silo_id = uuid4()
    food_id = uuid4()
    top_batch = SimpleNamespace(
        id=uuid4(),
        food_id=food_id,
        remaining_quantity_mg=150_000_000,
        position=2,
        updated_at=None,
    )
    result = MagicMock()
    repository, session = _repository_for_create(batches=[MagicMock(), top_batch], result=result)

    created = await repository.create_batch(silo_id, food_id, 50, "operator-1")

    assert created is result
    assert top_batch.remaining_quantity_mg == 200_000_000
    session.add.assert_not_called()
    repository._add_movement.assert_called_once_with(
        top_batch,
        SiloInventoryMovementType.INITIAL_LOAD,
        "operator-1",
        previous_quantity_mg=150_000_000,
        new_quantity_mg=200_000_000,
        previous_food_id=food_id,
        new_food_id=food_id,
        previous_position=2,
        new_position=2,
    )


@pytest.mark.asyncio
async def test_create_batch_keeps_separated_foods_as_distinct_batches():
    silo_id = uuid4()
    existing_food_id = uuid4()
    loaded_food_id = uuid4()
    top_batch = SimpleNamespace(
        id=uuid4(),
        food_id=existing_food_id,
        remaining_quantity_mg=100_000_000,
        position=2,
        updated_at=None,
    )
    result = MagicMock()
    repository, session = _repository_for_create(batches=[MagicMock(), top_batch], result=result)

    await repository.create_batch(silo_id, loaded_food_id, 50, "operator-1")

    model = session.add.call_args.args[0]
    assert model.food_id == loaded_food_id
    assert model.remaining_quantity_mg == 50_000_000
    assert model.position == 3
