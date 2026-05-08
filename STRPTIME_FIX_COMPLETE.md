# Windows strptime Threading Fix - Complete

## Problem
Windows systems were experiencing `No module named '_strptime'` errors when fetching biometric data, especially in ADMS mode. This is a known Python threading issue on Windows where the `_strptime` module must be imported in the main thread before any worker threads try to use `datetime.strptime()`.

## Root Cause
The HTTP server creates new threads for each request. When these threads call `datetime.strptime()` for the first time, Python tries to import the `_strptime` module, but this fails in worker threads on Windows.

## Solution Applied

### 1. Thread-Safe Initialization (All 3 Files)
Added at the top of each file before any threading:
```python
# Fix for Windows threading bug with strptime
try:
    import _strptime
except ImportError:
    datetime.strptime('2000-01-01', '%Y-%m-%d')
```

### 2. Safe Wrapper Function (All 3 Files)
Created a thread-safe wrapper with fallback:
```python
def safe_strptime(date_string, format_string):
    try:
        return datetime.strptime(date_string, format_string)
    except AttributeError:
        import time
        return datetime(*time.strptime(date_string, format_string)[:6])
```

### 3. Replaced All Usage
Replaced all `datetime.strptime()` calls with `safe_strptime()` in:

**biometric_web_app_fixed.py:**
- fetch_adms_data method (2 calls)
- fetch_device_data method (4 calls)
- generate_dummy_data method (2 calls)
- handle_send_to_erp method (1 call)

**zk_bridge.py:**
- fetch_logs function (2 calls)

**adms_listener.py:**
- _parse_adms_record function (1 call)
- do_POST method (1 call)

## Files Modified
1. `/biometric_web_app_fixed.py` - Main web application
2. `/zk_bridge.py` - ZKTeco device bridge
3. `/adms_listener.py` - ADMS push listener

## Testing
Run the test script to verify the fix:
```bash
python test_strptime_fix.py
```

All threads should show ✓ if the fix is working correctly.

## How It Works
1. The `_strptime` module is imported (or initialized) in the main thread at startup
2. All date parsing uses the `safe_strptime()` wrapper
3. The wrapper has a fallback using `time.strptime()` if issues persist
4. This ensures thread-safe date parsing across all Windows systems

## Result
The "No module named '_strptime'" error should no longer occur when:
- Fetching data from biometric devices
- Using ADMS mode
- Processing date filters
- Running in Windows environments
