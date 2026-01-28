from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from domain.enums import FeedingMode, SessionStatus

class StartFeedingRequest(BaseModel):
    line_id: UUID
    cage_id: UUID
    mode: FeedingMode
    target_amount_kg: float = Field(..., ge=0)
    blower_speed_percentage: float = Field(..., ge=0, le=100)
    dosing_rate_kg_min: float = Field(..., gt=0)

class UpdateParamsRequest(BaseModel):
    line_id: UUID
    blower_speed: Optional[float] = Field(None, ge=0, le=100)
    dosing_rate: Optional[float] = Field(None, gt=0)

class LineDashboardResponse(BaseModel):
    line_id: UUID
    line_name: str
    is_online: bool

    # Session Info
    active_session_id: Optional[UUID] = None
    session_status: Optional[SessionStatus] = None
    target_kg: Optional[float] = None
    total_dispensed_kg: Optional[float] = None
    current_mode: Optional[str] = None

    # Real-time Telemetry
    current_flow_rate: float = 0.0
    current_pressure: float = 0.0

    # Inventory
    silos: List[Dict[str, float]] = [] # {name, current_kg}
