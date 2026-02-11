"""
Tests para el router de silos (silo_router).
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.dependencies import (
    get_create_silo_use_case,
    get_delete_silo_use_case,
    get_get_silo_use_case,
    get_list_silos_use_case,
    get_update_silo_use_case,
)
from application.dtos.silo_dtos import ListSilosResponse, SiloDTO
from domain.exceptions import DuplicateSiloNameError, SiloInUseError, SiloNotFoundError
from main import app


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestListSilos:
    """Tests para GET /api/silos"""

    def test_list_silos_returns_200(self, client):
        """Lista de silos retorna 200 con datos válidos."""
        mock_use_case = MagicMock()
        silo_dto = SiloDTO(
            id=str(uuid4()),
            name="Silo 1",
            capacity_kg=10000.0,
            stock_level_kg=5000.0,
            is_assigned=False,
            created_at=datetime.now(),
            line_id=None,
            line_name=None,
            food_id=None,
        )
        mock_use_case.execute = AsyncMock(
            return_value=ListSilosResponse(silos=[silo_dto])
        )
        app.dependency_overrides[get_list_silos_use_case] = lambda: mock_use_case

        response = client.get("/api/silos")
        assert response.status_code == 200
        assert "silos" in response.json()

    def test_list_silos_with_assigned_filter_true(self, client):
        """Lista de silos con filtro is_assigned=true retorna 200."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=ListSilosResponse(silos=[])
        )
        app.dependency_overrides[get_list_silos_use_case] = lambda: mock_use_case

        response = client.get("/api/silos?is_assigned=true")
        assert response.status_code == 200


class TestGetSilo:
    """Tests para GET /api/silos/{silo_id}"""

    def test_get_silo_by_id_returns_200(self, client):
        """Obtener silo por ID retorna 200 con datos válidos."""
        silo_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=SiloDTO(
                id=silo_id,
                name="Silo Test",
                capacity_kg=10000.0,
                stock_level_kg=5000.0,
                is_assigned=False,
                created_at=datetime.now(),
                line_id=None,
                line_name=None,
                food_id=None,
            )
        )
        app.dependency_overrides[get_get_silo_use_case] = lambda: mock_use_case

        response = client.get(f"/api/silos/{silo_id}")
        assert response.status_code == 200
        assert response.json()["id"] == silo_id

    def test_get_silo_not_found_returns_404(self, client):
        """Obtener silo inexistente retorna 404."""
        silo_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=SiloNotFoundError("Silo not found")
        )
        app.dependency_overrides[get_get_silo_use_case] = lambda: mock_use_case

        response = client.get(f"/api/silos/{silo_id}")
        assert response.status_code == 404


class TestCreateSilo:
    """Tests para POST /api/silos"""

    def test_create_silo_with_valid_data_returns_201(self, client):
        """Crear silo con datos válidos retorna 201."""
        request_data = {
            "name": f"Silo Test {uuid4().hex[:8]}",
            "capacity_kg": 10000.0,
            "stock_level_kg": 5000.0,
        }
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=SiloDTO(
                id=str(uuid4()),
                name=request_data["name"],
                capacity_kg=10000.0,
                stock_level_kg=5000.0,
                is_assigned=False,
                created_at=datetime.now(),
                line_id=None,
                line_name=None,
                food_id=None,
            )
        )
        app.dependency_overrides[get_create_silo_use_case] = lambda: mock_use_case

        response = client.post("/api/silos", json=request_data)
        assert response.status_code == 201
        assert response.json()["name"] == request_data["name"]

    def test_create_silo_without_name_returns_422(self, client):
        """Crear silo sin nombre retorna 422 (validación)."""
        response = client.post("/api/silos", json={"capacity_kg": 10000.0})
        assert response.status_code == 422

    def test_create_silo_with_duplicate_name_returns_409(self, client):
        """Crear silo con nombre duplicado retorna 409."""
        request_data = {"name": "Silo Existente", "capacity_kg": 10000.0}
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=DuplicateSiloNameError("Silo name already exists")
        )
        app.dependency_overrides[get_create_silo_use_case] = lambda: mock_use_case

        response = client.post("/api/silos", json=request_data)
        assert response.status_code == 409


class TestUpdateSilo:
    """Tests para PATCH /api/silos/{silo_id}"""

    def test_update_silo_name_returns_200(self, client):
        """Actualizar nombre de silo retorna 200."""
        silo_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=SiloDTO(
                id=silo_id,
                name="Nuevo Nombre",
                capacity_kg=10000.0,
                stock_level_kg=5000.0,
                is_assigned=False,
                created_at=datetime.now(),
                line_id=None,
                line_name=None,
                food_id=None,
            )
        )
        app.dependency_overrides[get_update_silo_use_case] = lambda: mock_use_case

        response = client.patch(f"/api/silos/{silo_id}", json={"name": "Nuevo Nombre"})
        assert response.status_code == 200
        assert response.json()["name"] == "Nuevo Nombre"

    def test_update_silo_not_found_returns_404(self, client):
        """Actualizar silo inexistente retorna 404."""
        silo_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=SiloNotFoundError("Silo not found")
        )
        app.dependency_overrides[get_update_silo_use_case] = lambda: mock_use_case

        response = client.patch(f"/api/silos/{silo_id}", json={"name": "Nuevo"})
        assert response.status_code == 404


class TestDeleteSilo:
    """Tests para DELETE /api/silos/{silo_id}"""

    def test_delete_silo_returns_204(self, client):
        """Eliminar silo existente retorna 204."""
        silo_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_delete_silo_use_case] = lambda: mock_use_case

        response = client.delete(f"/api/silos/{silo_id}")
        assert response.status_code == 204

    def test_delete_silo_in_use_returns_409(self, client):
        """Eliminar silo en uso retorna 409."""
        silo_id = str(uuid4())
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            side_effect=SiloInUseError("Silo is assigned")
        )
        app.dependency_overrides[get_delete_silo_use_case] = lambda: mock_use_case

        response = client.delete(f"/api/silos/{silo_id}")
        assert response.status_code == 409
