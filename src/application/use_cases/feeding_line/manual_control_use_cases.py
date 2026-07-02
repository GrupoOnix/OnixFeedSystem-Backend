from application.dtos.feeding_line_dtos import FeedingLineStatusResponse
from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import LineId


class AcquireManualControlUseCase:
    def __init__(self, feeding_line_repository: IFeedingLineRepository):
        self._feeding_line_repository = feeding_line_repository

    async def execute(
        self,
        line_id: str,
        operator_id: str | None = None,
        reason: str | None = None,
    ) -> FeedingLineStatusResponse:
        feeding_line = await self._feeding_line_repository.find_by_id(LineId.from_string(line_id))
        if not feeding_line:
            raise FeedingLineNotFoundException(f"Línea de alimentación con ID {line_id} no encontrada")

        feeding_line.acquire_manual_control(operator_id=operator_id, reason=reason)
        await self._feeding_line_repository.save_available_status_transition(feeding_line)
        return _to_status_response(feeding_line)


class ReleaseManualControlUseCase:
    def __init__(self, feeding_line_repository: IFeedingLineRepository):
        self._feeding_line_repository = feeding_line_repository

    async def execute(self, line_id: str) -> FeedingLineStatusResponse:
        feeding_line = await self._feeding_line_repository.find_by_id(LineId.from_string(line_id))
        if not feeding_line:
            raise FeedingLineNotFoundException(f"Línea de alimentación con ID {line_id} no encontrada")

        feeding_line.release_manual_control()
        await self._feeding_line_repository.save(feeding_line)
        return _to_status_response(feeding_line)


def _to_status_response(feeding_line) -> FeedingLineStatusResponse:
    return FeedingLineStatusResponse(
        line_id=str(feeding_line.id),
        status=feeding_line.status.value,
        locked_by=feeding_line.locked_by,
        locked_reason=feeding_line.locked_reason,
        locked_at=feeding_line.locked_at,
    )
