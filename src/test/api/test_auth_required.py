"""Tests para verificar que endpoints protegidos requieren autenticación."""

import sys
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def client():
    """Cliente de test sin autenticación."""
    from fastapi.testclient import TestClient

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/api/cages", None),
        ("post", "/api/cages", {"name": "Jaula Test"}),
        ("get", "/api/cage-groups", None),
        ("post", "/api/cage-groups", {"name": "Grupo Test", "cage_ids": [str(uuid4())]}),
        ("get", "/api/silos", None),
        ("post", "/api/silos", {"name": "Silo Test", "capacity_kg": 1000.0}),
        ("get", "/api/foods", None),
        ("post", "/api/foods", {"name": "Comida Test", "brand": "Test", "energy_kg_per_liter": 1.0}),
        ("get", "/api/feeding-lines", None),
        ("get", "/api/feeding/manual/last-valid-configs", None),
        ("get", "/api/alerts", None),
        ("patch", "/api/alerts/read-all", None),
        ("post", "/api/feedback", {"message": "Mensaje de prueba"}),
        ("get", "/api/users", None),
        ("post", "/api/users", {"username": "newuser", "full_name": "New User", "password": "pass123", "role": "user"}),
        ("get", "/api/auth/me", None),
        ("patch", "/api/auth/me/password", {"current_password": "old", "new_password": "newpass123"}),
        ("get", "/api/system/config", None),
        ("patch", "/api/system/config", {"selector_positioning_time_seconds": 10}),
        ("get", "/api/system-layout", None),
        ("post", "/api/system-layout", {"cages": [], "feeding_lines": [], "silos": []}),
        ("post", "/api/feeding-lines/test-line/manual-control/acquire", {"reason": "test"}),
    ],
)
def test_protected_endpoint_rejects_request_without_token(client, method, path, body):
    """Endpoints protegidos deben retornar 401 si no se envía token."""
    response = client.request(method, path, json=body)
    assert response.status_code == 401, f"{method.upper()} {path} retornó {response.status_code}"


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/api/auth/login", None),
        ("post", "/api/auth/login", {"username": "adminOnix", "password": "OnixServicios"}),
    ],
)
def test_login_endpoint_is_public(client, method, path, body):
    """El endpoint de login debe ser público (no requiere token)."""
    response = client.request(method, path, json=body)
    assert response.status_code != 401, f"{method.upper()} {path} no debería requerir token"


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/"),
        ("get", "/health"),
    ],
)
def test_public_health_endpoints_are_open(client, method, path):
    """Endpoints de health deben ser accesibles sin token."""
    response = client.request(method, path)
    assert response.status_code == 200, f"{method.upper()} {path} retornó {response.status_code}"
