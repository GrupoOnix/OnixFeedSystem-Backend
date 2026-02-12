"""Casos de uso para control directo de devices."""

from .move_selector_to_slot import MoveSelectorToSlotDirectUseCase
from .reset_selector import ResetSelectorDirectUseCase
from .set_blower_power import SetBlowerPowerUseCase
from .set_cooler_power import SetCoolerPowerUseCase
from .set_doser_rate import SetDoserRateUseCase
from .set_doser_speed import SetDoserSpeedUseCase
from .turn_blower_on_off import TurnBlowerOffUseCase, TurnBlowerOnUseCase
from .turn_cooler_on_off import TurnCoolerOffUseCase, TurnCoolerOnUseCase
from .turn_doser_on_off import TurnDoserOffUseCase, TurnDoserOnUseCase

__all__ = [
    "SetBlowerPowerUseCase",
    "SetCoolerPowerUseCase",
    "SetDoserRateUseCase",
    "SetDoserSpeedUseCase",
    "MoveSelectorToSlotDirectUseCase",
    "ResetSelectorDirectUseCase",
    "TurnBlowerOnUseCase",
    "TurnBlowerOffUseCase",
    "TurnCoolerOnUseCase",
    "TurnCoolerOffUseCase",
    "TurnDoserOnUseCase",
    "TurnDoserOffUseCase",
]
