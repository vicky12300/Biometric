#!/usr/bin/env python3
"""
ESSL AirFace Orcus Diagnostic Tool

This script helps diagnose connection issues with ESSL AirFace Orcus devices.
It tries multiple connection methods and provides detailed feedback.

Usage:
    python test_essl_orcus.py <device_ip> [port]

Example:
    python test_essl_orcus.py 192.168.1.201
    python test_essl_orcus.py 192.168.1.201 4370
"""

import sys
import socket
from zk import ZK

def test_network_connectivity(ip, port):
    """Test basic network connectivity"""
    print(f"\n{'='*60}")
    print(f"1. Testing Network Connectivity to {ip}:{port}")
    print(f"{'='*60}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is OPEN and reachable")
            return True
        else:
            print(f"❌ Port {port} is CLOSED or unreachable")
            print(f"   Error code: {result}")
            return False
    except socket.timeout:
        print(f"❌ Connection timeout - device not responding")
        return False
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def test_ping(ip):
    """Test ICMP ping"""
    print(f"\n{'='*60}")
    print(f"2. Testing ICMP Ping to {ip}")
    print(f"{'='*60}")
    
    import platform
    import subprocess
    
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', ip]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Device responds to ping")
            return True
        else:
            print(f"⚠️  Device does not respond to ping (may be blocked by firewall)")
            return False
    except Exception as e:
        print(f"⚠️  Ping test failed: {e}")
        return False

def test_zk_connection(ip, port, password=0, force_udp=False, ommit_ping=True, timeout=10):
    """Test ZK protocol connection"""
    try:
        zk = ZK(ip, port=port, timeout=timeout, password=password, 
                force_udp=force_udp, ommit_ping=ommit_ping)
        conn = zk.connect()
        
        # Get device info
        firmware = conn.get_firmware_version()
        serialnumber = conn.get_serialnumber()
        platform = conn.get_platform()
        device_name = conn.get_device_name()
        
        print(f"✅ CONNECTION SUCCESSFUL!")
        print(f"   Device Name: {device_name}")
        print(f"   Firmware: {firmware}")
        print(f"   Serial: {serialnumber}")
        print(f"   Platform: {platform}")
        
        # Try to get user count
        try:
            users = conn.get_users()
            print(f"   Users: {len(users) if users else 0}")
        except:
            print(f"   Users: Unable to fetch")
        
        # Try to get attendance count
        try:
            attendance = conn.get_attendance()
            print(f"   Attendance Records: {len(attendance) if attendance else 0}")
            
            if not attendance or len(attendance) == 0:
                print(f"\n⚠️  WARNING: Device connected but has NO attendance records!")
                print(f"   Possible reasons:")
                print(f"   • Device is in PUSH mode (sends data to server automatically)")
                print(f"   • No punches have been recorded yet")
                print(f"   • Device memory was cleared")
                print(f"\n   To check device mode:")
                print(f"   1. Go to device menu → Communication → Connection Mode")
                print(f"   2. Should be set to 'TCP/IP' or 'RS232/485' (not ADMS/Push)")
        except Exception as e:
            print(f"   Attendance Records: Error - {e}")
        
        conn.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    ip = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 4370
    
    print(f"\n{'#'*60}")
    print(f"# ESSL AirFace Orcus Diagnostic Tool")
    print(f"# Device: {ip}:{port}")
    print(f"{'#'*60}")
    
    # Test 1: Network connectivity
    network_ok = test_network_connectivity(ip, port)
    
    # Test 2: Ping
    ping_ok = test_ping(ip)
    
    if not network_ok:
        print(f"\n{'='*60}")
        print(f"❌ DIAGNOSIS: Network connectivity failed")
        print(f"{'='*60}")
        print(f"Possible solutions:")
        print(f"1. Verify the IP address is correct")
        print(f"2. Check if device is powered on")
        print(f"3. Verify device is on the same network/VLAN")
        print(f"4. Check firewall settings")
        print(f"5. Try different port (common: 4370, 5005)")
        return
    
    # Test 3: Try multiple ZK connection strategies
    print(f"\n{'='*60}")
    print(f"3. Testing ZK Protocol Connections")
    print(f"{'='*60}")
    
    strategies = [
        (0, False, True, "TCP with ommit_ping=True, password=0"),
        (0, False, False, "TCP with ommit_ping=False, password=0"),
        (0, True, True, "UDP with ommit_ping=True, password=0"),
        (0, True, False, "UDP with ommit_ping=False, password=0"),
        (1234, False, True, "TCP with ommit_ping=True, password=1234"),
        (1234, True, True, "UDP with ommit_ping=True, password=1234"),
    ]
    
    success = False
    for i, (pwd, udp, omit, desc) in enumerate(strategies, 1):
        print(f"\nStrategy {i}: {desc}")
        print(f"-" * 60)
        if test_zk_connection(ip, port, pwd, udp, omit):
            success = True
            print(f"\n{'='*60}")
            print(f"✅ SUCCESS! Use this configuration:")
            print(f"{'='*60}")
            print(f"IP: {ip}")
            print(f"Port: {port}")
            print(f"Password: {pwd}")
            print(f"Force UDP: {udp}")
            print(f"Ommit Ping: {omit}")
            break
    
    if not success:
        print(f"\n{'='*60}")
        print(f"❌ DIAGNOSIS: All connection strategies failed")
        print(f"{'='*60}")
        print(f"Possible solutions:")
        print(f"1. Device may be in PUSH/ADMS mode:")
        print(f"   • Go to device: Menu → Comm → Connection Mode")
        print(f"   • Change from 'ADMS' to 'TCP/IP'")
        print(f"2. Check device communication password:")
        print(f"   • Go to device: Menu → Comm → Comm Password")
        print(f"   • Note the password and update in device settings")
        print(f"3. Update device firmware to latest version")
        print(f"4. Try different port numbers (4370, 5005, 8080)")
        print(f"5. Contact ESSL support for protocol documentation")

if __name__ == "__main__":
    main()
