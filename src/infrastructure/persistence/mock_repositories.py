from typing import Dict, List, Optional

from domain.aggregates.cage import Cage
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.aggregates.feeding_session import FeedingSession
from domain.aggregates.silo import Silo
from domain.entities.feeding_operation import FeedingOperation
from domain.enums import OperationStatus
from domain.repositories import (
    ICageRepository,
    IFeedingLineRepository,
    IFeedingOperationRepository,
    IFeedingSessionRepository,
    ISiloRepository,
)
from domain.value_objects import (
    CageId,
    CageName,
    LineId,
    LineName,
    OperationId,
    SessionId,
    SiloId,
    SiloName,
)


class MockFeedingLineRepository(IFeedingLineRepository):
    def __init__(self):
        self._lines: Dict[LineId, FeedingLine] = {}

    async def save(self, feeding_line: FeedingLine) -> None:
        self._lines[feeding_line.id] = feeding_line

    async def find_by_id(self, line_id: LineId) -> Optional[FeedingLine]:
        return self._lines.get(line_id)

    async def find_by_name(self, name: LineName) -> Optional[FeedingLine]:
        for line in self._lines.values():
            if line.name == name:
                return line
        return None

    async def get_all(self) -> list[FeedingLine]:
        return list(self._lines.values())

    async def delete(self, line_id: LineId) -> None:
        if line_id in self._lines:
            del self._lines[line_id]


class MockCageRepository(ICageRepository):
    def __init__(self):
        self._cages: Dict[CageId, Cage] = {}

    async def save(self, cage: Cage) -> None:
        self._cages[cage.id] = cage

    async def find_by_id(self, cage_id: CageId) -> Optional[Cage]:
        return self._cages.get(cage_id)

    async def find_by_name(self, name: CageName) -> Optional[Cage]:
        for cage in self._cages.values():
            if cage.name == name:
                return cage
        return None

    async def get_all(self) -> List[Cage]:
        return list(self._cages.values())

    async def get_next_id(self) -> CageId:
        return CageId.generate()

    async def delete(self, cage_id: CageId) -> None:
        if cage_id in self._cages:
            del self._cages[cage_id]


class MockSiloRepository(ISiloRepository):
    def __init__(self):
        self._silos: Dict[SiloId, Silo] = {}

    async def save(self, silo: Silo) -> None:
        self._silos[silo.id] = silo

    async def find_by_id(self, silo_id: SiloId) -> Optional[Silo]:
        return self._silos.get(silo_id)

    async def find_by_name(self, name: SiloName) -> Optional[Silo]:
        for silo in self._silos.values():
            if silo.name == name:
                return silo
        return None

    async def get_all(self) -> List[Silo]:
        return list(self._silos.values())

    async def get_next_id(self) -> SiloId:
        return SiloId.generate()

    async def delete(self, silo_id: SiloId) -> None:
        if silo_id in self._silos:
            del self._silos[silo_id]



class MockFeedingSessionRepository(IFeedingSessionRepository):
    """Mock repository for feeding sessions."""

    def __init__(self):
        self._sessions: Dict[SessionId, FeedingSession] = {}
    
    async def save(self, session: FeedingSession) -> None:
        self._sessions[session.id] = session
        # Clear events (simulate persistence)
        session.pop_events()
    
    async def find_by_id(self, session_id: SessionId) -> Optional[FeedingSession]:
        return self._sessions.get(session_id)
    
    async def find_active_by_line_id(self, line_id: LineId) -> Optional[FeedingSession]:
        from domain.enums import SessionStatus
        for session in self._sessions.values():
            if session.line_id == line_id and session.status == SessionStatus.ACTIVE:
                return session
        return None


class MockFeedingOperationRepository(IFeedingOperationRepository):
    """Mock repository for feeding operations."""

    def __init__(self):
        self._operations: Dict[OperationId, FeedingOperation] = {}
    
    async def save(self, operation: FeedingOperation) -> None:
        self._operations[operation.id] = operation
        # Clear new events (simulate persistence)
        operation.pop_new_events()
    
    async def find_by_id(self, operation_id: OperationId) -> Optional[FeedingOperation]:
        return self._operations.get(operation_id)
    
    async def find_current_by_session(self, session_id: SessionId) -> Optional[FeedingOperation]:
        """Find active operation (RUNNING or PAUSED) for a session."""
        for operation in self._operations.values():
            if operation.session_id == session_id:
                if operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                    return operation
        return None
    
    async def find_all_by_session(self, session_id: SessionId) -> List[FeedingOperation]:
        """Get all operations for a session."""
        return [
            op for op in self._operations.values()
            if op.session_id == session_id
        ]

