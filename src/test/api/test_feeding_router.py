"""
Tests para el router de alimentación (feeding_router).
"""

import sys
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


class TestStartFeeding:
    def test_start_feeding_returns_201(self, client):
        request_data = {
            "line_id": str(uuid4()), "cage_id": str(uuid4()), "mode": "MANUAL",
            "target_amount_kg": 10.5, "blower_speed_percentage": 75.0, "dosing_rate_kg_min": 2.5,
        }
        with patch("api.routers.feeding_router.StartFeedingSessionUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=str(uuid4()))
            response = client.post("/api/feeding/start", json=request_data)
        assert response.status_code == 201
        assert "session_id" in response.json()

    def test_start_feeding_with_invalid_line_returns_404(self, client):
        request_data = {"line_id": str(uuid4()), "cage_id": str(uuid4()), "mode": "MANUAL", "target_amount_kg": 10.5}
        with patch("api.routers.feeding_router.StartFeedingSessionUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(side_effect=ValueError("Line not found"))
            response = client.post("/api/feeding/start", json=request_data)
        assert response.status_code == 404

    def test_start_feeding_missing_required_fields_returns_422(self, client):
        response = client.post("/api/feeding/start", json={"mode": "MANUAL"})
        assert response.status_code == 422


class TestStopFeeding:
    def test_stop_feeding_returns_200(self, client):
        line_id = str(uuid4())
        with patch("api.routers.feeding_router.StopFeedingSessionUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.post(f"/api/feeding/lines/{line_id}/stop")
        assert response.status_code == 200

    def test_stop_feeding_no_active_session_returns_404(self, client):
        line_id = str(uuid4())
        with patch("api.routers.feeding_router.StopFeedingSessionUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(side_effect=ValueError("No active session"))
            response = client.post(f"/api/feeding/lines/{line_id}/stop")
        assert response.status_code == 404


class TestPauseFeeding:
    def test_pause_feeding_returns_200(self, client):
        line_id = str(uuid4())
        with patch("api.routers.feeding_router.PauseFeedingSessionUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.post(f"/api/feeding/lines/{line_id}/pause")
        assert response.status_code == 200

    def test_pause_feeding_not_running_returns_400(self, client):
        line_id = str(uuid4())
        with patch("api.routers.feeding_router.PauseFeedingSessionUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            from domain.exceptions import DomainException
            mock_instance.execute = pytest.AsyncMock(side_effect=DomainException("Session not running"))
            response = client.post(f"/api/feeding/lines/{line_id}/pause")
        assert response.status_code == 400


class TestResumeFeeding:
    def test_resume_feeding_returns_200(self, client):
        line_id = str(uuid4())
        with patch("api.routers.feeding_router.ResumeFeedingSessionUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.post(f"/api/feeding/lines/{line_id}/resume")
        assert response.status_code == 200


class TestUpdateFeedingParameters:
    def test_update_blower_speed_returns_200(self, client):
        line_id = str(uuid4())
        with patch("api.routers.feeding_router.UpdateFeedingParametersUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.patch(f"/api/feeding/lines/{line_id}/parameters", json={"blower_speed": 80.0})
        assert response.status_code == 200

    def test_update_parameters_no_session_returns_404(self, client):
        line_id = str(uuid4())
        with patch("api.routers.feeding_router.UpdateFeedingParametersUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(side_effect=ValueError("No active session"))
            response = client.patch(f"/api/feeding/lines/{line_id}/parameters", json={"blower_speed": 80.0})
        assert response.status_code == 404
