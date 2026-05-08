#!/usr/bin/env python3
"""
ADMS Push Listener for ESSL AIFace Orcus (and other ADMS-capable devices).

The device is configured to PUSH attendance records to a server via HTTP.
This module runs that server and stores received punches into the same
JSON storage used by the rest of the Biometric Tools Manager.

Device-side setup (do this once in the device web UI):
  Communication → Cloud Server
    Server Address : <this machine's LAN IP>
    Server Port    : 8000   (or whatever ADMS_PORT is set to)
    HTTPS          : OFF

Usage (standalone test):
    python3 adms_listener.py

The listener is also started automatically by biometric_web_app_fixed.py
when any device has mode='adms'.
"""

import http.server
import json
import threading
import urllib.parse
import urllib.request
from datetime import datetime
from data_storage import storage

# Fix for Windows threading bug with strptime
try:
    import _strptime
except ImportError:
    datetime.strptime('2000-01-01', '%Y-%m-%d')

# Thread-safe strptime wrapper
def safe_strptime(date_string, format_string):
    try:
        return datetime.strptime(date_string, format_string)
    except AttributeError:
        import time
        return datetime(*time.strptime(date_string, format_string)[:6])

ADMS_PORT = 8000

# ESSL Cloud Portal relay configuration
# Set ESSL_RELAY_URL to forward all data to ESSL's cloud portal
# Example: "http://cloud.esslsecurity.com:8000" or your ESSL portal URL
ESSL_RELAY_URL = None  # Set this to enable relay to ESSL portal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_adms_record(params):
    """
    Convert a flat ADMS query-string dict into a punch record.

    ADMS key reference (ZKTeco / ESSL ADMS protocol):
      table=ATTLOG  – attendance log push
      SN            – device serial number
      Stamp         – record timestamp  "YYYY-MM-DD HH:MM:SS"
      UserID        – employee ID on the device
      Verified      – verification method (0=finger,1=finger,4=face,15=face…)
      Status        – 0=check-in, 1=check-out, 4=OT-in, 5=OT-out …
    """
    table = params.get("table", [""])[0]
    if table.upper() != "ATTLOG":
        return None

    user_id   = params.get("UserID",  [None])[0]
    stamp     = params.get("Stamp",   [None])[0]
    status    = params.get("Status",  ["0"])[0]
    verified  = params.get("Verified",["0"])[0]
    sn        = params.get("SN",      ["unknown"])[0]

    if not user_id or not stamp:
        return None

    try:
        ts = safe_strptime(stamp.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    punch_type = "check-in" if str(status) in ("0", "4") else "check-out"

    return {
        "employeeId":   str(user_id).strip(),
        "employeeName": f"Employee {user_id}",   # name resolved later via ERP
        "timestamp":    ts.isoformat(),
        "punchType":    punch_type,
        "method":       "adms-push",
        "status":       "success",
        "deviceId":     sn,
        "rawData": {
            "verified": verified,
            "status":   status,
            "sn":       sn,
        },
    }


# ---------------------------------------------------------------------------
# In-memory buffer (also persisted via storage)
# ---------------------------------------------------------------------------

_lock    = threading.Lock()
_records = []


def get_buffered_records(clear=False):
    """Return (and optionally clear) all records received since last call."""
    with _lock:
        records = list(_records)
        if clear:
            _records.clear()
        return records


def _store_record(record):
    with _lock:
        _records.append(record)
    # Persist to adms_punches.json via storage helper
    try:
        existing = storage.load_adms_punches()
        existing.append(record)
        # Keep last 10 000 records on disk
        storage.save_adms_punches(existing[-10_000:])
    except Exception as e:
        print(f"[ADMS] storage error: {e}")


def _relay_to_essl(method: str, path: str, body: bytes = b"") -> bool:
    """Forward the request to ESSL cloud portal if relay is enabled."""
    if not ESSL_RELAY_URL:
        return True  # Relay disabled, consider success
    
    try:
        url = ESSL_RELAY_URL + path
        req = urllib.request.Request(url, data=body if method == "POST" else None, method=method)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            print(f"[ADMS-RELAY] ✅ Forwarded {method} to ESSL: {url[:80]}")
            return True
    except Exception as e:
        print(f"[ADMS-RELAY] ⚠️  Failed to forward to ESSL: {e}")
        return False


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class ADMSHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[ADMS] {self.address_string()} - {fmt % args}")

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode("utf-8", errors="replace")

    def _ok(self):
        body = b"OK"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs     = urllib.parse.parse_qs(parsed.query)
        sn     = qs.get("SN", ["?"])[0]

        print(f"[ADMS] GET {self.path} | SN={sn}")

        # Forward GET request to ESSL portal (relay)
        _relay_to_essl("GET", self.path)

        # ADMS registration/heartbeat — reply with server datetime + commands
        # The device reads this response and then POSTs its attendance logs
        # ATTLOGStamp=0 tells device to send ALL records (including old ones)
        # ATTLOGStamp=9999 tells device to only send new records
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = (f"GET OPTION FROM: {sn}\n"
                f"ATTLOGStamp=0\n"  # Changed from 9999 to 0 to request ALL records
                f"OPERLOGStamp=0\n"  # Changed from 9999 to 0
                f"ATTPHOTOStamp=0\n"  # Changed from 9999 to 0
                f"ErrorDelay=30\n"
                f"Delay=10\n"
                f"TransTimes=00:00;14:05\n"
                f"TransInterval=1\n"
                f"TransFlag=TransData AttLog\n"
                f"Realtime=1\n"
                f"Encrypt=None\n"
                f"ServerVer=2.4.1\n"
                f"PushProtVer=2.4.1\n"
                f"TableNameInstruction=ATTLOG\n").encode()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        print(f"[ADMS] ✅ Sent registration response to SN={sn} — device will now push ALL attendance records")

    def do_POST(self):
        parsed     = urllib.parse.urlparse(self.path)
        qs         = urllib.parse.parse_qs(parsed.query)
        raw_body   = self._read_body()
        body_params = urllib.parse.parse_qs(raw_body)
        params     = {**qs, **body_params}

        sn    = params.get("SN",    ["?"])[0]
        table = params.get("table", [""])[0]

        print(f"[ADMS] POST {self.path} | SN={sn} table={table}")
        print(f"[ADMS] Body: {raw_body[:500]}")

        saved = 0
        # ATTLOG can arrive as multiple lines in the body
        # Format per line: UserID Stamp Status Verified Reserved WorkCode
        for line in raw_body.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t") if "\t" in line else line.split()
            if len(parts) >= 3:
                try:
                    user_id = parts[0].strip()
                    stamp   = parts[1].strip()
                    status  = parts[2].strip()
                    verified = parts[3].strip() if len(parts) > 3 else "0"
                    ts = safe_strptime(stamp, "%Y-%m-%d %H:%M:%S")
                    punch_type = "check-in" if status in ("0", "4") else "check-out"
                    record = {
                        "employeeId":   user_id,
                        "employeeName": f"Employee {user_id}",
                        "timestamp":    ts.isoformat(),
                        "punchType":    punch_type,
                        "method":       "adms-push",
                        "status":       "success",
                        "deviceId":     sn,
                        "rawData":      {"verified": verified, "status": status, "sn": sn},
                    }
                    _store_record(record)
                    saved += 1
                    print(f"[ADMS] ✅ Punch: emp={user_id} time={stamp} type={punch_type}")
                except Exception as e:
                    print(f"[ADMS] ⚠️  Could not parse line '{line}': {e}")

        # Also try query-string / form-encoded single record (some firmware variants)
        if saved == 0:
            record = _parse_adms_record(params)
            if record:
                record["deviceId"] = sn
                _store_record(record)
                saved += 1
                print(f"[ADMS] ✅ Punch (form): emp={record['employeeId']} "
                      f"time={record['timestamp']} type={record['punchType']}")

        if saved == 0:
            print(f"[ADMS] ℹ️  No punch records parsed from POST body")

        # Forward POST request to ESSL portal (relay)
        _relay_to_essl("POST", self.path, raw_body.encode("utf-8"))

        self._ok()


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

_server = None
_thread = None


def start(port=ADMS_PORT):
    global _server, _thread
    if _server:
        return True
    try:
        _server = http.server.HTTPServer(("0.0.0.0", port), ADMSHandler)
        _thread = threading.Thread(target=_server.serve_forever, daemon=True)
        _thread.start()
        print(f"[ADMS] Listener started on port {port}")
        return True
    except Exception as e:
        print(f"[ADMS] Failed to start: {e}")
        _server = None
        return False


def stop():
    global _server, _thread
    if _server:
        _server.shutdown()
        _server = None
        _thread = None
        print("[ADMS] Listener stopped")


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Starting ADMS listener on port {ADMS_PORT} ...")
    print("Configure the device: Communication → Cloud Server → this machine's IP")
    print("Press Ctrl+C to stop.\n")
    start(ADMS_PORT)
    try:
        import time
        while True:
            time.sleep(5)
            recs = get_buffered_records()
            if recs:
                print(f"\n📋 {len(recs)} punch(es) received so far:")
                for r in recs:
                    print(f"  {r['employeeId']} | {r['timestamp']} | {r['punchType']} | device={r['deviceId']}")
    except KeyboardInterrupt:
        stop()
