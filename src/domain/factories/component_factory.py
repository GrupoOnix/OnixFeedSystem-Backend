"""Factory para creación de componentes de líneas de alimentación."""

from typing import Dict, Any, List

from ..interfaces import IBlower, IDoser, ISelector, ISensor
from ..value_objects import (
    BlowerName, BlowerPowerPercentage, BlowDurationInSeconds,
    DoserName, SiloId, DosingRange, DosingRate,
    SelectorName, SelectorCapacity, SelectorSpeedProfile,
    SensorName
)
from ..enums import SensorType
from ..aggregates.feeding_line.blower import Blower
from ..aggregates.feeding_line.doser import Doser
from ..aggregates.feeding_line.selector import Selector
from ..aggregates.feeding_line.sensor import Sensor


class ComponentFactory:
    """Crea instancias concretas de componentes basándose en su tipo."""

    @staticmethod
    def create_blower(
        blower_type: str,
        name: BlowerName,
        non_feeding_power: BlowerPowerPercentage,
        blow_before_time: BlowDurationInSeconds,
        blow_after_time: BlowDurationInSeconds
    ) -> IBlower:
        
        blower_type_lower = blower_type.lower()
        
        if blower_type_lower == "standard" or blower_type_lower == "blower":
            return Blower(
                name=name,
                non_feeding_power=non_feeding_power,
                blow_before_time=blow_before_time,
                blow_after_time=blow_after_time
            )
        
        # TODO: Extender con VariBlower, TurboBlower, etc.
        
        raise ValueError(f"Tipo de blower no soportado: '{blower_type}'")

    @staticmethod
    def create_doser(
        doser_type: str,
        name: DoserName,
        assigned_silo_id: SiloId,
        dosing_range: DosingRange,
        current_rate: DosingRate
    ) -> IDoser:
        
        doser_type_lower = doser_type.lower()
        
        if doser_type_lower in ["standard", "doser"]:
            return Doser(
                name=name,
                assigned_silo_id=assigned_silo_id,
                doser_type=doser_type,
                dosing_range=dosing_range,
                current_rate=current_rate
            )
        
        # TODO: Extender con VariDoser, PulseDoser, ScrewDoser
        
        raise ValueError(f"Tipo de doser no soportado: '{doser_type}'")

    @staticmethod
    def create_selector(
        selector_type: str,
        name: SelectorName,
        capacity: SelectorCapacity,
        speed_profile: SelectorSpeedProfile
    ) -> ISelector:
        
        selector_type_lower = selector_type.lower()
        
        if selector_type_lower in ["standard", "selector"]:
            return Selector(
                name=name,
                capacity=capacity,
                speed_profile=speed_profile
            )
        
        # TODO: Extender con nuevos tipos de selectoras
        
        raise ValueError(f"Tipo de selector no soportado: '{selector_type}'")

    @staticmethod
    def create_sensor(
        sensor_type: SensorType,
        name: SensorName
    ) -> ISensor:
        
        return Sensor(
            name=name,
            sensor_type=sensor_type
        )
        
        # TODO: Extender con implementaciones específicas por tipo de sensor
