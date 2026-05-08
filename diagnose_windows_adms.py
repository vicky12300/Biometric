#!/usr/bin/env python3
"""
Windows ADMS Listener Diagnostic Tool
Tests ADMS listener functionality and network connectivity on Windows
"""

import socket
import sys
import platform
import subprocess

def check_port_available(port=8000):
    """Check if port 8000 is available"""
    print(f"\n[1] Checking if port {port} is available...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"   ❌ Port {port} is already in use")
            return False
        else:
            print(f"   ✅ Port {port} is available")
            return True
    except Exception as e:
        print(f"   ⚠️  Error checking port: {e}")
        return False

def check_firewall_rules():
    """Check Windows Firewall rules for port 8000"""
    print("\n[2] Checking Windows Firewall rules...")
    
    if platform.system() != 'Windows':
        print("   ⚠️  Not running on Windows, skipping firewall check")
        return
    
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if 'Biometric ADMS' in result.stdout or '8000' in result.stdout:
            print("   ✅ Found firewall rules for ADMS listener")
        else:
            print("   ❌ No firewall rules found for port 8000")
            print("   💡 Run 'configure_windows_firewall.bat' as Administrator")
    except Exception as e:
        print(f"   ⚠️  Could not check firewall: {e}")

def get_local_ip():
    """Get local IP address"""
    print("\n[3] Getting local IP address...")
    try:
        # Connect to external server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"   ✅ Local IP: {local_ip}")
        return local_ip
    except Exception as e:
        print(f"   ⚠️  Could not determine local IP: {e}")
        return None

def test_device_connectivity(device_ip="192.168.1.119"):
    """Test if device is reachable"""
    print(f"\n[4] Testing connectivity to device {device_ip}...")
    
    if platform.system() == 'Windows':
        ping_cmd = ['ping', '-n', '2', device_ip]
    else:
        ping_cmd = ['ping', '-c', '2', device_ip]
    
    try:
        result = subprocess.run(
            ping_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"   ✅ Device {device_ip} is reachable")
            return True
        else:
            print(f"   ❌ Device {device_ip} is NOT reachable")
            print(f"   💡 Check network connection and device IP")
            return False
    except Exception as e:
        print(f"   ⚠️  Could not ping device: {e}")
        return False

def test_adms_listener_start():
    """Test if ADMS listener can start"""
    print("\n[5] Testing ADMS listener startup...")
    try:
        import adms_listener
        
        # Try to start listener
        success = adms_listener.start(8000)
        
        if success:
            print("   ✅ ADMS listener started successfully on port 8000")
            
            # Stop it after test
            adms_listener.stop()
            print("   ✅ ADMS listener stopped successfully")
            return True
        else:
            print("   ❌ ADMS listener failed to start")
            return False
    except ImportError:
        print("   ❌ Could not import adms_listener module")
        print("   💡 Make sure adms_listener.py is in the same directory")
        return False
    except Exception as e:
        print(f"   ❌ Error starting ADMS listener: {e}")
        return False

def print_summary(local_ip, device_ip="192.168.1.119"):
    """Print configuration summary"""
    print("\n" + "="*60)
    print("CONFIGURATION SUMMARY")
    print("="*60)
    print(f"\n📍 Server IP: {local_ip or 'Unknown'}")
    print(f"📍 Device IP: {device_ip}")
    print(f"📍 ADMS Port: 8000")
    print(f"\n🔧 Device Configuration:")
    print(f"   Server Address: {local_ip or 'YOUR_SERVER_IP'}")
    print(f"   Server Port: 8000")
    print(f"   HTTPS: OFF")
    print(f"\n🌐 Test URL: http://{local_ip or 'YOUR_SERVER_IP'}:8000")
    print("\n" + "="*60)

def main():
    print("="*60)
    print("Windows ADMS Listener Diagnostic Tool")
    print("="*60)
    
    # Run all checks
    port_ok = check_port_available(8000)
    check_firewall_rules()
    local_ip = get_local_ip()
    device_ok = test_device_connectivity("192.168.1.119")
    listener_ok = test_adms_listener_start()
    
    # Print summary
    print_summary(local_ip, "192.168.1.119")
    
    # Final verdict
    print("\n" + "="*60)
    print("DIAGNOSTIC RESULTS")
    print("="*60)
    
    all_ok = port_ok and device_ok and listener_ok
    
    if all_ok:
        print("\n✅ All checks passed! ADMS listener should work correctly.")
        print("\n📝 Next steps:")
        print("   1. Start the biometric application")
        print("   2. Configure device to push to this server")
        print("   3. Monitor ADMS listener logs for incoming data")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\n📝 Common fixes:")
        if not port_ok:
            print("   • Close any application using port 8000")
        if not device_ok:
            print("   • Check device IP address (currently: 192.168.1.119)")
            print("   • Verify device and server are on same network")
        if not listener_ok:
            print("   • Check Python dependencies (http.server)")
            print("   • Verify adms_listener.py is present")
        print("   • Run configure_windows_firewall.bat as Administrator")
    
    print("\n" + "="*60)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
