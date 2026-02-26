from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.feedback import Feedback
from domain.repositories import IFeedbackRepository
from infrastructure.persistence.models.feedback_model import FeedbackModel


class FeedbackRepository(IFeedbackRepository):
    """Implementación del repositorio de feedback."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, feedback: Feedback) -> None:
        """Guarda un nuevo feedback."""
        feedback_model = FeedbackModel.from_domain(feedback)
        self.session.add(feedback_model)
        await self.session.flush()
