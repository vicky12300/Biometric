# Biometric Tools Manager

Biometric Tools Manager is a Python-based toolkit that centralizes attendance device administration, punch log analysis, and ERP synchronization. It ships as a lightweight HTTP server with a rich browser UI and can be bundled into a Windows desktop executable via PyInstaller.

## Features
- **Biometric device dashboard** – register, edit, and monitor ZKTeco / ESSL / Suprema devices with status tracking.
- **Attendance insights** – fetch logs on demand or with date filters, inspect punch history, and export to CSV/Excel/PDF.
- **ERPNext integration** – configure API credentials, test connectivity, and push validated check-ins manually or through auto-sync.
- **Role-based access** – login overlay with Admin/Viewer roles, user CRUD modals, and activity history.
- **Persistent storage** – JSON-backed storage via `data_storage.py`, including device, user, settings, and sync history records.
- **Desktop packaging & background service** – `desktop_app.py` embeds the web UI inside a native window; `build_windows.bat` now also produces a headless `background_sync_service.exe` for unattended scheduling.

## Project Structure
```
Final Biometric/
├── biometric_web_app_fixed.py   # HTTP server + embedded HTML/JS UI
├── data_storage.py              # JSON persistence layer
├── desktop_app.py               # PyWebView desktop shell
├── zk_bridge.py                 # CLI helper for retrieving attendance from devices
├── build_windows.bat            # PyInstaller build script (desktop + background service)
├── background_sync_service.py   # Headless auto-sync worker for Task Scheduler
├── create_icon.py               # Optional icon generation helper
├── auriga.png / bio.ico         # Branding assets
├── scope.md                     # Scope & requirements document
└── README.md                    # You are here
```

## Prerequisites
- Python 3.8 or newer
- Network access to target biometric devices
- (Optional) ERPNext API endpoint and key/secret pair
- Windows build requires PyInstaller toolchain (installed automatically by the batch script)

Install Python dependencies manually if running from source:
```bash
pip install pywebview zk pillow
```
Additional modules (`pyinstaller`) are only required when packaging the desktop executable.

## Running the Web Application
1. Ensure dependencies are installed.
2. Launch the server:
   ```bash
   python biometric_web_app_fixed.py
   ```
3. The server listens on `http://localhost:8083` by default (with automatic fallback ports). A browser window opens automatically.
4. Log in with default credentials (`admin` / `admin123` or `viewer` / `viewer123`).

### Desktop Shell (PyWebView)
To run the bundled desktop experience instead of a browser tab:
```bash
python desktop_app.py
```
The script starts the same background server and renders the UI in a native window sized for 1400×900.

## Data Storage
User, device, settings, and history data persist as JSON files inside the platform-specific directory (e.g., `%APPDATA%/BiometricToolsManager` on Windows or `~/.biometric_tools` on Linux/macOS). The first run routine automatically seeds default users and settings.

## ERP Integration
1. Navigate to the **ERP Integration** tab in the UI.
2. Select ERP system (ERPNext by default) and supply the API URL and `api_key:api_secret` token.
3. Use **Test Connection** to validate credentials.
4. Push attendance via **Send to ERP**, schedule via **Auto-Sync**, or run a **Custom Sync** from a specific date/time.

A dedicated employee fetch routine maps device IDs to ERP employee records; ensure `attendance_device_id` is populated in ERPNext to prevent skipped records.

## Fetching Attendance from Devices
- Use the **Data & Reports** tab to pull logs, enable dummy data, and export results.
- For diagnostics or scripting, invoke `zk_bridge.py` directly:
  ```bash
  python zk_bridge.py <device_ip> [port] [start_date] [end_date]
  ```
  Dates should use the `YYYY-MM-DD` format.

## Building the Windows Executables
1. Open a Windows command prompt in the project directory.
2. Run the batch script:
   ```cmd
   build_windows.bat
   ```
3. The script cleans previous builds, installs required packages, and produces both `Biometric.exe` (desktop shell) and `background_sync_service.exe` (headless auto-sync worker) inside the `dist` folder.

### Scheduling the Background Sync Service (Windows)
1. Open **Task Scheduler** → **Create Task…** and choose **Run whether user is logged on or not**.
2. Set a trigger (e.g., at startup or repeat every N minutes) and point the action to the generated `background_sync_service.exe`.
3. The worker runs silently, writing activity logs to `%APPDATA%/BiometricToolsManager/auto_sync_service.log`.  Configure auto-sync settings inside the main app—`background_sync_service.py` reuses the same JSON configuration.

## Troubleshooting Tips
- **Port already in use:** the server automatically retries ports 8084–8087; ensure no other process locks these ports.
- **Device connectivity errors:** verify network reachability and firewall allowances; consult console logs for diagnostics printed by `zk_bridge.py`.
- **ERP sync failures:** double-check API tokens, URL, and employee device IDs; review error summaries in the ERP tab result pane.
- **Data not persisting:** confirm the user running the application has write access to the storage directory noted in the console output.

## Contributing & Next Steps
See `scope.md` for the current scope, assumptions, and potential enhancements. Future upgrades could include automated device discovery, secure credential handling, and database-backed storage for higher scale deployments.

https://kapilahr.m.frappe.cloud/
7c115c7c8420600:e121942f3b7e284