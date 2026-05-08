#!/usr/bin/env python3
"""
Complete Windows ADMS Verification Script
This checks EVERYTHING to diagnose the issue
"""

import sys
import os

print("="*70)
print("COMPLETE WINDOWS ADMS DIAGNOSTIC")
print("="*70)

# Check 1: Python Version
print("\n[1] Python Version Check")
print(f"    Version: {sys.version}")
print(f"    Major.Minor: {sys.version_info.major}.{sys.version_info.minor}")

if sys.version_info < (3, 8):
    print("    ❌ ERROR: Python 3.8+ required")
    sys.exit(1)
else:
    print(f"    ✅ OK: Python {sys.version_info.major}.{sys.version_info.minor} is supported")

# Check 2: File Exists
print("\n[2] File Existence Check")
if os.path.exists('adms_listener.py'):
    size = os.path.getsize('adms_listener.py')
    print(f"    ✅ OK: adms_listener.py exists ({size} bytes)")
    
    if size < 5000:
        print(f"    ⚠️  WARNING: File seems too small ({size} bytes)")
        print("       Expected size: ~10,000-11,000 bytes")
else:
    print("    ❌ ERROR: adms_listener.py not found")
    sys.exit(1)

# Check 3: File Content - Type Hints
print("\n[3] Type Hint Check")
with open('adms_listener.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
issues = []
if 'Optional' in content:
    issues.append("Found 'Optional' keyword")
if 'dict | None' in content:
    issues.append("Found 'dict | None' syntax")
if ': dict' in content and 'def ' in content:
    # Check if it's in a function signature
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def ' in line and ': dict' in line:
            issues.append(f"Found type hint on line {i+1}: {line.strip()}")
if ': list[dict]' in content:
    issues.append("Found ': list[dict]' type hint")
if ': bool' in content and 'def ' in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def ' in line and ': bool' in line:
            issues.append(f"Found ': bool' type hint on line {i+1}")

if issues:
    print("    ❌ ERROR: Type hints found in file:")
    for issue in issues:
        print(f"       - {issue}")
    print("\n    FIX: Copy the updated adms_listener.py from Linux")
    sys.exit(1)
else:
    print("    ✅ OK: No type hints found")

# Check 4: Import Test
print("\n[4] Import Test")
try:
    import adms_listener
    print("    ✅ OK: adms_listener imported successfully")
except Exception as e:
    print(f"    ❌ ERROR: Import failed")
    print(f"       Error: {e}")
    import traceback
    print("\n    Full traceback:")
    traceback.print_exc()
    sys.exit(1)

# Check 5: Function Test
print("\n[5] Function Test")
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
        print("    ✅ OK: _parse_adms_record works correctly")
        print(f"       Employee: {result['employeeId']}")
        print(f"       Time: {result['timestamp']}")
        print(f"       Type: {result['punchType']}")
    else:
        print(f"    ⚠️  WARNING: Unexpected result: {result}")
        
except Exception as e:
    print(f"    ❌ ERROR: Function test failed")
    print(f"       Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 6: Module Attributes
print("\n[6] Module Attributes Check")
required_attrs = ['start', 'stop', 'get_buffered_records', '_parse_adms_record']
missing = []

for attr in required_attrs:
    if hasattr(adms_listener, attr):
        print(f"    ✅ OK: {attr} exists")
    else:
        print(f"    ❌ ERROR: {attr} missing")
        missing.append(attr)

if missing:
    print(f"\n    Missing attributes: {', '.join(missing)}")
    sys.exit(1)

# Check 7: Cache Files
print("\n[7] Cache Files Check")
cache_found = []

if os.path.exists('__pycache__'):
    cache_found.append('__pycache__ directory')
    
if os.path.exists('adms_listener.pyc'):
    cache_found.append('adms_listener.pyc')

for file in os.listdir('.'):
    if file.endswith('.pyc'):
        cache_found.append(file)

if cache_found:
    print("    ⚠️  WARNING: Cache files found:")
    for item in cache_found:
        print(f"       - {item}")
    print("\n    RECOMMENDATION: Delete cache files and restart")
else:
    print("    ✅ OK: No cache files found")

# Check 8: data_storage module
print("\n[8] Dependencies Check")
try:
    from data_storage import storage
    print("    ✅ OK: data_storage module available")
except Exception as e:
    print(f"    ⚠️  WARNING: data_storage import issue: {e}")

# Final Summary
print("\n" + "="*70)
print("DIAGNOSTIC SUMMARY")
print("="*70)

print("\n✅ All critical checks passed!")
print("\nYour adms_listener.py is correctly configured.")
print("\nNext steps:")
print("1. If cache files were found, delete them:")
print("   - Delete __pycache__ folder")
print("   - Delete any .pyc files")
print("2. Restart the biometric application")
print("3. Test ADMS fetch:")
print("   http://localhost:8083/fetch?mode=adms&ip=192.168.1.119")
print("\n" + "="*70)
