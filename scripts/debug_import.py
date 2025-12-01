import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    from domain.aggregates.feeding_session import FeedingSession
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
