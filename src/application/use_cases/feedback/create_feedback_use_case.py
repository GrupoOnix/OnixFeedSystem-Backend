from application.dtos.feedback_dtos import CreateFeedbackRequest
from domain.aggregates.feedback import Feedback
from domain.repositories import IFeedbackRepository
from domain.value_objects import UserId


class CreateFeedbackUseCase:
    """Caso de uso para crear un nuevo feedback."""

    def __init__(self, feedback_repository: IFeedbackRepository):
        self._feedback_repository = feedback_repository

    async def execute(self, request: CreateFeedbackRequest, user_id: UserId) -> None:
        """
        Ejecuta el caso de uso para crear un nuevo feedback.

        Args:
            request: CreateFeedbackRequest con los datos del feedback
            user_id: ID del usuario que envía el feedback

        Raises:
            ValueError: Si los datos son inválidos (tipo o mensaje)
        """
        feedback = Feedback(
            type=request.type,
            message=request.message,
            name=request.name,
            email=request.email,
            user_id=user_id,
        )

        await self._feedback_repository.save(feedback)
