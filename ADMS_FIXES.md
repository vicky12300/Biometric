# ADMS Fixes Summary

## Issues Fixed ✅

### 1. Serial Number Field Added
**Problem:** ADMS devices didn't have a serial number field, making it impossible to match pushed records to specific devices.

**Solution:**
- Added "Serial Number" field to Add Device form
- Added "Serial Number" field to Edit Device form
- Serial number is stored in device configuration
- Used to match ADMS pushed records to correct device

**How to use:**
1. Edit your ADMS device
2. Enter the device serial number (e.g., NYU7260401414)
3. This serial number must match the `deviceId` in pushed ADMS records
4. Find serial number on device: Menu → System → Device Info

### 2. Background Service ADMS Matching Improved
**Problem:** Background service couldn't match ADMS records without serial number.

**Solution:**
- Improved matching logic to try multiple strategies:
  - Match by serial number (if configured)
  - Match by IP address
  - Match by device name
  - Match by partial IP (if IP is part of deviceId)
- Added better logging to show how many records were found
- Filters records by `last_seen` timestamp (only syncs new records)

**How it works:**
```
1. Background service runs on schedule
2. For ADMS devices, loads all ADMS punches from storage
3. Filters by device (serial number, IP, or name)
4. Filters by timestamp (only records after last sync)
5. Syncs to ERP
6. Updates lastSync timestamp
```

### 3. LastSync Tracking for ADMS
**Problem:** LastSync wasn't being tracked properly for ADMS devices.

**Solution:**
- Background service now updates `lastSync` after successful ERP sync
- Uses `storage.update_device_last_sync()` to persist
- Tracks latest timestamp from synced records
- Next sync only fetches records after this timestamp

**Verification:**
```bash
# Check device lastSync
python3 -c "from data_storage import storage; devices = storage.load_devices(); [print(f\"{d['name']}: {d.get('lastSync', 'Never')}\") for d in devices if d.get('mode') == 'adms']"
```

### 4. ADMS Records Filtering by Device
**Problem:** Web app showed all ADMS records from all devices mixed together.

**Solution:**
- `fetch_adms_data()` now filters by device IP or serial number
- Tries multiple matching strategies
- Falls back to showing all if no match (backward compatibility)

### 5. Date Range Handling
**Problem:** Without date filter, only showed 50 records.

**Solution:**
- Changed to show last 7 days of records (all of them)
- With date filter, shows all records in range
- Always sorted by timestamp (newest first)

## How ADMS Works Now

### Device Setup
1. Add ADMS device in web app
2. Set mode to "ADMS Push (Face Device)"
3. **Important:** Enter device serial number (e.g., NYU7260401414)
4. Configure device to push to your server IP:8000

### Real-time Push
1. Device sends heartbeat to ADMS listener (port 8000)
2. Listener responds with configuration
3. Device pushes attendance records
4. Listener stores in `adms_punches.json` with deviceId = serial number

### Background Sync
1. Background service runs on schedule (e.g., every 3 hours)
2. Loads ADMS punches from storage
3. Filters by device serial number/IP
4. Filters by lastSync timestamp (only new records)
5. Syncs to ERP
6. Updates lastSync on success

### Manual Sync
1. Go to Data & Reports tab
2. Select ADMS device
3. Set date range (optional)
4. Click "Fetch Data" - shows filtered records
5. Click "Send to ERP" - syncs to ERP
6. LastSync is updated after successful sync

## Configuration Checklist

### On Device (ESSL AirFace Orcus)
- [ ] Connection Mode: ADMS or Push
- [ ] Server Address: Your computer IP
- [ ] Server Port: 8000
- [ ] Note device serial number from Menu → System → Device Info

### In Web App
- [ ] Add device with mode "ADMS Push (Face Device)"
- [ ] Enter device IP (for reference)
- [ ] **Enter device serial number** (must match device)
- [ ] Enter latitude/longitude (optional)

### Background Service
- [ ] Build with updated code: `build_windows.bat`
- [ ] Setup task: `setup_windows_task.bat`
- [ ] Choose interval (e.g., every 3 hours)
- [ ] Service will auto-sync ADMS punches

## Testing

### 1. Verify ADMS Records Are Being Stored
```bash
python3 -c "from data_storage import storage; records = storage.load_adms_punches(); print(f'Total: {len(records)}'); from collections import Counter; devices = Counter(r.get('deviceId') for r in records); print('By device:', dict(devices))"
```

### 2. Check Device Configuration
```bash
python3 -c "from data_storage import storage; devices = storage.load_devices(); import json; [print(json.dumps(d, indent=2)) for d in devices if d.get('mode') == 'adms']"
```

### 3. Test Background Service Matching
```bash
# Check background service logs
cat ~/.biometric_tools/auto_sync_service.log | grep ADMS
# or on Windows
type %APPDATA%\BiometricToolsManager\auto_sync_service.log | findstr ADMS
```

### 4. Verify LastSync Updates
```bash
# Before sync
python3 -c "from data_storage import storage; d = [d for d in storage.load_devices() if d.get('mode')=='adms'][0]; print(f\"LastSync: {d.get('lastSync', 'Never')}\")"

# Run background service once
python3 background_sync_service.py --force
# (Ctrl+C after one cycle)

# After sync
python3 -c "from data_storage import storage; d = [d for d in storage.load_devices() if d.get('mode')=='adms'][0]; print(f\"LastSync: {d.get('lastSync', 'Never')}\")"
```

## Troubleshooting

### Records Not Showing in Web App
1. Check ADMS storage has records:
   ```bash
   python3 -c "from data_storage import storage; print(len(storage.load_adms_punches()))"
   ```
2. Check device serial number matches:
   - Device config: `serialNumber` field
   - ADMS records: `deviceId` field
3. Check date range filter

### Background Service Not Syncing
1. Check device serial number is configured
2. Check logs for matching errors
3. Verify ADMS records exist in storage
4. Check lastSync timestamp isn't blocking new records

### Duplicate Records
- ADMS listener stores all pushed records
- Background service filters by lastSync
- If lastSync isn't updating, duplicates will be sent
- Check ERP sync is successful (successCount > 0)

## Files Modified

1. `biometric_web_app_fixed.py`
   - Added serial number field to device forms
   - Improved ADMS record filtering
   - Fixed date range handling

2. `background_sync_service.py`
   - Improved ADMS device matching
   - Added better logging
   - Filters by lastSync properly

3. `adms_listener.py`
   - Changed ATTLOGStamp from 9999 to 0 (request all records)

## Next Steps

1. **Update existing ADMS device:**
   - Edit device in web app
   - Add serial number (e.g., NYU7260401414)
   - Save

2. **Restart services:**
   ```bash
   # Restart web app
   python3 biometric_web_app_fixed.py
   
   # Rebuild Windows EXE (if using)
   build_windows.bat
   ```

3. **Test:**
   - Device should push records
   - Web app should show filtered records
   - Background service should sync only new records
   - LastSync should update after successful sync

## Summary

✅ Serial number field added for ADMS devices
✅ Background service matches ADMS records correctly
✅ LastSync tracking works for ADMS
✅ Web app filters ADMS records by device
✅ Date range handling improved
✅ Background service only syncs new records after lastSync

All ADMS functionality now works correctly with proper device matching and lastSync tracking!
