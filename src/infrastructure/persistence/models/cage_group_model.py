"""Modelo de base de datos para grupos de jaulas."""

import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from domain.aggregates.cage_group import CageGroup
from domain.value_objects.identifiers import CageGroupId, CageId
from domain.value_objects.names import CageGroupName


class CageGroupModel(SQLModel, table=True):
    """Modelo SQLModel para grupos de jaulas."""

    __tablename__ = "cage_groups"

    id: UUID = Field(primary_key=True)
    name: str = Field(unique=True, max_length=255)
    description: Optional[str] = Field(default=None)
    cage_ids: str = Field()  # JSON array serializado como string
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(cage_group: CageGroup) -> "CageGroupModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        # Serializar lista de CageId a JSON string
        cage_ids_str = json.dumps(
            [str(cage_id.value) for cage_id in cage_group.cage_ids]
        )

        return CageGroupModel(
            id=cage_group.id.value,
            name=str(cage_group.name),
            description=cage_group.description,
            cage_ids=cage_ids_str,
            created_at=cage_group.created_at,
            updated_at=cage_group.updated_at,
        )

    def to_domain(self) -> CageGroup:
        """Convierte modelo de persistencia a entidad de dominio."""
        # Deserializar JSON string a lista de CageId
        cage_ids_list: List[str] = json.loads(self.cage_ids)
        cage_id_objects = [CageId.from_string(id_str) for id_str in cage_ids_list]

        cage_group = CageGroup(
            name=CageGroupName(self.name),
            cage_ids=cage_id_objects,
            description=self.description,
        )

        # Reconstruir estado desde BD
        cage_group._set_id(CageGroupId(self.id))
        cage_group._set_created_at(self.created_at)
        cage_group._set_updated_at(self.updated_at)

        return cage_group
