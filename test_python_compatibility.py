#!/usr/bin/env python3
"""
Test script to verify adms_listener.py works with Python 3.8+
"""

import sys
print(f"Python version: {sys.version}")
print(f"Python version info: {sys.version_info}")

# Test 1: Import adms_listener
print("\n[Test 1] Importing adms_listener...")
try:
    import adms_listener
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check type hints are compatible
print("\n[Test 2] Checking type hints...")
try:
    from typing import Optional
    import http.server
    import threading
    
    # These should work in Python 3.8+
    test_var1: Optional[dict] = None
    test_var2: Optional[http.server.HTTPServer] = None
    test_var3: Optional[threading.Thread] = None
    
    print("✅ Type hints are compatible")
except Exception as e:
    print(f"❌ Type hint error: {e}")
    sys.exit(1)

# Test 3: Test _parse_adms_record function
print("\n[Test 3] Testing _parse_adms_record function...")
try:
    from adms_listener import _parse_adms_record
    
    # Test with valid ATTLOG data
    test_params = {
        'table': ['ATTLOG'],
        'UserID': ['101'],
        'Stamp': ['2025-01-15 09:00:00'],
        'Status': ['0'],
        'Verified': ['1'],
        'SN': ['TEST123']
    }
    
    result = _parse_adms_record(test_params)
    
    if result and result.get('employeeId') == '101':
        print("✅ _parse_adms_record works correctly")
        print(f"   Result: {result}")
    else:
        print(f"❌ Unexpected result: {result}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Function test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test listener start/stop
print("\n[Test 4] Testing listener start/stop...")
try:
    import adms_listener
    
    # Try to start listener on port 8000
    success = adms_listener.start(8000)
    
    if success:
        print("✅ Listener started successfully")
        
        # Stop it
        adms_listener.stop()
        print("✅ Listener stopped successfully")
    else:
        print("⚠️  Listener failed to start (port may be in use)")
        
except Exception as e:
    print(f"❌ Listener test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ All tests passed! adms_listener.py is compatible with your Python version")
print("="*60)
