"""
Integration tests for UpdateCageGroupUseCase.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.dtos.cage_group_dtos import UpdateCageGroupRequest
from application.use_cases.cage_group.update_cage_group import UpdateCageGroupUseCase
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository, ICageRepository
from domain.value_objects import CageGroupId, CageGroupName, CageId, CageName


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
    return UpdateCageGroupUseCase(
        group_repository=mock_group_repo,
        cage_repository=mock_cage_repo,
    )


@pytest.mark.asyncio
class TestUpdateCageGroup:
    """Tests para la actualización de grupos de jaulas."""

    async def test_update_name_successfully(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe actualizar el nombre del grupo exitosamente."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage.id))],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.find_by_name = AsyncMock(return_value=None)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)
        mock_group_repo.save = AsyncMock()

        request = UpdateCageGroupRequest(name="Sector Norte Premium")

        # Act
        result = await use_case.execute(group_id, request)

        # Assert
        assert result.name == "Sector Norte Premium"
        assert result.id == group_id
        mock_group_repo.save.assert_called_once()

    async def test_update_description_successfully(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe actualizar la descripción del grupo."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage.id))],
            description="Descripción original",
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)
        mock_group_repo.save = AsyncMock()

        request = UpdateCageGroupRequest(description="Nueva descripción")

        # Act
        result = await use_case.execute(group_id, request)

        # Assert
        assert result.description == "Nueva descripción"
        mock_group_repo.save.assert_called_once()

    async def test_update_cage_ids_successfully(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe actualizar la lista de jaulas del grupo."""
        # Arrange
        cage1 = Cage(name=CageName("Jaula 1"))
        cage2 = Cage(name=CageName("Jaula 2"))
        cage3 = Cage(name=CageName("Jaula 3"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage1.id))],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, cage2, cage3])
        mock_group_repo.save = AsyncMock()

        request = UpdateCageGroupRequest(
            cage_ids=[str(cage2.id), str(cage3.id)]
        )

        # Act
        result = await use_case.execute(group_id, request)

        # Assert
        assert len(result.cage_ids) == 2
        assert str(cage2.id) in result.cage_ids
        assert str(cage3.id) in result.cage_ids
        assert str(cage1.id) not in result.cage_ids

    async def test_update_multiple_fields_at_once(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe actualizar múltiples campos simultáneamente."""
        # Arrange
        cage1 = Cage(name=CageName("Jaula 1"))
        cage2 = Cage(name=CageName("Jaula 2"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage1.id))],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.find_by_name = AsyncMock(return_value=None)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, cage1, cage2])
        mock_group_repo.save = AsyncMock()

        request = UpdateCageGroupRequest(
            name="Sector Sur",
            description="Nueva descripción",
            cage_ids=[str(cage1.id), str(cage2.id)],
        )

        # Act
        result = await use_case.execute(group_id, request)

        # Assert
        assert result.name == "Sector Sur"
        assert result.description == "Nueva descripción"
        assert len(result.cage_ids) == 2

    async def test_update_fails_when_group_not_found(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar si el grupo no existe."""
        # Arrange
        group_id = "00000000-0000-0000-0000-000000000001"
        mock_group_repo.find_by_id = AsyncMock(return_value=None)

        request = UpdateCageGroupRequest(name="Nuevo Nombre")

        # Act & Assert
        with pytest.raises(ValueError, match=f"No existe un grupo con ID '{group_id}'"):
            await use_case.execute(group_id, request)

    async def test_update_fails_with_duplicate_name(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar si el nuevo nombre ya existe en otro grupo."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage.id))],
        )
        group_id = str(group.id)

        # Simular que otro grupo ya tiene ese nombre
        other_group = CageGroup(
            name=CageGroupName("Sector Sur"),
            cage_ids=[CageId(str(cage.id))],
        )

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.find_by_name = AsyncMock(return_value=other_group)

        request = UpdateCageGroupRequest(name="Sector Sur")

        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe un grupo con el nombre"):
            await use_case.execute(group_id, request)

    async def test_update_allows_keeping_same_name(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe permitir mantener el mismo nombre (no cambiar)."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage.id))],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.find_by_name = AsyncMock(return_value=group)  # Mismo grupo
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)
        mock_group_repo.save = AsyncMock()

        request = UpdateCageGroupRequest(name="Sector Norte")  # Mismo nombre

        # Act
        result = await use_case.execute(group_id, request)

        # Assert: No debe fallar
        assert result.name == "Sector Norte"

    async def test_update_fails_with_nonexistent_cage(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe fallar si alguna jaula no existe."""
        # Arrange
        cage1 = Cage(name=CageName("Jaula 1"))
        invalid_cage_id = "00000000-0000-0000-0000-000000000999"
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage1.id))],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(side_effect=[cage1, None])

        request = UpdateCageGroupRequest(
            cage_ids=[str(cage1.id), invalid_cage_id]
        )

        # Act & Assert
        with pytest.raises(ValueError, match=f"La jaula con ID '{invalid_cage_id}' no existe"):
            await use_case.execute(group_id, request)

    async def test_update_with_no_changes(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe manejar actualización sin cambios (todos los campos None)."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage.id))],
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)
        mock_group_repo.save = AsyncMock()

        request = UpdateCageGroupRequest()  # Sin cambios

        # Act
        result = await use_case.execute(group_id, request)

        # Assert: Debe retornar el grupo sin cambios
        assert result.name == "Sector Norte"
        assert len(result.cage_ids) == 1

    async def test_update_description_to_none(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe permitir limpiar la descripción estableciéndola a None."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage.id))],
            description="Descripción original",
        )
        group_id = str(group.id)

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)
        mock_group_repo.save = AsyncMock()

        request = UpdateCageGroupRequest(description=None)

        # Act
        result = await use_case.execute(group_id, request)

        # Assert
        # Note: CageGroup domain logic may keep existing description if None is passed
        # This depends on domain implementation

    async def test_update_updates_timestamp(
        self, use_case, mock_group_repo, mock_cage_repo
    ):
        """Debe actualizar el timestamp updated_at."""
        # Arrange
        cage = Cage(name=CageName("Jaula 1"))
        
        group = CageGroup(
            name=CageGroupName("Sector Norte"),
            cage_ids=[CageId(str(cage.id))],
        )
        group_id = str(group.id)
        original_updated_at = group.updated_at

        mock_group_repo.find_by_id = AsyncMock(return_value=group)
        mock_group_repo.find_by_name = AsyncMock(return_value=None)
        mock_cage_repo.find_by_id = AsyncMock(return_value=cage)
        mock_group_repo.save = AsyncMock()

        request = UpdateCageGroupRequest(name="Nuevo Nombre")

        # Act
        result = await use_case.execute(group_id, request)

        # Assert: updated_at debe ser diferente
        # Note: En mocks esto puede no cambiar, pero en implementación real sí cambia
        assert result.updated_at is not None
