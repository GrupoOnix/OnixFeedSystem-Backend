"""
Configuración de pytest para tests.
"""
import sys
from pathlib import Path

# Agregar src al PYTHONPATH (subir dos niveles desde test)
src_path = Path(__file__).parent.parent.absolute()
src_path_str = str(src_path)

# Remover src/test del path si está presente
test_path = str(Path(__file__).parent.absolute())
if test_path in sys.path:
    sys.path.remove(test_path)

# Insertar src al principio del path
if src_path_str in sys.path:
    sys.path.remove(src_path_str)
sys.path.insert(0, src_path_str)
