"""
Integration tests for DeleteCageGroupUseCase.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.use_cases.cage_group.delete_cage_group import DeleteCageGroupUseCase
from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository
from domain.value_objects import CageGroupId, CageGroupName, CageId


@pytest.fixture
def mock_group_repo():
    """Fixture que proporciona un repositorio mock de grupos de jaulas."""
    repo = MagicMock(spec=ICageGroupRepository)
    return repo


@pytest.fixture
def use_case(mock_group_repo):
    """Fixture que proporciona una instancia del caso de uso."""
    return DeleteCageGroupUseCase(group_repository=mock_group_repo)


@pytest.mark.asyncio
class TestDeleteCageGroup:
    """Tests para la eliminación de grupos de jaulas."""

    async def test_delete_existing_group_successfully(
        self, use_case, mock_group_repo
    ):
        """Debe eliminar un grupo existente exitosamente."""
        # Arrange
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId("00000000-0000-0000-0000-000000000001")],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.delete = AsyncMock()

        # Act
        await use_case.execute(group_id)

        # Assert
        mock_group_repo.find_by_id.assert_called_once_with(CageGroupId(group_id))
        mock_group_repo.delete.assert_called_once_with(CageGroupId(group_id))

    async def test_delete_fails_when_group_not_found(
        self, use_case, mock_group_repo
    ):
        """Debe fallar si el grupo no existe."""
        # Arrange
        group_id = "00000000-0000-0000-0000-000000000001"
        mock_group_repo.find_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(ValueError, match=f"No existe un grupo con ID '{group_id}'"):
            await use_case.execute(group_id)

        # No debe intentar eliminar
        mock_group_repo.delete.assert_not_called()

    async def test_delete_with_invalid_uuid_format(
        self, use_case, mock_group_repo
    ):
        """Debe fallar con UUID inválido."""
        # Arrange
        invalid_id = "not-a-uuid"

        # Act & Assert: El ValueError debe venir de CageGroupId
        with pytest.raises(ValueError):
            await use_case.execute(invalid_id)

    async def test_delete_group_with_multiple_cages(
        self, use_case, mock_group_repo
    ):
        """Debe eliminar grupo que contiene múltiples jaulas."""
        # Arrange
        cage_ids = [CageId(f"00000000-0000-0000-0000-00000000000{i}") for i in range(1, 6)]

        group = CageGroup(
            name=CageGroupName("Sector Grande"),
            cage_ids=cage_ids,
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.delete = AsyncMock()

        # Act
        await use_case.execute(group_id)

        # Assert: Debe eliminar el grupo independientemente de cuántas jaulas tenga
        mock_group_repo.delete.assert_called_once_with(CageGroupId(group_id))

    async def test_delete_is_permanent(
        self, use_case, mock_group_repo
    ):
        """Debe realizar eliminación física (hard delete)."""
        # Arrange
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId("00000000-0000-0000-0000-000000000001")],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.delete = AsyncMock()

        # Act
        await use_case.execute(group_id)

        # Assert: Debe llamar al método delete (hard delete)
        mock_group_repo.delete.assert_called_once()

    async def test_delete_does_not_return_value(
        self, use_case, mock_group_repo
    ):
        """La eliminación no debe retornar ningún valor."""
        # Arrange
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId("00000000-0000-0000-0000-000000000001")],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.delete = AsyncMock()

        # Act
        result = await use_case.execute(group_id)

        # Assert: Debe retornar None
        assert result is None

    async def test_delete_group_with_description(
        self, use_case, mock_group_repo
    ):
        """Debe eliminar grupo que tiene descripción."""
        # Arrange
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId("00000000-0000-0000-0000-000000000001")],
            description="Descripción del grupo",
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.delete = AsyncMock()

        # Act
        await use_case.execute(group_id)

        # Assert
        mock_group_repo.delete.assert_called_once()

    async def test_delete_verifies_existence_before_deleting(
        self, use_case, mock_group_repo
    ):
        """Debe verificar que el grupo existe antes de intentar eliminar."""
        # Arrange
        group_id = "00000000-0000-0000-0000-000000000001"
        mock_group_repo.find_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(ValueError):
            await use_case.execute(group_id)

        # Verificar que find_by_id fue llamado
        mock_group_repo.find_by_id.assert_called_once()

        # Verificar que delete NO fue llamado
        mock_group_repo.delete.assert_not_called()

    async def test_delete_multiple_times_same_id(
        self, use_case, mock_group_repo
    ):
        """Segundo intento de eliminar el mismo ID debe fallar."""
        # Arrange
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId("00000000-0000-0000-0000-000000000001")],
        )
        group_id = str(group.id)

        # Primera vez: encontrar el grupo
        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.delete = AsyncMock()

        # Act: Primera eliminación
        await use_case.execute(group_id)

        # Arrange: Segunda vez el grupo ya no existe
        mock_group_repo.find_by_id = AsyncMock(return_value=None)

        # Act & Assert: Segunda eliminación debe fallar
        with pytest.raises(ValueError, match="No existe un grupo"):
            await use_case.execute(group_id)
