#!/usr/bin/env python3
"""
Quick diagnostic for ESSL AirFace Orcus.
Usage:  python3 test_orcus.py <device-ip> [port]

Example: python3 test_orcus.py 192.168.1.201 4370
"""
import sys, socket
from zk import ZK, const

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_orcus.py <ip> [port]")
        sys.exit(1)

    ip   = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 4370

    # ── Step 1: TCP reachability ───────────────────────────────────────────
    print(f"\n[1] Checking TCP reachability  {ip}:{port} …")
    s = socket.socket()
    s.settimeout(5)
    try:
        s.connect((ip, port))
        print("    ✅ Port is open")
    except Exception as e:
        print(f"    ❌ Port CLOSED / unreachable: {e}")
        print("    → Verify IP in device menu  (Menu → Comm → Network)")
        sys.exit(1)
    finally:
        s.close()

    # ── Step 2: Try connection strategies ─────────────────────────────────
    strategies = [
        dict(password=0,    force_udp=False, ommit_ping=True,  label="TCP  ommit_ping=True  pwd=0"),
        dict(password=0,    force_udp=False, ommit_ping=False, label="TCP  ommit_ping=False pwd=0"),
        dict(password=0,    force_udp=True,  ommit_ping=True,  label="UDP  ommit_ping=True  pwd=0"),
        dict(password=0,    force_udp=True,  ommit_ping=False, label="UDP  ommit_ping=False pwd=0"),
        dict(password=1234, force_udp=False, ommit_ping=True,  label="TCP  ommit_ping=True  pwd=1234"),
        dict(password=1234, force_udp=True,  ommit_ping=True,  label="UDP  ommit_ping=True  pwd=1234"),
    ]

    print(f"\n[2] Trying {len(strategies)} connection strategies …")
    conn = None
    for strat in strategies:
        label = strat.pop("label")
        try:
            zk   = ZK(ip, port=port, timeout=15, **strat)
            conn = zk.connect()
            print(f"    ✅ Connected! Strategy: {label}")
            break
        except Exception as e:
            print(f"    ✗  {label:45s}  → {e}")
            conn = None
        finally:
            strat["label"] = label

    if conn is None:
        print("\n❌ All strategies failed.")
        print("   ► Make sure 'TCP/IP Comm Key' on device is 0  (Menu → Comm → Connection Password)")
        print("   ► Or add your password to the strategies list in this script.")
        sys.exit(1)

    # ── Step 3: Read device info ───────────────────────────────────────────
    print("\n[3] Reading device info …")
    try:
        info = conn.get_firmware_version()
        print(f"    Firmware : {info}")
    except Exception as e:
        print(f"    ⚠️  get_firmware_version() failed: {e}")
    try:
        name = conn.get_device_name()
        print(f"    Device   : {name}")
    except Exception as e:
        print(f"    ⚠️  get_device_name() failed: {e}")
    try:
        platform = conn.get_platform()
        print(f"    Platform : {platform}")
    except Exception as e:
        print(f"    ⚠️  get_platform() failed: {e}")

    # ── Step 4: Users ─────────────────────────────────────────────────────
    print("\n[4] Fetching users …")
    try:
        conn.disable_device()
        users = conn.get_users()
        if users:
            print(f"    ✅ {len(users)} users found")
            for u in users[:5]:
                print(f"       uid={u.uid}  user_id={u.user_id}  name='{u.name}'")
        else:
            print("    ⚠️  No users returned")
    except Exception as e:
        print(f"    ❌ get_users() error: {e}")

    # ── Step 5: Attendance ────────────────────────────────────────────────
    print("\n[5] Fetching attendance logs …")
    try:
        att = conn.get_attendance()
        if att:
            print(f"    ✅ {len(att)} records found")
            latest = sorted(att, key=lambda r: r.timestamp, reverse=True)[:5]
            print("    Latest 5:")
            for r in latest:
                print(f"       user_id={r.user_id}  uid={getattr(r,'uid','?')}  "
                      f"ts={r.timestamp}  status={getattr(r,'status','?')}  punch={getattr(r,'punch','?')}")
        else:
            print("    ⚠️  No attendance records found.")
            print("    Possible reasons:")
            print("    ● Device is in Push/ADMS mode — punches are sent to a server, not stored locally")
            print("    ● Device clock may be wrong (all records filtered out)")
            print("    ● No punches have been made yet")
    except Exception as e:
        print(f"    ❌ get_attendance() error: {e}")

    try:
        conn.enable_device()
    except Exception:
        pass
    try:
        conn.disconnect()
    except Exception:
        pass

    print("\n✅ Diagnostic complete.\n")

if __name__ == "__main__":
    main()
