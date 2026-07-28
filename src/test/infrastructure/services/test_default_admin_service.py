"""Tests para el servicio de administrador por defecto."""

import pytest
from sqlalchemy.exc import IntegrityError
from unittest.mock import AsyncMock, MagicMock

from domain.aggregates.user import UserRole
from infrastructure.services.default_admin_service import (
    DEFAULT_ADMIN_FULL_NAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    seed_default_admin_if_needed,
)


@pytest.fixture
def mock_session():
    """Fixture que proporciona una sesión mock."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_user_repository():
    """Fixture que proporciona un UserRepository mock."""
    repo = MagicMock()
    repo.find_by_username = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    return repo


@pytest.mark.asyncio
class TestSeedDefaultAdmin:
    """Tests para seed_default_admin_if_needed."""

    async def test_creates_default_admin_when_not_exists(self, mock_session, mock_user_repository, monkeypatch):
        """Debe crear el admin por defecto si no existe."""
        from infrastructure import services

        monkeypatch.setattr(
            services.default_admin_service,
            "UserRepository",
            lambda session: mock_user_repository,
        )

        await seed_default_admin_if_needed(mock_session)

        mock_user_repository.find_by_username.assert_called_once_with(DEFAULT_ADMIN_USERNAME)
        mock_user_repository.save.assert_called_once()
        mock_session.commit.assert_called_once()

        saved_user = mock_user_repository.save.call_args[0][0]
        assert saved_user.username == DEFAULT_ADMIN_USERNAME
        assert saved_user.full_name == DEFAULT_ADMIN_FULL_NAME
        assert saved_user.role == UserRole.ADMIN
        assert saved_user.is_superadmin is True
        assert saved_user.is_active is True
        assert saved_user.hashed_password != DEFAULT_ADMIN_PASSWORD

    async def test_does_nothing_when_admin_already_exists(self, mock_session, mock_user_repository, monkeypatch):
        """No debe crear nada si el admin por defecto ya existe."""
        from infrastructure import services

        existing_admin = MagicMock()
        mock_user_repository.find_by_username = AsyncMock(return_value=existing_admin)
        monkeypatch.setattr(
            services.default_admin_service,
            "UserRepository",
            lambda session: mock_user_repository,
        )

        await seed_default_admin_if_needed(mock_session)

        mock_user_repository.find_by_username.assert_called_once_with(DEFAULT_ADMIN_USERNAME)
        mock_user_repository.save.assert_not_called()
        mock_session.commit.assert_not_called()

    async def test_handles_integrity_error_when_another_worker_creates_admin(
        self, mock_session, mock_user_repository, monkeypatch
    ):
        """Debe manejar IntegrityError si otro worker creó el admin concurrentemente."""
        from infrastructure import services

        mock_user_repository.save = AsyncMock(side_effect=IntegrityError("mock", "mock", "mock"))
        monkeypatch.setattr(
            services.default_admin_service,
            "UserRepository",
            lambda session: mock_user_repository,
        )

        await seed_default_admin_if_needed(mock_session)

        mock_user_repository.find_by_username.assert_called_once_with(DEFAULT_ADMIN_USERNAME)
        mock_user_repository.save.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
