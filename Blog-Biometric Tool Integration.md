# Introducing Biometric Tools Manager: One Hub for Attendance Devices and ERP Sync

Keeping biometric attendance data tidy across multiple locations—and making sure it reaches your ERP—can feel like juggling chainsaws. **Biometric Tools Manager** changes that. It bundles everything you need into a single, desktop-friendly experience: manage devices, review attendance, and sync clean data to your ERP with confidence.

## Why We Built It

Organizations juggling ZKTeco or ESSL devices often face three pain points: scattered device controls, messy punch logs, and error-prone ERP uploads. We designed Biometric Tools Manager to centralize all three, so ops teams can stop firefighting and start trusting their numbers.

## What You Get Out of the Box

- **Unified device dashboard** – register, monitor, and control biometric hardware with status tracking.
- **Attendance insights on tap** – filter by date, employee, or device, and export to CSV, Excel, or PDF.
- **ERP-ready data flows** – configure ERPNext (and future connectors), test API credentials, and push records manually or on a schedule.
- **Role-based peace of mind** – give admins full control while limiting viewers to read-only access.
- **Run it your way** – use the browser-based UI or launch the desktop shell that wraps the same experience in a native window.
- **Always-on syncing** – a background service keeps sending punches even after you close the main app.

## How It Works Behind the Scenes

Biometric Tools Manager ships with a built-in HTTP server backed by JSON storage. The desktop shell (powered by PyWebView) displays the UI while sharing the same configuration files as the headless background helper. That means whether you hit “Sync Now” in the app or let the Task Scheduler trigger the service overnight, both routines read and update the same settings, last-sync timestamps, and history logs.

## From Installation to Daily Use

1. **Set up devices** – add or edit device details, and keep an eye on online/offline status.
2. **Fetch attendance** – pull fresh logs on demand, or schedule auto-sync intervals that suit your team.
3. **Review and export** – filter punches, verify records, and download them for audits or backups.
4. **Send to ERP** – push validated punches directly to ERPNext via API, with custom sync windows for catch-up scenarios.
5. **Deploy confidence** – package everything into Windows executables with a single batch script, then schedule unattended syncs through Task Scheduler.

## Built for Today, Ready for Tomorrow

The current release targets small to mid-sized teams that rely on local JSON storage and Windows deployments. As organizations scale, the roadmap includes deeper security hardening, richer ERP connectors, LAN discovery for devices, and database-backed storage options.

## Get Started

Clone the repository, install dependencies, and launch the server locally—or run the PyWebView desktop shell for an all-in-one experience. When you are ready to deploy, generate the Windows executables and hand them to your admins. They will appreciate the intuitive dashboard, and you will enjoy accurate ERP data without the late-night sync marathons.

Ready to take biometric attendance management from chaos to calm? Biometric Tools Manager is your shortcut.
