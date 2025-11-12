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
    SlotAssignmentModel,
)
from application.dtos import (
    SystemLayoutDTO,
    SiloConfigDTO,
    CageConfigDTO,
    FeedingLineConfigDTO,
    BlowerConfigDTO,
    SensorConfigDTO,
    DoserConfigDTO,
    SelectorConfigDTO,
    SlotAssignmentDTO,
)


class SystemLayoutMapper:
    
    @staticmethod
    def to_app_dto(api_model: SystemLayoutModel) -> SystemLayoutDTO:
        """Convierte modelo API a DTO de aplicación."""
        return SystemLayoutDTO(
            silos=[
                SystemLayoutMapper._to_silo_dto(silo)
                for silo in api_model.silos
            ],
            cages=[
                SystemLayoutMapper._to_cage_dto(cage)
                for cage in api_model.cages
            ],
            feeding_lines=[
                SystemLayoutMapper._to_feeding_line_dto(line)
                for line in api_model.feeding_lines
            ],
            presentation_data=api_model.presentation_data.model_dump()
        )
    
    @staticmethod
    def _to_silo_dto(model: SiloConfigModel) -> SiloConfigDTO:
        """Convierte SiloConfigModel a SiloConfigDTO."""
        return SiloConfigDTO(
            id=model.id,
            name=model.name,
            capacity=model.capacity
        )
    
    @staticmethod
    def _to_cage_dto(model: CageConfigModel) -> CageConfigDTO:
        """Convierte CageConfigModel a CageConfigDTO."""
        return CageConfigDTO(
            id=model.id,
            name=model.name
        )
    
    @staticmethod
    def _to_feeding_line_dto(model: FeedingLineConfigModel) -> FeedingLineConfigDTO:
        """Convierte FeedingLineConfigModel a FeedingLineConfigDTO."""
        return FeedingLineConfigDTO(
            id=model.id,
            line_name=model.line_name,
            blower_config=SystemLayoutMapper._to_blower_dto(model.blower_config),
            sensors_config=[
                SystemLayoutMapper._to_sensor_dto(sensor)
                for sensor in model.sensors_config
            ],
            dosers_config=[
                SystemLayoutMapper._to_doser_dto(doser)
                for doser in model.dosers_config
            ],
            selector_config=SystemLayoutMapper._to_selector_dto(model.selector_config),
            slot_assignments=[
                SystemLayoutMapper._to_slot_assignment_dto(assignment)
                for assignment in model.slot_assignments
            ]
        )
    
    @staticmethod
    def _to_blower_dto(model: BlowerConfigModel) -> BlowerConfigDTO:
        """Convierte BlowerConfigModel a BlowerConfigDTO."""
        return BlowerConfigDTO(
            id=model.id,
            name=model.name,
            non_feeding_power=model.non_feeding_power,
            blow_before_time=model.blow_before_time,
            blow_after_time=model.blow_after_time
        )
    
    @staticmethod
    def _to_sensor_dto(model: SensorConfigModel) -> SensorConfigDTO:
        """Convierte SensorConfigModel a SensorConfigDTO."""
        return SensorConfigDTO(
            id=model.id,
            name=model.name,
            sensor_type=model.sensor_type
        )
    
    @staticmethod
    def _to_doser_dto(model: DoserConfigModel) -> DoserConfigDTO:
        """Convierte DoserConfigModel a DoserConfigDTO."""
        return DoserConfigDTO(
            id=model.id,
            name=model.name,
            assigned_silo_id=model.assigned_silo_id,
            doser_type=model.doser_type,
            min_rate=model.min_rate,
            max_rate=model.max_rate,
            current_rate=model.current_rate
        )
    
    @staticmethod
    def _to_selector_dto(model: SelectorConfigModel) -> SelectorConfigDTO:
        """Convierte SelectorConfigModel a SelectorConfigDTO."""
        return SelectorConfigDTO(
            id=model.id,
            name=model.name,
            capacity=model.capacity,
            fast_speed=model.fast_speed,
            slow_speed=model.slow_speed
        )
    
    @staticmethod
    def _to_slot_assignment_dto(model: SlotAssignmentModel) -> SlotAssignmentDTO:
        """Convierte SlotAssignmentModel a SlotAssignmentDTO."""
        return SlotAssignmentDTO(
            slot_number=model.slot_number,
            cage_id=model.cage_id
        )
    

    @staticmethod
    def to_api_model(app_dto: SystemLayoutDTO) -> SystemLayoutModel:
        """Convierte DTO de aplicación a modelo API."""
        from api.models.system_layout import PresentationDataModel
        
        return SystemLayoutModel(
            silos=[
                SiloConfigModel(
                    id=silo.id,
                    name=silo.name,
                    capacity=silo.capacity
                )
                for silo in app_dto.silos
            ],
            cages=[
                CageConfigModel(
                    id=cage.id,
                    name=cage.name
                )
                for cage in app_dto.cages
            ],
            feeding_lines=[
                SystemLayoutMapper._to_feeding_line_model(line)
                for line in app_dto.feeding_lines
            ],
            presentation_data=PresentationDataModel(**app_dto.presentation_data)
        )
    
    @staticmethod
    def _to_feeding_line_model(dto: FeedingLineConfigDTO) -> FeedingLineConfigModel:
        """Convierte FeedingLineConfigDTO a FeedingLineConfigModel."""
        return FeedingLineConfigModel(
            id=dto.id,
            line_name=dto.line_name,
            blower_config=BlowerConfigModel(
                id=dto.blower_config.id,
                name=dto.blower_config.name,
                non_feeding_power=dto.blower_config.non_feeding_power,
                blow_before_time=dto.blower_config.blow_before_time,
                blow_after_time=dto.blower_config.blow_after_time
            ),
            sensors_config=[
                SensorConfigModel(
                    id=sensor.id,
                    name=sensor.name,
                    sensor_type=sensor.sensor_type
                )
                for sensor in dto.sensors_config
            ],
            dosers_config=[
                DoserConfigModel(
                    id=doser.id,
                    name=doser.name,
                    assigned_silo_id=doser.assigned_silo_id,
                    doser_type=doser.doser_type,
                    min_rate=doser.min_rate,
                    max_rate=doser.max_rate,
                    current_rate=doser.current_rate
                )
                for doser in dto.dosers_config
            ],
            selector_config=SelectorConfigModel(
                id=dto.selector_config.id,
                name=dto.selector_config.name,
                capacity=dto.selector_config.capacity,
                fast_speed=dto.selector_config.fast_speed,
                slow_speed=dto.selector_config.slow_speed
            ),
            slot_assignments=[
                SlotAssignmentModel(
                    slot_number=assignment.slot_number,
                    cage_id=assignment.cage_id
                )
                for assignment in dto.slot_assignments
            ]
        )
