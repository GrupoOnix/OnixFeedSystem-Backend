from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.dependencies import (
    get_create_silo_batch_use_case,
    get_current_user,
    get_list_silo_batches_use_case,
    get_move_silo_batch_use_case,
    get_transfer_silo_stock_use_case,
    get_update_silo_batch_use_case,
    get_withdraw_silo_batch_use_case,
)
from application.dtos.auth_dtos import UserResponse
from application.dtos.silo_dtos import SiloBatchFoodDTO, SiloInventoryBatchDTO
from application.dtos.silo_inventory_dtos import (
    ListSiloBatchesResponse,
    TransferSiloStockResponse,
)
from main import app


@pytest.fixture
def client():
    fake_user = UserResponse(
        id=str(uuid4()),
        username="testuser",
        full_name="Test User",
        role="user",
        is_superadmin=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


def _batch_dto(status: str = "ACTIVE") -> SiloInventoryBatchDTO:
    now = datetime.now(timezone.utc)
    return SiloInventoryBatchDTO(
        id=str(uuid4()),
        food=SiloBatchFoodDTO(
            id=str(uuid4()),
            name="Alimento A",
            code="A-01",
            provider="Proveedor",
        ),
        remaining_quantity_kg=100,
        reserved_quantity_kg=20,
        available_quantity_kg=80,
        position=1,
        status=status,
        received_at=now,
        created_by_operator_id=str(uuid4()),
        created_at=now,
        updated_at=now,
    )


def test_create_batch_returns_201(client):
    use_case = MagicMock()
    use_case.execute = AsyncMock(return_value=_batch_dto())
    app.dependency_overrides[get_create_silo_batch_use_case] = lambda: use_case

    response = client.post(
        f"/api/silos/{uuid4()}/batches",
        json={
            "food_id": str(uuid4()),
            "quantity_kg": 100,
            "operator_id": str(uuid4()),
        },
    )

    assert response.status_code == 201
    assert response.json()["position"] == 1


def test_list_batch_history_is_paginated(client):
    use_case = MagicMock()
    use_case.execute = AsyncMock(
        return_value=ListSiloBatchesResponse(
            batches=[_batch_dto("DEPLETED")],
            offset=0,
            limit=20,
        )
    )
    app.dependency_overrides[get_list_silo_batches_use_case] = lambda: use_case

    response = client.get(f"/api/silos/{uuid4()}/batches?status=DEPLETED&limit=20")

    assert response.status_code == 200
    assert response.json()["batches"][0]["status"] == "DEPLETED"


@pytest.mark.parametrize(
    ("dependency", "suffix", "payload"),
    [
        (
            get_update_silo_batch_use_case,
            "",
            {"remaining_quantity_kg": 90, "operator_id": str(uuid4())},
        ),
        (
            get_move_silo_batch_use_case,
            "/move",
            {"after_batch_id": str(uuid4()), "operator_id": str(uuid4())},
        ),
        (
            get_withdraw_silo_batch_use_case,
            "/withdraw",
            {"operator_id": str(uuid4())},
        ),
    ],
)
def test_batch_mutations_return_updated_batch(client, dependency, suffix, payload):
    use_case = MagicMock()
    use_case.execute = AsyncMock(return_value=_batch_dto())
    app.dependency_overrides[dependency] = lambda: use_case
    method = client.patch if not suffix else client.post

    response = method(f"/api/silos/{uuid4()}/batches/{uuid4()}{suffix}", json=payload)

    assert response.status_code == 200


def test_transfer_silo_stock_returns_transferred_batches(client):
    source_silo_id = str(uuid4())
    destination_silo_id = str(uuid4())
    transferred_batch = _batch_dto()
    use_case = MagicMock()
    use_case.execute = AsyncMock(
        return_value=TransferSiloStockResponse(
            source_silo_id=source_silo_id,
            destination_silo_id=destination_silo_id,
            quantity_kg=100,
            transferred_batches=[transferred_batch],
        )
    )
    app.dependency_overrides[get_transfer_silo_stock_use_case] = lambda: use_case

    response = client.post(
        f"/api/silos/{source_silo_id}/transfer",
        json={
            "destination_silo_id": destination_silo_id,
            "quantity_kg": 100,
            "operator_id": str(uuid4()),
            "reason": "Balanceo de inventario",
        },
    )

    assert response.status_code == 200
    assert response.json()["source_silo_id"] == source_silo_id
    assert response.json()["destination_silo_id"] == destination_silo_id
    assert response.json()["quantity_kg"] == 100
    assert len(response.json()["transferred_batches"]) == 1
