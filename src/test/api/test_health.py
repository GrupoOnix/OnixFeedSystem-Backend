"""
Tests para los endpoints de health check.

Verifica que los endpoints de monitoreo respondan correctamente.
"""

import sys
from pathlib import Path

import pytest

# Configurar path antes de cualquier import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def client():
    """Fixture que proporciona el TestClient."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Tests para endpoints de health check."""

    def test_root_endpoint_returns_welcome_message(self, client):
        """Test: El endpoint raíz retorna mensaje de bienvenida."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "message" in data
        assert "Feeding System API" in data["message"]

    def test_health_endpoint_returns_healthy_status(self, client):
        """Test: El endpoint /health retorna estado healthy."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_endpoint_returns_json_content_type(self, client):
        """Test: El endpoint /health retorna content-type JSON."""
        response = client.get("/health")
        
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_is_fast(self, client):
        """Test: El endpoint /health responde rápidamente (< 100ms)."""
        import time
        
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.1  # 100ms


class TestAPIDocumentation:
    """Tests para documentación de API."""

    def test_swagger_ui_is_available(self, client):
        """Test: Swagger UI está disponible en /docs."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "swagger" in response.text.lower()

    def test_redoc_is_available(self, client):
        """Test: ReDoc está disponible en /redoc."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema_is_available(self, client):
        """Test: El esquema OpenAPI está disponible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/api/cages" in schema["paths"] or "/api/silos" in schema["paths"]
