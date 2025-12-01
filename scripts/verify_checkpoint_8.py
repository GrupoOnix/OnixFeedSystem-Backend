"""
Verification script for Task 8 - Application Startup Checkpoint

This script verifies:
1. Application starts without import errors
2. GET /health returns 200
3. GET /docs shows endpoints
4. Feeding endpoints are accessible
"""

import sys
import time
import subprocess
import httpx
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all modules can be imported without errors."""
    print("=" * 60)
    print("TEST 1: Verificar imports")
    print("=" * 60)
    
    try:
        from src.main import app
        from src.api.routers import feeding_router
        from src.api.dependencies import (
            get_start_feeding_use_case,
            get_stop_feeding_use_case,
            get_pause_feeding_use_case,
            get_resume_feeding_use_case,
            get_update_feeding_params_use_case
        )
        print("✓ Todos los imports exitosos")
        return True
    except Exception as e:
        print(f"✗ Error en imports: {e}")
        return False


def start_server():
    """Start the FastAPI server in background."""
    print("\n" + "=" * 60)
    print("Iniciando servidor...")
    print("=" * 60)
    
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("Esperando que el servidor inicie...")
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"✗ El servidor falló al iniciar")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return None
    
    print("✓ Servidor iniciado")
    return process


def test_health_endpoint():
    """Test GET /health returns 200."""
    print("\n" + "=" * 60)
    print("TEST 2: GET /health")
    print("=" * 60)
    
    try:
        with httpx.Client() as client:
            response = client.get("http://localhost:8000/health", timeout=5)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✓ Health check exitoso")
                    return True
                else:
                    print(f"✗ Respuesta inesperada: {data}")
                    return False
            else:
                print(f"✗ Status code incorrecto: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_docs_endpoint():
    """Test GET /docs is accessible."""
    print("\n" + "=" * 60)
    print("TEST 3: GET /docs")
    print("=" * 60)
    
    try:
        with httpx.Client() as client:
            response = client.get("http://localhost:8000/docs", timeout=5)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                # Check if feeding endpoints are mentioned in the docs
                content = response.text
                if "feeding" in content.lower():
                    print("✓ Documentación accesible y contiene endpoints de feeding")
                    return True
                else:
                    print("⚠ Documentación accesible pero no se encontraron endpoints de feeding")
                    return True
            else:
                print(f"✗ Status code incorrecto: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_openapi_schema():
    """Test that feeding endpoints are in OpenAPI schema."""
    print("\n" + "=" * 60)
    print("TEST 4: Verificar endpoints de feeding en OpenAPI")
    print("=" * 60)
    
    try:
        with httpx.Client() as client:
            response = client.get("http://localhost:8000/openapi.json", timeout=5)
            
            if response.status_code == 200:
                schema = response.json()
                paths = schema.get("paths", {})
                
                # Check for feeding endpoints
                feeding_endpoints = [
                    "/api/feeding/start",
                    "/api/feeding/lines/{line_id}/stop",
                    "/api/feeding/lines/{line_id}/pause",
                    "/api/feeding/lines/{line_id}/resume",
                    "/api/feeding/lines/{line_id}/parameters"
                ]
                
                found_endpoints = []
                missing_endpoints = []
                
                for endpoint in feeding_endpoints:
                    if endpoint in paths:
                        found_endpoints.append(endpoint)
                        print(f"  ✓ {endpoint}")
                    else:
                        missing_endpoints.append(endpoint)
                        print(f"  ✗ {endpoint} - NO ENCONTRADO")
                
                if len(found_endpoints) == len(feeding_endpoints):
                    print(f"\n✓ Todos los {len(feeding_endpoints)} endpoints de feeding están registrados")
                    return True
                else:
                    print(f"\n⚠ {len(found_endpoints)}/{len(feeding_endpoints)} endpoints encontrados")
                    return False
            else:
                print(f"✗ Status code incorrecto: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("CHECKPOINT 8: Verificación de Inicio de Aplicación")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Imports
    results["imports"] = test_imports()
    
    # Start server
    server_process = start_server()
    
    if server_process is None:
        print("\n" + "=" * 60)
        print("RESULTADO FINAL: FALLO")
        print("=" * 60)
        print("El servidor no pudo iniciar. Verifica los logs arriba.")
        return False
    
    try:
        # Test 2: Health endpoint
        results["health"] = test_health_endpoint()
        
        # Test 3: Docs endpoint
        results["docs"] = test_docs_endpoint()
        
        # Test 4: OpenAPI schema
        results["openapi"] = test_openapi_schema()
        
    finally:
        # Stop server
        print("\n" + "=" * 60)
        print("Deteniendo servidor...")
        print("=" * 60)
        server_process.terminate()
        server_process.wait(timeout=5)
        print("✓ Servidor detenido")
    
    # Print summary
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("RESULTADO FINAL: ✓ TODOS LOS TESTS PASARON")
    else:
        print("RESULTADO FINAL: ✗ ALGUNOS TESTS FALLARON")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
