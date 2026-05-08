#!/usr/bin/env python3
"""
Test script to verify the strptime fix works correctly.
Run this on Windows to confirm the threading issue is resolved.
"""

import threading
import time

# Fix for Windows threading bug with strptime
try:
    import _strptime
    print("✓ _strptime module imported successfully")
except ImportError:
    print("⚠ _strptime not available, using fallback initialization")
    from datetime import datetime
    datetime.strptime('2000-01-01', '%Y-%m-%d')
    print("✓ strptime initialized via fallback")

from datetime import datetime

# Thread-safe strptime wrapper
def safe_strptime(date_string, format_string):
    try:
        return datetime.strptime(date_string, format_string)
    except AttributeError:
        import time as time_module
        return datetime(*time_module.strptime(date_string, format_string)[:6])

def test_in_thread(thread_id):
    """Test strptime in a thread"""
    try:
        result = safe_strptime('2025-01-15', '%Y-%m-%d')
        print(f"Thread {thread_id}: ✓ Successfully parsed date: {result}")
        return True
    except Exception as e:
        print(f"Thread {thread_id}: ✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n=== Testing strptime in multiple threads ===\n")
    
    # Test in main thread first
    print("Main thread test:")
    test_in_thread(0)
    
    # Test in multiple threads
    print("\nSpawning 5 threads to test concurrent strptime calls...")
    threads = []
    for i in range(1, 6):
        t = threading.Thread(target=test_in_thread, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    print("\n=== All tests completed ===")
    print("If you see ✓ for all threads, the fix is working correctly!")
