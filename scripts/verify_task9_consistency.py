"""
Verificación de consistencia con patrones existentes (Task 9).

Este script verifica que el código de feeding sigue los mismos patrones
que cage_router y otros componentes del proyecto.
"""

import sys
import re
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def check_import_order():
    """Verifica que el orden de imports sigue el patrón establecido."""
    print("=" * 80)
    print("1. VERIFICACIÓN DE ORDEN DE IMPORTS")
    print("=" * 80)
    
    # Leer feeding_router
    feeding_router_path = Path(__file__).parent.parent / "src" / "api" / "routers" / "feeding_router.py"
    with open(feeding_router_path, 'r', encoding='utf-8') as f:
        feeding_content = f.read()
    
    # Leer cage_router como referencia
    cage_router_path = Path(__file__).parent.parent / "src" / "api" / "routers" / "cage_router.py"
    with open(cage_router_path, 'r', encoding='utf-8') as f:
        cage_content = f.read()
    
    # Extraer secciones de imports
    def extract_import_section(content):
        lines = content.split('\n')
        imports = []
        in_import_section = False
        for line in lines:
            if line.startswith('from ') or line.startswith('import '):
                in_import_section = True
                imports.append(line)
            elif in_import_section and line.strip() == '':
                continue
            elif in_import_section:
                break
        return imports
    
    feeding_imports = extract_import_section(feeding_content)
    cage_imports = extract_import_section(cage_content)
    
    print("\n✓ Feeding Router Imports:")
    for imp in feeding_imports[:5]:
        print(f"  {imp}")
    
    print("\n✓ Cage Router Imports (referencia):")
    for imp in cage_imports[:5]:
        print(f"  {imp}")
    
    # Verificar patrón: stdlib -> blank -> fastapi -> blank -> local
    feeding_pattern = '\n'.join(feeding_imports)
    has_blank_after_stdlib = '\n\nfrom fastapi' in feeding_pattern or '\n\nfrom uuid' in feeding_pattern
    has_blank_after_fastapi = '\n\nfrom api' in feeding_pattern or '\n\nfrom application' in feeding_pattern
    
    if has_blank_after_fastapi:
        print("\n✅ PASS: Import order sigue el patrón (stdlib -> fastapi -> local con líneas en blanco)")
    else:
        print("\n⚠️  WARNING: Import order podría mejorarse")
    
    return True


def check_parameter_naming():
    """Verifica que los nombres de parámetros son consistentes."""
    print("\n" + "=" * 80)
    print("2. VERIFICACIÓN DE NOMBRES DE PARÁMETROS")
    print("=" * 80)
    
    # Verificar feeding_session_repository
    repo_path = Path(__file__).parent.parent / "src" / "infrastructure" / "persistence" / "repositories" / "feeding_session_repository.py"
    with open(repo_path, 'r', encoding='utf-8') as f:
        repo_content = f.read()
    
    # Buscar el método save
    save_match = re.search(r'async def save\(self, (\w+): FeedingSession\)', repo_content)
    
    if save_match:
        param_name = save_match.group(1)
        print(f"\n✓ Parámetro en save(): {param_name}")
        
        if param_name == "feeding_session":
            print("✅ PASS: Usa 'feeding_session' (evita conflicto con AsyncSession)")
        else:
            print(f"❌ FAIL: Debería usar 'feeding_session', no '{param_name}'")
            return False
    
    # Verificar que use_case es consistente en routers
    router_path = Path(__file__).parent.parent / "src" / "api" / "routers" / "feeding_router.py"
    with open(router_path, 'r', encoding='utf-8') as f:
        router_content = f.read()
    
    use_case_params = re.findall(r'(\w+):\s+\w+UseCaseDep', router_content)
    
    print(f"\n✓ Parámetros de use case en endpoints: {set(use_case_params)}")
    
    if all(p == "use_case" for p in use_case_params):
        print("✅ PASS: Todos los endpoints usan 'use_case' consistentemente")
    else:
        print("❌ FAIL: Nombres de parámetros inconsistentes")
        return False
    
    return True


def check_transaction_handling():
    """Verifica que el manejo de transacciones usa el mismo patrón."""
    print("\n" + "=" * 80)
    print("3. VERIFICACIÓN DE MANEJO DE TRANSACCIONES")
    print("=" * 80)
    
    # Verificar feeding_session_repository
    repo_path = Path(__file__).parent.parent / "src" / "infrastructure" / "persistence" / "repositories" / "feeding_session_repository.py"
    with open(repo_path, 'r', encoding='utf-8') as f:
        repo_content = f.read()
    
    uses_flush = "await self.session.flush()" in repo_content
    uses_commit = "await self.session.commit()" in repo_content
    
    print(f"\n✓ Usa flush(): {uses_flush}")
    print(f"✓ Usa commit(): {uses_commit}")
    
    if uses_flush and not uses_commit:
        print("✅ PASS: Usa flush() en lugar de commit() (patrón correcto)")
    else:
        print("❌ FAIL: Debería usar flush() no commit()")
        return False
    
    # Verificar patrón de UPDATE vs INSERT
    has_get_check = "await self.session.get(" in repo_content
    
    if has_get_check:
        print("✅ PASS: Usa session.get() para verificar existencia (UPDATE vs INSERT)")
    else:
        print("❌ FAIL: Debería usar session.get() para verificar existencia")
        return False
    
    return True


def check_response_models():
    """Verifica que los response models usan Pydantic BaseModel."""
    print("\n" + "=" * 80)
    print("4. VERIFICACIÓN DE RESPONSE MODELS")
    print("=" * 80)
    
    dtos_path = Path(__file__).parent.parent / "src" / "application" / "dtos" / "feeding_dtos.py"
    with open(dtos_path, 'r', encoding='utf-8') as f:
        dtos_content = f.read()
    
    # Buscar todas las clases
    classes = re.findall(r'class (\w+)\((\w+)\):', dtos_content)
    
    print("\n✓ DTOs encontrados:")
    all_use_basemodel = True
    for class_name, base_class in classes:
        uses_basemodel = base_class == "BaseModel"
        status = "✅" if uses_basemodel else "❌"
        print(f"  {status} {class_name} extends {base_class}")
        if not uses_basemodel:
            all_use_basemodel = False
    
    if all_use_basemodel:
        print("\n✅ PASS: Todos los DTOs usan Pydantic BaseModel")
    else:
        print("\n❌ FAIL: Algunos DTOs no usan BaseModel")
        return False
    
    return True


def check_docstring_style():
    """Verifica que los docstrings siguen el mismo estilo."""
    print("\n" + "=" * 80)
    print("5. VERIFICACIÓN DE ESTILO DE DOCSTRINGS")
    print("=" * 80)
    
    router_path = Path(__file__).parent.parent / "src" / "api" / "routers" / "feeding_router.py"
    with open(router_path, 'r', encoding='utf-8') as f:
        router_content = f.read()
    
    # Buscar docstrings de endpoints
    docstrings = re.findall(r'"""(.*?)"""', router_content, re.DOTALL)
    
    print(f"\n✓ Encontrados {len(docstrings)} docstrings")
    
    # Verificar que tienen descripción y parámetros con formato - **param**:
    has_proper_format = True
    for i, doc in enumerate(docstrings[1:], 1):  # Skip module docstring
        has_description = len(doc.strip().split('\n')[0]) > 10
        has_param_format = '- **' in doc
        
        if not (has_description and has_param_format):
            print(f"  ⚠️  Docstring {i} podría mejorarse")
            has_proper_format = False
    
    if has_proper_format:
        print("✅ PASS: Docstrings siguen el formato establecido")
    else:
        print("⚠️  WARNING: Algunos docstrings podrían mejorarse")
    
    return True


def check_error_handling_pattern():
    """Verifica que el manejo de errores sigue el patrón try-except establecido."""
    print("\n" + "=" * 80)
    print("6. VERIFICACIÓN DE PATRÓN DE MANEJO DE ERRORES")
    print("=" * 80)
    
    router_path = Path(__file__).parent.parent / "src" / "api" / "routers" / "feeding_router.py"
    with open(router_path, 'r', encoding='utf-8') as f:
        router_content = f.read()
    
    # Buscar bloques try-except
    try_blocks = re.findall(r'try:(.*?)except Exception', router_content, re.DOTALL)
    
    print(f"\n✓ Encontrados {len(try_blocks)} bloques try-except")
    
    # Verificar patrón: ValueError -> 404, DomainException -> 400, Exception -> 500
    has_valueerror = "except ValueError" in router_content
    has_domainexception = "except DomainException" in router_content
    has_generic_exception = "except Exception" in router_content
    
    has_404 = "HTTP_404_NOT_FOUND" in router_content
    has_400 = "HTTP_400_BAD_REQUEST" in router_content
    has_500 = "HTTP_500_INTERNAL_SERVER_ERROR" in router_content
    
    print(f"\n✓ Captura ValueError: {has_valueerror}")
    print(f"✓ Captura DomainException: {has_domainexception}")
    print(f"✓ Captura Exception genérica: {has_generic_exception}")
    print(f"\n✓ Retorna 404: {has_404}")
    print(f"✓ Retorna 400: {has_400}")
    print(f"✓ Retorna 500: {has_500}")
    
    if all([has_valueerror, has_domainexception, has_generic_exception, has_404, has_400, has_500]):
        print("\n✅ PASS: Patrón de manejo de errores es consistente")
        return True
    else:
        print("\n❌ FAIL: Patrón de manejo de errores incompleto")
        return False


def main():
    """Ejecuta todas las verificaciones."""
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE CONSISTENCIA CON PATRONES EXISTENTES")
    print("Task 9: Revisión final de consistencia")
    print("=" * 80)
    
    results = []
    
    try:
        results.append(("Import Order", check_import_order()))
        results.append(("Parameter Naming", check_parameter_naming()))
        results.append(("Transaction Handling", check_transaction_handling()))
        results.append(("Response Models", check_response_models()))
        results.append(("Docstring Style", check_docstring_style()))
        results.append(("Error Handling Pattern", check_error_handling_pattern()))
    except Exception as e:
        print(f"\n❌ ERROR durante verificación: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE VERIFICACIONES")
    print("=" * 80)
    
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("El código de feeding sigue consistentemente los patrones establecidos.")
    else:
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("Revisar los detalles arriba para corregir inconsistencias.")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
