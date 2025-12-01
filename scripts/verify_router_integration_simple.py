"""
Simple script to verify feeding router integration without database dependencies.

Checks:
1. Router file exists and has correct structure
2. Router is imported in __init__.py
3. Router configuration (prefix, tags)
"""

import re
from pathlib import Path


def verify_router_file():
    """Verify the feeding_router.py file structure."""
    print("1. Checking feeding_router.py file...")
    
    router_file = Path("src/api/routers/feeding_router.py")
    if not router_file.exists():
        print("   ✗ feeding_router.py not found")
        return False
    
    content = router_file.read_text(encoding='utf-8')
    
    # Check for router definition with correct prefix and tags
    if 'router = APIRouter(prefix="/feeding"' in content:
        print('   ✓ Router has correct prefix: /feeding')
    else:
        print('   ✗ Router prefix not found or incorrect')
        return False
    
    if 'tags=["Feeding Operations"]' in content:
        print('   ✓ Router has correct tags: ["Feeding Operations"]')
    else:
        print('   ✗ Router tags not found or incorrect')
        return False
    
    # Check for all expected endpoints
    endpoints = [
        ('POST', '/start'),
        ('POST', '/lines/{line_id}/stop'),
        ('POST', '/lines/{line_id}/pause'),
        ('POST', '/lines/{line_id}/resume'),
        ('PATCH', '/lines/{line_id}/parameters')
    ]
    
    print("   ✓ Checking endpoints:")
    for method, path in endpoints:
        pattern = f'@router.{method.lower()}\\("{re.escape(path)}"'
        if re.search(pattern, content):
            print(f"      ✓ {method:6} {path}")
        else:
            print(f"      ✗ {method:6} {path} not found")
            return False
    
    return True


def verify_router_registration():
    """Verify router is registered in __init__.py."""
    print("\n2. Checking router registration in __init__.py...")
    
    init_file = Path("src/api/routers/__init__.py")
    if not init_file.exists():
        print("   ✗ __init__.py not found")
        return False
    
    content = init_file.read_text(encoding='utf-8')
    
    # Check import
    if 'from . import system_layout, cage_router, feeding_router' in content:
        print('   ✓ feeding_router is imported')
    else:
        print('   ✗ feeding_router import not found')
        return False
    
    # Check api_router prefix
    if 'api_router = APIRouter(prefix="/api")' in content:
        print('   ✓ api_router has correct prefix: /api')
    else:
        print('   ✗ api_router prefix not found or incorrect')
        return False
    
    # Check router inclusion
    if 'api_router.include_router(feeding_router.router)' in content:
        print('   ✓ feeding_router is included in api_router')
    else:
        print('   ✗ feeding_router not included in api_router')
        return False
    
    return True


def verify_consistency_with_other_routers():
    """Verify feeding_router follows same pattern as cage_router."""
    print("\n3. Checking consistency with other routers...")
    
    cage_router_file = Path("src/api/routers/cage_router.py")
    feeding_router_file = Path("src/api/routers/feeding_router.py")
    
    if not cage_router_file.exists():
        print("   ⚠ cage_router.py not found for comparison")
        return True  # Not a failure, just can't compare
    
    cage_content = cage_router_file.read_text(encoding='utf-8')
    feeding_content = feeding_router_file.read_text(encoding='utf-8')
    
    # Check import patterns
    cage_imports = [
        'from fastapi import APIRouter, HTTPException, status',
        'from domain.exceptions import DomainException'
    ]
    
    for import_line in cage_imports:
        if import_line in feeding_content:
            print(f'   ✓ Has consistent import: {import_line[:50]}...')
        else:
            print(f'   ⚠ Missing import pattern: {import_line[:50]}...')
    
    # Check error handling pattern
    error_patterns = [
        'except ValueError as e:',
        'except DomainException as e:',
        'except Exception as e:',
        'status.HTTP_404_NOT_FOUND',
        'status.HTTP_400_BAD_REQUEST',
        'status.HTTP_500_INTERNAL_SERVER_ERROR'
    ]
    
    for pattern in error_patterns:
        if pattern in feeding_content:
            print(f'   ✓ Uses consistent error handling: {pattern}')
        else:
            print(f'   ✗ Missing error handling pattern: {pattern}')
            return False
    
    return True


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("FEEDING ROUTER INTEGRATION VERIFICATION")
    print("=" * 70)
    print()
    
    checks = [
        verify_router_file(),
        verify_router_registration(),
        verify_consistency_with_other_routers()
    ]
    
    print()
    print("=" * 70)
    
    if all(checks):
        print("✓ ALL CHECKS PASSED")
        print()
        print("Summary:")
        print("  • Router is properly configured with /feeding prefix")
        print("  • Router has appropriate tags: ['Feeding Operations']")
        print("  • Router is registered in api_router with /api prefix")
        print("  • Complete URL structure: /api/feeding/*")
        print("  • All 5 endpoints are defined")
        print("  • Error handling follows established patterns")
        print("=" * 70)
        return True
    else:
        print("✗ SOME CHECKS FAILED")
        print("=" * 70)
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
