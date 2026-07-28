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

from api.dependencies import get_current_user, get_feeding_rate_timeline_use_case
from application.dtos.auth_dtos import UserResponse
from application.dtos.feeding_rate_timeline_dtos import (
    FeedingRateTimelineDTO,
    RateTimelinePointDTO,
    RateTimelineSeriesDTO,
    RateTimelineSummaryDTO,
    TotalRateTimelinePointDTO,
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
        must_change_password=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_rate_timeline_is_routed_under_api_feeding_prefix(client):
    line_id = str(uuid4())
    cage_id = str(uuid4())
    start_at = datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc)
    end_at = datetime(2026, 5, 29, 0, 0, tzinfo=timezone.utc)
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(
        return_value=FeedingRateTimelineDTO(
            start_at=start_at,
            end_at=end_at,
            bucket_seconds=60,
            timezone="America/Santiago",
            summary=RateTimelineSummaryDTO(
                total_dispensed_kg=4.1,
                active_minutes=1,
                avg_active_rate_kg_per_min=4.1,
                peak_total_rate_kg_per_min=4.1,
                peak_total_rate_at=start_at,
                max_overlapping_sessions=1,
            ),
            total_series=[
                TotalRateTimelinePointDTO(
                    timestamp=start_at,
                    rate_kg_per_min=4.1,
                    active_sessions=1,
                )
            ],
            series=[
                RateTimelineSeriesDTO(
                    id=line_id,
                    name="Linea 1",
                    kind="LINE",
                    color_hint="#2563eb",
                    points=[
                        RateTimelinePointDTO(
                            timestamp=start_at,
                            rate_kg_per_min=4.1,
                            dispensed_kg=4.1,
                            active_sessions=1,
                        )
                    ],
                )
            ],
        )
    )
    app.dependency_overrides[get_feeding_rate_timeline_use_case] = lambda: mock_use_case

    response = client.get(
        "/api/feeding/stats/rate-timeline",
        params={
            "start_at": "2026-05-28T00:00:00Z",
            "end_at": "2026-05-29T00:00:00Z",
            "line_id": line_id,
            "cage_id": cage_id,
            "type": "MANUAL",
            "bucket_seconds": 60,
            "include_series": "lines",
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"] == {
        "total_dispensed_kg": 4.1,
        "active_minutes": 1,
        "avg_active_rate_kg_per_min": 4.1,
        "peak_total_rate_kg_per_min": 4.1,
        "peak_total_rate_at": "2026-05-28T00:00:00Z",
        "max_overlapping_sessions": 1,
    }
    assert response.json()["total_series"][0] == {
        "timestamp": "2026-05-28T00:00:00Z",
        "rate_kg_per_min": 4.1,
        "active_sessions": 1,
    }
    mock_use_case.execute.assert_awaited_once()
    call_kwargs = mock_use_case.execute.await_args.kwargs
    assert call_kwargs["start_at"] == start_at
    assert call_kwargs["end_at"] == end_at
    assert call_kwargs["line_id"] == line_id
    assert call_kwargs["cage_id"] == cage_id
    assert call_kwargs["feeding_type"] == "MANUAL"
    assert call_kwargs["bucket_seconds"] == 60
    assert call_kwargs["include_series"] == "lines"


def test_get_rate_timeline_rejects_invalid_include_series(client):
    response = client.get(
        "/api/feeding/stats/rate-timeline",
        params={
            "start_at": "2026-05-28T00:00:00Z",
            "end_at": "2026-05-29T00:00:00Z",
            "include_series": "foods",
        },
    )

    assert response.status_code == 422
