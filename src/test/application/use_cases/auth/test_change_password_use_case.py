"""Tests para ChangePasswordUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.dtos.auth_dtos import ChangePasswordRequest
from application.use_cases.auth.change_password_use_case import ChangePasswordUseCase
from domain.aggregates.user import User
from domain.exceptions import InvalidCredentialsError
from domain.repositories import IUserRepository
from infrastructure.security.password_service import PasswordService


@pytest.fixture
def mock_user_repo():
    """Fixture que proporciona un repositorio mock de usuarios."""
    return MagicMock(spec=IUserRepository)


@pytest.fixture
def password_service():
    """Fixture que proporciona una instancia real del servicio de contraseñas."""
    return PasswordService()


@pytest.fixture
def use_case(mock_user_repo, password_service):
    """Fixture que proporciona una instancia del caso de uso."""
    return ChangePasswordUseCase(
        user_repository=mock_user_repo,
        password_service=password_service,
    )


@pytest.mark.asyncio
class TestChangePasswordUseCase:
    """Tests para el caso de uso de cambio de contraseña propia."""

    async def test_change_password_clears_must_change_flag(self, use_case, mock_user_repo, password_service):
        """Debe cambiar la contraseña y limpiar must_change_password."""
        user = User.create(
            username="operator1",
            full_name="Operador Uno",
            hashed_password=password_service.hash_password("oldpass123"),
            must_change_password=True,
        )
        mock_user_repo.find_by_id = AsyncMock(return_value=user)
        mock_user_repo.save = AsyncMock()

        request = ChangePasswordRequest(
            current_password="oldpass123",
            new_password="newpass123",
        )

        await use_case.execute(user_id=str(user.id), request=request)

        assert user.must_change_password is False
        assert password_service.verify_password("newpass123", user.hashed_password)
        mock_user_repo.save.assert_called_once_with(user)

    async def test_change_password_with_wrong_current_password_raises(self, use_case, mock_user_repo, password_service):
        """Debe fallar si la contraseña actual no coincide."""
        user = User.create(
            username="operator1",
            full_name="Operador Uno",
            hashed_password=password_service.hash_password("oldpass123"),
        )
        mock_user_repo.find_by_id = AsyncMock(return_value=user)

        request = ChangePasswordRequest(
            current_password="wrongpass",
            new_password="newpass123",
        )

        with pytest.raises(InvalidCredentialsError, match="contraseña actual es incorrecta"):
            await use_case.execute(user_id=str(user.id), request=request)

    async def test_change_password_with_short_new_password_raises(self, use_case, mock_user_repo, password_service):
        """Debe fallar si la nueva contraseña tiene menos de 6 caracteres."""
        user = User.create(
            username="operator1",
            full_name="Operador Uno",
            hashed_password=password_service.hash_password("oldpass123"),
        )
        mock_user_repo.find_by_id = AsyncMock(return_value=user)

        request = ChangePasswordRequest(
            current_password="oldpass123",
            new_password="123",
        )

        with pytest.raises(ValueError, match="al menos 6 caracteres"):
            await use_case.execute(user_id=str(user.id), request=request)
