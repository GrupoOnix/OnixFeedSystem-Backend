from datetime import datetime
from domain.value_objects import SiloId, SiloName, Weight


class Silo:
    def __init__(self, name: SiloName, capacity: Weight, stock_level: Weight = Weight.zero()):

        if stock_level > capacity:
            raise ValueError("El stock no puede ser mayor que la capacidad.")
        
        self._id = SiloId.generate()
        self._name = name
        self._capacity = capacity
        self._stock_level = stock_level
        self._created_at = datetime.utcnow()

    @property
    def id(self) -> SiloId:
        return self._id
    
    @property
    def name(self) -> SiloName:
        return self._name
    
    @name.setter
    def name(self, new_name: SiloName) -> None:
        self._name = new_name

    @property
    def capacity_kg(self) -> Weight: 
        return self._capacity
    
    @property
    def stock_level_kg(self) -> Weight: 
        return self._stock_level
    
