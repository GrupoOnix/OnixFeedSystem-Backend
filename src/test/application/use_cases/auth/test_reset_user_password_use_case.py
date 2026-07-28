"""Tests para ResetUserPasswordUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.dtos.auth_dtos import ResetPasswordRequest
from application.use_cases.users.reset_user_password_use_case import ResetUserPasswordUseCase
from domain.aggregates.user import User
from domain.exceptions import InsufficientPermissionsError
from domain.repositories import IUserRepository
from infrastructure.security.password_service import PasswordService


@pytest.fixture
def mock_user_repo():
    """Fixture que proporciona un repositorio mock de usuarios."""
    repo = MagicMock(spec=IUserRepository)
    repo.find_by_id = AsyncMock()
    return repo


@pytest.fixture
def password_service():
    """Fixture que proporciona una instancia real del servicio de contraseñas."""
    return PasswordService()


@pytest.fixture
def use_case(mock_user_repo, password_service):
    """Fixture que proporciona una instancia del caso de uso."""
    return ResetUserPasswordUseCase(
        user_repository=mock_user_repo,
        password_service=password_service,
    )


@pytest.mark.asyncio
class TestResetUserPasswordUseCase:
    """Tests para el caso de uso de reseteo de contraseña."""

    async def test_reset_password_generates_six_digit_temporary_password(
        self, use_case, mock_user_repo, password_service
    ):
        """Debe generar una contraseña temporal numérica de 6 dígitos."""
        target_user = User.create(
            username="operator1",
            full_name="Operador Uno",
            hashed_password=password_service.hash_password("oldpass123"),
        )
        requester_user = User.create(
            username="superadmin",
            full_name="Super Admin",
            hashed_password=password_service.hash_password("adminpass"),
            is_superadmin=True,
        )
        mock_user_repo.find_by_id.return_value = target_user
        mock_user_repo.save = AsyncMock()

        result = await use_case.execute(
            user_id=str(target_user.id),
            request=ResetPasswordRequest(),
            requester_id=str(requester_user.id),
            requester_is_superadmin=True,
        )

        assert result.must_change_password is True
        assert len(result.temporary_password) == 6
        assert result.temporary_password.isdigit()
        assert password_service.verify_password(result.temporary_password, target_user.hashed_password)
        mock_user_repo.save.assert_called_once_with(target_user)

    async def test_reset_password_requires_superadmin(self, use_case):
        """Debe fallar si el solicitante no es superadmin."""
        with pytest.raises(InsufficientPermissionsError, match="Solo un superadmin"):
            await use_case.execute(
                user_id="00000000-0000-0000-0000-000000000001",
                request=ResetPasswordRequest(),
                requester_id="00000000-0000-0000-0000-000000000002",
                requester_is_superadmin=False,
            )

    async def test_reset_password_rejects_self_reset(self, use_case, password_service):
        """Debe fallar si el superadmin intenta resetear su propia contraseña."""
        requester_user = User.create(
            username="superadmin",
            full_name="Super Admin",
            hashed_password=password_service.hash_password("adminpass"),
            is_superadmin=True,
        )

        with pytest.raises(InsufficientPermissionsError, match="No puedes resetear tu propia contraseña"):
            await use_case.execute(
                user_id=str(requester_user.id),
                request=ResetPasswordRequest(),
                requester_id=str(requester_user.id),
                requester_is_superadmin=True,
            )

    async def test_reset_password_not_found_user_raises(self, use_case, mock_user_repo, password_service):
        """Debe fallar si el usuario no existe."""
        requester_user = User.create(
            username="superadmin",
            full_name="Super Admin",
            hashed_password=password_service.hash_password("adminpass"),
            is_superadmin=True,
        )
        mock_user_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="Usuario no encontrado"):
            await use_case.execute(
                user_id="00000000-0000-0000-0000-000000000001",
                request=ResetPasswordRequest(),
                requester_id=str(requester_user.id),
                requester_is_superadmin=True,
            )
