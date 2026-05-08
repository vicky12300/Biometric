# Windows ADMS Listener Troubleshooting Guide

## Problem: ADMS listener works on Linux but not on Windows

### Network Configuration
- **Linux Server**: 192.168.1.113 ✅ WORKING
- **Windows Server**: 192.168.1.14 ❌ NOT WORKING  
- **Device**: 192.168.1.119 (ESSL AirFace Orcus)
- **All on same network**: 192.168.1.x/24

### Root Cause Analysis

The code is **identical** on both systems and **correctly implemented**. The issue is **Windows-specific** and likely caused by:

1. **Windows Firewall blocking port 8000** (most common)
2. **Windows Defender or antivirus blocking Python network access**
3. **Port 8000 already in use by another application**
4. **Windows network adapter configuration**

---

## Step-by-Step Fix

### Step 1: Configure Windows Firewall

**Option A: Using the provided batch script (RECOMMENDED)**

1. Open File Explorer and navigate to the project folder
2. Right-click `configure_windows_firewall.bat`
3. Select **"Run as administrator"**
4. Wait for confirmation message
5. Press any key to close

**Option B: Manual firewall configuration**

1. Open **Windows Defender Firewall with Advanced Security**
   - Press `Win + R`, type `wf.msc`, press Enter
2. Click **Inbound Rules** → **New Rule...**
3. Select **Port** → Next
4. Select **TCP**, enter port **8000** → Next
5. Select **Allow the connection** → Next
6. Check all profiles (Domain, Private, Public) → Next
7. Name: `Biometric ADMS Listener` → Finish
8. Repeat for **UDP** port 8000 (optional)

---

### Step 2: Run Diagnostic Tool

1. Open Command Prompt in the project folder
2. Run: `python diagnose_windows_adms.py`
3. Review the diagnostic results
4. Fix any issues reported

**Expected output when working:**
```
✅ Port 8000 is available
✅ Found firewall rules for ADMS listener
✅ Local IP: 192.168.1.14
✅ Device 192.168.1.119 is reachable
✅ ADMS listener started successfully on port 8000
```

---

### Step 3: Verify Port is Open

**Check if port 8000 is listening:**

```cmd
netstat -an | findstr :8000
```

**Expected output when app is running:**
```
TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING
```

---

### Step 4: Test from Device

1. **Configure device** (via device web UI):
   - Communication → Cloud Server
   - Server Address: `192.168.1.14`
   - Server Port: `8000`
   - HTTPS: `OFF`
   - Save settings

2. **Test connection** from device:
   - Device should send GET request to server
   - Check ADMS listener logs in application console

3. **Expected log output:**
```
[ADMS] Listener started on port 8000
[ADMS] GET /?SN=NYU7260401414&... | SN=NYU7260401414
[ADMS] ✅ Sent registration response to SN=NYU7260401414
```

---

### Step 5: Verify Network Connectivity

**From Windows server, ping the device:**

```cmd
ping 192.168.1.119
```

**Expected output:**
```
Reply from 192.168.1.119: bytes=32 time<1ms TTL=64
```

**From device, test server connectivity:**

Open browser on device (if available) and navigate to:
```
http://192.168.1.14:8000
```

You should see "OK" response or ADMS listener response.

---

## Common Issues and Solutions

### Issue 1: Port 8000 Already in Use

**Symptoms:**
- Error: "Address already in use"
- Diagnostic shows port is not available

**Solution:**
```cmd
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

---

### Issue 2: Windows Defender Blocking Python

**Symptoms:**
- Firewall rules exist but connection still fails
- No error messages in console

**Solution:**
1. Open **Windows Security** → **Virus & threat protection**
2. Click **Manage settings**
3. Scroll to **Exclusions** → **Add or remove exclusions**
4. Add exclusion for:
   - Python executable: `C:\Python3X\python.exe`
   - Project folder: `C:\...\Final Biometric\`

---

### Issue 3: Antivirus Software Blocking

**Symptoms:**
- Connection works briefly then stops
- Antivirus shows blocked connection alerts

**Solution:**
1. Open your antivirus software (Norton, McAfee, Kaspersky, etc.)
2. Add exception for:
   - Python executable
   - Port 8000
   - Project folder

---

### Issue 4: Network Adapter Issues

**Symptoms:**
- Server shows correct IP but device can't connect
- Ping works but HTTP doesn't

**Solution:**
```cmd
# Reset network adapter
ipconfig /release
ipconfig /renew
ipconfig /flushdns

# Restart network adapter
netsh interface set interface "Ethernet" admin=disable
netsh interface set interface "Ethernet" admin=enable
```

---

### Issue 5: Multiple Network Adapters

**Symptoms:**
- Server has multiple IPs (VPN, virtual adapters)
- Device connects to wrong IP

**Solution:**
1. Check all IPs: `ipconfig /all`
2. Identify the correct adapter (usually "Ethernet" or "Wi-Fi")
3. Use that specific IP in device configuration
4. Disable unused network adapters temporarily

---

## Verification Checklist

Before contacting support, verify:

- [ ] Windows Firewall rules added for port 8000
- [ ] Port 8000 is not in use by another application
- [ ] Device IP (192.168.1.119) is pingable from Windows server
- [ ] Windows server IP (192.168.1.14) is correct and reachable
- [ ] Device is configured with correct server IP and port
- [ ] ADMS listener is started (check console logs)
- [ ] No antivirus blocking Python or port 8000
- [ ] Biometric application is running as Administrator (if needed)

---

## Testing Without Device

You can test ADMS listener without the physical device:

**1. Start the application on Windows**

**2. From another computer on the same network, test:**

```bash
# Test GET request (device registration)
curl "http://192.168.1.14:8000/?SN=TEST123"

# Test POST request (attendance data)
curl -X POST "http://192.168.1.14:8000/?SN=TEST123" \
  -d "101	2025-01-15 09:00:00	0	1"
```

**3. Check Windows application console for logs:**
```
[ADMS] GET /?SN=TEST123 | SN=TEST123
[ADMS] ✅ Sent registration response to SN=TEST123
[ADMS] POST /?SN=TEST123 | SN=TEST123 table=
[ADMS] ✅ Punch: emp=101 time=2025-01-15 09:00:00 type=check-in
```

---

## Advanced Debugging

### Enable Detailed Logging

Edit `adms_listener.py` and add debug prints:

```python
def do_GET(self):
    print(f"[DEBUG] Received GET from {self.client_address}")
    print(f"[DEBUG] Path: {self.path}")
    print(f"[DEBUG] Headers: {self.headers}")
    # ... rest of code
```

### Monitor Network Traffic

Use **Wireshark** to capture traffic on port 8000:

1. Install Wireshark
2. Start capture on network adapter
3. Filter: `tcp.port == 8000`
4. Trigger device connection
5. Analyze captured packets

---

## Still Not Working?

If you've tried all the above and it still doesn't work:

1. **Compare with Linux setup:**
   - Check if Linux has any special network configuration
   - Compare firewall rules
   - Check if Linux is using any proxy or NAT

2. **Try different port:**
   - Edit `adms_listener.py`: change `ADMS_PORT = 8000` to `ADMS_PORT = 8080`
   - Update firewall rules for new port
   - Configure device with new port

3. **Check Windows Event Viewer:**
   - Press `Win + R`, type `eventvwr.msc`
   - Check **Windows Logs** → **System** for network errors
   - Check **Windows Logs** → **Security** for firewall blocks

4. **Temporarily disable Windows Firewall** (for testing only):
   ```cmd
   netsh advfirewall set allprofiles state off
   ```
   
   If this fixes it, the issue is firewall configuration. Re-enable and configure properly:
   ```cmd
   netsh advfirewall set allprofiles state on
   ```

---

## Success Indicators

When everything is working correctly, you should see:

**In Windows application console:**
```
[ADMS] Listener started on port 8000
[ADMS] GET /?SN=NYU7260401414&... | SN=NYU7260401414
[ADMS] ✅ Sent registration response to SN=NYU7260401414
[ADMS] POST /?SN=NYU7260401414&table=ATTLOG | SN=NYU7260401414 table=ATTLOG
[ADMS] ✅ Punch: emp=101 time=2025-01-15 09:00:00 type=check-in
```

**In application UI (Data & Reports tab):**
- ADMS records appear in the punch list
- Records show correct employee ID, timestamp, and device serial number

**In device logs (if accessible):**
- Successful connection to server
- Data transmission confirmed
- No error messages

---

## Contact Information

If you need further assistance:
- Check `WINDOWS_ADMS_TROUBLESHOOTING.md` for more details
- Review `scope.md` for system architecture
- Check console logs for specific error messages
