#!/usr/bin/env python3
"""
zk_bridge.py — Attendance fetcher for ESSL AirFace Orcus (and compatible ZKTeco devices)

The AirFace Orcus uses a newer hardware platform that sometimes requires:
  1. TCP connection with ommit_ping=True  (avoids ICMP ping blocking on network)
  2. UDP fallback if TCP handshake fails
  3. Different communication passwords (0 is default)
  4. Longer timeouts for face recognition units
  5. Correct punch-type decoding (status vs punch field)

Usage:
  python zk_bridge.py <ip> [port] [start_date YYYY-MM-DD] [end_date YYYY-MM-DD]
"""

import sys
import json
import html
from zk import ZK, const
from datetime import datetime

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


# ──────────────────────────────────────────────
# Punch-type helpers
# ──────────────────────────────────────────────

PUNCH_TYPE_MAP = {
    0: 'check-in',
    1: 'check-out',
    2: 'break-out',
    3: 'break-in',
    4: 'overtime-in',
    5: 'overtime-out',
}

STATUS_MAP = {
    0: 'check-in',
    1: 'check-out',
}


def _punch_label(record):
    """
    Newer devices (incl. face units) encode punch direction in the `punch`
    field, whilst older ones use the `status` field.  We try both.
    """
    punch = getattr(record, 'punch', None)
    status = getattr(record, 'status', None)

    # Prefer punch field if it gives a meaningful value
    if punch is not None and punch in PUNCH_TYPE_MAP:
        return PUNCH_TYPE_MAP[punch]
    if status is not None and status in STATUS_MAP:
        return STATUS_MAP[status]
    # Fallback: treat any non-zero as check-out
    if status is not None:
        return 'check-out' if status != 0 else 'check-in'
    return 'check-in'


# ──────────────────────────────────────────────
# Connection helper — tries several strategies
# ──────────────────────────────────────────────

def _try_connect(ip, port, password, timeout, force_udp, ommit_ping, verbose=False):
    """Attempt one specific connection strategy; raises on failure."""
    zk = ZK(
        ip,
        port=port,
        timeout=timeout,
        password=password,
        force_udp=force_udp,
        ommit_ping=ommit_ping,
        verbose=verbose,
    )
    conn = zk.connect()
    return conn


def _connect_with_fallback(ip, port=4370, timeout=30):
    """
    Try multiple connection strategies in order.
    Returns (conn, strategy_description) or raises the last exception.
    """
    strategies = [
        # (password, force_udp, ommit_ping, verbose, label)
        (0,    False, True,  False, "TCP, ommit_ping=True,  pwd=0"),
        (0,    False, False, False, "TCP, ommit_ping=False, pwd=0"),
        (0,    True,  True,  False, "UDP, ommit_ping=True,  pwd=0"),
        (0,    True,  False, False, "UDP, ommit_ping=False, pwd=0"),
        # Some ESSL units ship with non-zero default password
        (1234, False, True,  False, "TCP, ommit_ping=True,  pwd=1234"),
        (1234, True,  True,  False, "UDP, ommit_ping=True,  pwd=1234"),
        # Verbose mode for debugging
        (0,    False, True,  True,  "TCP, ommit_ping=True,  pwd=0, verbose=True"),
        (0,    True,  True,  True,  "UDP, ommit_ping=True,  pwd=0, verbose=True"),
    ]

    last_exc = None
    for password, force_udp, ommit_ping, verbose, label in strategies:
        print(f"  ↳ Trying strategy: {label} …")
        try:
            conn = _try_connect(ip, port, password, timeout, force_udp, ommit_ping, verbose)
            print(f"  ✅ Connected using: {label}")
            return conn, label
        except Exception as exc:
            print(f"  ✗ Failed ({label}): {exc}")
            last_exc = exc

    raise last_exc


# ──────────────────────────────────────────────
# Main fetch function
# ──────────────────────────────────────────────

def fetch_logs(ip, port=4370, start_date=None, end_date=None):
    """
    Connect to ESSL AirFace Orcus and fetch attendance data.
    Returns a dict suitable for JSON serialisation.
    """
    conn = None
    strategy_used = "unknown"

    try:
        print(f"� Connecting to ESSL AirFace Orcus at {ip}:{port} …")
        conn, strategy_used = _connect_with_fallback(ip, port)

        # Disable device while reading (prevents new punches mid-read)
        try:
            conn.disable_device()
            print("⏸  Device disabled for safe read")
        except Exception as de:
            print(f"⚠️  disable_device() failed (non-fatal): {de}")

        # ── Users ────────────────────────────────────────────────
        print("👥 Fetching users …")
        user_dict = {}
        try:
            users = conn.get_users()
            if users:
                for u in users:
                    clean_name = html.unescape(u.name) if u.name else f'Employee {u.uid}'
                    user_dict[u.uid] = clean_name
                print(f"   ✅ {len(users)} users found")
                for u in users:
                    print(f"   User uid={u.uid}  user_id={u.user_id}  name='{u.name}'")
            else:
                print("   ⚠️  No users returned")
        except Exception as ue:
            print(f"   ⚠️  get_users() failed (non-fatal): {ue}")

        # ── Attendance ───────────────────────────────────────────
        print("� Fetching attendance logs …")
        attendance = conn.get_attendance()

        records = []

        if not attendance:
            print("⚠️  No attendance records returned from device.")
            print("   Possible causes:")
            print("   • Device has no punches stored yet")
            print("   • Device uses Push mode — it sends data to a server instead of storing locally")
            print("   • Protocol/firmware mismatch — try enabling ADMS/PUSH on the device")
        else:
            print(f"✅ {len(attendance)} raw records received")

            # Date filtering
            start_dt = safe_strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end_dt   = safe_strptime(end_date,   "%Y-%m-%d").date() if end_date   else None

            filtered = []
            for rec in attendance:
                rd = rec.timestamp.date()
                if start_dt and rd < start_dt:
                    continue
                if end_dt and rd > end_dt:
                    continue
                filtered.append(rec)

            # If no date filter, return last 200 records to avoid huge payloads
            if not start_dt and not end_dt:
                filtered = sorted(attendance, key=lambda x: x.timestamp, reverse=True)[:200]
                print(f"ℹ️  No date filter — showing latest {len(filtered)} records")
            else:
                print(f"📅 {len(filtered)} records match filter ({start_date or 'any'} → {end_date or 'any'})")

            # Debug: show first 5
            print("📊 Sample records:")
            for i, rec in enumerate(filtered[:5]):
                uid       = getattr(rec, 'uid', '?')
                user_id   = rec.user_id
                ts        = rec.timestamp
                status    = getattr(rec, 'status', '?')
                punch     = getattr(rec, 'punch', '?')
                ptype     = _punch_label(rec)
                name      = user_dict.get(user_id, user_dict.get(uid, f'ID_{user_id}'))
                print(f"  [{i+1}] uid={uid} user_id={user_id} name='{name}' ts={ts} status={status} punch={punch} → {ptype}")

            # Build output records
            for rec in filtered:
                uid     = getattr(rec, 'uid', rec.user_id)
                user_id = rec.user_id
                name    = user_dict.get(user_id, user_dict.get(uid, f'Employee_{user_id}'))
                ptype   = _punch_label(rec)

                records.append({
                    'employeeId':   str(user_id),
                    'employeeName': name,
                    'timestamp':    rec.timestamp.isoformat(),
                    'punchType':    ptype,
                    'method':       'zk-python',
                    'status':       'success',
                    'deviceId':     'ESSL_AirFace_Orcus',
                    'rawData': {
                        'uid':     uid,
                        'user_id': user_id,
                        'status':  getattr(rec, 'status', None),
                        'punch':   getattr(rec, 'punch',  None),
                    },
                })

        # Re-enable device
        try:
            conn.enable_device()
            print("▶  Device re-enabled")
        except Exception as ee:
            print(f"⚠️  enable_device() failed (non-fatal): {ee}")

        return {
            'success':      True,
            'timestamp':    datetime.now().isoformat(),
            'deviceStatus': 'online',
            'deviceId':     'ESSL_AirFace_Orcus',
            'strategy':     strategy_used,
            'punchRecords': records,
            'source':       'zk-python',
            'message':      f'✅ Connected via {strategy_used} — {len(records)} record(s) found',
        }

    except Exception as e:
        err = str(e)
        print(f"❌ Fatal error: {err}")

        # Actionable advice based on common error messages
        if 'timed out' in err.lower() or 'timeout' in err.lower():
            advice = ("Timeout — check IP/port and network. "
                      "Verify device is on the same LAN and firewall allows port 4370.")
        elif 'connection refused' in err.lower():
            advice = ("Connection refused — device may be using a different port. "
                      "Check device Network settings (some ESSL devices use port 4370 or 5005).")
        elif 'no route to host' in err.lower():
            advice = "No route to host — device is unreachable. Verify IP address."
        else:
            advice = ("Try: (1) Set ommit_ping=True in code, "
                      "(2) Verify device supports ZK TCP/IP protocol, "
                      "(3) Check if device uses 'Push' (ADMS) mode instead of pull. "
                      "If device is in Push mode, you need a receiver server instead of this poller.")

        return {
            'success': False,
            'error':   err,
            'advice':  advice,
            'message': f'❌ All connection strategies failed: {err}',
        }

    finally:
        if conn:
            try:
                conn.disconnect()
                print("🔌 Disconnected.")
            except Exception:
                pass


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'Usage: zk_bridge.py <ip> [port] [start_date] [end_date]'}))
        sys.exit(1)

    _ip         = sys.argv[1]
    _port       = int(sys.argv[2]) if len(sys.argv) > 2 else 4370
    _start_date = sys.argv[3] if len(sys.argv) > 3 else None
    _end_date   = sys.argv[4] if len(sys.argv) > 4 else None

    result = fetch_logs(_ip, _port, _start_date, _end_date)
    # Print final JSON result on the LAST line (caller parses this)
    print("\n--- RESULT ---")
    print(json.dumps(result, indent=2))