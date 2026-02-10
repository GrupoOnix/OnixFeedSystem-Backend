"""
Tests de integración para endpoints de la API.

Estos tests se ejecutan contra el servidor real en localhost:8000.
Requieren: docker-compose up -d
"""

import pytest
import requests  # type: ignore[import-untyped]
from uuid import uuid4

BASE_URL = "http://localhost:8000"


@pytest.mark.integration
class TestHealthIntegration:
    """Tests de integración para health checks."""

    def test_root_endpoint(self):
        """Test: El endpoint raíz responde correctamente."""
        response = requests.get(f"{BASE_URL}/", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "message" in data

    def test_health_endpoint(self):
        """Test: El endpoint de health responde correctamente."""
        response = requests.get(f"{BASE_URL}/health", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_swagger_ui_available(self):
        """Test: Swagger UI está disponible."""
        response = requests.get(f"{BASE_URL}/docs", timeout=5)

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_schema_available(self):
        """Test: El esquema OpenAPI está disponible."""
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)

        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema


@pytest.mark.integration
class TestCagesIntegration:
    """Tests de integración para el módulo de jaulas."""

    def test_list_cages_returns_200(self):
        """Test: Listar jaulas retorna 200."""
        response = requests.get(f"{BASE_URL}/api/cages", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "cages" in data
        assert "total" in data

    def test_get_cage_not_found_returns_404(self):
        """Test: Obtener jaula inexistente retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.get(f"{BASE_URL}/api/cages/{fake_id}", timeout=5)

        assert response.status_code == 404

    def test_create_cage_validation_error(self):
        """Test: Crear jaula con datos inválidos retorna 422."""
        invalid_data = {
            "fcr": 1.5,
            # Falta "name" que es requerido
        }
        response = requests.post(f"{BASE_URL}/api/cages", json=invalid_data, timeout=5)

        assert response.status_code == 422

    def test_update_cage_not_found(self):
        """Test: Actualizar jaula inexistente retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        data = {"name": "Nuevo Nombre"}
        response = requests.patch(f"{BASE_URL}/api/cages/{fake_id}", json=data, timeout=5)

        assert response.status_code == 404

    def test_delete_cage_not_found(self):
        """Test: Eliminar jaula inexistente retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.delete(f"{BASE_URL}/api/cages/{fake_id}", timeout=5)

        assert response.status_code == 404

    def test_set_population_validation_error(self):
        """Test: Establecer población con datos inválidos retorna 422."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        invalid_data = {
            "fish_count": 0,  # Debe ser > 0
            "avg_weight_grams": 150.0,
            "event_date": "2024-01-15",
        }
        response = requests.put(f"{BASE_URL}/api/cages/{fake_id}/population", json=invalid_data, timeout=5)

        assert response.status_code == 422

    def test_register_mortality_validation_error(self):
        """Test: Registrar mortalidad con datos inválidos retorna 422."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        invalid_data = {
            "dead_count": -1,  # Debe ser > 0
            "event_date": "2024-01-15",
        }
        response = requests.post(f"{BASE_URL}/api/cages/{fake_id}/mortality", json=invalid_data, timeout=5)

        assert response.status_code == 422


@pytest.mark.integration
class TestSilosIntegration:
    """Tests de integración para el módulo de silos."""

    def test_list_silos_returns_200(self):
        """Test: Listar silos retorna 200."""
        response = requests.get(f"{BASE_URL}/api/silos", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "silos" in data

    def test_get_silo_not_found_returns_404(self):
        """Test: Obtener silo inexistente retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.get(f"{BASE_URL}/api/silos/{fake_id}", timeout=5)

        assert response.status_code == 404

    def test_create_silo_validation_error(self):
        """Test: Crear silo sin nombre retorna 422."""
        invalid_data = {
            "capacity_kg": 10000.0,
        }
        response = requests.post(f"{BASE_URL}/api/silos", json=invalid_data, timeout=5)

        assert response.status_code == 422


@pytest.mark.integration
class TestAlertsIntegration:
    """Tests de integración para el módulo de alertas."""

    def test_list_alerts_returns_200(self):
        """Test: Listar alertas retorna 200."""
        response = requests.get(f"{BASE_URL}/api/alerts", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data

    def test_get_unread_count_returns_200(self):
        """Test: Obtener contador de no leídas retorna 200."""
        response = requests.get(f"{BASE_URL}/api/alerts/unread/count", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "count" in data

    def test_get_alert_counts_returns_200(self):
        """Test: Obtener contadores por tipo retorna 200."""
        response = requests.get(f"{BASE_URL}/api/alerts/counts", timeout=5)

        assert response.status_code == 200

    def test_list_scheduled_alerts_returns_200(self):
        """Test: Listar alertas programadas retorna 200."""
        response = requests.get(f"{BASE_URL}/api/alerts/scheduled", timeout=5)

        assert response.status_code == 200

    def test_list_snoozed_alerts_returns_200(self):
        """Test: Listar alertas silenciadas retorna 200."""
        response = requests.get(f"{BASE_URL}/api/alerts/snoozed", timeout=5)

        assert response.status_code == 200

    def test_mark_alert_read_not_found(self):
        """Test: Marcar alerta inexistente como leída retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.post(f"{BASE_URL}/api/alerts/{fake_id}/read", timeout=5)

        assert response.status_code == 404


@pytest.mark.integration
class TestFeedingIntegration:
    """Tests de integración para el módulo de alimentación."""

    def test_start_feeding_validation_error(self):
        """Test: Iniciar alimentación sin datos requeridos retorna 422."""
        invalid_data = {
            "mode": "MANUAL",
        }
        response = requests.post(f"{BASE_URL}/api/feeding/start", json=invalid_data, timeout=5)

        assert response.status_code == 422

    def test_stop_feeding_not_found(self):
        """Test: Detener alimentación en línea sin sesión retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.post(f"{BASE_URL}/api/feeding/lines/{fake_id}/stop", timeout=5)

        assert response.status_code == 404

    def test_pause_feeding_not_found(self):
        """Test: Pausar alimentación sin sesión activa retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.post(f"{BASE_URL}/api/feeding/lines/{fake_id}/pause", timeout=5)

        assert response.status_code == 404

    def test_resume_feeding_not_found(self):
        """Test: Reanudar alimentación sin sesión activa retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.post(f"{BASE_URL}/api/feeding/lines/{fake_id}/resume", timeout=5)

        assert response.status_code == 404


@pytest.mark.integration
class TestSystemLayoutIntegration:
    """Tests de integración para el layout del sistema."""

    def test_get_system_layout_returns_200(self):
        """Test: Obtener layout del sistema retorna 200."""
        response = requests.get(f"{BASE_URL}/api/system-layout", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "silos" in data
        assert "cages" in data
        assert "feeding_lines" in data

    def test_sync_system_layout_validation_error(self):
        """Test: Sincronizar layout con datos inválidos retorna 422."""
        invalid_data = {
            "silos": [],
            # Faltan cages y feeding_lines
        }
        response = requests.post(f"{BASE_URL}/api/system-layout", json=invalid_data, timeout=5)

        assert response.status_code == 422


@pytest.mark.integration
class TestFeedingLinesIntegration:
    """Tests de integración para líneas de alimentación."""

    def test_list_feeding_lines_returns_200(self):
        """Test: Listar líneas de alimentación retorna 200."""
        response = requests.get(f"{BASE_URL}/api/feeding-lines", timeout=5)

        assert response.status_code == 200

    def test_get_feeding_line_not_found(self):
        """Test: Obtener línea inexistente retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.get(f"{BASE_URL}/api/feeding-lines/{fake_id}", timeout=5)

        assert response.status_code == 404


@pytest.mark.integration
class TestCageGroupsIntegration:
    """Tests de integración para grupos de jaulas."""

    def test_list_cage_groups_returns_200(self):
        """Test: Listar grupos de jaulas retorna 200."""
        response = requests.get(f"{BASE_URL}/api/cage-groups", timeout=5)

        assert response.status_code == 200

    def test_get_cage_group_not_found(self):
        """Test: Obtener grupo inexistente retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.get(f"{BASE_URL}/api/cage-groups/{fake_id}", timeout=5)

        assert response.status_code == 404


@pytest.mark.integration
class TestFoodIntegration:
    """Tests de integración para el módulo de alimentos."""

    def test_list_foods_returns_200(self):
        """Test: Listar alimentos retorna 200."""
        response = requests.get(f"{BASE_URL}/api/foods", timeout=5)

        assert response.status_code == 200


@pytest.mark.integration
class TestSensorsIntegration:
    """Tests de integración para sensores."""

    def test_list_sensors_by_line_not_found(self):
        """Test: Listar sensores de línea inexistente retorna 404."""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.get(f"{BASE_URL}/api/lines/{fake_id}/sensors", timeout=5)

        assert response.status_code == 404
