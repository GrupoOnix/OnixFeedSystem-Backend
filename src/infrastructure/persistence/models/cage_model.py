from datetime import datetime
from uuid import UUID
from sqlmodel import Field, SQLModel
from domain.aggregates.cage import Cage
from domain.enums import CageStatus
from domain.value_objects import CageId, CageName


class CageModel(SQLModel, table=True):
    __tablename__ = "cages"

    id: UUID = Field(primary_key=True)
    name: str = Field(unique=True, max_length=100)
    status: str
    created_at: datetime

    @staticmethod
    def from_domain(cage: Cage) -> "CageModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return CageModel(
            id=cage.id.value,
            name=str(cage.name),
            status=cage.status.value,
            created_at=cage._created_at,
        )

    def to_domain(self) -> Cage:
        """Convierte modelo de persistencia a entidad de dominio."""
        cage = Cage(
            name=CageName(self.name),
            status=CageStatus(self.status),
        )
        cage._id = CageId(self.id)
        cage._created_at = self.created_at
        return cage
