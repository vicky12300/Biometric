# ESSL AirFace Orcus Troubleshooting Guide

## Quick Diagnostic Steps

### 1. Run the Diagnostic Tool
```bash
python test_essl_orcus.py <device_ip> [port]
```

Example:
```bash
python test_essl_orcus.py 192.168.1.201
python test_essl_orcus.py 192.168.1.201 4370
```

### 2. Common Issues and Solutions

#### Issue: "Connection Timeout" or "Device Not Responding"

**Possible Causes:**
- Wrong IP address
- Device is powered off
- Network/firewall blocking connection
- Wrong port number

**Solutions:**
1. Verify IP address from device menu: `Menu → Comm → IP Address`
2. Check device is powered on and network cable connected
3. Ping the device: `ping <device_ip>`
4. Try different ports: 4370 (default), 5005, 8080
5. Disable firewall temporarily to test
6. Ensure device and computer are on same network/VLAN

#### Issue: "Connected but No Attendance Records"

**Possible Causes:**
- Device is in PUSH/ADMS mode (sends data automatically to server)
- No punches recorded yet
- Device memory cleared

**Solutions:**
1. Check device connection mode:
   - Go to device: `Menu → Comm → Connection Mode`
   - Should be: **TCP/IP** or **RS232/485**
   - Should NOT be: **ADMS** or **Push**
   
2. If in ADMS/Push mode, change to TCP/IP:
   - `Menu → Comm → Connection Mode → TCP/IP`
   - Save and restart device

3. Verify punches exist:
   - `Menu → Attendance → Check Records`
   - If empty, record a test punch

#### Issue: "Authentication Failed" or "Invalid Password"

**Possible Causes:**
- Device has non-default communication password

**Solutions:**
1. Check device password:
   - `Menu → Comm → Comm Password`
   - Note the password (default is usually 0)

2. Update device settings in the app:
   - Add device with correct password
   - Common passwords: 0, 1234, 0000

#### Issue: "Protocol Error" or "Unsupported Device"

**Possible Causes:**
- Device firmware too old or too new
- Device uses different protocol

**Solutions:**
1. Update device firmware:
   - Download latest firmware from ESSL website
   - Update via USB or network

2. Check device protocol support:
   - ESSL AirFace Orcus should support ZKTeco protocol
   - Verify in device specifications

3. Enable compatibility mode:
   - Some devices have "ZK Protocol" option in settings
   - `Menu → System → Protocol → ZK`

### 3. Device Configuration Checklist

Before using the device with this software, ensure:

- [ ] Device has static IP address (not DHCP)
- [ ] Connection Mode is set to **TCP/IP** (not ADMS/Push)
- [ ] Communication Password is known (default: 0)
- [ ] Port is set to 4370 (default) or note custom port
- [ ] Device is on same network as computer
- [ ] Firewall allows port 4370 (or custom port)
- [ ] Device has at least one user enrolled
- [ ] Device has at least one attendance record

### 4. Recommended Device Settings

#### Network Settings
```
Menu → Comm → Network Settings
- IP Address: 192.168.1.201 (example - use your network)
- Subnet Mask: 255.255.255.0
- Gateway: 192.168.1.1 (your router)
- DHCP: Disabled (use static IP)
```

#### Communication Settings
```
Menu → Comm → Connection Mode
- Mode: TCP/IP (NOT ADMS or Push)
- Port: 4370 (default)
- Comm Password: 0 (or note custom password)
```

#### Time Settings
```
Menu → System → Date/Time
- Ensure correct date and time
- Timezone should match your location
```

### 5. Testing Connection from Command Line

#### Test with zk_bridge.py
```bash
python zk_bridge.py 192.168.1.201 4370
```

#### Test with date range
```bash
python zk_bridge.py 192.168.1.201 4370 2026-01-01 2026-01-31
```

### 6. Common Error Messages

| Error Message | Meaning | Solution |
|--------------|---------|----------|
| `Connection timed out` | Device not reachable | Check IP, network, firewall |
| `Connection refused` | Wrong port or service not running | Try different port (4370, 5005) |
| `No route to host` | Network routing issue | Check network configuration |
| `Invalid password` | Wrong communication password | Check device password setting |
| `No attendance records` | Device has no data or in Push mode | Check connection mode, record test punch |

### 7. ESSL AirFace Orcus Specific Notes

The ESSL AirFace Orcus is a face recognition device that:
- Uses ZKTeco protocol (compatible with this software)
- Default port: 4370
- Supports both TCP and UDP connections
- May require `ommit_ping=True` for some network configurations
- Stores attendance locally when in TCP/IP mode
- Can be configured for Push mode (sends data to server automatically)

**Important:** If device is in Push/ADMS mode, you need to:
1. Either change to TCP/IP mode (recommended for this software)
2. Or set up a push receiver server (advanced)

### 8. Getting Help

If you still can't connect after trying all solutions:

1. Check device manual for specific model configuration
2. Contact ESSL support: https://www.esslsecurity.com/support
3. Verify device supports ZKTeco protocol
4. Check if device firmware needs update
5. Try connecting with ESSL's official software first to verify device works

### 9. Alternative: Using Dummy Mode for Testing

If you can't connect to the device but want to test the software:

1. In the web app, add device with "Dummy Mode" enabled
2. This generates test data for development/testing
3. Once device connection is fixed, disable dummy mode

### 10. Contact Information

**ESSL Support:**
- Website: https://www.esslsecurity.com
- Product Page: https://www.esslsecurity.com/face/aiface-orcus

**Software Support:**
- Check README.md for software documentation
- Review scope.md for feature details
