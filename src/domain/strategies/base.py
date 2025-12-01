from abc import ABC, abstractmethod
from typing import List
from domain.dtos import MachineConfiguration

class IFeedingStrategy(ABC):
    """
    Define la lógica para calcular los parámetros de alimentación
    según el modo (Manual, Cíclico, Programado).
    """

    @abstractmethod
    def get_plc_configuration(self) -> MachineConfiguration:
        """
        Genera la configuración técnica para el PLC.
        
        La estrategia debe conocer internamente qué jaulas/slots alimentar.
        Esto permite alimentar una o múltiples jaulas en secuencia.
        
        Returns:
            DTO listo para ser enviado a IFeedingMachine, incluyendo
            la lista de slots a alimentar en orden.
        """
        pass