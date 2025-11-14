from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlmodel import Field, Relationship, SQLModel
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.value_objects import LineId, LineName


class FeedingLineModel(SQLModel, table=True):
    __tablename__ = "feeding_lines"

    id: UUID = Field(primary_key=True)
    name: str = Field(unique=True, max_length=100)
    created_at: datetime

    blower: Optional["BlowerModel"] = Relationship(
        back_populates="feeding_line",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    dosers: List["DoserModel"] = Relationship(
        back_populates="feeding_line",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    selector: Optional["SelectorModel"] = Relationship(
        back_populates="feeding_line",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    sensors: List["SensorModel"] = Relationship(
        back_populates="feeding_line",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    slot_assignments: List["SlotAssignmentModel"] = Relationship(
        back_populates="feeding_line",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    @staticmethod
    def from_domain(line: FeedingLine) -> "FeedingLineModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        from .blower_model import BlowerModel
        from .doser_model import DoserModel
        from .selector_model import SelectorModel
        from .sensor_model import SensorModel
        from .slot_assignment_model import SlotAssignmentModel

        line_model = FeedingLineModel(
            id=line.id.value,
            name=str(line.name),
            created_at=line._created_at,
        )

        if line._blower:
            line_model.blower = BlowerModel.from_domain(line._blower, line.id.value)

        line_model.dosers = [
            DoserModel.from_domain(doser, line.id.value) for doser in line.dosers
        ]

        if line._selector:
            line_model.selector = SelectorModel.from_domain(
                line._selector, line.id.value
            )

        line_model.sensors = [
            SensorModel.from_domain(sensor, line.id.value) for sensor in line._sensors
        ]

        line_model.slot_assignments = [
            SlotAssignmentModel.from_domain(assignment, line.id.value)
            for assignment in line.get_slot_assignments()
        ]

        return line_model

    def to_domain(self) -> FeedingLine:
        """Convierte modelo de persistencia a entidad de dominio."""
        from domain.aggregates.feeding_line.blower import Blower
        from domain.aggregates.feeding_line.doser import Doser
        from domain.aggregates.feeding_line.selector import Selector
        from domain.aggregates.feeding_line.sensor import Sensor

        if not self.blower or not self.selector:
            raise ValueError(
                "FeedingLine debe tener blower y selector para reconstruir el dominio"
            )

        blower_domain = self.blower.to_domain()
        dosers_domain = [doser.to_domain() for doser in self.dosers]
        selector_domain = self.selector.to_domain()
        sensors_domain = [sensor.to_domain() for sensor in self.sensors]

        line = FeedingLine.create(
            name=LineName(self.name),
            blower=blower_domain,
            dosers=dosers_domain,
            selector=selector_domain,
            sensors=sensors_domain,
        )

        line._id = LineId(self.id)
        line._created_at = self.created_at

        slot_assignments_domain = [
            assignment.to_domain() for assignment in self.slot_assignments
        ]
        line.update_assignments(slot_assignments_domain)

        return line
