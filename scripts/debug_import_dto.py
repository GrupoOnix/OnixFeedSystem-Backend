import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    from domain.dtos.machine_io import MachineConfiguration
    print("Import MachineConfiguration successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
