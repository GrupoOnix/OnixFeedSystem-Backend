"""
Integration tests for CreateCageGroupUseCase.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.dtos.cage_group_dtos import CreateCageGroupRequest
from application.use_cases.cage_group.create_cage_group import CreateCageGroupUseCase
from domain.aggregates.cage import Cage
from domain.repositories import ICageGroupRepository, ICageRepository
from domain.value_objects import CageName


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
    return CreateCageGroupUseCase(
        group_repository=mock_group_repo,
        cage_repository=mock_cage_repo,
    )


@pytest.mark.asyncio
class TestCreateCageGroup:
    """Tests para la creación de grupos de jaulas."""

    async def test_create_group_successfully(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe crear un grupo exitosamente con datos válidos."""
        # Arrange: Configurar mocks
        cage1 = Cage(name=CageName("Jaula 1"))
        cage2 = Cage(name=CageName("Jaula 2"))

        mock_group_repo.exists_by_name = AsyncMock(return_value=False)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, cage2])
        mock_group_repo.save = AsyncMock()

        request = CreateCageGroupRequest(
            name="Sector Norte",
            cage_ids=[str(cage1.id), str(cage2.id)],
            description="Jaulas del sector norte",
        )

        # Act: Ejecutar caso de uso
        result = await use_case.execute(request)

        # Assert: Verificar resultado
        assert result.name == "Sector Norte"
        assert result.description == "Jaulas del sector norte"
        assert len(result.cage_ids) == 2
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

        # Verificar que se llamaron los métodos correctos
        mock_group_repo.exists_by_name.assert_called_once_with("Sector Norte")
        assert mock_cage_repo.find_by_id.call_count == 2
        mock_group_repo.save.assert_called_once()

    async def test_create_group_with_one_cage(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe crear un grupo con una sola jaula (mínimo permitido)."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))

        mock_group_repo.exists_by_name = AsyncMock(return_value=False)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)
        mock_group_repo.save = AsyncMock()

        request = CreateCageGroupRequest(
            name="Grupo Pequeño",
            cage_ids=[str(cage.id)],
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.name == "Grupo Pequeño"
        assert len(result.cage_ids) == 1
        assert result.description is None

    async def test_create_group_fails_with_duplicate_name(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar si ya existe un grupo con el mismo nombre."""
        # Arrange
        mock_group_repo.exists_by_name = AsyncMock(return_value=True)

        request = CreateCageGroupRequest(
            name="Sector Norte",
            cage_ids=["00000000-0000-0000-0000-000000000001"],
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe un grupo con el nombre"):
            await use_case.execute(request)

        # No debe intentar guardar
        mock_group_repo.save.assert_not_called()

    async def test_create_group_fails_with_nonexistent_cage(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar si alguna jaula no existe."""
        # Arrange
        cage_id = "00000000-0000-0000-0000-000000000001"

        mock_group_repo.exists_by_name = AsyncMock(return_value=False)
        mock_cage_repo.exists = AsyncMock(return_value=False)

        request = CreateCageGroupRequest(
            name="Grupo Test",
            cage_ids=[cage_id],
        )

        # Act & Assert
        with pytest.raises(ValueError, match=f"La jaula con ID '{cage_id}' no existe"):
            await use_case.execute(request)

        # No debe guardar el grupo
        mock_group_repo.save.assert_not_called()

    async def test_create_group_fails_with_empty_name(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar con nombre vacío."""
        # Arrange
        mock_group_repo.exists_by_name = AsyncMock(return_value=False)
        mock_cage_repo.exists = AsyncMock(return_value=True)

        request = CreateCageGroupRequest(
            name="",
            cage_ids=["00000000-0000-0000-0000-000000000001"],
        )

        # Act & Assert
        with pytest.raises(ValueError, match="El nombre del grupo de jaulas no puede estar vacío"):
            await use_case.execute(request)

    async def test_create_group_fails_with_empty_cage_list(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar con lista de jaulas vacía."""
        # Arrange
        mock_group_repo.exists_by_name = AsyncMock(return_value=False)

        request = CreateCageGroupRequest(
            name="Grupo Test",
            cage_ids=[],
        )

        # Act & Assert
        with pytest.raises(ValueError, match="debe contener al menos una jaula"):
            await use_case.execute(request)

    async def test_create_group_with_multiple_cages(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe crear un grupo con múltiples jaulas."""
        # Arrange
        cages = [Cage(name=CageName(f"Jaula {i}")) for i in range(1, 6)]
        cage_ids = [str(c.id) for c in cages]

        mock_group_repo.exists_by_name = AsyncMock(return_value=False)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=cages)
        mock_group_repo.save = AsyncMock()

        request = CreateCageGroupRequest(
            name="Sector Grande",
            cage_ids=cage_ids,
            description="Grupo con 5 jaulas",
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert len(result.cage_ids) == 5
        assert mock_cage_repo.find_by_id.call_count == 5

    async def test_create_group_name_is_case_insensitive(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """La validación de nombre debe ser case-insensitive."""
        # Arrange
        mock_group_repo.exists_by_name = AsyncMock(return_value=True)

        request = CreateCageGroupRequest(
            name="SECTOR NORTE",  # Mayúsculas
            cage_ids=["00000000-0000-0000-0000-000000000001"],
        )

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(request)

        # Verificar que se buscó el nombre como se proporcionó
        mock_group_repo.exists_by_name.assert_called_once_with("SECTOR NORTE")

    async def test_create_group_with_long_description(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe permitir descripciones largas."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        long_description = "A" * 500  # Descripción larga

        mock_group_repo.exists_by_name = AsyncMock(return_value=False)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)
        mock_group_repo.save = AsyncMock()

        request = CreateCageGroupRequest(
            name="Grupo Test",
            cage_ids=[str(cage.id)],
            description=long_description,
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.description == long_description
