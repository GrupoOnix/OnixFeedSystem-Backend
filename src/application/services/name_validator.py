from typing import Optional

from domain.repositories import ISiloRepository, ICageRepository, IFeedingLineRepository
from domain.value_objects import SiloId, SiloName, CageId, CageName, LineId, LineName
from domain.value_objects.identifiers import UserId
from domain.exceptions import DuplicateLineNameException


class NameValidator:
    """Valida unicidad de nombres en agregados."""

    @staticmethod
    async def validate_unique_silo_name(
        name: str,
        exclude_id: Optional[SiloId],
        repo: ISiloRepository,
        user_id: UserId,
    ) -> None:
        """Valida que el nombre del silo sea único."""
        existing = await repo.find_by_name(SiloName(name), user_id)
        if existing and existing.id != exclude_id:
            raise DuplicateLineNameException(f"Ya existe un silo con el nombre '{name}'")

    @staticmethod
    async def validate_unique_cage_name(
        name: str,
        exclude_id: Optional[CageId],
        repo: ICageRepository,
        user_id: UserId,
    ) -> None:
        """Valida que el nombre de la jaula sea único."""
        existing = await repo.find_by_name(CageName(name), user_id)
        if existing and existing.id != exclude_id:
            raise DuplicateLineNameException(f"Ya existe una jaula con el nombre '{name}'")

    @staticmethod
    async def validate_unique_line_name(
        name: str,
        exclude_id: Optional[LineId],
        repo: IFeedingLineRepository,
        user_id: UserId,
    ) -> None:
        """Valida que el nombre de la línea sea único."""
        existing = await repo.find_by_name(LineName(name), user_id)
        if existing and existing.id != exclude_id:
            raise DuplicateLineNameException(f"Ya existe una línea con el nombre '{name}'")
