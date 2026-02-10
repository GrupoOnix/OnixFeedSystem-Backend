"""
Tests para el router de jaulas (cage_router).

Estos tests verifican:
- CRUD de jaulas
- Endpoints de población (siembra, mortalidad, biometría)
- Validaciones de request
- Manejo de errores
"""

import sys
from pathlib import Path
from datetime import date
from unittest.mock import patch
from uuid import uuid4

import pytest

# Configurar path antes de cualquier import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def client():
    """Fixture que proporciona el TestClient."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


class TestCreateCage:
    """Tests para POST /api/cages"""

    def test_create_cage_with_valid_data_returns_201(self, client):
        """Test: Crear jaula con datos válidos retorna 201."""
        request_data = {
            "name": f"Jaula Test {uuid4().hex[:8]}",
            "fcr": 1.5,
            "volume_m3": 1000.0,
            "max_density_kg_m3": 50.0,
            "transport_time_seconds": 30,
            "blower_power": 75,
        }

        with patch("api.routers.cage_router.CreateCageUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": str(uuid4()),
                "name": request_data["name"],
                "status": "AVAILABLE",
                "created_at": "2024-01-15T10:00:00",
                "fish_count": 0,
                "avg_weight_grams": None,
                "biomass_kg": 0.0,
                "config": {
                    "fcr": 1.5,
                    "volume_m3": 1000.0,
                    "max_density_kg_m3": 50.0,
                    "transport_time_seconds": 30,
                    "blower_power": 75,
                },
                "current_density_kg_m3": None,
            })

            response = client.post("/api/cages", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == request_data["name"]
        assert data["status"] == "AVAILABLE"

    def test_create_cage_without_name_returns_422(self, client):
        """Test: Crear jaula sin nombre retorna 422 (validation error)."""
        request_data = {
            "fcr": 1.5,
        }

        response = client.post("/api/cages", json=request_data)

        assert response.status_code == 422
        assert "name" in str(response.json()).lower() or "field required" in str(response.json()).lower()

    def test_create_cage_with_invalid_fcr_returns_422(self, client):
        """Test: Crear jaula con FCR fuera de rango retorna 422."""
        request_data = {
            "name": "Jaula Test",
            "fcr": 5.0,  # Debe ser <= 3.0
        }

        response = client.post("/api/cages", json=request_data)

        assert response.status_code == 422
        assert "fcr" in str(response.json()).lower()

    def test_create_cage_with_invalid_blower_power_returns_422(self, client):
        """Test: Crear jaula con blower_power fuera de rango retorna 422."""
        request_data = {
            "name": "Jaula Test",
            "blower_power": 150,  # Debe ser <= 100
        }

        response = client.post("/api/cages", json=request_data)

        assert response.status_code == 422

    def test_create_cage_with_negative_volume_returns_422(self, client):
        """Test: Crear jaula con volumen negativo retorna 422."""
        request_data = {
            "name": "Jaula Test",
            "volume_m3": -100.0,
        }

        response = client.post("/api/cages", json=request_data)

        assert response.status_code == 422


class TestListCages:
    """Tests para GET /api/cages"""

    def test_list_cages_returns_200(self, client):
        """Test: Listar jaulas retorna 200."""
        with patch("api.routers.cage_router.ListCagesUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "cages": [
                    {
                        "id": str(uuid4()),
                        "name": "Jaula 1",
                        "status": "AVAILABLE",
                        "fish_count": 1000,
                        "avg_weight_grams": 150.0,
                        "biomass_kg": 150.0,
                        "created_at": "2024-01-15T10:00:00",
                    }
                ],
                "total": 1,
            })

            response = client.get("/api/cages")

        assert response.status_code == 200
        data = response.json()
        assert "cages" in data
        assert "total" in data

    def test_list_cages_returns_empty_list_when_no_cages(self, client):
        """Test: Listar jaulas retorna lista vacía cuando no hay jaulas."""
        with patch("api.routers.cage_router.ListCagesUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "cages": [],
                "total": 0,
            })

            response = client.get("/api/cages")

        assert response.status_code == 200
        data = response.json()
        assert data["cages"] == []
        assert data["total"] == 0


class TestGetCage:
    """Tests para GET /api/cages/{cage_id}"""

    def test_get_cage_by_id_returns_200(self, client):
        """Test: Obtener jaula por ID retorna 200."""
        cage_id = str(uuid4())
        
        with patch("api.routers.cage_router.GetCageUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": cage_id,
                "name": "Jaula 1",
                "status": "AVAILABLE",
                "created_at": "2024-01-15T10:00:00",
                "fish_count": 1000,
                "avg_weight_grams": 150.0,
                "biomass_kg": 150.0,
                "config": {
                    "fcr": 1.5,
                    "volume_m3": 1000.0,
                    "max_density_kg_m3": 50.0,
                    "transport_time_seconds": 30,
                    "blower_power": 75,
                },
                "current_density_kg_m3": 0.15,
            })

            response = client.get(f"/api/cages/{cage_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cage_id

    def test_get_cage_not_found_returns_404(self, client):
        """Test: Obtener jaula inexistente retorna 404."""
        cage_id = str(uuid4())
        
        with patch("api.routers.cage_router.GetCageUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(side_effect=ValueError("Cage not found"))

            response = client.get(f"/api/cages/{cage_id}")

        assert response.status_code == 404

    def test_get_cage_with_invalid_uuid_returns_404(self, client):
        """Test: Obtener jaula con UUID inválido retorna 404 o 400."""
        response = client.get("/api/cages/invalid-uuid")
        
        assert response.status_code in [404, 400]


class TestUpdateCage:
    """Tests para PATCH /api/cages/{cage_id}"""

    def test_update_cage_name_returns_200(self, client):
        """Test: Actualizar nombre de jaula retorna 200."""
        cage_id = str(uuid4())
        request_data = {"name": "Nuevo Nombre"}
        
        with patch("api.routers.cage_router.UpdateCageUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": cage_id,
                "name": "Nuevo Nombre",
                "status": "AVAILABLE",
                "created_at": "2024-01-15T10:00:00",
                "fish_count": 0,
                "avg_weight_grams": None,
                "biomass_kg": 0.0,
                "config": {
                    "fcr": None,
                    "volume_m3": None,
                    "max_density_kg_m3": None,
                    "transport_time_seconds": None,
                    "blower_power": None,
                },
                "current_density_kg_m3": None,
            })

            response = client.patch(f"/api/cages/{cage_id}", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nuevo Nombre"

    def test_update_cage_status_returns_200(self, client):
        """Test: Actualizar status de jaula retorna 200."""
        cage_id = str(uuid4())
        request_data = {"status": "MAINTENANCE"}
        
        with patch("api.routers.cage_router.UpdateCageUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": cage_id,
                "name": "Jaula 1",
                "status": "MAINTENANCE",
                "created_at": "2024-01-15T10:00:00",
                "fish_count": 0,
                "avg_weight_grams": None,
                "biomass_kg": 0.0,
                "config": {
                    "fcr": None,
                    "volume_m3": None,
                    "max_density_kg_m3": None,
                    "transport_time_seconds": None,
                    "blower_power": None,
                },
                "current_density_kg_m3": None,
            })

            response = client.patch(f"/api/cages/{cage_id}", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "MAINTENANCE"


class TestDeleteCage:
    """Tests para DELETE /api/cages/{cage_id}"""

    def test_delete_cage_returns_204(self, client):
        """Test: Eliminar jaula retorna 204."""
        cage_id = str(uuid4())
        
        with patch("api.routers.cage_router.DeleteCageUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value=None)

            response = client.delete(f"/api/cages/{cage_id}")

        assert response.status_code == 204

    def test_delete_cage_not_found_returns_404(self, client):
        """Test: Eliminar jaula inexistente retorna 404."""
        cage_id = str(uuid4())
        
        with patch("api.routers.cage_router.DeleteCageUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(side_effect=ValueError("Cage not found"))

            response = client.delete(f"/api/cages/{cage_id}")

        assert response.status_code == 404


class TestSetPopulation:
    """Tests para PUT /api/cages/{cage_id}/population"""

    def test_set_population_returns_200(self, client):
        """Test: Establecer población retorna 200."""
        cage_id = str(uuid4())
        request_data = {
            "fish_count": 1000,
            "avg_weight_grams": 150.5,
            "event_date": date.today().isoformat(),
            "note": "Siembra inicial",
        }
        
        with patch("api.routers.cage_router.SetPopulationUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": cage_id,
                "name": "Jaula 1",
                "status": "IN_USE",
                "created_at": "2024-01-15T10:00:00",
                "fish_count": 1000,
                "avg_weight_grams": 150.5,
                "biomass_kg": 150.5,
                "config": {
                    "fcr": 1.5,
                    "volume_m3": 1000.0,
                    "max_density_kg_m3": 50.0,
                    "transport_time_seconds": 30,
                    "blower_power": 75,
                },
                "current_density_kg_m3": 0.15,
            })

            response = client.put(f"/api/cages/{cage_id}/population", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["fish_count"] == 1000
        assert data["avg_weight_grams"] == 150.5

    def test_set_population_with_zero_fish_returns_422(self, client):
        """Test: Establecer población con 0 peces retorna 422."""
        cage_id = str(uuid4())
        request_data = {
            "fish_count": 0,  # Debe ser > 0
            "avg_weight_grams": 150.5,
            "event_date": date.today().isoformat(),
        }

        response = client.put(f"/api/cages/{cage_id}/population", json=request_data)

        assert response.status_code == 422


class TestRegisterMortality:
    """Tests para POST /api/cages/{cage_id}/mortality"""

    def test_register_mortality_returns_200(self, client):
        """Test: Registrar mortalidad retorna 200."""
        cage_id = str(uuid4())
        request_data = {
            "dead_count": 10,
            "event_date": date.today().isoformat(),
            "note": "Mortalidad por estrés",
        }
        
        with patch("api.routers.cage_router.RegisterMortalityUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": cage_id,
                "name": "Jaula 1",
                "status": "IN_USE",
                "created_at": "2024-01-15T10:00:00",
                "fish_count": 990,  # 1000 - 10
                "avg_weight_grams": 150.5,
                "biomass_kg": 148.995,
                "config": {
                    "fcr": 1.5,
                    "volume_m3": 1000.0,
                    "max_density_kg_m3": 50.0,
                    "transport_time_seconds": 30,
                    "blower_power": 75,
                },
                "current_density_kg_m3": 0.15,
            })

            response = client.post(f"/api/cages/{cage_id}/mortality", json=request_data)

        assert response.status_code == 200


class TestUpdateBiometry:
    """Tests para PATCH /api/cages/{cage_id}/biometry"""

    def test_update_biometry_returns_200(self, client):
        """Test: Actualizar biometría retorna 200."""
        cage_id = str(uuid4())
        request_data = {
            "avg_weight_grams": 200.0,
            "event_date": date.today().isoformat(),
            "note": "Muestreo mensual",
        }
        
        with patch("api.routers.cage_router.UpdateBiometryUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "id": cage_id,
                "name": "Jaula 1",
                "status": "IN_USE",
                "created_at": "2024-01-15T10:00:00",
                "fish_count": 1000,
                "avg_weight_grams": 200.0,
                "biomass_kg": 200.0,
                "config": {
                    "fcr": 1.5,
                    "volume_m3": 1000.0,
                    "max_density_kg_m3": 50.0,
                    "transport_time_seconds": 30,
                    "blower_power": 75,
                },
                "current_density_kg_m3": 0.2,
            })

            response = client.patch(f"/api/cages/{cage_id}/biometry", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["avg_weight_grams"] == 200.0


class TestGetPopulationHistory:
    """Tests para GET /api/cages/{cage_id}/history"""

    def test_get_population_history_returns_200(self, client):
        """Test: Obtener historial de población retorna 200."""
        cage_id = str(uuid4())
        
        with patch("api.routers.cage_router.GetPopulationHistoryUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "events": [
                    {
                        "id": str(uuid4()),
                        "cage_id": cage_id,
                        "event_type": "INITIAL_STOCK",
                        "event_date": "2024-01-15",
                        "fish_count_delta": 1000,
                        "new_fish_count": 1000,
                        "avg_weight_grams": 150.0,
                        "biomass_kg": 150.0,
                        "note": "Siembra inicial",
                        "created_at": "2024-01-15T10:00:00",
                    }
                ],
                "pagination": {
                    "total": 1,
                    "limit": 50,
                    "offset": 0,
                    "has_next": False,
                    "has_previous": False,
                },
            })

            response = client.get(f"/api/cages/{cage_id}/history")

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "pagination" in data

    def test_get_population_history_with_pagination(self, client):
        """Test: Obtener historial con paginación."""
        cage_id = str(uuid4())
        
        with patch("api.routers.cage_router.GetPopulationHistoryUseCase") as mock_use_case:
            mock_instance = mock_use_case.return_value
            mock_instance.execute = pytest.AsyncMock(return_value={
                "events": [],
                "pagination": {
                    "total": 0,
                    "limit": 10,
                    "offset": 0,
                    "has_next": False,
                    "has_previous": False,
                },
            })

            response = client.get(f"/api/cages/{cage_id}/history?limit=10&offset=0")

        assert response.status_code == 200

    def test_get_population_history_with_invalid_limit_returns_422(self, client):
        """Test: Obtener historial con límite inválido retorna 422."""
        cage_id = str(uuid4())
        
        response = client.get(f"/api/cages/{cage_id}/history?limit=200")
        
        assert response.status_code == 422  # max 100

    def test_get_population_history_with_invalid_offset_returns_422(self, client):
        """Test: Obtener historial con offset negativo retorna 422."""
        cage_id = str(uuid4())
        
        response = client.get(f"/api/cages/{cage_id}/history?offset=-1")
        
        assert response.status_code == 422
