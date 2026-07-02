import os

import pytest
from fastapi import HTTPException

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")
os.environ.setdefault("DB_NAME", "test")

from api.routers.feeding_line_router import acquire_manual_control
from api.routers.feeding_router import start_cyclic_feeding, start_manual_feeding
from domain.exceptions import FeedingLineUnavailableException


class BusyUseCase:
    async def execute(self, *args, **kwargs):
        raise FeedingLineUnavailableException("linea ocupada")


class ManualControlRequest:
    reason = "test"


class FakeCurrentUser:
    id = "123e4567-e89b-12d3-a456-426614174000"
    full_name = "Test User"
    username = "testuser"


@pytest.mark.asyncio
async def test_manual_feeding_line_unavailable_maps_to_409():
    with pytest.raises(HTTPException) as exc_info:
        await start_manual_feeding(FakeCurrentUser(), object(), BusyUseCase())

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_cyclic_feeding_line_unavailable_maps_to_409():
    with pytest.raises(HTTPException) as exc_info:
        await start_cyclic_feeding(FakeCurrentUser(), object(), BusyUseCase())

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_acquire_manual_control_line_unavailable_maps_to_409():
    with pytest.raises(HTTPException) as exc_info:
        await acquire_manual_control(FakeCurrentUser(), "line-id", ManualControlRequest(), BusyUseCase())

    assert exc_info.value.status_code == 409
