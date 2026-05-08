# Biometric Tools Manager Scope Document

## 1. Project Overview
Biometric Tools Manager is a desktop-packaged web application that centralizes administration of biometric attendance devices—primarily ZKTeco / ESSL models—and synchronizes the collected punch data with ERP systems such as ERPNext. The solution bundles an embedded HTTP server, persistent JSON-backed storage, ERP connectors, and an enhanced browser UI rendered inside a native window.

## 2. Objectives
- Provide administrators with a unified dashboard to register, monitor, and control biometric devices across locations.
- Automate the retrieval, filtering, and export of biometric attendance logs, with optional dummy/testing data support.
- Streamline ERP integration by pushing validated attendance records to ERPNext (and other systems) via API.
- Offer role-based access (Admin/Viewer) to ensure secure management of devices, data, and settings.
- Enable packaging of the tooling as a Windows executable for easy deployment without manual Python setup.

## 3. Scope of Work
### In Scope
1. **Device Lifecycle Management**
   - Manual addition, editing, and deletion of biometric devices with metadata (name, type, IP, port, mode).
   - Auto-discovery workflow stub for scanning LAN devices.
   - Activity logging for device operations and online/offline status display.

2. **Attendance Data Handling**
   - Fetch logs from ZK-based devices via `zk` Python SDK bridge with date filtering.
   - Persist punch records, device history, user history, and ERP sync history via JSON files managed by `data_storage.py`.
   - Present attendance data in UI with advanced filters (employee, punch type, device) and pagination hooks.
   - Export punch data to CSV/Excel/PDF and enable manual/dummy data downloads.
   - Support scheduled background syncing through a headless worker (`background_sync_service.py`) that reuses the same persistence layer.

3. **ERP Integration**
   - Configuration UI for ERP endpoints, API tokens, and system selection (ERPNext/SAP placeholder).
   - Test-connection workflow and “Send to ERP”/auto-sync trigger points.
   - Custom sync modal for backfilling data since a selected date/time.

4. **User & Access Management**
   - Login overlay with predefined credentials, session handling in front-end scripts, and logout flows.
   - CRUD management of user accounts, roles, statuses, and password resets.
   - User activity history tracking via persistent storage module.

5. **Settings & Automation**
   - Auto-sync scheduler configuration (intervals, dummy/test mode) with status reporting.
   - Sync history view and manual sync controls, plus Windows Task Scheduler-friendly background executable.

6. **Desktop Packaging**
   - `desktop_app.py` wrapper using `pywebview` to host the web UI in a native window.
   - Windows build automation through `build_windows.bat`, bundling assets and hidden imports via PyInstaller.

### Out of Scope
- Real-time LAN discovery implementation (current stub relies on future development).
- Production-grade backend security (e.g., hashed passwords, JWT, HTTPS certificate management).
- Cross-platform installers beyond the provided Windows batch build.
- High-availability server deployment; current architecture targets single-node desktop/server use.
- Advanced ERP workflows beyond ERPNext push (e.g., bidirectional sync, approval flows).

## 4. Deliverables
- Python-based web server (`biometric_web_app_fixed.py`) with enhanced UI and REST endpoints.
- Front-end HTML/CSS/JS embedded in handler response for login, device, data, ERP, user, and settings tabs.
- Persistent storage module (`data_storage.py`) managing JSON data files under user-specific directories.
- Desktop launcher (`desktop_app.py`) and Windows build script (`build_windows.bat`).
- Headless background sync worker (`background_sync_service.py`) packaged alongside the desktop app for unattended ERP pushes.
- ZK device bridge utility (`zk_bridge.py`) for diagnostic data retrieval from biometric hardware.
- Project documentation (scope document and README).

## 5. Assumptions
- Target biometric hardware exposes the ZKTeco-compatible protocol accessible over TCP/IP.
- Python dependencies (e.g., `pywebview`, `pyinstaller`, `zk`, `pillow`) are installable on target systems.
- ERPNext instance provides API keys with sufficient permissions and network access from the host.
- Deployment occurs within trusted networks; sensitive data storage hardening is handled externally.

## 6. Constraints
- Storage relies on local filesystem JSON files—no relational database integration.
- Web UI is served from Python’s built-in HTTP server; scalability is limited to small teams.
- Windows build script assumes a Windows environment with Python and pip available.
- External ERP connections require valid credentials; no credential vaulting is implemented.

## 7. Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Device connectivity failures due to network/firewall issues | Attendance gaps | Provide diagnostics in UI, allow manual retry and logging |
| Plaintext credential storage | Security exposure | Recommend external hardening (hashed storage) and restricted host access |
| ERP API downtime | Sync backlogs | Allow manual export and re-sync when services resume |
| Large data volumes in JSON files | Performance degradation | Encourage periodic exports and archival, consider DB migration if scale grows |

## 8. Success Metrics
- Successful connection and data retrieval from target biometric devices.
- Accurate, filterable attendance views and exports from UI.
- Successful test ERP connection and data push from application UI.
- Positive user feedback on admin workflow simplicity and stability.

## 9. Future Enhancements (Optional)
- Implement LAN discovery service and background heartbeats for device status.
- Migrate to hashed password storage and backend authentication service.
- Introduce database-backed storage (SQLite/PostgreSQL) for scalability.
- Expand ERP connectors (SAP, Oracle, custom REST) with configurable mappings.
- Add scheduling engine for unattended sync and reporting.
