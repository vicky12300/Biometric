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
import os
import sys
import threading
import traceback
import builtins
import urllib.parse
import urllib.request
from datetime import datetime
from data_storage import storage

DEBUG_LOG_FILE = os.path.join(storage.get_data_dir(), "adms_debug.log")

def debug_log(message, exc=None):
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"[{timestamp}] [ADMS] {message}", flush=True)
    if exc is not None:
        print(f"[{timestamp}] [ADMS] EXCEPTION: {repr(exc)}", flush=True)
        traceback.print_exc()
    try:
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] [ADMS] {message}\n")
            if exc is not None:
                log_file.write(f"[{timestamp}] [ADMS] EXCEPTION: {repr(exc)}\n")
                log_file.write(traceback.format_exc())
                log_file.write("\n")
    except Exception:
        pass

# Thread-safe strptime wrapper
def safe_strptime(date_string, format_string):
    value = str(date_string).strip()
    debug_log(f"safe_strptime called value={value!r}, format={format_string!r}")

    if format_string == "%Y-%m-%d":
        try:
            year, month, day = map(int, value.split("-"))
            parsed = datetime(year, month, day)
            debug_log(f"safe_strptime parsed date value={value!r} -> {parsed.isoformat()}")
            return parsed
        except Exception as exc:
            debug_log(f"safe_strptime failed for date value={value!r}", exc)
            raise

    if format_string == "%Y-%m-%d %H:%M:%S":
        try:
            date_part, time_part = value.replace("T", " ", 1).split(" ", 1)
            year, month, day = map(int, date_part.split("-"))
            hour, minute, second = map(int, time_part.split(":"))
            parsed = datetime(year, month, day, hour, minute, second)
            debug_log(f"safe_strptime parsed datetime value={value!r} -> {parsed.isoformat()}")
            return parsed
        except Exception as exc:
            debug_log(f"safe_strptime failed for datetime value={value!r}", exc)
            raise

    debug_log(f"safe_strptime unsupported format={format_string!r}, value={value!r}")
    raise ValueError(f"Unsupported date format: {format_string}")

debug_log(
    "module loaded; "
    f"python={sys.version!r}; executable={sys.executable!r}; "
    f"frozen={getattr(sys, 'frozen', False)!r}; "
    f"_MEIPASS={getattr(sys, '_MEIPASS', None)!r}; "
    f"_strptime_loaded={'_strptime' in sys.modules}; "
    f"log_file={DEBUG_LOG_FILE!r}"
)

_original_import = builtins.__import__

def _debug_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "_strptime":
        debug_log("IMPORT ATTEMPT for _strptime\n" + "".join(traceback.format_stack(limit=20)))
    try:
        return _original_import(name, globals, locals, fromlist, level)
    except ModuleNotFoundError as exc:
        if name == "_strptime" or getattr(exc, "name", None) == "_strptime":
            debug_log(f"IMPORT FAILED for name={name!r}, exc_name={getattr(exc, 'name', None)!r}", exc)
        raise

builtins.__import__ = _debug_import

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
    debug_log(f"_parse_adms_record params_keys={list(params.keys())!r}")
    table = params.get("table", [""])[0]
    if table.upper() != "ATTLOG":
        debug_log(f"_parse_adms_record skipped table={table!r}")
        return None

    user_id   = params.get("UserID",  [None])[0]
    stamp     = params.get("Stamp",   [None])[0]
    status    = params.get("Status",  ["0"])[0]
    verified  = params.get("Verified",["0"])[0]
    sn        = params.get("SN",      ["unknown"])[0]

    if not user_id or not stamp:
        debug_log(f"_parse_adms_record missing user_id/stamp user_id={user_id!r}, stamp={stamp!r}")
        return None

    try:
        ts = safe_strptime(stamp.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        debug_log(f"_parse_adms_record invalid stamp={stamp!r}", exc)
        return None

    punch_type = "check-in" if str(status) in ("0", "4") else "check-out"

    record = {
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
    debug_log(f"_parse_adms_record parsed record employee={record['employeeId']!r}, timestamp={record['timestamp']!r}, punchType={record['punchType']!r}, deviceId={record['deviceId']!r}")
    return record


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
        debug_log(f"get_buffered_records clear={clear!r}, count={len(records)}")
        return records


def _store_record(record):
    debug_log(f"_store_record called employee={record.get('employeeId')!r}, timestamp={record.get('timestamp')!r}, deviceId={record.get('deviceId')!r}")
    with _lock:
        _records.append(record)
        debug_log(f"_store_record memory_count={len(_records)}")
    # Persist to adms_punches.json via storage helper
    try:
        existing = storage.load_adms_punches()
        existing.append(record)
        # Keep last 10 000 records on disk
        storage.save_adms_punches(existing[-10_000:])
        debug_log(f"_store_record saved total_after_append={len(existing)}")
    except Exception as e:
        debug_log("_store_record storage error", e)
        print(f"[ADMS] storage error: {e}")


def _relay_to_essl(method: str, path: str, body: bytes = b"") -> bool:
    """Forward the request to ESSL cloud portal if relay is enabled."""
    if not ESSL_RELAY_URL:
        debug_log(f"_relay_to_essl skipped relay disabled method={method!r}, path={path!r}, body_len={len(body)}")
        return True  # Relay disabled, consider success
    
    try:
        url = ESSL_RELAY_URL + path
        debug_log(f"_relay_to_essl forwarding method={method!r}, url={url!r}, body_len={len(body)}")
        req = urllib.request.Request(url, data=body if method == "POST" else None, method=method)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            debug_log(f"_relay_to_essl success response_preview={response_body[:200]!r}")
            print(f"[ADMS-RELAY] ✅ Forwarded {method} to ESSL: {url[:80]}")
            return True
    except Exception as e:
        debug_log("_relay_to_essl failed", e)
        print(f"[ADMS-RELAY] ⚠️  Failed to forward to ESSL: {e}")
        return False


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class ADMSHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        debug_log(f"http log from={self.address_string()!r}, message={fmt % args!r}")
        print(f"[ADMS] {self.address_string()} - {fmt % args}")

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        debug_log(f"_read_body content_length={length}")
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        debug_log(f"_read_body body_preview={body[:500]!r}")
        return body

    def _ok(self):
        body = b"OK"
        debug_log("_ok sending OK response")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs     = urllib.parse.parse_qs(parsed.query)
        sn     = qs.get("SN", ["?"])[0]
        debug_log(f"do_GET path={self.path!r}, client={self.client_address!r}, qs={qs!r}, sn={sn!r}")

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
        debug_log(f"do_GET sent registration response sn={sn!r}, body_len={len(body)}")
        print(f"[ADMS] ✅ Sent registration response to SN={sn} — device will now push ALL attendance records")

    def do_POST(self):
        parsed     = urllib.parse.urlparse(self.path)
        qs         = urllib.parse.parse_qs(parsed.query)
        raw_body   = self._read_body()
        body_params = urllib.parse.parse_qs(raw_body)
        params     = {**qs, **body_params}
        debug_log(f"do_POST path={self.path!r}, client={self.client_address!r}, qs={qs!r}, body_params_keys={list(body_params.keys())!r}, raw_body_preview={raw_body[:500]!r}")

        sn    = params.get("SN",    ["?"])[0]
        table = params.get("table", [""])[0]

        print(f"[ADMS] POST {self.path} | SN={sn} table={table}")
        print(f"[ADMS] Body: {raw_body[:500]}")
        debug_log(f"do_POST parsed sn={sn!r}, table={table!r}")

        saved = 0
        # ATTLOG can arrive as multiple lines in the body
        # Format per line: UserID Stamp Status Verified Reserved WorkCode
        for line in raw_body.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t") if "\t" in line else line.split()
            debug_log(f"do_POST processing line={line!r}, parts={parts!r}")
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
                    debug_log(f"do_POST saved line punch employee={user_id!r}, stamp={stamp!r}, punch_type={punch_type!r}, saved={saved}")
                    print(f"[ADMS] ✅ Punch: emp={user_id} time={stamp} type={punch_type}")
                except Exception as e:
                    debug_log(f"do_POST could not parse line={line!r}", e)
                    print(f"[ADMS] ⚠️  Could not parse line '{line}': {e}")

        # Also try query-string / form-encoded single record (some firmware variants)
        if saved == 0:
            record = _parse_adms_record(params)
            if record:
                record["deviceId"] = sn
                _store_record(record)
                saved += 1
                debug_log(f"do_POST saved form punch employee={record['employeeId']!r}, timestamp={record['timestamp']!r}, saved={saved}")
                print(f"[ADMS] ✅ Punch (form): emp={record['employeeId']} "
                      f"time={record['timestamp']} type={record['punchType']}")

        if saved == 0:
            debug_log("do_POST no punch records parsed")
            print(f"[ADMS] ℹ️  No punch records parsed from POST body")

        # Forward POST request to ESSL portal (relay)
        _relay_to_essl("POST", self.path, raw_body.encode("utf-8"))

        debug_log(f"do_POST completed saved={saved}")
        self._ok()


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

_server = None
_thread = None


def start(port=ADMS_PORT):
    global _server, _thread
    if _server:
        debug_log(f"start skipped existing server port={port}")
        return True
    try:
        debug_log(f"start attempting port={port}")
        _server = http.server.HTTPServer(("0.0.0.0", port), ADMSHandler)
        _thread = threading.Thread(target=_server.serve_forever, daemon=True)
        _thread.start()
        debug_log(f"start success port={port}, thread_alive={_thread.is_alive()}")
        print(f"[ADMS] Listener started on port {port}")
        return True
    except Exception as e:
        debug_log(f"start failed port={port}", e)
        print(f"[ADMS] Failed to start: {e}")
        _server = None
        return False


def stop():
    global _server, _thread
    if _server:
        debug_log("stop called")
        _server.shutdown()
        _server = None
        _thread = None
        debug_log("stop completed")
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
