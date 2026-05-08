# Background Sync Service Setup Guide

This guide explains how to configure the Biometric Background Sync Service to run automatically in Windows at your desired interval.

## Overview

The `background_sync_service.exe` runs continuously in the background and syncs biometric data from your devices to your ERP system at configurable intervals. It works even when the main Biometric application is closed.

## How It Works

1. **Configuration**: The service reads settings from the same configuration files used by the main application
2. **Interval**: You can set the sync interval (1 min, 5 min, 10 min, etc.)
3. **Auto-Start**: The service can be configured to start automatically when Windows boots
4. **Background Operation**: Runs silently in the background without showing a window
5. **Independent Operation**: When run with `--force` flag (via Task Scheduler), it works independently of the main app's auto-sync setting

## Setup Methods

### Method 1: Quick Setup (Recommended)

1. **Build the executables** (if not already done):
   ```batch
   build_windows.bat
   ```
   This creates both `Biometric.exe` and `background_sync_service.exe` in the `dist` folder.

2. **Run the setup script**:
   ```batch
   setup_windows_task.bat
   ```
   
3. **Select your interval**:
   - Choose from preset intervals (1, 5, 10, 15, 30 minutes)
   - Or enter a custom interval
   - **Recommended: 5 minutes** for most use cases

4. **Done!** The service will now run automatically every X minutes.

### Method 2: Advanced Setup (XML Configuration)

For more control over scheduling options:

1. **Generate the XML configuration**:
   ```batch
   python create_task_xml.py 5
   ```
   Replace `5` with your desired interval in minutes.

2. **Import into Task Scheduler**:
   - Open Task Scheduler (`Win+R`, type `taskschd.msc`)
   - Click "Import Task..." in the Actions panel
   - Select `BiometricBackgroundSync.xml`
   - Review settings and click OK

### Method 3: Manual Task Scheduler Setup

1. Open Task Scheduler (`taskschd.msc`)
2. Click "Create Task..." (not "Create Basic Task")
3. **General Tab**:
   - Name: `BiometricBackgroundSync`
   - Description: `Biometric Background Sync Service`
   - Select "Run whether user is logged on or not"
   - Check "Run with highest privileges"
   
4. **Triggers Tab**:
   - Click "New..."
   - Begin the task: "On a schedule"
   - Settings: "Daily"
   - Advanced settings:
     - Check "Repeat task every:" and select your interval (e.g., 5 minutes)
     - For duration: "Indefinitely"
   - Click OK
   
5. **Actions Tab**:
   - Click "New..."
   - Action: "Start a program"
   - Program/script: Browse to `dist\background_sync_service.exe`
   - Click OK
   
6. **Settings Tab**:
   - Uncheck "Stop the task if it runs longer than:"
   - Check "Run task as soon as possible after a scheduled start is missed"
   - Check "If the task fails, restart every: 1 minute"
   - Click OK

## Configuration Options

### Understanding Auto-Sync vs Background Service

> [!IMPORTANT]
> There are **two separate ways** to run auto-sync:
> 
> 1. **UI Auto-Sync**: Runs only when the Biometric.exe application is open
>    - Controlled by the "Enable Auto-Sync" checkbox in Settings
>    - Stops when you close the application
> 
> 2. **Background Service**: Runs via Windows Task Scheduler
>    - Uses the `--force` flag to run independently
>    - Continues running even when the application is closed
>    - Controlled by Task Scheduler, not the UI checkbox

### Sync Interval Settings

The service respects the interval configured in your application settings. You can control this in two ways:

1. **Via the main Biometric application**:
   - Open the Biometric application
   - Go to Settings → Auto Sync
   - Set your desired interval
   - Enable/disable auto-sync

2. **Via configuration file** (Advanced):
   - Edit the settings file in `%APPDATA%\BiometricToolsManager\settings.json`
   - Modify the `autoSync` section:
   ```json
   {
     "autoSync": {
       "enabled": true,
       "interval": 5,
       "testMode": false
     }
   }
   ```

### Recommended Intervals

| Interval | Use Case |
|----------|----------|
| **1 minute** | Real-time sync required, high-traffic environments |
| **5 minutes** | ✅ **Recommended** - Good balance of timeliness and system load |
| **10 minutes** | Lower traffic, less critical timing |
| **15-30 minutes** | Minimal traffic, batch processing acceptable |

## Managing the Service

### Check if Service is Running

1. Open Task Scheduler (`taskschd.msc`)
2. Look for `BiometricBackgroundSync` in the Task Scheduler Library
3. Check the "Status" and "Last Run Time" columns

### Start/Stop the Service

**Using the setup script**:
```batch
setup_windows_task.bat
```
Choose option 7 to remove the task (stop the service)

**Using Task Scheduler**:
1. Open Task Scheduler
2. Find `BiometricBackgroundSync`
3. Right-click → Run (to start immediately)
4. Right-click → End (to stop)
5. Right-click → Disable (to prevent from running)

### View Service Logs

The service writes logs to:
```
%APPDATA%\BiometricToolsManager\auto_sync_service.log
```

To view logs:
```batch
notepad %APPDATA%\BiometricToolsManager\auto_sync_service.log
```

### Remove the Service

**Option 1 - Using setup script**:
```batch
setup_windows_task.bat
```
Select option 7

**Option 2 - Command line**:
```batch
schtasks /Delete /TN "BiometricBackgroundSync" /F
```

**Option 3 - Task Scheduler GUI**:
1. Open Task Scheduler
2. Find `BiometricBackgroundSync`
3. Right-click → Delete

## Troubleshooting

### Service Not Running

1. **Check Task Scheduler**:
   - Open Task Scheduler
   - Verify the task exists and is enabled
   - Check "Last Run Result" (0x0 means success)
   - **Verify the task includes `--force` flag**: Right-click task → Properties → Actions tab

2. **Check Logs**:
   - View `auto_sync_service.log` for errors
   - Common issues:
     - ERP configuration not set
     - No devices configured
     - Network connectivity issues

3. **Run Manually**:
   - Navigate to the `dist` folder
   - Double-click `background_sync_service.exe`
   - Check for any error messages

### No Data Being Synced

1. **Verify Configuration**:
   - Open the main Biometric application
   - Check that devices are configured
   - Verify ERP settings are correct
   - Ensure Auto Sync is enabled

2. **Check Interval**:
   - The service only syncs NEW data since the last run
   - Wait for the configured interval to pass
   - Check the logs to see if sync is occurring

3. **Test Mode**:
   - If `testMode` is enabled, the service uses dummy data
   - Disable test mode for production use

### High CPU/Memory Usage

1. **Increase Interval**:
   - If syncing every 1 minute, try 5 or 10 minutes
   - Reduce the number of devices being monitored

2. **Check Device Connectivity**:
   - Slow or unresponsive devices can cause delays
   - Verify network connectivity to all devices

## Advanced Configuration

### Running Multiple Instances

If you need different sync intervals for different device groups:

1. Create separate configuration profiles
2. Build multiple executables with different names
3. Create separate scheduled tasks for each

### Custom Scheduling

The XML method (Method 2) allows for advanced scheduling:
- Run only during business hours
- Different intervals for different days
- Run on specific events (login, unlock, etc.)

Edit the generated `BiometricBackgroundSync.xml` file to customize triggers.

## Security Considerations

1. **Privileges**: The service runs with highest available privileges to access devices
2. **Credentials**: ERP API keys are stored in local configuration files
3. **Network**: Ensure firewall allows connections to devices and ERP
4. **Logs**: Logs may contain sensitive data; secure the log directory

## Best Practices

1. ✅ **Start with 5-minute interval** and adjust based on needs
2. ✅ **Monitor logs** for the first few hours after setup
3. ✅ **Test with dummy mode** first before connecting to real ERP
4. ✅ **Keep the main application** for manual sync and configuration
5. ✅ **Regular backups** of configuration files
6. ✅ **Update both executables** together when rebuilding

## Support

If you encounter issues:

1. Check the logs: `%APPDATA%\BiometricToolsManager\auto_sync_service.log`
2. Verify configuration: `%APPDATA%\BiometricToolsManager\settings.json`
3. Test with the main application first
4. Ensure all devices are accessible from the Windows machine
5. Verify ERP connectivity and API credentials

---

**Note**: The background service uses the same configuration as the main application. Any changes made in the main application (devices, ERP settings, intervals) will be automatically picked up by the background service on its next run.
