"""
Integration tests for GetCageGroupUseCase.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.use_cases.cage_group.get_cage_group import GetCageGroupUseCase
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository, ICageRepository
from domain.value_objects import CageGroupId, CageGroupName, CageId, CageName
from domain.value_objects.cage_configuration import CageConfiguration


@pytest.fixture
def mock_group_repo():
    """Fixture que proporciona un repositorio mock de grupos de jaulas."""
    repo = MagicMock(spec=ICageGroupRepository)
    return repo


@pytest.fixture
def mock_cage_repo():
    """Fixture que proporciona un repositorio mock de jaulas."""
    repo = MagicMock(spec=ICageRepository)
    return repo


@pytest.fixture
def use_case(mock_group_repo, mock_cage_repo):
    """Fixture que proporciona una instancia del caso de uso."""
    return GetCageGroupUseCase(
        group_repository=mock_group_repo,
        cage_repository=mock_cage_repo,
    )


@pytest.mark.asyncio
class TestGetCageGroup:
    """Tests para la obtención de un grupo de jaulas por ID."""

    async def test_get_existing_group_successfully(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe obtener un grupo existente con sus datos completos."""
        # Arrange
        cage1 = Cage(name=CageName("Jaula 1"))
        cage1._set_fish_count(1000)
        cage1._set_avg_weight_grams(200.0)

        cage2 = Cage(name=CageName("Jaula 2"))
        cage2._set_fish_count(1500)
        cage2._set_avg_weight_grams(250.0)

        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[cage1.id, cage2.id],
            description="Grupo de prueba",
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, cage2])

        # Act
        result = await use_case.execute(group_id)

        # Assert
        assert result.id == group_id
        assert result.name == "Sector Norte"
        assert result.description == "Grupo de prueba"
        assert len(result.cage_ids) == 2
        assert result.metrics is not None
        assert result.metrics.total_population == 2500

        mock_group_repo.find_by_id.assert_called_once_with(CageGroupId.from_string(group_id))
        assert mock_cage_repo.find_by_id.call_count == 2

    async def test_get_group_fails_when_not_found(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar con error cuando el grupo no existe."""
        # Arrange
        group_id = "00000000-0000-0000-0000-000000000001"
        mock_group_repo.find_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(ValueError, match=f"No existe un grupo con ID '{group_id}'"):
            await use_case.execute(group_id)

    async def test_get_group_with_metrics(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe calcular métricas correctamente."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        cage._set_fish_count(2000)
        cage._set_avg_weight_grams(300.0)
        cage.update_config(CageConfiguration(volume_m3=1000.0))

        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[cage.id],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)

        # Act
        result = await use_case.execute(group_id)

        # Assert
        assert result.metrics.total_population == 2000
        assert result.metrics.total_biomass == 600.0  # 2000 * 300 / 1000
        assert result.metrics.avg_weight == 300.0
        assert result.metrics.total_volume == 1000.0

    async def test_get_group_handles_missing_cages(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe manejar jaulas faltantes sin fallar."""
        # Arrange
        cage1 = Cage(name=CageName("Jaula 1"))
        cage1._set_fish_count(1000)
        cage1._set_avg_weight_grams(200.0)

        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[
                cage1.id,
                CageId.from_string("00000000-0000-0000-0000-000000000999"),  # No existe
            ],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        # Retornar None para la jaula que no existe
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, None])

        # Act
        result = await use_case.execute(group_id)

        # Assert: Debe calcular métricas solo con jaulas existentes
        assert result.metrics.total_population == 1000

    async def test_get_group_with_no_description(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe manejar grupos sin descripción."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))

        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[cage.id],
            description=None,
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)

        # Act
        result = await use_case.execute(group_id)

        # Assert
        assert result.description is None

    async def test_get_group_with_multiple_cages(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe obtener grupo con múltiples jaulas."""
        # Arrange
        cages = [Cage(name=CageName(f"Jaula {i}")) for i in range(1, 11)]
        for cage in cages:
            cage._set_fish_count(500)
            cage._set_avg_weight_grams(150.0)

        cage_ids = [c.id for c in cages]

        group = CageGroup(
            name=CageGroupName("Sector Grande"),
            cage_ids=cage_ids,
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=cages)

        # Act
        result = await use_case.execute(group_id)

        # Assert
        assert len(result.cage_ids) == 10
        assert result.metrics.total_population == 5000  # 500 * 10
        assert mock_cage_repo.find_by_id.call_count == 10

    async def test_get_group_with_invalid_uuid_format(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar con UUID inválido."""
        # Arrange
        invalid_id = "not-a-uuid"

        # Act & Assert: El ValueError debe venir de CageGroupId
        with pytest.raises(ValueError):
            await use_case.execute(invalid_id)

    async def test_get_group_includes_timestamps(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe incluir timestamps de creación y actualización."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))

        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[cage.id],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)

        # Act
        result = await use_case.execute(group_id)

        # Assert
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_get_group_with_zero_population_cages(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe manejar jaulas sin población."""
        # Arrange
        cage = Cage(name=CageName("Jaula Vacía"))
        # No establecer población

        group = CageGroup(
            name=CageGroupName("Sector Vacío"),
            cage_ids=[cage.id],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)

        # Act
        result = await use_case.execute(group_id)

        # Assert
        assert result.metrics.total_population == 0
        assert result.metrics.total_biomass == 0.0
