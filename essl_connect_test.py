#!/usr/bin/env python3
"""
Alternative ESSL AirFace Orcus Connection Script
This script uses extended timeout and different connection parameters
"""

import sys
import json
from zk import ZK
from datetime import datetime

def connect_essl_orcus(ip, port=4370):
    """
    Try to connect to ESSL AirFace Orcus with extended parameters
    """
    print(f"Attempting to connect to ESSL AirFace Orcus at {ip}:{port}")
    print(f"Using extended timeout (60 seconds)...")
    
    # Try with very long timeout - ESSL face devices can be slow
    strategies = [
        # Extended timeout strategies
        {'password': 0, 'timeout': 60, 'force_udp': False, 'ommit_ping': True, 'verbose': True},
        {'password': 0, 'timeout': 60, 'force_udp': True, 'ommit_ping': True, 'verbose': True},
        {'password': 0, 'timeout': 30, 'force_udp': False, 'ommit_ping': True, 'verbose': False},
        {'password': 1234, 'timeout': 60, 'force_udp': False, 'ommit_ping': True, 'verbose': True},
    ]
    
    for i, params in enumerate(strategies, 1):
        print(f"\n--- Strategy {i}/{len(strategies)} ---")
        print(f"Password: {params['password']}, Timeout: {params['timeout']}s, "
              f"UDP: {params['force_udp']}, Ommit Ping: {params['ommit_ping']}, "
              f"Verbose: {params['verbose']}")
        
        try:
            zk = ZK(
                ip,
                port=port,
                timeout=params['timeout'],
                password=params['password'],
                force_udp=params['force_udp'],
                ommit_ping=params['ommit_ping'],
                verbose=params['verbose']
            )
            
            print("Connecting...")
            conn = zk.connect()
            print("✅ CONNECTED!")
            
            # Get device info
            try:
                print("\nDevice Information:")
                print(f"  Firmware: {conn.get_firmware_version()}")
                print(f"  Serial: {conn.get_serialnumber()}")
                print(f"  Platform: {conn.get_platform()}")
                print(f"  Device Name: {conn.get_device_name()}")
            except Exception as e:
                print(f"  Could not get device info: {e}")
            
            # Get users
            try:
                print("\nFetching users...")
                users = conn.get_users()
                print(f"  Users found: {len(users) if users else 0}")
                if users:
                    for u in users[:5]:  # Show first 5
                        print(f"    - UID: {u.uid}, User ID: {u.user_id}, Name: {u.name}")
            except Exception as e:
                print(f"  Could not get users: {e}")
            
            # Get attendance
            try:
                print("\nFetching attendance records...")
                attendance = conn.get_attendance()
                print(f"  Attendance records found: {len(attendance) if attendance else 0}")
                
                if not attendance or len(attendance) == 0:
                    print("\n⚠️  WARNING: No attendance records found!")
                    print("  This usually means:")
                    print("  1. Device is in PUSH/ADMS mode (check device settings)")
                    print("  2. No punches have been recorded yet")
                    print("  3. Device memory was cleared")
                    print("\n  To fix:")
                    print("  - Go to device: Menu → Comm → Connection Mode")
                    print("  - Change to 'TCP/IP' (not ADMS or Push)")
                    print("  - Restart device and try again")
                else:
                    # Show sample records
                    print("\n  Sample records:")
                    for i, rec in enumerate(attendance[:5]):
                        print(f"    [{i+1}] User: {rec.user_id}, Time: {rec.timestamp}, "
                              f"Status: {getattr(rec, 'status', '?')}, "
                              f"Punch: {getattr(rec, 'punch', '?')}")
            except Exception as e:
                print(f"  Could not get attendance: {e}")
            
            conn.disconnect()
            print("\n✅ SUCCESS! Device is working correctly.")
            print(f"\nUse these settings in your app:")
            print(f"  IP: {ip}")
            print(f"  Port: {port}")
            print(f"  Password: {params['password']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            continue
    
    print("\n" + "="*60)
    print("❌ ALL CONNECTION ATTEMPTS FAILED")
    print("="*60)
    print("\nTroubleshooting steps:")
    print("1. Verify device IP address:")
    print("   - Check on device: Menu → Comm → IP Address")
    print("   - Try pinging: ping", ip)
    print("\n2. Check device connection mode:")
    print("   - Go to: Menu → Comm → Connection Mode")
    print("   - Should be: TCP/IP (NOT ADMS or Push)")
    print("\n3. Check port number:")
    print("   - Default is 4370")
    print("   - Some devices use 5005 or 8080")
    print("   - Try: python3", sys.argv[0], ip, "5005")
    print("\n4. Check firewall:")
    print("   - Ensure port", port, "is not blocked")
    print("   - Try disabling firewall temporarily")
    print("\n5. Check device password:")
    print("   - Go to: Menu → Comm → Comm Password")
    print("   - Default is usually 0 or 1234")
    print("\n6. Network connectivity:")
    print("   - Ensure device and computer are on same network")
    print("   - Check if device responds to ping")
    print("\n7. Device firmware:")
    print("   - Update to latest firmware from ESSL website")
    print("   - https://www.esslsecurity.com/support")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 essl_connect_test.py <ip> [port]")
        print("Example: python3 essl_connect_test.py 192.168.1.201")
        print("Example: python3 essl_connect_test.py 192.168.1.201 4370")
        sys.exit(1)
    
    ip = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 4370
    
    connect_essl_orcus(ip, port)
