from uuid import UUID
from sqlmodel import Field, Relationship, SQLModel
from domain.aggregates.feeding_line.sensor import Sensor
from domain.enums import SensorType
from domain.interfaces import ISensor
from domain.value_objects import SensorId, SensorName


class SensorModel(SQLModel, table=True):
    __tablename__ = "sensors"

    id: UUID = Field(primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    sensor_type: str

    feeding_line: "FeedingLineModel" = Relationship(back_populates="sensors")

    @staticmethod
    def from_domain(sensor: ISensor, line_id: UUID) -> "SensorModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return SensorModel(
            id=sensor.id.value,
            line_id=line_id,
            name=str(sensor.name),
            sensor_type=sensor.sensor_type.value,
        )

    def to_domain(self) -> Sensor:
        """Convierte modelo de persistencia a entidad de dominio."""
        sensor = Sensor(
            name=SensorName(self.name), sensor_type=SensorType(self.sensor_type)
        )
        sensor._id = SensorId(self.id)
        return sensor
