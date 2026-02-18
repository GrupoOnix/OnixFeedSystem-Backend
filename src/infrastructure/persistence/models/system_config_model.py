
from datetime import time

from sqlmodel import Field, SQLModel

from domain.aggregates.system_config import SystemConfig


class SystemConfigModel(SQLModel, table=True):
    """
    Registro singleton que almacena la configuración operativa global.
    Siempre existe un único registro con id=1.
    """

    __tablename__ = "system_config"

    id: int = Field(default=1, primary_key=True)
    feeding_start_time: time = Field(nullable=False)
    feeding_end_time: time = Field(nullable=False)
    timezone_id: str = Field(max_length=64, nullable=False)

    @staticmethod
    def from_domain(config: SystemConfig) -> "SystemConfigModel":
        return SystemConfigModel(
            id=config.id,
            feeding_start_time=config.feeding_start_time,
            feeding_end_time=config.feeding_end_time,
            timezone_id=config.timezone_id,
        )

    def to_domain(self) -> SystemConfig:
        return SystemConfig(
            feeding_start_time=self.feeding_start_time,
            feeding_end_time=self.feeding_end_time,
            timezone_id=self.timezone_id,
        )
