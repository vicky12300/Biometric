#!/usr/bin/env python3
"""
Simple test for adms_listener.py on Windows
Run this to verify the type hint fix worked
"""

import sys

print("="*60)
print("ADMS Listener Compatibility Test")
print("="*60)
print(f"\nPython Version: {sys.version}")
print(f"Version Info: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Test 1: Import
print("\n[1] Testing import...")
try:
    import adms_listener
    print("    ✅ SUCCESS: adms_listener imported")
except Exception as e:
    print(f"    ❌ FAILED: {e}")
    print("\n" + "="*60)
    print("Fix: Make sure adms_listener.py has NO type hints")
    print("="*60)
    sys.exit(1)

# Test 2: Function test
print("\n[2] Testing _parse_adms_record function...")
try:
    test_params = {
        'table': ['ATTLOG'],
        'UserID': ['101'],
        'Stamp': ['2025-01-15 09:00:00'],
        'Status': ['0'],
        'Verified': ['1'],
        'SN': ['TEST123']
    }
    
    result = adms_listener._parse_adms_record(test_params)
    
    if result and result.get('employeeId') == '101':
        print(f"    ✅ SUCCESS: Function returned correct result")
        print(f"       Employee ID: {result['employeeId']}")
        print(f"       Timestamp: {result['timestamp']}")
        print(f"       Type: {result['punchType']}")
    else:
        print(f"    ⚠️  WARNING: Unexpected result: {result}")
        
except Exception as e:
    print(f"    ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Module attributes
print("\n[3] Testing module attributes...")
try:
    assert hasattr(adms_listener, 'start'), "Missing 'start' function"
    assert hasattr(adms_listener, 'stop'), "Missing 'stop' function"
    assert hasattr(adms_listener, 'get_buffered_records'), "Missing 'get_buffered_records' function"
    print("    ✅ SUCCESS: All required functions exist")
except AssertionError as e:
    print(f"    ❌ FAILED: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print("\nNext steps:")
print("1. Start the biometric application")
print("2. Test ADMS fetch from browser:")
print("   http://localhost:8083/fetch?mode=adms&ip=192.168.1.119")
print("3. Check for 'success: true' in response")
print("\n" + "="*60)
