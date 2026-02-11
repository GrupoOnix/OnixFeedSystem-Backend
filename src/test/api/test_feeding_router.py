"""
Tests para el router de alimentación (feeding_router).

Utiliza app.dependency_overrides de FastAPI para inyectar mocks
de los casos de uso, en lugar de patchear clases que no están
importadas a nivel de módulo en el router.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from api.dependencies import (
    get_start_feeding_use_case,
    get_stop_feeding_use_case,
    get_pause_feeding_use_case,
    get_resume_feeding_use_case,
    get_update_feeding_params_use_case,
)
from domain.exceptions import DomainException


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestStartFeeding:
    """Tests para el endpoint POST /api/feeding/start."""

    def test_start_feeding_returns_201(self, client):
        """Iniciar alimentación retorna 201 con session_id."""
        mock_use_case = MagicMock()
        session_id = str(uuid4())
        mock_use_case.execute = AsyncMock(return_value=session_id)
        app.dependency_overrides[get_start_feeding_use_case] = lambda: mock_use_case

        request_data = {
            "line_id": str(uuid4()),
            "cage_id": str(uuid4()),
            "mode": "Manual",
            "target_amount_kg": 10.5,
            "blower_speed_percentage": 75.0,
            "dosing_rate_kg_min": 2.5,
        }
        response = client.post("/api/feeding/start", json=request_data)

        assert response.status_code == 201
        assert "session_id" in response.json()
        assert response.json()["session_id"] == session_id

    def test_start_feeding_with_invalid_line_returns_404(self, client):
        """Iniciar alimentación con línea inválida retorna 404."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=ValueError("Line not found"))
        app.dependency_overrides[get_start_feeding_use_case] = lambda: mock_use_case

        request_data = {
            "line_id": str(uuid4()),
            "cage_id": str(uuid4()),
            "mode": "Manual",
            "target_amount_kg": 10.5,
            "blower_speed_percentage": 75.0,
            "dosing_rate_kg_min": 2.5,
        }
        response = client.post("/api/feeding/start", json=request_data)

        assert response.status_code == 404

    def test_start_feeding_missing_required_fields_returns_422(self, client):
        """Iniciar alimentación sin campos requeridos retorna 422."""
        response = client.post("/api/feeding/start", json={"mode": "Manual"})
        assert response.status_code == 422

    def test_start_feeding_domain_exception_returns_400(self, client):
        """Iniciar alimentación con excepción de dominio retorna 400."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=DomainException("Session already active")
        )
        app.dependency_overrides[get_start_feeding_use_case] = lambda: mock_use_case

        request_data = {
            "line_id": str(uuid4()),
            "cage_id": str(uuid4()),
            "mode": "Manual",
            "target_amount_kg": 10.5,
            "blower_speed_percentage": 75.0,
            "dosing_rate_kg_min": 2.5,
        }
        response = client.post("/api/feeding/start", json=request_data)

        assert response.status_code == 400


class TestStopFeeding:
    """Tests para el endpoint POST /api/feeding/lines/{line_id}/stop."""

    def test_stop_feeding_returns_200(self, client):
        """Detener alimentación retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_stop_feeding_use_case] = lambda: mock_use_case

        line_id = str(uuid4())
        response = client.post(f"/api/feeding/lines/{line_id}/stop")

        assert response.status_code == 200

    def test_stop_feeding_no_active_session_returns_404(self, client):
        """Detener alimentación sin sesión activa retorna 404."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=ValueError("No active session")
        )
        app.dependency_overrides[get_stop_feeding_use_case] = lambda: mock_use_case

        line_id = str(uuid4())
        response = client.post(f"/api/feeding/lines/{line_id}/stop")

        assert response.status_code == 404


class TestPauseFeeding:
    """Tests para el endpoint POST /api/feeding/lines/{line_id}/pause."""

    def test_pause_feeding_returns_200(self, client):
        """Pausar alimentación retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_pause_feeding_use_case] = lambda: mock_use_case

        line_id = str(uuid4())
        response = client.post(f"/api/feeding/lines/{line_id}/pause")

        assert response.status_code == 200

    def test_pause_feeding_not_running_returns_400(self, client):
        """Pausar alimentación cuando no está corriendo retorna 400."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=DomainException("Session not running")
        )
        app.dependency_overrides[get_pause_feeding_use_case] = lambda: mock_use_case

        line_id = str(uuid4())
        response = client.post(f"/api/feeding/lines/{line_id}/pause")

        assert response.status_code == 400


class TestResumeFeeding:
    """Tests para el endpoint POST /api/feeding/lines/{line_id}/resume."""

    def test_resume_feeding_returns_200(self, client):
        """Reanudar alimentación retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_resume_feeding_use_case] = lambda: mock_use_case

        line_id = str(uuid4())
        response = client.post(f"/api/feeding/lines/{line_id}/resume")

        assert response.status_code == 200


class TestUpdateFeedingParameters:
    """Tests para el endpoint PATCH /api/feeding/lines/{line_id}/parameters."""

    def test_update_blower_speed_returns_200(self, client):
        """Actualizar velocidad de soplador retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_update_feeding_params_use_case] = lambda: mock_use_case

        line_id = str(uuid4())
        response = client.patch(
            f"/api/feeding/lines/{line_id}/parameters",
            json={"line_id": line_id, "blower_speed": 80.0},
        )

        assert response.status_code == 200

    def test_update_parameters_no_session_returns_404(self, client):
        """Actualizar parámetros sin sesión activa retorna 404."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=ValueError("No active session")
        )
        app.dependency_overrides[get_update_feeding_params_use_case] = lambda: mock_use_case

        line_id = str(uuid4())
        response = client.patch(
            f"/api/feeding/lines/{line_id}/parameters",
            json={"line_id": line_id, "blower_speed": 80.0},
        )

        assert response.status_code == 404
