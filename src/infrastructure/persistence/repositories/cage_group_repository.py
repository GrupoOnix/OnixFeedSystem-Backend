"""Implementación del repositorio de grupos de jaulas."""

import json
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository
from domain.value_objects.identifiers import CageGroupId
from domain.value_objects.names import CageGroupName
from infrastructure.persistence.models.cage_group_model import CageGroupModel


class CageGroupRepository(ICageGroupRepository):
    """Implementación SQLAlchemy del repositorio de grupos de jaulas."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, cage_group: CageGroup) -> None:
        """Guarda o actualiza un grupo de jaulas."""
        existing = await self.session.get(CageGroupModel, cage_group.id.value)

        if existing:
            # Actualizar campos
            existing.name = str(cage_group.name)
            existing.description = cage_group.description
            existing.cage_ids = json.dumps(
                [str(cage_id.value) for cage_id in cage_group.cage_ids]
            )
            existing.updated_at = cage_group.updated_at
        else:
            group_model = CageGroupModel.from_domain(cage_group)
            self.session.add(group_model)

        await self.session.flush()

    async def find_by_id(self, group_id: CageGroupId) -> Optional[CageGroup]:
        """Busca un grupo por su ID."""
        group_model = await self.session.get(CageGroupModel, group_id.value)
        return group_model.to_domain() if group_model else None

    async def find_by_name(self, name: CageGroupName) -> Optional[CageGroup]:
        """Busca un grupo por su nombre."""
        result = await self.session.execute(
            select(CageGroupModel).where(CageGroupModel.name == str(name))
        )
        group_model = result.scalar_one_or_none()
        return group_model.to_domain() if group_model else None

    async def list(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CageGroup]:
        """
        Lista grupos de jaulas con filtros opcionales.

        La búsqueda se realiza en:
        - name (case-insensitive)
        - description (case-insensitive)
        - cage_ids (búsqueda exacta de UUID en el array JSON)
        """
        query = select(CageGroupModel)

        if search:
            search_lower = search.lower()
            # Búsqueda en nombre y descripción
            query = query.where(
                or_(
                    func.lower(CageGroupModel.name).contains(search_lower),
                    func.lower(CageGroupModel.description).contains(search_lower),
                    # Búsqueda en cage_ids (si search es un UUID válido)
                    CageGroupModel.cage_ids.contains(search),
                )
            )

        query = query.order_by(CageGroupModel.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        group_models = result.scalars().all()
        return [model.to_domain() for model in group_models]

    async def count(self, search: Optional[str] = None) -> int:
        """Cuenta total de grupos con filtros opcionales."""
        query = select(func.count()).select_from(CageGroupModel)

        if search:
            search_lower = search.lower()
            query = query.where(
                or_(
                    func.lower(CageGroupModel.name).contains(search_lower),
                    func.lower(CageGroupModel.description).contains(search_lower),
                    CageGroupModel.cage_ids.contains(search),
                )
            )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def delete(self, group_id: CageGroupId) -> None:
        """Elimina un grupo de jaulas (hard delete)."""
        group_model = await self.session.get(CageGroupModel, group_id.value)
        if group_model:
            await self.session.delete(group_model)
            await self.session.flush()

    async def exists_by_name(
        self, name: str, exclude_id: Optional[CageGroupId] = None
    ) -> bool:
        """
        Verifica si existe un grupo con el nombre dado (case-insensitive).

        Args:
            name: Nombre a buscar
            exclude_id: ID de grupo a excluir (útil para updates)

        Returns:
            True si existe un grupo con ese nombre, False en caso contrario
        """
        query = select(CageGroupModel).where(func.lower(CageGroupModel.name) == name.lower())

        if exclude_id:
            query = query.where(CageGroupModel.id != exclude_id.value)

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
