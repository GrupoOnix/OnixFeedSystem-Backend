"""Modelo de base de datos para jaulas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from domain.aggregates.cage import Cage
from domain.enums import CageStatus
from domain.value_objects.cage_configuration import CageConfiguration
from domain.value_objects.identifiers import CageId, UserId
from domain.value_objects.names import CageName


class CageModel(SQLModel, table=True):
    """Modelo SQLModel para jaulas."""

    __tablename__ = "cages"
    __table_args__ = (UniqueConstraint("name", "user_id", name="uq_cages_name_user"),)

    id: UUID = Field(primary_key=True)
    name: str = Field(max_length=100)
    status: str
    user_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True),
    )
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    # Población
    fish_count: int = Field(default=0)
    avg_weight_grams: Optional[float] = Field(default=None)

    # Configuración
    fcr: Optional[float] = Field(default=None)
    volume_m3: Optional[float] = Field(default=None)
    max_density_kg_m3: Optional[float] = Field(default=None)
    transport_time_seconds: Optional[int] = Field(default=None)
    blower_power: Optional[int] = Field(default=None)
    daily_feeding_target_kg: Optional[float] = Field(default=None)

    @staticmethod
    def from_domain(cage: Cage) -> "CageModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return CageModel(
            id=cage.id.value,
            name=str(cage.name),
            status=cage.status.value,
            user_id=cage.user_id.value if cage.user_id else None,
            created_at=cage.created_at,
            # Población
            fish_count=cage.fish_count,
            avg_weight_grams=cage.avg_weight_grams,
            # Configuración
            fcr=cage.config.fcr,
            volume_m3=cage.config.volume_m3,
            max_density_kg_m3=cage.config.max_density_kg_m3,
            transport_time_seconds=cage.config.transport_time_seconds,
            blower_power=cage.config.blower_power,
            daily_feeding_target_kg=cage.config.daily_feeding_target_kg,
        )

    def to_domain(self) -> Cage:
        """Convierte modelo de persistencia a entidad de dominio."""
        config = CageConfiguration(
            fcr=self.fcr,
            volume_m3=self.volume_m3,
            max_density_kg_m3=self.max_density_kg_m3,
            transport_time_seconds=self.transport_time_seconds,
            blower_power=self.blower_power,
            daily_feeding_target_kg=self.daily_feeding_target_kg,
        )

        cage = Cage(
            name=CageName(self.name),
            config=config,
            status=CageStatus(self.status),
        )

        # Reconstruir estado desde BD
        cage._set_id(CageId(self.id))
        cage._set_created_at(self.created_at)
        cage._set_fish_count(self.fish_count)
        cage._set_avg_weight_grams(self.avg_weight_grams)
        if self.user_id:
            cage._user_id = UserId(self.user_id)

        return cage
