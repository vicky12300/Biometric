# Testing Guide: Background Service Fix

## What Was Changed

### Problem
The background service was checking `autoSync.enabled` setting and skipping sync if disabled. When the main Biometric.exe was closed, this setting would be `False`, preventing the background service from fetching punches.

### Solution
Added a `--force` flag that Task Scheduler uses to bypass the `autoSync.enabled` check, allowing the background service to run independently.

## Files Modified

1. **`background_sync_service.py`**:
   - Added `argparse` import
   - Added `force_mode` parameter to `__init__`
   - Modified `run_once()` to bypass enabled check when `force_mode=True`
   - Updated `main()` to parse `--force` command-line argument

2. **`setup_windows_task.bat`**:
   - Updated task creation to include `--force` flag: `"%EXE_PATH%" --force`

3. **`quick_start_background_service.bat`**:
   - Updated manual test to use `--force` flag

4. **`create_task_xml.py`**:
   - Added `<Arguments>--force</Arguments>` to XML configuration

5. **`BACKGROUND_SERVICE_SETUP.md`**:
   - Added explanation of UI Auto-Sync vs Background Service
   - Documented the `--force` flag

## Testing Steps

### Step 1: Rebuild the Executables

On Windows, run:
```batch
build_windows.bat
```

This will create:
- `dist\Biometric.exe`
- `dist\background_sync_service.exe` (with --force flag support)

### Step 2: Test Background Service Manually

#### Test A: With --force flag (should always run)
```batch
cd dist
background_sync_service.exe --force
```

**Expected behavior**:
- Service starts and logs: "BackgroundSyncService initialised in FORCE MODE"
- If `autoSync.enabled` is `False`, logs: "Running in FORCE MODE - bypassing auto-sync disabled setting"
- Fetches punches from devices
- Syncs to ERP
- Check logs at: `%APPDATA%\BiometricToolsManager\auto_sync_service.log`

#### Test B: Without --force flag (should respect settings)
```batch
cd dist
background_sync_service.exe
```

**Expected behavior**:
- If `autoSync.enabled` is `False`: logs "Auto-sync disabled in settings; sleeping for X minute(s)" and does NOT fetch punches
- If `autoSync.enabled` is `True`: fetches punches normally

### Step 3: Setup Task Scheduler

Run the setup script:
```batch
setup_windows_task.bat
```

Choose your interval (recommend 5 minutes for testing, then 1 minute for production).

**Verify the task**:
1. Open Task Scheduler (`Win+R`, type `taskschd.msc`)
2. Find `BiometricBackgroundSync`
3. Right-click → Properties → Actions tab
4. **Verify**: The command should show `"C:\path\to\background_sync_service.exe" --force`

### Step 4: Test with Auto-Sync Disabled

1. **Open Biometric.exe**
2. **Go to Settings → Auto Sync**
3. **UNCHECK "Enable Auto-Sync"**
4. **Click "Save Settings"**
5. **Close Biometric.exe**

6. **Wait for the scheduled task to run** (check Task Scheduler)
7. **Check the logs**:
   ```batch
   notepad %APPDATA%\BiometricToolsManager\auto_sync_service.log
   ```

**Expected log entries**:
```
[timestamp] [INFO] biometric_auto_sync: BackgroundSyncService initialised in FORCE MODE; data dir=...
[timestamp] [INFO] biometric_auto_sync: Running in FORCE MODE - bypassing auto-sync disabled setting
[timestamp] [INFO] biometric_auto_sync: Preparing to sync X record(s) to ERP
[timestamp] [INFO] biometric_auto_sync: ERP sync successful: ...
```

### Step 5: Verify Data in ERP

1. Log into your Frappe ERP
2. Go to Attendance or Employee Checkin list
3. **Verify**: New records appear with timestamps matching device punches
4. **Check**: Records are created even though auto-sync was disabled in the UI

## Success Criteria

✅ **All tests pass if**:
1. Background service runs with `--force` flag regardless of `autoSync.enabled` setting
2. Background service respects `autoSync.enabled` setting when run WITHOUT `--force` flag
3. Task Scheduler successfully runs the service every configured interval
4. Punches are fetched from devices and synced to ERP
5. Logs show "FORCE MODE" messages when running via Task Scheduler
6. Data appears in ERP even when main application is closed and auto-sync is disabled

## Troubleshooting

### Service still not fetching punches

1. **Check the Task Scheduler command**:
   - Open Task Scheduler → BiometricBackgroundSync → Properties → Actions
   - Verify it includes `--force` flag
   - If not, delete the task and run `setup_windows_task.bat` again

2. **Check the logs**:
   ```batch
   notepad %APPDATA%\BiometricToolsManager\auto_sync_service.log
   ```
   - Look for "FORCE MODE" message
   - Look for "bypassing auto-sync disabled setting"
   - Check for any errors

3. **Verify ERP configuration**:
   - Open Biometric.exe
   - Go to Settings → ERP Integration
   - Verify URL and API Key are set
   - Click "Test Connection"

4. **Verify devices are configured**:
   - Open Biometric.exe
   - Go to Devices tab
   - Ensure at least one device is added

### Logs show "ERP configuration incomplete"

- Open Biometric.exe
- Configure ERP settings (URL, API Key)
- Save settings
- The background service will pick up the new configuration on next run

### Logs show "No devices configured"

- Open Biometric.exe
- Add at least one device
- The background service will pick up the new devices on next run

## Quick Test Commands

```batch
# View logs
notepad %APPDATA%\BiometricToolsManager\auto_sync_service.log

# View settings
notepad %APPDATA%\BiometricToolsManager\settings.json

# View devices
notepad %APPDATA%\BiometricToolsManager\devices.json

# View ERP config
notepad %APPDATA%\BiometricToolsManager\erp_config.json

# Check if task is running
schtasks /Query /TN "BiometricBackgroundSync" /V /FO LIST

# Run task manually (immediate)
schtasks /Run /TN "BiometricBackgroundSync"

# Delete task
schtasks /Delete /TN "BiometricBackgroundSync" /F
```

## Next Steps After Testing

Once testing is successful:

1. **Set your desired interval**:
   - Run `setup_windows_task.bat` again
   - Choose your production interval (1, 5, or 10 minutes)

2. **Monitor for a few hours**:
   - Check logs periodically
   - Verify data is syncing to ERP

3. **Configure auto-start on boot** (optional):
   - The current setup already includes boot trigger in XML method
   - Or use `create_task_xml.py` for advanced boot configuration

4. **Backup your configuration**:
   - Copy `%APPDATA%\BiometricToolsManager` folder
   - Keep a backup of your settings and device configurations
