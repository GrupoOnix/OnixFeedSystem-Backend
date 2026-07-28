"""Tests para el router de gestión de usuarios."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.dependencies import (
    get_current_admin_user,
    get_current_superadmin_user,
    get_list_users_use_case,
    get_register_user_use_case,
    get_reset_user_password_use_case,
    get_update_user_role_use_case,
    get_update_user_status_use_case,
)
from application.dtos.auth_dtos import ListUsersResponse, ResetPasswordResponse, UserResponse
from main import app


@pytest.fixture
def client():
    """Fixture que proporciona el TestClient."""
    from fastapi.testclient import TestClient

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user_response():
    """Admin de ejemplo para tests."""
    return UserResponse(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        username="adminOnix",
        full_name="Admin Onix",
        role="admin",
        is_superadmin=True,
        is_active=True,
        must_change_password=False,
        created_at=datetime(2024, 1, 1, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0),
    )


@pytest.fixture
def regular_user_response():
    """Usuario normal de ejemplo."""
    return UserResponse(
        id="b2c3d4e5-f6a7-8901-bcde-f23456789012",
        username="operator1",
        full_name="Operador Uno",
        role="user",
        is_superadmin=False,
        is_active=True,
        must_change_password=False,
        created_at=datetime(2024, 1, 1, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0),
    )


class TestRegisterUser:
    """Tests para POST /api/users"""

    def test_register_user_by_admin_returns_201(self, client, admin_user_response, regular_user_response):
        """Test: Un admin puede crear un usuario."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=regular_user_response)
        app.dependency_overrides[get_current_admin_user] = lambda: admin_user_response
        app.dependency_overrides[get_register_user_use_case] = lambda: mock_use_case

        response = client.post(
            "/api/users",
            json={
                "username": "operator1",
                "full_name": "Operador Uno",
                "password": "pass1234",
                "role": "user",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "operator1"
        assert data["role"] == "user"


class TestListUsers:
    """Tests para GET /api/users"""

    def test_list_users_by_admin(self, client, admin_user_response, regular_user_response):
        """Test: Un admin puede listar usuarios."""
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(
            return_value=ListUsersResponse(users=[admin_user_response, regular_user_response])
        )
        app.dependency_overrides[get_current_admin_user] = lambda: admin_user_response
        app.dependency_overrides[get_list_users_use_case] = lambda: mock_use_case

        response = client.get("/api/users")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2


class TestUpdateUserStatus:
    """Tests para PATCH /api/users/{id}/status"""

    def test_update_user_status_by_admin(self, client, admin_user_response, regular_user_response):
        """Test: Un admin puede desactivar un usuario user."""
        updated_user = regular_user_response
        updated_user.is_active = False

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=updated_user)
        app.dependency_overrides[get_current_admin_user] = lambda: admin_user_response
        app.dependency_overrides[get_update_user_status_use_case] = lambda: mock_use_case

        response = client.patch(
            f"/api/users/{regular_user_response.id}/status",
            json={"is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False


class TestUpdateUserRole:
    """Tests para PATCH /api/users/{id}/role"""

    def test_update_user_role_by_superadmin(self, client, admin_user_response, regular_user_response):
        """Test: Un superadmin puede cambiar el rol de un usuario."""
        updated_user = regular_user_response
        updated_user.role = "admin"

        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=updated_user)
        app.dependency_overrides[get_current_superadmin_user] = lambda: admin_user_response
        app.dependency_overrides[get_update_user_role_use_case] = lambda: mock_use_case

        response = client.patch(
            f"/api/users/{regular_user_response.id}/role",
            json={"role": "admin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"


class TestResetUserPassword:
    """Tests para PATCH /api/users/{id}/password"""

    def test_reset_password_by_superadmin(self, client, admin_user_response, regular_user_response):
        """Test: Un superadmin puede resetear la contraseña de un usuario."""
        reset_response = ResetPasswordResponse(
            id=regular_user_response.id,
            username=regular_user_response.username,
            full_name=regular_user_response.full_name,
            role=regular_user_response.role,
            is_superadmin=regular_user_response.is_superadmin,
            is_active=regular_user_response.is_active,
            must_change_password=True,
            created_at=regular_user_response.created_at,
            updated_at=regular_user_response.updated_at,
            temporary_password="123456",
        )
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=reset_response)
        app.dependency_overrides[get_current_superadmin_user] = lambda: admin_user_response
        app.dependency_overrides[get_reset_user_password_use_case] = lambda: mock_use_case

        response = client.patch(
            f"/api/users/{regular_user_response.id}/password",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "operator1"
        assert data["must_change_password"] is True
        assert data["temporary_password"] == "123456"
