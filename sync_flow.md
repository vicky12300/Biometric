# Synchronization Flow – Plain Language Guide

This guide explains how **Biometric Tools Manager** keeps attendance data in sync with your ERP system. It is written for team members who just want the big picture without digging into code.

## 1. Big Picture

Think of synchronization as a conversation between three sides:

1. **The app that people use** – the desktop screen with buttons such as *Sync Device* or *Send to ERP*.
2. **The storage box** – a set of small files that remember which devices you have, your ERP login, and the last time each device synced.
3. **The ERP system** – the place where the final attendance records must end up.

Whenever someone triggers a sync (manually, on a schedule, or through the background helper), the app reads the storage box, collects new punches from each biometric device, and sends the results to the ERP. When the ERP confirms everything looks good, the app updates the storage box so we know where to continue next time.

## 2. Main Parts in Everyday Terms

| Piece | What it does |
| --- | --- |
| **Desktop interface** | Shows buttons and reports. Lets you choose devices, dates, and actions. |
| **Request handler** | Interprets button clicks and turns them into actions (fetching device data, saving settings, etc.). |
| **Storage files** | Remember devices, ERP credentials, auto-sync schedule, and a log of past syncs. |
| **ERP helper** | Talks to the biometric devices and the ERP server. It knows how to fetch punches and how to send them onward. |
| **Background helper** | Runs quietly on a schedule (even when the main window is closed) to keep data flowing automatically. |

## 3. Ways to Start a Sync

### 3.1 Sync a Single Device
1. You click **Sync** next to a device.
2. The app checks your ERP details, pulls the last week of punches from that device, and sends them to the ERP.
3. The storage files are updated with the time of the most recent punch so future syncs only collect what is new.

### 3.2 Send Filtered Records to the ERP
1. In the **Data & Reports** area, you filter the punches you want (by date, employee, or device).
2. Choosing **Send to ERP** pushes everything currently on the screen straight to the ERP in one go.

### 3.3 Sync Right Now from Settings
1. The **Sync Now** button in Settings triggers the same routine used for automatic syncing.
2. It is a manual “run it immediately” option when you do not want to wait for the timer.

### 3.4 Keep Syncing Automatically
1. When auto-sync is turned on, you pick how often it should run.
2. Every cycle, the app reads your saved settings, asks each device for new punches, sends them to the ERP, then saves the latest timestamps.
3. Turning auto-sync off stops the timer but keeps your settings for later.

### 3.5 Run a Custom Sync Window
1. Choose a custom start date and time in Settings.
2. The app gathers punches from that moment forward for every device and forwards them to the ERP.
3. Each device’s “last synced” time is updated so you can continue from there next time.

### 3.6 Let the Background Helper Work
1. A small background program reads the same settings the main app uses.
2. On each loop it checks whether auto-sync is enabled and whether the ERP login is ready.
3. It collects new punches for every device, sends them to the ERP, and logs the outcome.
4. After a successful run, it saves fresh timestamps so it does not re-send the same data.
5. On Windows you can schedule this helper so syncing continues even when the main app is closed.

## 4. What Information Gets Shared

1. **Settings and devices** – stored in simple JSON files. Both the desktop app and the background helper rely on the same files, so changes in one place apply everywhere.
2. **Punch collection** – every sync only asks for punches that are newer than the last saved timestamp. If you are testing, the app can generate sample punches instead of contacting a real device.
3. **Sending to the ERP** – no matter which button you press, the data eventually goes through the same “send to ERP” routine. The result includes counts of successful punches, duplicates, or errors so you can see what happened.
4. **History and logs** – sync attempts are recorded so you can review past runs. The desktop app shows a history list, while the background helper keeps its own log file for troubleshooting.

## 5. Need the Technical Details?

If you do need to explore the code, the main logic lives in three files:

1. `biometric_web_app_fixed.py` – user interface actions and the send-to-ERP routine.
2. `background_sync_service.py` – the scheduled background helper.
3. `data_storage.py` – helpers for reading and writing the JSON files mentioned above.

## 6. Quick Deployment Checklist

1. Run `build_windows.bat` to create both the main app (`Biometric.exe`) and the background helper (`background_sync_service.exe`).
2. Use Windows Task Scheduler to run the background helper at the interval you prefer.
3. Within the desktop app, update ERP credentials, sync intervals, and test mode. Both programs share these settings automatically.

---

Use this guide when you need a quick refresher on how syncing works or when explaining the process to new teammates. It focuses on the *what* and *why* so you can support users without digging into the full codebase.
