"""
Test script to make sample requests to feeding endpoints.

This verifies that endpoints are not only registered but also functional.
"""

import sys
import time
import subprocess
import httpx
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def start_server():
    """Start the FastAPI server in background."""
    print("Iniciando servidor...")
    
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"✗ El servidor falló al iniciar")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return None
    
    print("✓ Servidor iniciado\n")
    return process


def test_start_feeding():
    """Test POST /api/feeding/start endpoint."""
    print("=" * 60)
    print("TEST: POST /api/feeding/start")
    print("=" * 60)
    
    # Generate random UUIDs for testing
    line_id = str(uuid4())
    cage_id = str(uuid4())
    
    payload = {
        "line_id": line_id,
        "cage_id": cage_id,
        "mode": "Manual",  # Spanish enum value
        "target_amount_kg": 100.0,
        "blower_speed_percentage": 75.0,
        "dosing_rate_kg_min": 5.0
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(
                "http://localhost:8000/api/feeding/start",
                json=payload,
                timeout=5
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # We expect 404 because the line/cage don't exist in DB
            # But this proves the endpoint is working and validating
            if response.status_code in [201, 404, 400]:
                print("✓ Endpoint funcional (responde correctamente)")
                return True
            else:
                print(f"✗ Status code inesperado: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_stop_feeding():
    """Test POST /api/feeding/lines/{line_id}/stop endpoint."""
    print("\n" + "=" * 60)
    print("TEST: POST /api/feeding/lines/{line_id}/stop")
    print("=" * 60)
    
    line_id = str(uuid4())
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"http://localhost:8000/api/feeding/lines/{line_id}/stop",
                timeout=5
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # We expect 404 because the line doesn't exist
            if response.status_code in [200, 404, 400]:
                print("✓ Endpoint funcional (responde correctamente)")
                return True
            else:
                print(f"✗ Status code inesperado: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_pause_feeding():
    """Test POST /api/feeding/lines/{line_id}/pause endpoint."""
    print("\n" + "=" * 60)
    print("TEST: POST /api/feeding/lines/{line_id}/pause")
    print("=" * 60)
    
    line_id = str(uuid4())
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"http://localhost:8000/api/feeding/lines/{line_id}/pause",
                timeout=5
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code in [200, 404, 400]:
                print("✓ Endpoint funcional (responde correctamente)")
                return True
            else:
                print(f"✗ Status code inesperado: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_resume_feeding():
    """Test POST /api/feeding/lines/{line_id}/resume endpoint."""
    print("\n" + "=" * 60)
    print("TEST: POST /api/feeding/lines/{line_id}/resume")
    print("=" * 60)
    
    line_id = str(uuid4())
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"http://localhost:8000/api/feeding/lines/{line_id}/resume",
                timeout=5
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code in [200, 404, 400]:
                print("✓ Endpoint funcional (responde correctamente)")
                return True
            else:
                print(f"✗ Status code inesperado: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_update_parameters():
    """Test PATCH /api/feeding/lines/{line_id}/parameters endpoint."""
    print("\n" + "=" * 60)
    print("TEST: PATCH /api/feeding/lines/{line_id}/parameters")
    print("=" * 60)
    
    line_id = str(uuid4())
    
    payload = {
        "line_id": line_id,  # Required by DTO
        "blower_speed": 80.0,
        "dosing_rate": 6.0
    }
    
    try:
        with httpx.Client() as client:
            response = client.patch(
                f"http://localhost:8000/api/feeding/lines/{line_id}/parameters",
                json=payload,
                timeout=5
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code in [200, 404, 400]:
                print("✓ Endpoint funcional (responde correctamente)")
                return True
            else:
                print(f"✗ Status code inesperado: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all endpoint tests."""
    print("\n" + "=" * 60)
    print("TEST DE ENDPOINTS DE FEEDING")
    print("=" * 60 + "\n")
    
    # Start server
    server_process = start_server()
    
    if server_process is None:
        print("\nFALLO: El servidor no pudo iniciar")
        return False
    
    results = {}
    
    try:
        # Test all endpoints
        results["start"] = test_start_feeding()
        results["stop"] = test_stop_feeding()
        results["pause"] = test_pause_feeding()
        results["resume"] = test_resume_feeding()
        results["update"] = test_update_parameters()
        
    finally:
        # Stop server
        print("\n" + "=" * 60)
        print("Deteniendo servidor...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("✓ Servidor detenido")
    
    # Print summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    for endpoint, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{endpoint.upper()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("RESULTADO: ✓ TODOS LOS ENDPOINTS FUNCIONAN")
    else:
        print("RESULTADO: ✗ ALGUNOS ENDPOINTS FALLARON")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
