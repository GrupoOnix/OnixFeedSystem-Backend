"""
Tests para el router de silos (silo_router).
"""

import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


class TestListSilos:
    def test_list_silos_returns_200(self, client):
        with patch("api.routers.silo_router.ListSilosUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "silos": [{"id": str(uuid4()), "name": "Silo 1", "capacity_kg": 10000.0,
                          "stock_level_kg": 5000.0, "is_assigned": False,
                          "created_at": datetime.now().isoformat(), "line_id": None,
                          "line_name": None, "food_id": None}],
            })
            response = client.get("/api/silos")
        assert response.status_code == 200
        assert "silos" in response.json()

    def test_list_silos_with_assigned_filter_true(self, client):
        with patch("api.routers.silo_router.ListSilosUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={"silos": []})
            response = client.get("/api/silos?is_assigned=true")
        assert response.status_code == 200


class TestGetSilo:
    def test_get_silo_by_id_returns_200(self, client):
        silo_id = str(uuid4())
        with patch("api.routers.silo_router.GetSiloUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": silo_id, "name": "Silo Test", "capacity_kg": 10000.0,
                "stock_level_kg": 5000.0, "is_assigned": False,
                "created_at": datetime.now().isoformat(), "line_id": None,
                "line_name": None, "food_id": None,
            })
            response = client.get(f"/api/silos/{silo_id}")
        assert response.status_code == 200
        assert response.json()["id"] == silo_id

    def test_get_silo_not_found_returns_404(self, client):
        silo_id = str(uuid4())
        with patch("api.routers.silo_router.GetSiloUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            from domain.exceptions import SiloNotFoundError
            mock_instance.execute = pytest.AsyncMock(side_effect=SiloNotFoundError("Silo not found"))
            response = client.get(f"/api/silos/{silo_id}")
        assert response.status_code == 404


class TestCreateSilo:
    def test_create_silo_with_valid_data_returns_201(self, client):
        request_data = {"name": f"Silo Test {uuid4().hex[:8]}", "capacity_kg": 10000.0, "stock_level_kg": 5000.0}
        with patch("api.routers.silo_router.CreateSiloUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": str(uuid4()), "name": request_data["name"], "capacity_kg": 10000.0,
                "stock_level_kg": 5000.0, "is_assigned": False,
                "created_at": datetime.now().isoformat(), "line_id": None, "line_name": None, "food_id": None,
            })
            response = client.post("/api/silos", json=request_data)
        assert response.status_code == 201
        assert response.json()["name"] == request_data["name"]

    def test_create_silo_without_name_returns_422(self, client):
        response = client.post("/api/silos", json={"capacity_kg": 10000.0})
        assert response.status_code == 422

    def test_create_silo_with_duplicate_name_returns_409(self, client):
        request_data = {"name": "Silo Existente", "capacity_kg": 10000.0}
        with patch("api.routers.silo_router.CreateSiloUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            from domain.exceptions import DuplicateSiloNameError
            mock_instance.execute = pytest.AsyncMock(side_effect=DuplicateSiloNameError("Silo name already exists"))
            response = client.post("/api/silos", json=request_data)
        assert response.status_code == 409


class TestUpdateSilo:
    def test_update_silo_name_returns_200(self, client):
        silo_id = str(uuid4())
        with patch("api.routers.silo_router.UpdateSiloUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": silo_id, "name": "Nuevo Nombre", "capacity_kg": 10000.0,
                "stock_level_kg": 5000.0, "is_assigned": False,
                "created_at": datetime.now().isoformat(), "line_id": None, "line_name": None, "food_id": None,
            })
            response = client.patch(f"/api/silos/{silo_id}", json={"name": "Nuevo Nombre"})
        assert response.status_code == 200
        assert response.json()["name"] == "Nuevo Nombre"

    def test_update_silo_not_found_returns_404(self, client):
        silo_id = str(uuid4())
        with patch("api.routers.silo_router.UpdateSiloUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            from domain.exceptions import SiloNotFoundError
            mock_instance.execute = pytest.AsyncMock(side_effect=SiloNotFoundError("Silo not found"))
            response = client.patch(f"/api/silos/{silo_id}", json={"name": "Nuevo"})
        assert response.status_code == 404


class TestDeleteSilo:
    def test_delete_silo_returns_204(self, client):
        silo_id = str(uuid4())
        with patch("api.routers.silo_router.DeleteSiloUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)
            response = client.delete(f"/api/silos/{silo_id}")
        assert response.status_code == 204

    def test_delete_silo_in_use_returns_409(self, client):
        silo_id = str(uuid4())
        with patch("api.routers.silo_router.DeleteSiloUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            from domain.exceptions import SiloInUseError
            mock_instance.execute = pytest.AsyncMock(side_effect=SiloInUseError("Silo is assigned"))
            response = client.delete(f"/api/silos/{silo_id}")
        assert response.status_code == 409
