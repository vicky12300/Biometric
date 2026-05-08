#!/usr/bin/env python3
"""Background auto-sync worker for Biometric Tools Manager.

This script reuses the persisted UI configuration to fetch punches from all
configured devices and forward them to the configured ERP integration on a
fixed interval. It is designed to be run on Windows as a scheduled task or
service so that syncing continues even when the desktop application window is
closed.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from biometric_web_app_fixed import EnhancedBiometricHandler
from data_storage import storage
import adms_listener

LOGGER_NAME = "biometric_auto_sync"
DEFAULT_INTERVAL_MINUTES = 5
LOOKBACK_HOURS = 24
STATE_FILENAME = "auto_sync_state.json"
LOG_FILENAME = "auto_sync_service.log"


class BackgroundSyncService:
    """Continuously syncs device data to ERP based on saved UI configuration."""

    def __init__(self, force_mode: bool = False) -> None:
        self.data_dir = Path(storage.get_data_dir())
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.data_dir / STATE_FILENAME
        self.log_file = self.data_dir / LOG_FILENAME

        self._configure_logging()
        self.logger = logging.getLogger(LOGGER_NAME)

        # Use an uninitialised handler instance solely for helper methods.
        self.handler = EnhancedBiometricHandler.__new__(EnhancedBiometricHandler)

        self.state: Dict[str, Any] = self._load_state()
        self.force_mode = force_mode
        
        if self.force_mode:
            self.logger.info("BackgroundSyncService initialised in FORCE MODE; data dir=%s", self.data_dir)
        else:
            self.logger.info("BackgroundSyncService initialised; data dir=%s", self.data_dir)

    # ------------------------------------------------------------------
    # State handling
    # ------------------------------------------------------------------
    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                with self.state_file.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    devices = data.get("devices", {})
                    if isinstance(devices, dict):
                        return {"devices": devices, "last_run": data.get("last_run")}
            except Exception as exc:  # pragma: no cover - best-effort safeguard
                logging.getLogger(LOGGER_NAME).warning(
                    "Failed to read state file %s: %s", self.state_file, exc
                )
        return {"devices": {}, "last_run": None}

    def _save_state(self) -> None:
        self.state["last_run"] = datetime.utcnow().isoformat()
        try:
            with self.state_file.open("w", encoding="utf-8") as fh:
                json.dump(self.state, fh, indent=2)
        except Exception as exc:  # pragma: no cover - best-effort safeguard
            self.logger.error("Could not write state file %s: %s", self.state_file, exc)

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    def _load_auto_sync_config(self) -> Dict[str, Any]:
        settings = storage.load_settings() or {}
        auto_sync_cfg = settings.get("autoSync")

        if isinstance(auto_sync_cfg, dict):
            return {
                "enabled": bool(auto_sync_cfg.get("enabled", False)),
                "interval": int(auto_sync_cfg.get("interval", DEFAULT_INTERVAL_MINUTES) or DEFAULT_INTERVAL_MINUTES),
                "testMode": bool(auto_sync_cfg.get("testMode", False)),
            }

        # Backwards compatibility for legacy settings structure
        return {
            "enabled": bool(settings.get("autoSync", False)),
            "interval": int(settings.get("syncInterval", DEFAULT_INTERVAL_MINUTES) or DEFAULT_INTERVAL_MINUTES),
            "testMode": False,
        }

    # ------------------------------------------------------------------
    # Core syncing logic
    # ------------------------------------------------------------------
    def run_once(self) -> int:
        cfg = self._load_auto_sync_config()
        interval = max(int(cfg.get("interval", DEFAULT_INTERVAL_MINUTES)), 1)

        # In force mode (Task Scheduler), bypass the enabled check
        if not self.force_mode and not cfg.get("enabled", False):
            self.logger.info("Auto-sync disabled in settings; sleeping for %s minute(s)", interval)
            return interval
        
        if self.force_mode and not cfg.get("enabled", False):
            self.logger.info("Running in FORCE MODE - bypassing auto-sync disabled setting")

        erp_config = storage.load_erp_config() or {}
        if not erp_config.get("url") or not erp_config.get("apiKey"):
            self.logger.warning("ERP configuration incomplete; skipping sync cycle")
            return interval

        self.logger.debug(
            "Loaded ERP configuration for system=%s", erp_config.get("system")
        )

        devices = storage.load_devices() or []
        if not devices:
            self.logger.info("No devices configured; nothing to sync")
            return interval

        now = datetime.utcnow()
        all_records: List[Dict[str, Any]] = []
        device_updates: Dict[str, str] = {}

        for device in devices:
            device_id = str(device.get("id") or device.get("ip") or device.get("name") or "unknown")
            last_seen = self.state.get("devices", {}).get(device_id)
            lookback_start = now - timedelta(hours=LOOKBACK_HOURS)

            start_date = (datetime.fromisoformat(last_seen).date().isoformat() if last_seen else lookback_start.date().isoformat())
            end_date = now.date().isoformat()

            use_dummy = cfg.get("testMode", False) or device.get("mode") == "dummy"
            use_adms = device.get("mode") == "adms"

            try:
                if use_adms:
                    # For ADMS devices, fetch from stored punches
                    self.logger.debug("%s: ADMS mode - fetching from stored punches", device.get("name", device_id))
                    adms_records = storage.load_adms_punches()
                    
                    # Filter records for this device and after last_seen
                    device_sn = device.get("serialNumber") or device.get("ip") or device_id
                    filtered_records = []
                    for rec in adms_records:
                        rec_device = rec.get("deviceId", "")
                        rec_ts = rec.get("timestamp", "")
                        if rec_device == device_sn or rec_device == device_id:
                            if not last_seen or rec_ts > last_seen:
                                filtered_records.append(rec)
                    
                    result = {
                        "success": True,
                        "punchRecords": filtered_records,
                        "message": f"Loaded {len(filtered_records)} ADMS records"
                    }
                    storage.update_device_status(device_id, 'online', datetime.now().isoformat())
                elif use_dummy:
                    result = EnhancedBiometricHandler.generate_dummy_data(self.handler, start_date, end_date)
                    # Mark device as online for dummy mode
                    storage.update_device_status(device_id, 'online', datetime.now().isoformat())
                else:
                    port = int(device.get("port", 4370) or 4370)
                    result = EnhancedBiometricHandler.fetch_device_data(
                        self.handler,
                        device.get("ip"),
                        port=port,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    # Mark device as online on successful connection
                    storage.update_device_status(device_id, 'online', datetime.now().isoformat())
                    
            except Exception as exc:
                self.logger.error("%s: fetch error: %s", device.get("name", device_id), exc)
                # Mark device as offline on connection failure
                storage.update_device_status(device_id, 'offline')
                continue

            if not result.get("success"):
                self.logger.warning(
                    "%s: device fetch unsuccessful: %s",
                    device.get("name", device_id),
                    result.get("error") or result.get("message"),
                )
                # Mark device as offline if fetch was unsuccessful
                storage.update_device_status(device_id, 'offline')
                continue

            records = result.get("punchRecords", [])
            if not records:
                self.logger.debug("%s: no records returned", device.get("name", device_id))
                continue

            latest_ts = last_seen
            new_records = []

            for record in records:
                ts = record.get("timestamp")
                if not ts:
                    continue
                if last_seen and ts <= last_seen:
                    continue

                enriched = dict(record)
                enriched.setdefault("deviceName", device.get("name") or device.get("ip") or device_id)
                enriched["latitude"] = device.get("latitude")
                enriched["longitude"] = device.get("longitude")
                new_records.append(enriched)

                if latest_ts is None or ts > latest_ts:
                    latest_ts = ts

            if not new_records:
                self.logger.debug("%s: no new records after filtering", device.get("name", device_id))
                continue

            all_records.extend(new_records)
            if latest_ts:
                device_updates[device_id] = latest_ts

        if not all_records:
            self.logger.info("No new records to sync; next check in %s minute(s)", interval)
            self._save_state()
            return interval

        self.logger.info("Preparing to sync %d record(s) to ERP", len(all_records))

        try:
            if erp_config.get("system") == "frappe":
                response = EnhancedBiometricHandler.send_to_frappe(self.handler, all_records, erp_config)
            else:
                response = {
                    "success": True,
                    "message": f"Simulated sync for {len(all_records)} record(s) to {erp_config.get('system', 'ERP')}",
                    "details": {"success": len(all_records), "skipped": 0, "errors": 0},
                }
        except Exception as exc:
            self.logger.error("ERP sync failed: %s", exc)
            return interval

        if response.get("success"):
            self.logger.info("ERP sync successful: %s", response.get("message"))
            self._record_sync_history(len(all_records), response)
            # Persist last-seen timestamps only after successful push
            for key, ts in device_updates.items():
                self.state.setdefault("devices", {})[key] = ts
                # Also update the device record in storage so UI shows lastSync
                try:
                    storage.update_device_last_sync(key, ts)
                    self.logger.debug("Updated lastSync for device %s to %s", key, ts)
                except Exception as e:
                    self.logger.warning("Failed to update device lastSync for %s: %s", key, e)
            self._save_state()
        else:
            self.logger.error("ERP sync failed: %s", response.get("error") or response.get("message"))

        return interval

    # ------------------------------------------------------------------
    # History helpers
    # ------------------------------------------------------------------
    def _record_sync_history(self, sent_count: int, response: Dict[str, Any]) -> None:
        try:
            history = storage.load_sync_history() or []
            history_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "background_service",
                "recordsSent": sent_count,
                "details": response.get("details"),
                "message": response.get("message"),
            }
            history.append(history_entry)
            storage.save_sync_history(history)
        except Exception as exc:
            self.logger.warning("Unable to record sync history: %s", exc)

    # ------------------------------------------------------------------
    # Runtime loop
    # ------------------------------------------------------------------
    def run_forever(self) -> None:
        self.logger.info("Starting background sync loop")
        while True:
            try:
                interval = self.run_once()
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.exception("Unexpected error in run_once: %s", exc)
                interval = DEFAULT_INTERVAL_MINUTES
            time.sleep(max(interval, 1) * 60)

    # ------------------------------------------------------------------
    # Logging configuration
    # ------------------------------------------------------------------
    def _configure_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(self.log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Background auto-sync service for Biometric Tools Manager"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force sync to run regardless of autoSync.enabled setting (for Task Scheduler)"
    )
    
    args = parser.parse_args()
    
    service = BackgroundSyncService(force_mode=args.force)
    service.run_forever()


if __name__ == "__main__":
    main()
