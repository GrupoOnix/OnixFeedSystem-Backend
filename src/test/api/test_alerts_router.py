"""
Tests para el router de alertas (alerts_router).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


class TestListAlerts:
    def test_list_alerts_returns_200(self, client):
        with patch("api.routers.alerts_router.ListAlertsUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "alerts": [{"id": str(uuid4()), "title": "Alerta", "message": "Test", "type": "WARNING",
                           "category": "SYSTEM", "status": "UNREAD", "source": "test",
                           "created_at": datetime.now().isoformat(), "snoozed_until": None}],
                "total": 1, "limit": 50, "offset": 0,
            })
            response = client.get("/api/alerts")
        assert response.status_code == 200
        assert "alerts" in response.json()

    def test_list_alerts_with_filters(self, client):
        with patch("api.routers.alerts_router.ListAlertsUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={"alerts": [], "total": 0, "limit": 50, "offset": 0})
            response = client.get("/api/alerts?status=UNREAD,READ&type=CRITICAL")
        assert response.status_code == 200

    def test_list_alerts_with_invalid_limit_returns_422(self, client):
        response = client.get("/api/alerts?limit=200")
        assert response.status_code == 422


class TestGetUnreadCount:
    def test_get_unread_count_returns_200(self, client):
        with patch("api.routers.alerts_router.GetUnreadCountUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={"count": 5})
            response = client.get("/api/alerts/unread/count")
        assert response.status_code == 200
        assert response.json()["count"] == 5


class TestGetAlertCounts:
    def test_get_alert_counts_returns_200(self, client):
        with patch("api.routers.alerts_router.GetAlertCountsUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={"CRITICAL": 2, "WARNING": 5, "INFO": 10})
            response = client.get("/api/alerts/counts")
        assert response.status_code == 200
        assert response.json()["CRITICAL"] == 2


class TestMarkAlertRead:
    def test_mark_alert_read_returns_200(self, client):
        alert_id = str(uuid4())
        with patch("api.routers.alerts_router.MarkAlertReadUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.post(f"/api/alerts/{alert_id}/read")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_mark_alert_read_not_found_returns_404(self, client):
        alert_id = str(uuid4())
        with patch("api.routers.alerts_router.MarkAlertReadUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(side_effect=ValueError("Alert not found"))
            response = client.post(f"/api/alerts/{alert_id}/read")
        assert response.status_code == 404


class TestMarkAllAlertsRead:
    def test_mark_all_alerts_read_returns_200(self, client):
        with patch("api.routers.alerts_router.MarkAllAlertsReadUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={"marked_as_read": 10})
            response = client.patch("/api/alerts/read-all")
        assert response.status_code == 200
        assert response.json()["marked_as_read"] == 10


class TestSnoozeAlert:
    def test_snooze_alert_for_1_day_returns_200(self, client):
        alert_id = str(uuid4())
        with patch("api.routers.alerts_router.SnoozeAlertUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.post(f"/api/alerts/{alert_id}/snooze", json={"duration_days": 1})
        assert response.status_code == 200
        assert response.json()["duration_days"] == 1


class TestUnsnoozeAlert:
    def test_unsnooze_alert_returns_200(self, client):
        alert_id = str(uuid4())
        with patch("api.routers.alerts_router.UnsnoozeAlertUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.delete(f"/api/alerts/{alert_id}/snooze")
        assert response.status_code == 200
        assert "alert_id" in response.json()


class TestListSnoozedAlerts:
    def test_list_snoozed_alerts_returns_200(self, client):
        with patch("api.routers.alerts_router.ListSnoozedAlertsUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "alerts": [], "total": 0, "limit": 50, "offset": 0,
            })
            response = client.get("/api/alerts/snoozed")
        assert response.status_code == 200


class TestListScheduledAlerts:
    def test_list_scheduled_alerts_returns_200(self, client):
        with patch("api.routers.alerts_router.ListScheduledAlertsUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "scheduled_alerts": [{"id": str(uuid4()), "title": "Mantenimiento", "is_active": True}],
            })
            response = client.get("/api/alerts/scheduled")
        assert response.status_code == 200


class TestCreateScheduledAlert:
    def test_create_scheduled_alert_returns_201(self, client):
        request_data = {
            "title": "Mantenimiento", "message": "Revisar", "type": "WARNING",
            "category": "MAINTENANCE", "frequency": "MONTHLY",
            "next_trigger_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
        }
        with patch("api.routers.alerts_router.CreateScheduledAlertUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": str(uuid4()), "title": "Mantenimiento", "is_active": True,
            })
            response = client.post("/api/alerts/scheduled", json=request_data)
        assert response.status_code == 201
        assert response.json()["title"] == "Mantenimiento"


class TestDeleteScheduledAlert:
    def test_delete_scheduled_alert_returns_204(self, client):
        alert_id = str(uuid4())
        with patch("api.routers.alerts_router.DeleteScheduledAlertUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.delete(f"/api/alerts/scheduled/{alert_id}")
        assert response.status_code == 204

    def test_delete_scheduled_alert_not_found_returns_404(self, client):
        alert_id = str(uuid4())
        with patch("api.routers.alerts_router.DeleteScheduledAlertUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(side_effect=ValueError("Not found"))
            response = client.delete(f"/api/alerts/scheduled/{alert_id}")
        assert response.status_code == 404
