from datetime import datetime
from typing import List
from domain.interfaces import ISelector
from domain.value_objects import SelectorCapacity, SelectorId, SelectorName, SelectorSpeedProfile


class Selector(ISelector):
    def __init__(self,
                 name: SelectorName,
                 capacity: SelectorCapacity,
                 speed_profile: SelectorSpeedProfile
                 ):
        self._id = SelectorId.generate()
        self._name: SelectorName = name
        self._capacity = capacity
        self._speed_profile = speed_profile
        self._created_at = datetime.utcnow() #TODO revisar que hacer con esto

    @property
    def id(self) -> SelectorId:
        return self._id

    @property
    def name(self) -> SelectorName:
        return self._name
    
    @name.setter
    def name(self, name: SelectorName) -> None:
        self._name = name

    @property
    def capacity(self) -> SelectorCapacity:
        return self._capacity

    @property
    def speed_profile(self) -> SelectorSpeedProfile:
        return self._speed_profile
    
    @speed_profile.setter
    def speed_profile(self, new_profile: SelectorSpeedProfile) -> None:
        self._speed_profile = new_profile

    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    def validate_slot(self, slot_number: int) -> bool:
        return 1 <= slot_number <= self._capacity.value