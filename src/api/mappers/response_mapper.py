from typing import List

from api.models.system_layout import (
    SystemLayoutModel,
    SiloConfigModel,
    CageConfigModel,
    FeedingLineConfigModel,
    BlowerConfigModel,
    SensorConfigModel,
    DoserConfigModel,
    SelectorConfigModel,
    SlotAssignmentModel
)
from domain.aggregates.silo import Silo
from domain.aggregates.cage import Cage
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.interfaces import IBlower, IDoser, ISelector, ISensor
from domain.value_objects import SlotAssignment


class ResponseMapper:
    """Convierte entidades de dominio a modelos Pydantic para respuesta API."""

    @staticmethod
    def to_system_layout_model(
        silos: List[Silo],
        cages: List[Cage],
        lines: List[FeedingLine]
    ) -> SystemLayoutModel:
        return SystemLayoutModel(
            silos=[ResponseMapper._to_silo_model(s) for s in silos],
            cages=[ResponseMapper._to_cage_model(c) for c in cages],
            feeding_lines=[ResponseMapper._to_feeding_line_model(l) for l in lines]
        )

    @staticmethod
    def _to_silo_model(silo: Silo) -> SiloConfigModel:
        return SiloConfigModel(
            id=str(silo.id),
            name=str(silo.name),
            capacity=silo.capacity.as_kg
        )

    @staticmethod
    def _to_cage_model(cage: Cage) -> CageConfigModel:
        return CageConfigModel(
            id=str(cage.id),
            name=str(cage.name)
        )

    @staticmethod
    def _to_feeding_line_model(line: FeedingLine) -> FeedingLineConfigModel:
        return FeedingLineConfigModel(
            id=str(line.id),
            line_name=str(line.name),
            blower_config=ResponseMapper._to_blower_model(line.blower),
            sensors_config=[ResponseMapper._to_sensor_model(s) for s in line._sensors],
            dosers_config=[ResponseMapper._to_doser_model(d) for d in line.dosers],
            selector_config=ResponseMapper._to_selector_model(line.selector),
            slot_assignments=[ResponseMapper._to_slot_assignment_model(a) for a in line.get_slot_assignments()]
        )

    @staticmethod
    def _to_blower_model(blower: IBlower) -> BlowerConfigModel:
        blower_type = blower.__class__.__name__.lower()
        if blower_type == "blower":
            blower_type = "standard"
        
        return BlowerConfigModel(
            id=str(blower.id),
            name=str(blower.name),
            blower_type=blower_type,
            non_feeding_power=blower.non_feeding_power.value,
            blow_before_time=blower.blow_before_feeding_time.value,
            blow_after_time=blower.blow_after_feeding_time.value
        )

    @staticmethod
    def _to_sensor_model(sensor: ISensor) -> SensorConfigModel:
        return SensorConfigModel(
            id=str(sensor.id),
            name=str(sensor.name),
            sensor_type=sensor.sensor_type.name
        )

    @staticmethod
    def _to_doser_model(doser: IDoser) -> DoserConfigModel:
        return DoserConfigModel(
            id=str(doser.id),
            name=str(doser.name),
            assigned_silo_id=str(doser.assigned_silo_id),
            doser_type=doser.doser_type.value,
            min_rate=doser.dosing_range.min_rate,
            max_rate=doser.dosing_range.max_rate,
            current_rate=doser.current_rate.value
        )

    @staticmethod
    def _to_selector_model(selector: ISelector) -> SelectorConfigModel:
        selector_type = selector.__class__.__name__.lower()
        if selector_type == "selector":
            selector_type = "standard"
        
        return SelectorConfigModel(
            id=str(selector.id),
            name=str(selector.name),
            selector_type=selector_type,
            capacity=selector.capacity.value,
            fast_speed=selector.speed_profile.fast_speed.value,
            slow_speed=selector.speed_profile.slow_speed.value
        )

    @staticmethod
    def _to_slot_assignment_model(assignment: SlotAssignment) -> SlotAssignmentModel:
        return SlotAssignmentModel(
            slot_number=assignment.slot_number.value,
            cage_id=str(assignment.cage_id)
        )
