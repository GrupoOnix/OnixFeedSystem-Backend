from typing import List
from domain.strategies.base import IFeedingStrategy
from domain.dtos import MachineConfiguration
from domain.enums import FeedingMode

class ManualFeedingStrategy(IFeedingStrategy):
    """
    Estrategia para alimentación manual.
    
    Características:
    - Se enfoca en UNA sola jaula/slot a la vez.
    - No tiene límite de cantidad (target_amount = 0.0 o infinito).
    - Depende del operador para detenerse.
    """

    def __init__(self, target_slot: int, blower_speed: float, doser_speed: float, target_amount_kg: float):
        """
        Args:
            target_slot: El número físico del slot a alimentar.
            blower_speed: La velocidad deseada del soplador (0-100%).
            doser_speed: La velocidad deseada del dosificador (0-100%).
            target_amount_kg: Cantidad objetivo en kg (0.0 para infinito/manual puro).
        """
        self.target_slot = target_slot
        self.blower_speed = blower_speed
        self.doser_speed = doser_speed
        self.target_amount_kg = target_amount_kg

    def get_plc_configuration(self) -> MachineConfiguration:
        return MachineConfiguration(
            start_command=True,
            mode=FeedingMode.MANUAL,
            
            # En manual, la lista es de un solo elemento
            slot_numbers=[self.target_slot],
            
            blower_speed_percentage=self.blower_speed,
            doser_speed_percentage=self.doser_speed,
            
            # Meta de alimentación
            target_amount_kg=self.target_amount_kg,
            
            # Parámetros cíclicos no aplican
            batch_amount_kg=0.0,
            pause_time_seconds=0
        )