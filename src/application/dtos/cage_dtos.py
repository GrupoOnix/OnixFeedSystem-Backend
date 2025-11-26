from dataclasses import dataclass
from datetime import datetime
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
    current_fish_count: Optional[int]
    biomass_kg: float
    avg_fish_weight_g: Optional[float]
    created_at: datetime
    volume_m3: Optional[float]
    max_density_kg_m3: Optional[float]
    fcr: Optional[float]
    feeding_table_id: Optional[str]
    transport_time_seconds: Optional[int]
    status: str


@dataclass
class ListCagesResponse:
    cages: List[CageListItemResponse]
