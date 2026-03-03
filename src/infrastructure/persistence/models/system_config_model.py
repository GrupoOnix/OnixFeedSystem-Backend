from datetime import time
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from domain.aggregates.system_config import SystemConfig
from domain.value_objects.identifiers import UserId


class SystemConfigModel(SQLModel, table=True):
    """
    Configuración operativa por usuario.
    Anteriormente singleton (id=1), ahora cada usuario tiene su propia configuración.
    """

    __tablename__ = "system_config"
    __table_args__ = (UniqueConstraint("user_id", name="uq_system_config_user"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    feeding_start_time: time = Field(nullable=False)
    feeding_end_time: time = Field(nullable=False)
    timezone_id: str = Field(max_length=64, nullable=False)
    selector_positioning_time_seconds: int = Field(default=10, nullable=False)
    user_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True),
    )

    @staticmethod
    def from_domain(config: SystemConfig) -> "SystemConfigModel":
        return SystemConfigModel(
            feeding_start_time=config.feeding_start_time,
            feeding_end_time=config.feeding_end_time,
            timezone_id=config.timezone_id,
            selector_positioning_time_seconds=config.selector_positioning_time_seconds,
            user_id=config.user_id.value if config.user_id else None,
        )

    def to_domain(self) -> SystemConfig:
        config = SystemConfig(
            feeding_start_time=self.feeding_start_time,
            feeding_end_time=self.feeding_end_time,
            timezone_id=self.timezone_id,
            selector_positioning_time_seconds=self.selector_positioning_time_seconds,
        )
        if self.user_id:
            config._user_id = UserId(self.user_id)
        return config
