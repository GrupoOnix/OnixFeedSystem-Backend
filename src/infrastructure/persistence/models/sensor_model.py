from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from domain.enums import SensorType
from domain.value_objects import SensorId, SensorName

if TYPE_CHECKING:
    from domain.aggregates.feeding_line.sensor import Sensor
    from domain.interfaces import ISensor


class SensorModel(SQLModel, table=True):
    __tablename__ = "sensors"

    id: UUID = Field(primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    sensor_type: str
    is_enabled: bool = Field(default=True)
    warning_threshold: Optional[float] = Field(default=None)
    critical_threshold: Optional[float] = Field(default=None)

    feeding_line: "FeedingLineModel" = Relationship(back_populates="sensors")

    @staticmethod
    def from_domain(sensor: "ISensor", line_id: UUID) -> "SensorModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return SensorModel(
            id=sensor.id.value,
            line_id=line_id,
            name=str(sensor.name),
            sensor_type=sensor.sensor_type.value,
            is_enabled=sensor.is_enabled,
            warning_threshold=sensor.warning_threshold,
            critical_threshold=sensor.critical_threshold,
        )

    def to_domain(self) -> "Sensor":
        """Convierte modelo de persistencia a entidad de dominio."""
        # Import local para evitar circular imports pero tenerlo disponible en runtime
        from domain.aggregates.feeding_line.sensor import Sensor

        sensor = Sensor(
            name=SensorName(self.name),
            sensor_type=SensorType(self.sensor_type),
            is_enabled=self.is_enabled,
            warning_threshold=self.warning_threshold,
            critical_threshold=self.critical_threshold,
        )
        sensor._id = SensorId(self.id)
        return sensor
