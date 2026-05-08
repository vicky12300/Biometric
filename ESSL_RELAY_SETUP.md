# ESSL Cloud Portal Relay Setup

## Overview
The ADMS listener now acts as a **proxy/relay** that:
1. Receives attendance data from your ESSL device
2. Stores it locally in your application
3. Forwards the same data to ESSL's cloud portal

This allows you to use **both** your local app AND the ESSL portal simultaneously without data loss.

## Configuration Steps

### 1. Set ESSL Relay URL in Code
Edit `adms_listener.py` and set the ESSL cloud portal URL:

```python
# Line 11 in adms_listener.py
ESSL_RELAY_URL = "http://cloud.esslsecurity.com:8000"  # Replace with actual ESSL portal URL
```

**Common ESSL Portal URLs:**
- `http://cloud.esslsecurity.com:8000`
- `http://portal.esslsecurity.com:8000`
- `https://cloud.esslsecurity.com` (if HTTPS)
- Contact ESSL support for your specific portal URL

### 2. Configure Device Cloud Settings
In your ESSL device web interface:

**Communication → Cloud Server:**
- **Server Address**: `192.168.1.136` (your Windows server IP)
- **Server Port**: `8000`
- **HTTPS**: OFF (unless using HTTPS)

### 3. How It Works

```
ESSL Device
    ↓
    ↓ (pushes attendance data)
    ↓
Your ADMS Listener (192.168.1.136:8000)
    ↓
    ├─→ Stores locally (adms_punches.json)
    └─→ Forwards to ESSL Portal (cloud.esslsecurity.com:8000)
```

### 4. Verify Relay is Working

Check console logs when device pushes data:
```
[ADMS] POST /iclock/cdata?SN=NYU7260401414 | SN=NYU7260401414 table=ATTLOG
[ADMS] ✅ Punch: emp=101 time=2025-01-05 09:30:00 type=check-in
[ADMS-RELAY] ✅ Forwarded POST to ESSL: http://cloud.esslsecurity.com:8000/iclock/cdata?SN=...
```

### 5. Troubleshooting

**Relay not forwarding:**
- Check `ESSL_RELAY_URL` is set correctly
- Verify internet connectivity to ESSL portal
- Check ESSL portal URL is correct (contact ESSL support)

**Device not pushing to local listener:**
- Verify device can reach 192.168.1.136:8000
- Check Windows Firewall allows port 8000
- Ensure ADMS listener is running

**Data only going to one destination:**
- If only local: ESSL_RELAY_URL not set or wrong URL
- If only ESSL: Device configured with ESSL URL directly (should use local IP)

## Benefits

✅ **No Data Loss**: All punches stored locally even if ESSL portal is down
✅ **Dual Access**: Use both your app and ESSL portal
✅ **Automatic Sync**: No manual intervention needed
✅ **Backup**: Local storage acts as backup if ESSL portal fails

## Disabling Relay

To disable forwarding to ESSL portal (local only):
```python
ESSL_RELAY_URL = None  # Set to None to disable relay
```
