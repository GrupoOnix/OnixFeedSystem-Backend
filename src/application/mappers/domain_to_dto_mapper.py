from application.dtos import (
    SiloConfigDTO,
    CageConfigDTO,
    FeedingLineConfigDTO,
    BlowerConfigDTO,
    SensorConfigDTO,
    DoserConfigDTO,
    SelectorConfigDTO,
    SlotAssignmentDTO
)
from domain.aggregates.silo import Silo
from domain.aggregates.cage import Cage
from domain.aggregates.feeding_line.feeding_line import FeedingLine


class DomainToDTOMapper:

    @staticmethod
    def silo_to_dto(silo: Silo) -> SiloConfigDTO:
        """Convierte una entidad Silo a DTO."""
        return SiloConfigDTO(
            id=str(silo.id),
            name=str(silo.name),
            capacity=silo.capacity.as_kg
        )

    @staticmethod
    def cage_to_dto(cage: Cage) -> CageConfigDTO:
        """Convierte una entidad Cage a DTO."""
        return CageConfigDTO(
            id=str(cage.id),
            name=str(cage.name)
        )

    @staticmethod
    def feeding_line_to_dto(line: FeedingLine) -> FeedingLineConfigDTO:

        return FeedingLineConfigDTO(
            id=str(line.id),
            line_name=str(line.name),
            blower_config=BlowerConfigDTO(
                id=str(line.blower.id),
                name=str(line.blower.name),
                non_feeding_power=line.blower.non_feeding_power.value,
                blow_before_time=line.blower.blow_before_feeding_time.value,
                blow_after_time=line.blower.blow_after_feeding_time.value
            ),
            sensors_config=[
                SensorConfigDTO(
                    id=str(sensor.id),
                    name=str(sensor.name),
                    sensor_type=sensor.sensor_type.name
                )
                for sensor in line._sensors
            ],
            dosers_config=[
                DoserConfigDTO(
                    id=str(doser.id),
                    name=str(doser.name),
                    assigned_silo_id=str(doser.assigned_silo_id),
                    doser_type=doser.doser_type,
                    min_rate=doser.dosing_range.min_rate,
                    max_rate=doser.dosing_range.max_rate,
                    current_rate=doser.current_rate.value
                )
                for doser in line.dosers
            ],
            selector_config=SelectorConfigDTO(
                id=str(line.selector.id),
                name=str(line.selector.name),
                capacity=line.selector.capacity.value,
                fast_speed=line.selector.speed_profile.fast_speed.value,
                slow_speed=line.selector.speed_profile.slow_speed.value
            ),
            slot_assignments=[
                SlotAssignmentDTO(
                    slot_number=assignment.slot_number.value,
                    cage_id=str(assignment.cage_id)
                )
                for assignment in line.get_slot_assignments()
            ]
        )
