# ADMS Support - Windows Build Changes Summary

## Overview
ADMS (Attendance Data Management System) is a push-based protocol used by ESSL AirFace Orcus and similar face recognition devices. Instead of polling the device, the device pushes attendance data to a server.

## Changes Made

### 1. build_windows.bat ✅
**Changes:**
- Added `adms_listener.py` to the main desktop app build
- Added `adms_listener.py` to the background service build
- Added `--hidden-import=adms_listener` for both executables

**Why:**
- The ADMS listener needs to be bundled into both executables
- The desktop app runs the ADMS listener on port 8000
- The background service needs to read ADMS punches from storage

**Build commands updated:**
```batch
# Desktop app
--add-data "adms_listener.py;." ^
--hidden-import=adms_listener

# Background service
--add-data "adms_listener.py;." ^
--hidden-import=adms_listener
```

### 2. background_sync_service.py ✅
**Changes:**
- Added `import adms_listener`
- Added ADMS mode detection: `use_adms = device.get("mode") == "adms"`
- Added logic to fetch ADMS punches from storage instead of polling device
- Filters ADMS records by device serial number and timestamp

**Why:**
- Background service needs to sync ADMS punches that were pushed to the listener
- ADMS devices don't support polling - data comes via push
- Records are stored in `adms_punches.json` by the listener

**Logic flow:**
```
1. Check if device mode is "adms"
2. Load stored ADMS punches from storage
3. Filter by device serial number/ID
4. Filter by timestamp (only new records after last_seen)
5. Sync to ERP like normal punches
```

### 3. setup_windows_task.bat ✅
**Changes:**
- Fixed error handling (captures error level immediately after schtasks)
- Added error code display for better diagnostics
- Fixed option number reference (12 instead of 7)

**Why:**
- Previous version showed success messages before checking if task creation succeeded
- Better error diagnostics help troubleshoot Task Scheduler issues
- No ADMS-specific changes needed - works with all device modes

## How ADMS Works in the System

### Desktop App (Biometric.exe)
1. Starts ADMS listener on port 8000 automatically
2. Device sends heartbeat to `http://<server_ip>:8000/iclock/cdata.aspx`
3. Listener responds with configuration
4. Device pushes attendance records
5. Listener stores records in `adms_punches.json`
6. UI can fetch and display ADMS records
7. Manual sync sends ADMS records to ERP

### Background Service (background_sync_service.exe)
1. Runs on schedule (e.g., every 3 hours)
2. Checks each device's mode
3. For ADMS devices:
   - Reads `adms_punches.json`
   - Filters records for that device
   - Filters records newer than last sync
   - Syncs to ERP
4. Updates lastSync timestamp after successful sync

### Device Configuration
On the ESSL AirFace Orcus device:
```
Menu → Communication → Cloud Server
- Server Address: <computer_ip>
- Server Port: 8000
- HTTPS: OFF
- Connection Mode: ADMS or Push
```

In the web app:
```
Add Device:
- Name: AIFace Orcus
- IP: <device_ip>
- Port: 4370 (not used for ADMS)
- Mode: ADMS Push (Face Device)
- Serial Number: <device_serial> (important for filtering)
```

## Files Involved

### Core ADMS Files
- `adms_listener.py` - HTTP server that receives push data from device
- `data_storage.py` - Has `save_adms_punches()` and `load_adms_punches()`
- `biometric_web_app_fixed.py` - Starts ADMS listener, handles ADMS mode in UI

### Build Files (Updated)
- `build_windows.bat` - Bundles ADMS listener into executables
- `background_sync_service.py` - Syncs ADMS punches from storage

### Config Files (No changes needed)
- `setup_windows_task.bat` - Works with all device modes including ADMS

## Testing the Build

### 1. Build the executables
```batch
build_windows.bat
```

### 2. Check the dist folder
```
dist/
├── Biometric.exe              (desktop app with ADMS listener)
└── background_sync_service.exe (background service with ADMS support)
```

### 3. Test desktop app
1. Run `Biometric.exe`
2. Add device with mode "ADMS Push (Face Device)"
3. Configure device to push to `http://<your_ip>:8000`
4. Check console for ADMS listener messages
5. Device should start pushing punches

### 4. Test background service
1. Run `setup_windows_task.bat` as Administrator
2. Choose interval (e.g., option 7 for every 3 hours)
3. Task will sync ADMS punches automatically
4. Check logs in `%APPDATA%/BiometricToolsManager/auto_sync_service.log`

## Troubleshooting

### ADMS Listener Not Starting
- Check if port 8000 is already in use
- Check firewall allows port 8000
- Look for error messages in console

### Device Not Pushing Data
- Verify device is configured with correct server IP
- Check device connection mode is ADMS/Push
- Ping the server from device network
- Check firewall on server allows port 8000

### Background Service Not Syncing ADMS
- Check `adms_punches.json` exists and has records
- Verify device serial number matches in device config
- Check background service logs for errors
- Ensure device mode is set to "adms" in web app

### Build Errors
- Ensure all Python dependencies installed: `pip install pywebview pyinstaller pyzk pillow`
- Check `adms_listener.py` exists in project directory
- Run build as Administrator if permission errors

## Port Usage

| Port | Service | Purpose |
|------|---------|---------|
| 8083 | Web App | Main web interface |
| 8000 | ADMS Listener | Receives push data from devices |
| 4370 | ZK Protocol | Polling mode (not used for ADMS) |

## Data Storage

| File | Purpose |
|------|---------|
| `devices.json` | Device configurations |
| `adms_punches.json` | ADMS push records (last 10,000) |
| `auto_sync_state.json` | Background service state |
| `auto_sync_service.log` | Background service logs |

All files stored in:
- Windows: `%APPDATA%/BiometricToolsManager/`
- Linux: `~/.biometric_tools/`

## Summary

✅ **build_windows.bat** - Updated to include ADMS listener in both executables
✅ **background_sync_service.py** - Updated to sync ADMS punches from storage
✅ **setup_windows_task.bat** - Fixed error handling (no ADMS-specific changes)

The system now fully supports ADMS push mode for face recognition devices like ESSL AirFace Orcus, both in the desktop app and background service.
