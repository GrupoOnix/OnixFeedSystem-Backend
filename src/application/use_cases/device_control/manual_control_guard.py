from domain.enums import FeedingLineStatus
from domain.exceptions import FeedingLineUnavailableException


def require_manual_control(line_name: str, line_status: str) -> None:
    if line_status != FeedingLineStatus.MANUAL_CONTROL.value:
        raise FeedingLineUnavailableException(
            f"La línea {line_name} debe estar en MANUAL_CONTROL para control directo (estado actual: {line_status})"
        )
