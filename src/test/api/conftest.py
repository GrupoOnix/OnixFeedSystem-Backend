"""
Fixtures compartidos para tests de API.

Estos fixtures proporcionan:
- Cliente HTTP de test
- Mock de repositorios
- Datos de prueba
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.fixture
def mock_cage_repository():
    """Mock del repositorio de jaulas."""
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_name = AsyncMock()
    repo.list = AsyncMock()
    repo.delete = AsyncMock()
    repo.exists = AsyncMock()
    return repo


@pytest.fixture
def mock_silo_repository():
    """Mock del repositorio de silos."""
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_name = AsyncMock()
    repo.get_all = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_alert_repository():
    """Mock del repositorio de alertas."""
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.list = AsyncMock()
    repo.count_unread = AsyncMock()
    repo.mark_all_as_read = AsyncMock()
    repo.find_active_by_silo = AsyncMock()
    repo.list_snoozed = AsyncMock()
    repo.count_snoozed = AsyncMock()
    repo.count_by_type = AsyncMock()
    return repo


@pytest.fixture
def mock_feeding_session_repository():
    """Mock del repositorio de sesiones de alimentación."""
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_active_by_line_id = AsyncMock()
    return repo


@pytest.fixture
def sample_cage_id():
    """ID de jaula de ejemplo."""
    return str(uuid4())


@pytest.fixture
def sample_silo_id():
    """ID de silo de ejemplo."""
    return str(uuid4())


@pytest.fixture
def sample_line_id():
    """ID de línea de ejemplo."""
    return str(uuid4())


@pytest.fixture
def sample_cage_response(sample_cage_id):
    """Respuesta de ejemplo para una jaula."""
    return {
        "id": sample_cage_id,
        "name": "Jaula Test",
        "status": "AVAILABLE",
        "created_at": datetime.now().isoformat(),
        "fish_count": 0,
        "avg_weight_grams": None,
        "biomass_kg": 0.0,
        "config": {
            "fcr": None,
            "volume_m3": None,
            "max_density_kg_m3": None,
            "transport_time_seconds": None,
            "blower_power": None,
        },
        "current_density_kg_m3": None,
    }


@pytest.fixture
def sample_silo_response(sample_silo_id):
    """Respuesta de ejemplo para un silo."""
    return {
        "id": sample_silo_id,
        "name": "Silo Test",
        "capacity_kg": 10000.0,
        "stock_level_kg": 5000.0,
        "is_assigned": False,
        "created_at": datetime.now().isoformat(),
        "line_id": None,
        "line_name": None,
        "food_id": None,
    }


@pytest.fixture
def sample_alert_response():
    """Respuesta de ejemplo para una alerta."""
    return {
        "id": str(uuid4()),
        "title": "Alerta de prueba",
        "message": "Mensaje de prueba",
        "type": "WARNING",
        "category": "SYSTEM",
        "status": "UNREAD",
        "source": "test",
        "created_at": datetime.now().isoformat(),
        "snoozed_until": None,
    }


@pytest.fixture
def create_cage_request_data():
    """Datos para crear una jaula."""
    return {
        "name": "Nueva Jaula",
        "fcr": 1.5,
        "volume_m3": 1000.0,
        "max_density_kg_m3": 50.0,
        "transport_time_seconds": 30,
        "blower_power": 75,
    }


@pytest.fixture
def create_silo_request_data():
    """Datos para crear un silo."""
    return {
        "name": "Nuevo Silo",
        "capacity_kg": 10000.0,
        "stock_level_kg": 5000.0,
    }


@pytest.fixture
def set_population_request_data():
    """Datos para establecer población."""
    return {
        "fish_count": 1000,
        "avg_weight_grams": 150.5,
        "event_date": date.today().isoformat(),
        "note": "Siembra inicial",
    }


@pytest.fixture
def register_mortality_request_data():
    """Datos para registrar mortalidad."""
    return {
        "dead_count": 10,
        "event_date": date.today().isoformat(),
        "note": "Mortalidad por estrés",
    }


@pytest.fixture
def update_biometry_request_data():
    """Datos para actualizar biometría."""
    return {
        "avg_weight_grams": 200.0,
        "event_date": date.today().isoformat(),
        "note": "Muestreo mensual",
    }
