from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ListCagesRequest:
    line_id: Optional[str] = None


@dataclass
class CageListItemResponse:
    cage_id: str
    name: str
    line_id: Optional[str]
    line_name: Optional[str]
    slot_number: Optional[int]
    initial_fish_count: Optional[int]
    current_fish_count: Optional[int]
    biomass_kg: float
    avg_fish_weight_g: Optional[float]


@dataclass
class ListCagesResponse:
    cages: List[CageListItemResponse]
