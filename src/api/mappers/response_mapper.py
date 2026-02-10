from typing import Dict, List

from api.models.system_layout import (
    BlowerConfigModel,
    CageConfigModel,
    CoolerConfigModel,
    DoserConfigModel,
    FeedingLineConfigModel,
    SelectorConfigModel,
    SensorConfigModel,
    SiloConfigModel,
    SlotAssignmentModel,
    SystemLayoutModel,
)
from domain.aggregates.cage import Cage
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.aggregates.silo import Silo
from domain.entities.slot_assignment import SlotAssignment
from domain.interfaces import IBlower, ICooler, IDoser, ISelector, ISensor
from domain.value_objects import LineId


class ResponseMapper:
    """Convierte entidades de dominio a modelos Pydantic para respuesta API."""

    @staticmethod
    def to_system_layout_model(
        silos: List[Silo],
        cages: List[Cage],
        lines: List[FeedingLine],
        slot_assignments_by_line: Dict[LineId, List[SlotAssignment]],
    ) -> SystemLayoutModel:
        return SystemLayoutModel(
            silos=[ResponseMapper._to_silo_model(s) for s in silos],
            cages=[ResponseMapper._to_cage_model(c) for c in cages],
            feeding_lines=[
                ResponseMapper._to_feeding_line_model(
                    line, slot_assignments_by_line.get(line.id, [])
                )
                for line in lines
            ],
        )

    @staticmethod
    def _to_silo_model(silo: Silo) -> SiloConfigModel:
        return SiloConfigModel(
            id=str(silo.id),
            name=str(silo.name),
            capacity=silo.capacity.as_kg,
            food_id=str(silo.food_id) if silo.food_id else None,
            stock_level=silo.stock_level.as_kg,
        )

    @staticmethod
    def _to_cage_model(cage: Cage) -> CageConfigModel:
        return CageConfigModel(id=str(cage.id), name=str(cage.name))

    @staticmethod
    def _to_feeding_line_model(
        line: FeedingLine, slot_assignments: List[SlotAssignment]
    ) -> FeedingLineConfigModel:
        # Ordenar por slot_number para consistencia
        sorted_assignments = sorted(slot_assignments, key=lambda a: a.slot_number)

        return FeedingLineConfigModel(
            id=str(line.id),
            line_name=str(line.name),
            blower_config=ResponseMapper._to_blower_model(line.blower),
            cooler_config=ResponseMapper._to_cooler_model(line.cooler)
            if line.cooler
            else None,
            sensors_config=[ResponseMapper._to_sensor_model(s) for s in line._sensors],
            dosers_config=[ResponseMapper._to_doser_model(d) for d in line.dosers],
            selector_config=ResponseMapper._to_selector_model(line.selector),
            slot_assignments=[
                ResponseMapper._to_slot_assignment_model(assignment)
                for assignment in sorted_assignments
            ],
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
            blow_after_time=blower.blow_after_feeding_time.value,
        )

    @staticmethod
    def _to_cooler_model(cooler: ICooler) -> CoolerConfigModel:
        """Mapea entidad Cooler a CoolerConfigModel para respuesta API."""
        return CoolerConfigModel(
            id=str(cooler.id),
            name=str(cooler.name),
            cooling_power_percentage=cooler.cooling_power_percentage.value,
            is_on=cooler.is_on,
        )

    @staticmethod
    def _to_sensor_model(sensor: ISensor) -> SensorConfigModel:
        return SensorConfigModel(
            id=str(sensor.id),
            name=str(sensor.name),
            sensor_type=sensor.sensor_type.name,
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
            current_rate=doser.current_rate.value,
            speed_percentage=doser.speed_percentage,
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
            slow_speed=selector.speed_profile.slow_speed.value,
        )

    @staticmethod
    def _to_slot_assignment_model(assignment: SlotAssignment) -> SlotAssignmentModel:
        """Mapea SlotAssignment a SlotAssignmentModel para respuesta API."""
        return SlotAssignmentModel(
            slot_number=assignment.slot_number,
            cage_id=str(assignment.cage_id),
        )
