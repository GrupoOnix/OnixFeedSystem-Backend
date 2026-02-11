"""
Tests para el router de alertas (alerts_router).
Usa app.dependency_overrides para inyectar mocks de los casos de uso,
en vez de patchear nombres que no existen a nivel de módulo del router.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from api.dependencies import (
    get_list_alerts_use_case,
    get_unread_count_use_case,
    get_alert_counts_use_case,
    get_mark_alert_read_use_case,
    get_mark_all_alerts_read_use_case,
    get_snooze_alert_use_case,
    get_unsnooze_alert_use_case,
    get_list_snoozed_alerts_use_case,
    get_list_scheduled_alerts_use_case,
    get_create_scheduled_alert_use_case,
    get_delete_scheduled_alert_use_case,
)
from application.dtos.alert_dtos import (
    AlertCountsResponse,
    AlertDTO,
    ListAlertsResponse,
    ListScheduledAlertsResponse,
    MarkAllReadResponse,
    ScheduledAlertDTO,
    UnreadCountResponse,
)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_alert_dto(**overrides) -> AlertDTO:
    """Helper para crear un AlertDTO con valores por defecto."""
    defaults = {
        "id": str(uuid4()),
        "type": "WARNING",
        "status": "UNREAD",
        "category": "SYSTEM",
        "title": "Alerta",
        "message": "Test",
        "source": "test",
        "timestamp": datetime.now(),
        "read_at": None,
        "resolved_at": None,
        "resolved_by": None,
        "snoozed_until": None,
        "metadata": {},
    }
    defaults.update(overrides)
    return AlertDTO(**defaults)


def _make_scheduled_alert_dto(**overrides) -> ScheduledAlertDTO:
    """Helper para crear un ScheduledAlertDTO con valores por defecto."""
    defaults = {
        "id": str(uuid4()),
        "title": "Mantenimiento",
        "message": "Revisar",
        "type": "WARNING",
        "category": "MAINTENANCE",
        "frequency": "MONTHLY",
        "next_trigger_date": datetime.now() + timedelta(days=30),
        "days_before_warning": 0,
        "is_active": True,
        "device_id": None,
        "device_name": None,
        "custom_days_interval": None,
        "metadata": {},
        "created_at": datetime.now(),
        "last_triggered_at": None,
    }
    defaults.update(overrides)
    return ScheduledAlertDTO(**defaults)


class TestListAlerts:
    """Tests para el endpoint GET /api/alerts."""

    def test_list_alerts_returns_200(self, client):
        """Verifica que listar alertas retorna 200 con la estructura correcta."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=ListAlertsResponse(
                alerts=[_make_alert_dto()],
                total=1,
            )
        )
        app.dependency_overrides[get_list_alerts_use_case] = lambda: mock_use_case

        response = client.get("/api/alerts")
        assert response.status_code == 200
        assert "alerts" in response.json()

    def test_list_alerts_with_filters(self, client):
        """Verifica que listar alertas con filtros funciona correctamente."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=ListAlertsResponse(alerts=[], total=0)
        )
        app.dependency_overrides[get_list_alerts_use_case] = lambda: mock_use_case

        response = client.get("/api/alerts?status=UNREAD,READ&type=CRITICAL")
        assert response.status_code == 200

    def test_list_alerts_with_invalid_limit_returns_422(self, client):
        """Verifica que un límite inválido retorna 422 (validación de FastAPI)."""
        response = client.get("/api/alerts?limit=200")
        assert response.status_code == 422


class TestGetUnreadCount:
    """Tests para el endpoint GET /api/alerts/unread/count."""

    def test_get_unread_count_returns_200(self, client):
        """Verifica que obtener el contador de no leídas retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=UnreadCountResponse(count=5)
        )
        app.dependency_overrides[get_unread_count_use_case] = lambda: mock_use_case

        response = client.get("/api/alerts/unread/count")
        assert response.status_code == 200
        assert response.json()["count"] == 5


class TestGetAlertCounts:
    """Tests para el endpoint GET /api/alerts/counts."""

    def test_get_alert_counts_returns_200(self, client):
        """Verifica que obtener contadores por tipo retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=AlertCountsResponse(
                critical=2, warning=5, info=10, success=0
            )
        )
        app.dependency_overrides[get_alert_counts_use_case] = lambda: mock_use_case

        response = client.get("/api/alerts/counts")
        assert response.status_code == 200
        assert response.json()["critical"] == 2


class TestMarkAlertRead:
    """Tests para el endpoint POST /api/alerts/{alert_id}/read."""

    def test_mark_alert_read_returns_200(self, client):
        """Verifica que marcar una alerta como leída retorna 200."""
        alert_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_mark_alert_read_use_case] = lambda: mock_use_case

        response = client.post(f"/api/alerts/{alert_id}/read")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_mark_alert_read_not_found_returns_404(self, client):
        """Verifica que marcar una alerta inexistente retorna 404."""
        alert_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=ValueError("Alert not found"))
        app.dependency_overrides[get_mark_alert_read_use_case] = lambda: mock_use_case

        response = client.post(f"/api/alerts/{alert_id}/read")
        assert response.status_code == 404


class TestMarkAllAlertsRead:
    """Tests para el endpoint PATCH /api/alerts/read-all."""

    def test_mark_all_alerts_read_returns_200(self, client):
        """Verifica que marcar todas las alertas como leídas retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=MarkAllReadResponse(count=10, message="10 alertas marcadas como leídas")
        )
        app.dependency_overrides[get_mark_all_alerts_read_use_case] = lambda: mock_use_case

        response = client.patch("/api/alerts/read-all")
        assert response.status_code == 200
        assert response.json()["count"] == 10


class TestSnoozeAlert:
    """Tests para el endpoint POST /api/alerts/{alert_id}/snooze."""

    def test_snooze_alert_for_1_day_returns_200(self, client):
        """Verifica que silenciar una alerta por 1 día retorna 200."""
        alert_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_snooze_alert_use_case] = lambda: mock_use_case

        response = client.post(f"/api/alerts/{alert_id}/snooze", json={"duration_days": 1})
        assert response.status_code == 200
        assert response.json()["duration_days"] == 1


class TestUnsnoozeAlert:
    """Tests para el endpoint DELETE /api/alerts/{alert_id}/snooze."""

    def test_unsnooze_alert_returns_200(self, client):
        """Verifica que reactivar una alerta silenciada retorna 200."""
        alert_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_unsnooze_alert_use_case] = lambda: mock_use_case

        response = client.delete(f"/api/alerts/{alert_id}/snooze")
        assert response.status_code == 200
        assert "alert_id" in response.json()


class TestListSnoozedAlerts:
    """Tests para el endpoint GET /api/alerts/snoozed."""

    def test_list_snoozed_alerts_returns_200(self, client):
        """Verifica que listar alertas silenciadas retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=ListAlertsResponse(alerts=[], total=0)
        )
        app.dependency_overrides[get_list_snoozed_alerts_use_case] = lambda: mock_use_case

        response = client.get("/api/alerts/snoozed")
        assert response.status_code == 200


class TestListScheduledAlerts:
    """Tests para el endpoint GET /api/alerts/scheduled."""

    def test_list_scheduled_alerts_returns_200(self, client):
        """Verifica que listar alertas programadas retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=ListScheduledAlertsResponse(
                scheduled_alerts=[_make_scheduled_alert_dto()]
            )
        )
        app.dependency_overrides[get_list_scheduled_alerts_use_case] = lambda: mock_use_case

        response = client.get("/api/alerts/scheduled")
        assert response.status_code == 200


class TestCreateScheduledAlert:
    """Tests para el endpoint POST /api/alerts/scheduled."""

    def test_create_scheduled_alert_returns_201(self, client):
        """Verifica que crear una alerta programada retorna 201."""
        request_data = {
            "title": "Mantenimiento",
            "message": "Revisar",
            "type": "WARNING",
            "category": "MAINTENANCE",
            "frequency": "MONTHLY",
            "next_trigger_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
        }
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=_make_scheduled_alert_dto(title="Mantenimiento")
        )
        app.dependency_overrides[get_create_scheduled_alert_use_case] = lambda: mock_use_case

        response = client.post("/api/alerts/scheduled", json=request_data)
        assert response.status_code == 201
        assert response.json()["title"] == "Mantenimiento"


class TestDeleteScheduledAlert:
    """Tests para el endpoint DELETE /api/alerts/scheduled/{alert_id}."""

    def test_delete_scheduled_alert_returns_204(self, client):
        """Verifica que eliminar una alerta programada retorna 204."""
        alert_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_delete_scheduled_alert_use_case] = lambda: mock_use_case

        response = client.delete(f"/api/alerts/scheduled/{alert_id}")
        assert response.status_code == 204

    def test_delete_scheduled_alert_not_found_returns_404(self, client):
        """Verifica que eliminar una alerta programada inexistente retorna 404."""
        alert_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=ValueError("Not found"))
        app.dependency_overrides[get_delete_scheduled_alert_use_case] = lambda: mock_use_case

        response = client.delete(f"/api/alerts/scheduled/{alert_id}")
        assert response.status_code == 404
