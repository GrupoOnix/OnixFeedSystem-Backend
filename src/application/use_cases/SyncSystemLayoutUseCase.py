

from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.repositories import IFeedingLineRepository


class SynsSystemLayoutUseCase:

    def __init__(self, line_repository: IFeedingLineRepository):
        pass

    def execute(self, line_data: dict) -> FeedingLine:
        pass
    