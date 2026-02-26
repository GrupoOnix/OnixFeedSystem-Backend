from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateFeedbackRequest:
    """Request para crear un nuevo feedback."""

    type: str
    message: str
    name: Optional[str] = None
    email: Optional[str] = None
