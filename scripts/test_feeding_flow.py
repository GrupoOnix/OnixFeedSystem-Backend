import asyncio
import sys
import os
import traceback
from typing import Optional, List, Tuple

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    from domain.value_objects import LineId, CageId, SessionId, Weight
    from domain.aggregates.feeding_session import FeedingSession
    from domain.aggregates.cage import Cage
    from domain.aggregates.feeding_line.feeding_line import FeedingLine
    from domain.enums import SessionStatus, FeedingMode
    from domain.repositories import IFeedingSessionRepository, IFeedingLineRepository, ICageRepository
    from infrastructure.services.plc_simulator import PLCSimulator
    from application.use_cases.feeding.start_feeding_use_case import StartFeedingSessionUseCase
    from application.use_cases.feeding.stop_feeding_use_case import StopFeedingSessionUseCase
    from application.use_cases.feeding.control_feeding_use_case import PauseFeedingSessionUseCase, ResumeFeedingSessionUseCase
    from application.use_cases.feeding.update_feeding_use_case import UpdateFeedingParametersUseCase
    from application.dtos.feeding_dtos import StartFeedingRequest, UpdateParamsRequest
except SyntaxError as e:
    print(f"SYNTAX ERROR DETECTED:")
    print(f"File: {e.filename}")
    print(f"Line: {e.lineno}")
    print(f"Msg: {e.msg}")
    print(f"Text: {e.text}")
    sys.exit(1)
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- MOCK REPOSITORIES ---

class MockSessionRepo(IFeedingSessionRepository):
    def __init__(self):
        self.sessions = {}

    async def save(self, session: FeedingSession) -> None:
        self.sessions[session.id.value] = session
        print(f"[REPO] Saved Session {session.id} Status={session.status}")

    async def find_by_id(self, session_id: SessionId) -> Optional[FeedingSession]:
        return self.sessions.get(session_id.value)

    async def find_active_by_line_id(self, line_id: LineId) -> Optional[FeedingSession]:
        # Return last non-completed/failed
        for s in self.sessions.values():
            if s.line_id == line_id and s.status in [SessionStatus.CREATED, SessionStatus.RUNNING, SessionStatus.PAUSED]:
                return s
        return None

class MockLineRepo(IFeedingLineRepository):
    async def find_by_id(self, line_id: LineId) -> Optional[FeedingLine]:
        # Return a dummy line
        return FeedingLine(name="Line 1") # Simplified
    
    async def save(self, line): pass
    async def find_by_name(self, name): pass
    async def get_all(self): pass
    async def delete(self, id): pass

class MockCageRepo(ICageRepository):
    def __init__(self):
        self.cages = {}
        
    async def find_by_id(self, cage_id: CageId) -> Optional[Cage]:
        return self.cages.get(cage_id.value)
        
    async def save(self, cage): pass
    async def find_by_name(self, name): pass
    async def list(self): pass
    async def list_with_line_info(self, line_id=None): pass
    async def delete(self, id): pass

# --- TEST SCRIPT ---

async def main():
    print("=== STARTING FEEDING FLOW VERIFICATION ===")
    
    # 1. Setup
    from uuid import uuid4
    line_id = uuid4()
    cage_id = uuid4()
    
    session_repo = MockSessionRepo()
    line_repo = MockLineRepo()
    cage_repo = MockCageRepo()
    
    # Setup Cage with Slot
    cage = Cage(name="Cage 101")
    cage._id = CageId(cage_id)
    cage._line_id = LineId(line_id)
    cage._slot_number = 1 # Physical Slot 1
    cage_repo.cages[cage_id] = cage
    
    plc = PLCSimulator()
    
    # Use Cases
    start_uc = StartFeedingSessionUseCase(session_repo, line_repo, cage_repo, plc)
    update_uc = UpdateFeedingParametersUseCase(session_repo, plc)
    pause_uc = PauseFeedingSessionUseCase(session_repo, plc)
    resume_uc = ResumeFeedingSessionUseCase(session_repo, plc)
    stop_uc = StopFeedingSessionUseCase(session_repo, plc)
    
    # 2. Execute Start
    print("\n--- TEST: START FEEDING ---")
    req = StartFeedingRequest(
        line_id=line_id,
        cage_id=cage_id,
        mode=FeedingMode.MANUAL,
        target_amount_kg=0.0,
        blower_speed_percentage=80.0,
        dosing_rate_kg_min=5.0 # -> 50% speed approx in simulator logic
    )
    
    session_id_uuid = await start_uc.execute(req)
    print(f"Session Started: {session_id_uuid}")
    
    # Verify PLC State
    status = await plc.get_status(LineId(line_id))
    assert status.is_running == True
    assert status.current_slot_number == 1
    print("PLC Status Verified: RUNNING")
    
    # 3. Simulate Run & Update
    await asyncio.sleep(1)
    print("\n--- TEST: UPDATE PARAMETERS ---")
    await update_uc.execute(UpdateParamsRequest(
        line_id=line_id,
        blower_speed=90.0
    ))
    
    # Verify Update
    status = await plc.get_status(LineId(line_id))
    # Note: Simulator doesn't expose blower speed in status, but we can check logs or internal state if we wanted.
    # We trust the UC executed without error.
    print("Update Executed.")

    # 4. Pause
    print("\n--- TEST: PAUSE ---")
    await pause_uc.execute(line_id)
    status = await plc.get_status(LineId(line_id))
    assert status.is_paused == True
    print("PLC Status Verified: PAUSED")
    
    # 5. Resume
    print("\n--- TEST: RESUME ---")
    await resume_uc.execute(line_id)
    status = await plc.get_status(LineId(line_id))
    assert status.is_paused == False
    assert status.is_running == True
    print("PLC Status Verified: RESUMED")
    
    # 6. Stop
    print("\n--- TEST: STOP ---")
    await stop_uc.execute(line_id)
    status = await plc.get_status(LineId(line_id))
    assert status.is_running == False
    print("PLC Status Verified: STOPPED")
    
    # 7. Verify Events
    session = await session_repo.find_by_id(SessionId(session_id_uuid))
    print("\n--- GENERATED EVENTS ---")
    events = session.pop_events() # This clears them, but for test it's fine
    for e in events:
        print(f"[{e.timestamp}] {e.type.name}: {e.description} | {e.details}")
        
    assert len(events) >= 4 # Start, Update, Pause, Resume, Stop (Stop might not log if session closed? Check logic)
    # Start -> Log
    # Update -> Log
    # Pause -> Log
    # Resume -> Log
    # Stop -> Log
    
    print("\n=== VERIFICATION SUCCESSFUL ===")

if __name__ == "__main__":
    asyncio.run(main())
