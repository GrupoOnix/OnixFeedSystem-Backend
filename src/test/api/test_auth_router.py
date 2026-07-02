"""Tests para el router de autenticación."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.dependencies import (
    get_authenticate_user_use_case,
    get_change_password_use_case,
    get_current_user,
)
from application.dtos.auth_dtos import LoginResponse, UserResponse
from main import app


@pytest.fixture
def client():
    """Fixture que proporciona el TestClient."""
    from fastapi.testclient import TestClient

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_response():
    """Usuario de ejemplo para tests."""
    return UserResponse(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        username="adminOnix",
        full_name="Admin Onix",
        role="admin",
        is_superadmin=True,
        is_active=True,
        created_at=datetime(2024, 1, 1, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0),
    )


class TestLogin:
    """Tests para POST /api/auth/login"""

    def test_login_with_valid_credentials_returns_token(self, client, sample_user_response):
        """Test: Login exitoso retorna token y datos del usuario."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=LoginResponse(
                access_token="fake-jwt-token",
                token_type="bearer",
                user=sample_user_response,
            )
        )
        app.dependency_overrides[get_authenticate_user_use_case] = lambda: mock_use_case

        response = client.post(
            "/api/auth/login",
            json={"username": "adminOnix", "password": "OnixServicios"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "fake-jwt-token"
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "adminOnix"

    def test_login_with_invalid_credentials_returns_401(self, client):
        """Test: Login con credenciales inválidas retorna 401."""
        from domain.exceptions import InvalidCredentialsError

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=InvalidCredentialsError("Credenciales inválidas"))
        app.dependency_overrides[get_authenticate_user_use_case] = lambda: mock_use_case

        response = client.post(
            "/api/auth/login",
            json={"username": "wrong", "password": "wrong"},
        )

        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests para GET /api/auth/me"""

    def test_get_current_user_with_valid_token(self, client, sample_user_response):
        """Test: /me retorna el usuario autenticado."""
        app.dependency_overrides[get_current_user] = lambda: sample_user_response

        response = client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "adminOnix"
        assert data["role"] == "admin"

    def test_get_current_user_without_token_returns_401(self, client):
        """Test: /me sin token retorna 401."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401


class TestChangePassword:
    """Tests para PATCH /api/auth/me/password"""

    def test_change_password_success(self, client, sample_user_response):
        """Test: Cambio de contraseña exitoso retorna 204."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=None)
        app.dependency_overrides[get_current_user] = lambda: sample_user_response
        app.dependency_overrides[get_change_password_use_case] = lambda: mock_use_case

        response = client.patch(
            "/api/auth/me/password",
            json={"current_password": "old", "new_password": "newpass123"},
        )

        assert response.status_code == 204
