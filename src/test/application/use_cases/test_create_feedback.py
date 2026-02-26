"""
Tests para CreateFeedbackUseCase.

Verifica que el caso de uso crea feedback correctamente,
valida tipos y mensajes, y maneja campos opcionales.
"""

from unittest.mock import AsyncMock

import pytest

from application.dtos.feedback_dtos import CreateFeedbackRequest
from application.use_cases.feedback.create_feedback_use_case import CreateFeedbackUseCase
from domain.aggregates.feedback import Feedback
from domain.repositories import IFeedbackRepository


@pytest.fixture
def mock_feedback_repo() -> AsyncMock:
    """Fixture que proporciona un repositorio mock de feedback."""
    repo = AsyncMock(spec=IFeedbackRepository)
    repo.save = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def use_case(mock_feedback_repo: AsyncMock) -> CreateFeedbackUseCase:
    """Fixture que proporciona una instancia del caso de uso."""
    return CreateFeedbackUseCase(feedback_repository=mock_feedback_repo)


class TestCreateFeedback:
    """Tests para la creación de feedback."""

    @pytest.mark.asyncio
    async def test_create_feedback_all_fields(self, use_case, mock_feedback_repo):
        """Debe crear un feedback con todos los campos proporcionados."""
        request = CreateFeedbackRequest(
            name="Juan Pérez",
            email="juan@email.com",
            type="bug",
            message="El dashboard no actualiza el progreso en tiempo real.",
        )

        await use_case.execute(request)

        mock_feedback_repo.save.assert_called_once()
        saved_feedback: Feedback = mock_feedback_repo.save.call_args[0][0]
        assert saved_feedback.name == "Juan Pérez"
        assert saved_feedback.email == "juan@email.com"
        assert saved_feedback.type == "bug"
        assert saved_feedback.message == "El dashboard no actualiza el progreso en tiempo real."

    @pytest.mark.asyncio
    async def test_create_feedback_optional_fields_omitted(self, use_case, mock_feedback_repo):
        """Debe crear un feedback sin nombre ni email."""
        request = CreateFeedbackRequest(
            type="suggestion",
            message="Sería útil agregar gráficos de tendencia.",
        )

        await use_case.execute(request)

        mock_feedback_repo.save.assert_called_once()
        saved_feedback: Feedback = mock_feedback_repo.save.call_args[0][0]
        assert saved_feedback.name is None
        assert saved_feedback.email is None
        assert saved_feedback.type == "suggestion"
        assert saved_feedback.message == "Sería útil agregar gráficos de tendencia."

    @pytest.mark.asyncio
    async def test_create_feedback_general_type(self, use_case, mock_feedback_repo):
        """Debe aceptar tipo 'general'."""
        request = CreateFeedbackRequest(
            type="general",
            message="Comentario general sobre el sistema.",
        )

        await use_case.execute(request)

        mock_feedback_repo.save.assert_called_once()
        saved_feedback: Feedback = mock_feedback_repo.save.call_args[0][0]
        assert saved_feedback.type == "general"

    @pytest.mark.asyncio
    async def test_create_feedback_invalid_type_raises_error(self, use_case):
        """Debe lanzar ValueError si el tipo de feedback no es válido."""
        request = CreateFeedbackRequest(
            type="complaint",
            message="Esto no debería funcionar.",
        )

        with pytest.raises(ValueError, match="Tipo de feedback inválido"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_create_feedback_empty_message_raises_error(self, use_case):
        """Debe lanzar ValueError si el mensaje está vacío."""
        request = CreateFeedbackRequest(
            type="bug",
            message="",
        )

        with pytest.raises(ValueError, match="El mensaje de feedback no puede estar vacío"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_create_feedback_whitespace_message_raises_error(self, use_case):
        """Debe lanzar ValueError si el mensaje solo tiene espacios en blanco."""
        request = CreateFeedbackRequest(
            type="bug",
            message="   ",
        )

        with pytest.raises(ValueError, match="El mensaje de feedback no puede estar vacío"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_create_feedback_message_is_trimmed(self, use_case, mock_feedback_repo):
        """Debe recortar los espacios del mensaje."""
        request = CreateFeedbackRequest(
            type="suggestion",
            message="  Mensaje con espacios  ",
        )

        await use_case.execute(request)

        saved_feedback: Feedback = mock_feedback_repo.save.call_args[0][0]
        assert saved_feedback.message == "Mensaje con espacios"

    @pytest.mark.asyncio
    async def test_create_feedback_name_is_trimmed(self, use_case, mock_feedback_repo):
        """Debe recortar los espacios del nombre."""
        request = CreateFeedbackRequest(
            name="  Juan  ",
            type="general",
            message="Un mensaje.",
        )

        await use_case.execute(request)

        saved_feedback: Feedback = mock_feedback_repo.save.call_args[0][0]
        assert saved_feedback.name == "Juan"
