"""Script para verificar que el sistema de inyección de dependencias funciona correctamente."""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.dependencies import get_machine_service


def test_singleton_behavior():
    """Verifica que get_machine_service() retorna la misma instancia."""
    print("Testing singleton behavior of get_machine_service()...")
    
    # Llamar múltiples veces
    instance1 = get_machine_service()
    instance2 = get_machine_service()
    instance3 = get_machine_service()
    
    # Verificar que todas son la misma instancia
    assert id(instance1) == id(instance2), "instance1 and instance2 should be the same"
    assert id(instance2) == id(instance3), "instance2 and instance3 should be the same"
    assert id(instance1) == id(instance3), "instance1 and instance3 should be the same"
    
    print(f"✓ All instances have the same id: {id(instance1)}")
    print("✓ Singleton behavior verified successfully!")


def test_docstrings():
    """Verifica que todas las funciones de dependencia tienen docstrings."""
    print("\nTesting that all dependency functions have docstrings...")
    
    from api import dependencies
    import inspect
    
    functions_without_docstrings = []
    
    for name, obj in inspect.getmembers(dependencies):
        if inspect.isfunction(obj) and name.startswith('get_'):
            # Skip get_session as it's imported from database module
            if name == 'get_session':
                continue
            if not obj.__doc__ or not obj.__doc__.strip():
                functions_without_docstrings.append(name)
    
    if functions_without_docstrings:
        print(f"✗ Functions without docstrings: {functions_without_docstrings}")
        return False
    else:
        print("✓ All dependency functions have docstrings!")
        return True


def test_type_aliases():
    """Verifica que los type aliases están definidos correctamente."""
    print("\nTesting type aliases...")
    
    from api.dependencies import (
        StartFeedingUseCaseDep,
        StopFeedingUseCaseDep,
        PauseFeedingUseCaseDep,
        ResumeFeedingUseCaseDep,
        UpdateFeedingParamsUseCaseDep
    )
    
    # Verificar que los type aliases existen
    assert StartFeedingUseCaseDep is not None
    assert StopFeedingUseCaseDep is not None
    assert PauseFeedingUseCaseDep is not None
    assert ResumeFeedingUseCaseDep is not None
    assert UpdateFeedingParamsUseCaseDep is not None
    
    print("✓ All feeding type aliases are defined correctly!")


if __name__ == "__main__":
    try:
        test_singleton_behavior()
        test_docstrings()
        test_type_aliases()
        print("\n" + "="*60)
        print("All dependency injection tests passed! ✓")
        print("="*60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
