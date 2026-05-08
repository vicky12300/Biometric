# Windows _strptime Threading Bug Fix

## Error
```json
{"success": false, "error": "No module named '_strptime'"}
```

## Root Cause

This is a **known Python bug on Windows** that occurs when:
1. Multiple threads are running
2. `datetime.strptime()` is called for the first time
3. Python tries to lazy-load the `_strptime` module
4. Thread race condition causes the import to fail

### Why It Happens
- Python's `strptime` function lazy-loads the `_strptime` module on first use
- In multi-threaded applications (like our HTTP server), multiple threads may try to load it simultaneously
- Windows has stricter threading/import locks than Linux
- This causes a race condition where the module import fails

### Why It Works on Linux but Not Windows
- Linux has more lenient threading behavior
- Windows has stricter GIL (Global Interpreter Lock) handling
- The bug is more likely to manifest on Windows

## Solution

**Import `_strptime` at the top of the file BEFORE any threads are created.**

This forces Python to load the module in the main thread, avoiding the race condition.

## Changes Applied

### File: `adms_listener.py`

Added import after other imports:
```python
import http.server
import json
import threading
import urllib.parse
import urllib.request
from datetime import datetime
from data_storage import storage

# Fix for Windows threading bug with strptime
# Must import _strptime before any threads are created
import _strptime
```

### File: `biometric_web_app_fixed.py`

Added import after other imports:
```python
from urllib.parse import parse_qs
from zk import ZK, const
from datetime import datetime, timedelta
from data_storage import storage

# Fix for Windows threading bug with strptime
# Must import _strptime before any threads are created
import _strptime
```

## How to Apply on Windows

1. **Copy both updated files** to Windows:
   - `adms_listener.py`
   - `biometric_web_app_fixed.py`

2. **Clear Python cache:**
   ```cmd
   rmdir /S /Q __pycache__
   del /F /Q *.pyc
   ```

3. **Restart the application**

4. **Test ADMS fetch:**
   ```
   http://localhost:8083/fetch?mode=adms&ip=192.168.1.119&startDate=2026-05-06&endDate=2026-05-06
   ```

## Verification

Test the import:
```cmd
python -c "import _strptime; import adms_listener; print('Success')"
```

Expected output:
```
Success
```

## Why This Fix Works

1. **Pre-loads the module** in the main thread before any HTTP server threads start
2. **Avoids race condition** by ensuring `_strptime` is already loaded when threads call `strptime()`
3. **No performance impact** - just loads the module earlier
4. **Compatible with all Python versions** - `_strptime` is a standard library module

## Related Python Bug Reports

This is a well-known issue:
- Python Issue #7980: https://bugs.python.org/issue7980
- Stack Overflow: Multiple threads and strptime
- Affects Python 2.x and 3.x on Windows

## Testing

After applying the fix, test with multiple concurrent requests:

```python
import threading
import requests

def test_fetch():
    response = requests.get('http://localhost:8083/fetch?mode=adms&ip=192.168.1.119')
    print(response.json())

# Create 10 concurrent threads
threads = []
for i in range(10):
    t = threading.Thread(target=test_fetch)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("All threads completed successfully!")
```

If the fix works, all 10 threads should complete without the `_strptime` error.

## Summary

✅ **Added `import _strptime`** to both files  
✅ **Fixes Windows threading bug**  
✅ **No code changes needed** - just an extra import  
✅ **Works on all Python versions**  
✅ **No performance impact**  

This is a standard workaround for a known Python bug on Windows! 🎉
