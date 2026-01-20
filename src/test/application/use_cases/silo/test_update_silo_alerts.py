"""
Tests para verificar que UpdateSiloUseCase dispara alertas de nivel bajo.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.dtos.silo_dtos import UpdateSiloRequest
from application.services.alert_trigger_service import AlertTriggerService
from application.use_cases.silo.update_silo_use_case import UpdateSiloUseCase
from domain.aggregates.silo import Silo
from domain.repositories import ISiloRepository
from domain.value_objects import SiloId, SiloName, Weight


@pytest.fixture
def mock_silo_repo():
    """Fixture que proporciona un repositorio mock de silos."""
    repo = MagicMock(spec=ISiloRepository)
    return repo


@pytest.fixture
def mock_alert_trigger_service():
    """Fixture que proporciona un servicio mock de alertas."""
    service = MagicMock(spec=AlertTriggerService)
    service.silo_low_level = AsyncMock()
    return service


@pytest.fixture
def use_case(mock_silo_repo, mock_alert_trigger_service):
    """Fixture que proporciona una instancia del caso de uso."""
    return UpdateSiloUseCase(
        silo_repository=mock_silo_repo,
        alert_trigger_service=mock_alert_trigger_service,
    )


@pytest.mark.asyncio
class TestUpdateSiloAlerts:
    """Tests para alertas de nivel bajo en silos."""

    async def test_alert_not_triggered_when_level_above_threshold(
        self, use_case, mock_silo_repo, mock_alert_trigger_service
    ):
        """No debe disparar alerta cuando el nivel está sobre el umbral (>20%)."""
        # Arrange: Crear silo con 50% de capacidad
        silo = Silo(
            name=SiloName("Silo 1"),
            capacity=Weight.from_kg(1000),
            stock_level=Weight.from_kg(500),  # 50%
        )
        silo_id = str(silo.id)

        mock_silo_repo.find_by_id = AsyncMock(return_value=silo)
        mock_silo_repo.find_by_name = AsyncMock(return_value=None)
        mock_silo_repo.save = AsyncMock()
        mock_silo_repo.find_by_id_with_line_info = AsyncMock(
            return_value=(silo, None, None)
        )

        request = UpdateSiloRequest(stock_level_kg=500)

        # Act: Actualizar silo
        await use_case.execute(silo_id, request)

        # Assert: No debe disparar alerta
        mock_alert_trigger_service.silo_low_level.assert_not_called()

    async def test_alert_triggered_when_level_at_warning_threshold(
        self, use_case, mock_silo_repo, mock_alert_trigger_service
    ):
        """Debe disparar alerta WARNING cuando el nivel está al 20%."""
        # Arrange: Crear silo con 20% de capacidad
        silo = Silo(
            name=SiloName("Silo 1"),
            capacity=Weight.from_kg(1000),
            stock_level=Weight.from_kg(200),  # 20%
        )
        silo_id = str(silo.id)

        mock_silo_repo.find_by_id = AsyncMock(return_value=silo)
        mock_silo_repo.find_by_name = AsyncMock(return_value=None)
        mock_silo_repo.save = AsyncMock()
        mock_silo_repo.find_by_id_with_line_info = AsyncMock(
            return_value=(silo, None, None)
        )

        request = UpdateSiloRequest(stock_level_kg=150)  # Bajar a 15%

        # Act: Actualizar silo
        await use_case.execute(silo_id, request)

        # Assert: Debe disparar alerta
        mock_alert_trigger_service.silo_low_level.assert_called_once()
        call_args = mock_alert_trigger_service.silo_low_level.call_args[1]
        assert call_args["silo_id"] == silo_id
        assert call_args["silo_name"] == "Silo 1"
        assert call_args["current_level"] == 150.0
        assert call_args["max_capacity"] == 1000.0
        assert call_args["percentage"] == 15.0

    async def test_alert_triggered_when_level_at_critical_threshold(
        self, use_case, mock_silo_repo, mock_alert_trigger_service
    ):
        """Debe disparar alerta CRITICAL cuando el nivel está al 10%."""
        # Arrange: Crear silo con 100 kg de capacidad
        silo = Silo(
            name=SiloName("Silo 1"),
            capacity=Weight.from_kg(1000),
            stock_level=Weight.from_kg(200),
        )
        silo_id = str(silo.id)

        mock_silo_repo.find_by_id = AsyncMock(return_value=silo)
        mock_silo_repo.find_by_name = AsyncMock(return_value=None)
        mock_silo_repo.save = AsyncMock()
        mock_silo_repo.find_by_id_with_line_info = AsyncMock(
            return_value=(silo, None, None)
        )

        request = UpdateSiloRequest(stock_level_kg=50)  # Bajar a 5%

        # Act: Actualizar silo
        await use_case.execute(silo_id, request)

        # Assert: Debe disparar alerta
        mock_alert_trigger_service.silo_low_level.assert_called_once()
        call_args = mock_alert_trigger_service.silo_low_level.call_args[1]
        assert call_args["percentage"] == 5.0

    async def test_no_alert_when_service_not_provided(
        self, mock_silo_repo
    ):
        """No debe fallar si no se proporciona AlertTriggerService."""
        # Arrange: Crear caso de uso sin servicio de alertas
        use_case_no_alerts = UpdateSiloUseCase(
            silo_repository=mock_silo_repo,
            alert_trigger_service=None,
        )

        silo = Silo(
            name=SiloName("Silo 1"),
            capacity=Weight.from_kg(1000),
            stock_level=Weight.from_kg(200),
        )
        silo_id = str(silo.id)

        mock_silo_repo.find_by_id = AsyncMock(return_value=silo)
        mock_silo_repo.find_by_name = AsyncMock(return_value=None)
        mock_silo_repo.save = AsyncMock()
        mock_silo_repo.find_by_id_with_line_info = AsyncMock(
            return_value=(silo, None, None)
        )

        request = UpdateSiloRequest(stock_level_kg=50)  # 5%

        # Act & Assert: No debe fallar
        await use_case_no_alerts.execute(silo_id, request)

    async def test_alert_with_zero_capacity(
        self, use_case, mock_silo_repo, mock_alert_trigger_service
    ):
        """No debe disparar alerta ni fallar con capacidad cero."""
        # Arrange: Crear silo con capacidad cero (edge case)
        silo = Silo(
            name=SiloName("Silo 1"),
            capacity=Weight.from_kg(0),
            stock_level=Weight.from_kg(0),
        )
        silo_id = str(silo.id)

        mock_silo_repo.find_by_id = AsyncMock(return_value=silo)
        mock_silo_repo.find_by_name = AsyncMock(return_value=None)
        mock_silo_repo.save = AsyncMock()
        mock_silo_repo.find_by_id_with_line_info = AsyncMock(
            return_value=(silo, None, None)
        )

        request = UpdateSiloRequest(stock_level_kg=0)

        # Act: Actualizar silo
        await use_case.execute(silo_id, request)

        # Assert: No debe disparar alerta
        mock_alert_trigger_service.silo_low_level.assert_not_called()
