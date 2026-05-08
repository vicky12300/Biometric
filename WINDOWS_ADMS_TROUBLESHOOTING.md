# Windows ADMS Listener Troubleshooting Guide

## Issue: ADMS Listener Not Starting on Windows

### Quick Diagnosis

Run this command in Windows Command Prompt (in project directory):
```cmd
python test_adms_windows.py
```

This will test if ADMS listener can start properly.

### Common Issues & Solutions

#### 1. **Port 8000 Already in Use**

**Symptoms:**
- `curl http://192.168.1.136:8000` fails
- Test script shows port binding error

**Solution:**
```cmd
# Check what's using port 8000
netstat -ano | findstr ":8000"

# If something is using it, kill the process
taskkill /PID <process_id> /F

# Or change ADMS port in adms_listener.py (line 10)
ADMS_PORT = 8001  # Use different port
```

#### 2. **Windows Firewall Blocking Port 8000**

**Symptoms:**
- Listener starts but device can't connect
- Local curl works but device connection fails

**Solution:**
```cmd
# Add firewall rule for port 8000
netsh advfirewall firewall add rule name="ADMS Listener" dir=in action=allow protocol=TCP localport=8000

# Or open Windows Defender Firewall → Advanced Settings → Inbound Rules → New Rule
# - Rule Type: Port
# - Protocol: TCP
# - Port: 8000
# - Action: Allow
# - Profile: All
# - Name: ADMS Listener
```

#### 3. **Console Window Hidden (Can't See Errors)**

**Symptoms:**
- App runs but no console output
- Can't see if ADMS listener started

**Solution:**
Edit `biometric_web_app_fixed.py` lines 11-18, comment out the hide_console_window() call:

```python
if os.name == 'nt':
    import ctypes
    def hide_console_window():
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass
    # hide_console_window()  # COMMENT THIS OUT TO SEE CONSOLE
```

#### 4. **ADMS Listener Not Starting in EXE**

**Symptoms:**
- Works in Python but not in built EXE
- Port 8000 not listening when running Biometric.exe

**Solution:**
Rebuild EXE with updated `build_windows.bat` (already includes adms_listener):

```cmd
build_windows.bat
```

Check that `dist/Biometric.exe` includes adms_listener.

#### 5. **Network Configuration Issue**

**Symptoms:**
- Listener starts on Windows
- Device can't reach Windows server

**Solution:**
```cmd
# 1. Check Windows IP address
ipconfig

# 2. Verify device can ping Windows server
ping 192.168.1.136

# 3. Check if both are on same network
# Device: 172.20.10.4 (different network!)
# Server: 192.168.1.136 (different network!)
# ❌ These can't communicate!

# Solution: Put both on same network or configure routing
```

### Testing ADMS Listener

#### Test 1: Local Test (on Windows machine)
```cmd
# Start the app
python biometric_web_app_fixed.py

# In another command prompt, test locally
curl http://localhost:8000
# Should return: OK

curl http://192.168.1.136:8000
# Should return: OK
```

#### Test 2: Device Test
Configure device:
- Server Address: `192.168.1.136`
- Server Port: `8000`
- HTTPS: OFF

Check device logs for connection status.

#### Test 3: Manual ADMS Request
```cmd
# Simulate device heartbeat
curl "http://192.168.1.136:8000/iclock/cdata?SN=TEST123&options=all&pushver=2.4.1"

# Should return ADMS configuration response
```

### Checking ADMS Data

```cmd
# Check if punches are being stored
python -c "from data_storage import storage; print(storage.load_adms_punches())"
```

### Enable Debug Logging

Edit `adms_listener.py` to add more logging:

```python
def do_GET(self):
    print(f"[ADMS-DEBUG] Received GET request: {self.path}")
    print(f"[ADMS-DEBUG] Client: {self.client_address}")
    # ... rest of code

def do_POST(self):
    print(f"[ADMS-DEBUG] Received POST request: {self.path}")
    print(f"[ADMS-DEBUG] Client: {self.client_address}")
    # ... rest of code
```

### Network Mismatch Issue (YOUR CASE)

**Problem:** Device (172.20.10.4) and Server (192.168.1.136) are on different networks!

**Solutions:**

1. **Move device to same network as server:**
   - Change device IP to 192.168.1.x range
   - Update device network settings

2. **Move server to same network as device:**
   - Change Windows server IP to 172.20.10.x range
   - Update network adapter settings

3. **Configure routing (advanced):**
   - Set up router to route between 172.20.10.0/24 and 192.168.1.0/24
   - Add static routes on both networks

### Recommended Solution for Your Setup

1. **Check device network settings:**
   - Login to device web interface
   - Go to Network Settings
   - Change IP to 192.168.1.x (e.g., 192.168.1.200)
   - Gateway: 192.168.1.1
   - Subnet: 255.255.255.0

2. **Update device cloud server settings:**
   - Server Address: `192.168.1.136`
   - Server Port: `8000`

3. **Test connectivity:**
   ```cmd
   ping 192.168.1.200  # Should work now
   ```

4. **Restart app and test:**
   ```cmd
   python biometric_web_app_fixed.py
   ```

### Still Not Working?

Run the full diagnostic:
```cmd
python test_adms_windows.py
```

And share the output for further troubleshooting.
