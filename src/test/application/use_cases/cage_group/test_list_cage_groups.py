"""
Integration tests for ListCageGroupsUseCase.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.use_cases.cage_group.list_cage_groups import ListCageGroupsUseCase
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository, ICageRepository
from domain.value_objects import CageGroupName, CageId, CageName


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
    return ListCageGroupsUseCase(
        group_repository=mock_group_repo,
        cage_repository=mock_cage_repo,
    )


@pytest.mark.asyncio
class TestListCageGroups:
    """Tests para el listado de grupos de jaulas."""

    async def test_list_all_groups_without_filters(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe listar todos los grupos sin filtros."""
        # Arrange
        cage1 = Cage(name=CageName("Jaula 1"))
        cage2 = Cage(name=CageName("Jaula 2"))

        group1 = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage1.id))],
        )
        group2 = CageGroup(
            name=CageGroupName("Sector Sur"),
            cage_ids=[CageId(str(cage2.id))],
        )

        mock_group_repo.search = AsyncMock(return_value=[group1, group2])
        mock_group_repo.count = AsyncMock(return_value=2)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, cage2])

        # Act
        result = await use_case.execute()

        # Assert
        assert result.total == 2
        assert len(result.groups) == 2
        assert result.groups[0].name == "Sector Norte"
        assert result.groups[1].name == "Sector Sur"

        mock_group_repo.search.assert_called_once_with(
            search_term=None, limit=50, offset=0
        )
        mock_group_repo.count.assert_called_once_with(search_term=None)

    async def test_list_groups_with_search_term(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe filtrar grupos por término de búsqueda."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        group = CageGroup(
            name=CageGroupName("Sector Norte Premium"),
            cage_ids=[CageId(str(cage.id))],
        )

        mock_group_repo.search = AsyncMock(return_value=[group])
        mock_group_repo.count = AsyncMock(return_value=1)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)

        # Act
        result = await use_case.execute(search="premium")

        # Assert
        assert result.total == 1
        assert len(result.groups) == 1
        assert "Premium" in result.groups[0].name

        mock_group_repo.search.assert_called_once_with(
            search_term="premium", limit=50, offset=0
        )
        mock_group_repo.count.assert_called_once_with(search_term="premium")

    async def test_list_groups_with_pagination(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe paginar resultados correctamente."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        group = CageGroup(
            name=CageGroupName("Sector Centro"),
            cage_ids=[CageId(str(cage.id))],
        )

        mock_group_repo.search = AsyncMock(return_value=[group])
        mock_group_repo.count = AsyncMock(return_value=100)  # Total mayor
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)

        # Act
        result = await use_case.execute(limit=10, offset=20)

        # Assert
        assert result.total == 100
        assert len(result.groups) == 1

        mock_group_repo.search.assert_called_once_with(
            search_term=None, limit=10, offset=20
        )

    async def test_list_empty_when_no_groups_exist(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe retornar lista vacía cuando no hay grupos."""
        # Arrange
        mock_group_repo.search = AsyncMock(return_value=[])
        mock_group_repo.count = AsyncMock(return_value=0)

        # Act
        result = await use_case.execute()

        # Assert
        assert result.total == 0
        assert len(result.groups) == 0

    async def test_list_groups_with_metrics(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe calcular métricas para cada grupo."""
        # Arrange
        cage1 = Cage(name=CageName("Jaula 1"))
        cage1.set_population(count=1000, avg_weight_g=200.0)

        cage2 = Cage(name=CageName("Jaula 2"))
        cage2.set_population(count=1500, avg_weight_g=250.0)

        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage1.id)), CageId(str(cage2.id))],
        )

        mock_group_repo.search = AsyncMock(return_value=[group])
        mock_group_repo.count = AsyncMock(return_value=1)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, cage2])

        # Act
        result = await use_case.execute()

        # Assert
        assert len(result.groups) == 1
        metrics = result.groups[0].metrics

        assert metrics.total_population == 2500  # 1000 + 1500
        assert metrics.total_biomass == 575.0  # (1000*200 + 1500*250) / 1000
        assert metrics.avg_weight > 0  # Promedio ponderado

    async def test_list_groups_handles_missing_cages_gracefully(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe manejar jaulas faltantes sin fallar."""
        # Arrange
        cage1 = Cage(name=CageName("Jaula 1"))

        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[
                CageId(str(cage1.id)),
                CageId("00000000-0000-0000-0000-000000000999"),  # No existe
            ],
        )

        mock_group_repo.search = AsyncMock(return_value=[group])
        mock_group_repo.count = AsyncMock(return_value=1)
        # Retornar None para la jaula que no existe
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, None])

        # Act
        result = await use_case.execute()

        # Assert: Solo debe calcular métricas con jaulas existentes
        assert len(result.groups) == 1
        assert result.groups[0].metrics is not None

    async def test_list_uses_default_pagination_values(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe usar valores por defecto de paginación."""
        # Arrange
        mock_group_repo.search = AsyncMock(return_value=[])
        mock_group_repo.count = AsyncMock(return_value=0)

        # Act
        result = await use_case.execute()

        # Assert: Verificar valores por defecto (limit=50, offset=0)
        mock_group_repo.search.assert_called_once_with(
            search_term=None, limit=50, offset=0
        )

    async def test_list_groups_with_multiple_cages(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe listar grupos con múltiples jaulas correctamente."""
        # Arrange
        cages = [Cage(name=CageName(f"Jaula {i}")) for i in range(1, 6)]
        cage_ids = [CageId(str(c.id)) for c in cages]

        group = CageGroup(
            name=CageGroupName("Sector Grande"),
            cage_ids=cage_ids,
        )

        mock_group_repo.search = AsyncMock(return_value=[group])
        mock_group_repo.count = AsyncMock(return_value=1)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=cages)

        # Act
        result = await use_case.execute()

        # Assert
        assert len(result.groups) == 1
        assert len(result.groups[0].cage_ids) == 5
        assert mock_cage_repo.find_by_id.call_count == 5

    async def test_list_respects_custom_limit(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe respetar límite personalizado."""
        # Arrange
        mock_group_repo.search = AsyncMock(return_value=[])
        mock_group_repo.count = AsyncMock(return_value=0)

        # Act
        result = await use_case.execute(limit=100, offset=0)

        # Assert
        mock_group_repo.search.assert_called_once_with(
            search_term=None, limit=100, offset=0
        )
