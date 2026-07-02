import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")
os.environ.setdefault("DB_NAME", "feedsystemdb")

from api.dependencies import get_current_user, get_daily_feeding_summary_use_case
from application.dtos.auth_dtos import UserResponse
from application.dtos.feeding_history_dtos import DailyFeedingSummaryDTO, DailyFeedingSummaryPointDTO
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


def test_get_daily_summary_is_routed_under_api_feeding_prefix(client):
    line_id = str(uuid4())
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(
        return_value=DailyFeedingSummaryDTO(
            start_date="2026-05-01",
            end_date="2026-05-02",
            points=[
                DailyFeedingSummaryPointDTO(
                    date="2026-05-01",
                    total_dispensed_kg=120.5,
                    total_programmed_kg=130.0,
                    sessions_completed=4,
                    sessions_cancelled=0,
                    sessions_interrupted=1,
                ),
                DailyFeedingSummaryPointDTO(
                    date="2026-05-02",
                    total_dispensed_kg=0.0,
                    total_programmed_kg=0.0,
                    sessions_completed=0,
                    sessions_cancelled=0,
                    sessions_interrupted=0,
                ),
            ],
        )
    )
    app.dependency_overrides[get_daily_feeding_summary_use_case] = lambda: mock_use_case

    response = client.get(
        "/api/feeding/stats/daily-summary",
        params={
            "start_date": "2026-05-01",
            "end_date": "2026-05-02",
            "line_id": line_id,
            "type": "MANUAL",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "start_date": "2026-05-01",
        "end_date": "2026-05-02",
        "points": [
            {
                "date": "2026-05-01",
                "total_dispensed_kg": 120.5,
                "total_programmed_kg": 130.0,
                "sessions_completed": 4,
                "sessions_cancelled": 0,
                "sessions_interrupted": 1,
            },
            {
                "date": "2026-05-02",
                "total_dispensed_kg": 0.0,
                "total_programmed_kg": 0.0,
                "sessions_completed": 0,
                "sessions_cancelled": 0,
                "sessions_interrupted": 0,
            },
        ],
    }
    mock_use_case.execute.assert_awaited_once()
    call_kwargs = mock_use_case.execute.await_args.kwargs
    assert call_kwargs["start_date"].isoformat() == "2026-05-01"
    assert call_kwargs["end_date"].isoformat() == "2026-05-02"
    assert call_kwargs["line_id"] == line_id
    assert call_kwargs["feeding_type"] == "MANUAL"


def test_get_daily_summary_rejects_invalid_type(client):
    response = client.get(
        "/api/feeding/stats/daily-summary",
        params={
            "start_date": "2026-05-01",
            "end_date": "2026-05-02",
            "type": "SCHEDULED",
        },
    )

    assert response.status_code == 422
