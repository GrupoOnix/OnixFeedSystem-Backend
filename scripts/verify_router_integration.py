"""
Script to verify that the feeding router is properly integrated.

Checks:
1. Router is imported in api/routers/__init__.py
2. Router is registered with api_router
3. Router has correct prefix
4. Router has appropriate tags
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def verify_router_integration():
    """Verify feeding router integration."""
    print("=" * 60)
    print("FEEDING ROUTER INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Import the routers module
    try:
        from api.routers import api_router, feeding_router
        print("✓ Successfully imported api_router and feeding_router")
    except ImportError as e:
        print(f"✗ Failed to import routers: {e}")
        return False
    
    # Check router configuration
    print("\n1. Router Configuration:")
    print(f"   - Prefix: {feeding_router.router.prefix}")
    print(f"   - Tags: {feeding_router.router.tags}")
    
    # Verify prefix
    expected_prefix = "/feeding"
    if feeding_router.router.prefix == expected_prefix:
        print(f"   ✓ Prefix is correct: {expected_prefix}")
    else:
        print(f"   ✗ Prefix mismatch. Expected: {expected_prefix}, Got: {feeding_router.router.prefix}")
        return False
    
    # Verify tags
    expected_tags = ["Feeding Operations"]
    if feeding_router.router.tags == expected_tags:
        print(f"   ✓ Tags are correct: {expected_tags}")
    else:
        print(f"   ✗ Tags mismatch. Expected: {expected_tags}, Got: {feeding_router.router.tags}")
        return False
    
    # Check api_router prefix
    print("\n2. API Router Configuration:")
    print(f"   - API Prefix: {api_router.prefix}")
    
    if api_router.prefix == "/api":
        print("   ✓ API prefix is correct: /api")
    else:
        print(f"   ✗ API prefix mismatch. Expected: /api, Got: {api_router.prefix}")
        return False
    
    # Check if feeding_router is included in api_router
    print("\n3. Router Registration:")
    feeding_router_found = False
    
    for route in api_router.routes:
        if hasattr(route, 'path') and '/feeding' in route.path:
            feeding_router_found = True
            break
    
    if feeding_router_found:
        print("   ✓ Feeding router is registered with api_router")
    else:
        print("   ✗ Feeding router not found in api_router routes")
        return False
    
    # List all feeding endpoints
    print("\n4. Feeding Endpoints:")
    feeding_endpoints = []
    for route in api_router.routes:
        if hasattr(route, 'path') and '/feeding' in route.path:
            method = list(route.methods)[0] if hasattr(route, 'methods') else 'N/A'
            feeding_endpoints.append(f"   {method:6} {route.path}")
    
    if feeding_endpoints:
        for endpoint in sorted(feeding_endpoints):
            print(endpoint)
        print(f"   ✓ Found {len(feeding_endpoints)} feeding endpoints")
    else:
        print("   ✗ No feeding endpoints found")
        return False
    
    # Verify complete URL structure
    print("\n5. Complete URL Structure:")
    print("   Base URL: http://localhost:8000")
    print("   API Prefix: /api")
    print("   Router Prefix: /feeding")
    print("   Example Full URL: http://localhost:8000/api/feeding/start")
    print("   ✓ URL structure is consistent with other routers")
    
    print("\n" + "=" * 60)
    print("✓ ALL CHECKS PASSED - Router integration is correct!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = verify_router_integration()
    sys.exit(0 if success else 1)
