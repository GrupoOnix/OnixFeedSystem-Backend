"""
Configuración global de pytest.
"""
import sys
import os
from pathlib import Path

# Agregar src al PYTHONPATH
src_path = Path(__file__).parent / "src"
src_path_str = str(src_path.absolute())

if src_path_str not in sys.path:
    sys.path.insert(0, src_path_str)

# También configurar PYTHONPATH como variable de entorno
os.environ['PYTHONPATH'] = src_path_str + os.pathsep + os.environ.get('PYTHONPATH', '')
