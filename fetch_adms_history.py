#!/usr/bin/env python3
"""
Manual Historical Data Fetch for ADMS Devices

This script allows you to fetch old punches (1-2 days ago) from an ADMS device
using the ZK protocol (polling mode), even though the device is configured for ADMS push.

The device stores punches locally AND pushes them. This script polls the device
to get historical data that wasn't pushed when you changed servers.

Usage:
    python3 fetch_adms_history.py <device_ip> <days_back>

Example:
    python3 fetch_adms_history.py 172.20.10.4 3
    (fetches last 3 days of punches)
"""

import sys
import json
from datetime import datetime, timedelta
from zk import ZK
from data_storage import storage

def fetch_historical_punches(ip, days_back=3, port=4370):
    """
    Fetch historical punches from ADMS device using ZK protocol
    """
    print(f"\n{'='*60}")
    print(f"Fetching Historical Punches from ADMS Device")
    print(f"{'='*60}")
    print(f"Device IP: {ip}")
    print(f"Port: {port}")
    print(f"Days back: {days_back}")
    print(f"{'='*60}\n")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n")
    
    # Try to connect using ZK protocol
    strategies = [
        {'password': 0, 'force_udp': False, 'ommit_ping': True, 'timeout': 30},
        {'password': 0, 'force_udp': False, 'ommit_ping': False, 'timeout': 30},
        {'password': 0, 'force_udp': True, 'ommit_ping': True, 'timeout': 30},
        {'password': 1234, 'force_udp': False, 'ommit_ping': True, 'timeout': 30},
    ]
    
    conn = None
    for i, params in enumerate(strategies, 1):
        print(f"Trying connection strategy {i}/{len(strategies)}...")
        try:
            zk = ZK(ip, port=port, **params)
            conn = zk.connect()
            print(f"✅ Connected successfully!\n")
            break
        except Exception as e:
            print(f"❌ Failed: {e}")
            if i < len(strategies):
                print(f"Trying next strategy...\n")
    
    if not conn:
        print("\n❌ Could not connect to device using any strategy.")
        print("\nPossible reasons:")
        print("1. Device IP is incorrect")
        print("2. Device is not reachable on network")
        print("3. Device port is not 4370")
        print("4. Device does not support ZK protocol polling")
        return False
    
    try:
        # Disable device for safe reading
        try:
            conn.disable_device()
            print("⏸  Device disabled for safe read\n")
        except:
            pass
        
        # Get users
        print("Fetching users...")
        user_dict = {}
        try:
            users = conn.get_users()
            if users:
                for u in users:
                    user_dict[u.user_id] = u.name or f'Employee {u.user_id}'
                print(f"✅ Found {len(users)} users\n")
        except Exception as e:
            print(f"⚠️  Could not get users: {e}\n")
        
        # Get attendance
        print("Fetching attendance records...")
        attendance = conn.get_attendance()
        
        if not attendance:
            print("❌ No attendance records found on device")
            print("\nThis could mean:")
            print("1. Device has no punches stored")
            print("2. Device is in pure PUSH mode (doesn't store locally)")
            print("3. Device memory was cleared")
            return False
        
        print(f"✅ Found {len(attendance)} total records on device\n")
        
        # Filter by date range
        filtered = []
        for rec in attendance:
            rec_date = rec.timestamp.date()
            if start_date.date() <= rec_date <= end_date.date():
                filtered.append(rec)
        
        print(f"📅 {len(filtered)} records in date range ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})\n")
        
        if not filtered:
            print("No records found in the specified date range.")
            return False
        
        # Convert to our format
        records = []
        for rec in filtered:
            user_id = rec.user_id
            name = user_dict.get(user_id, f'Employee {user_id}')
            
            # Determine punch type
            status = getattr(rec, 'status', 0)
            punch = getattr(rec, 'punch', None)
            if punch is not None and punch in (0, 4):
                punch_type = 'check-in'
            elif punch is not None and punch in (1, 5):
                punch_type = 'check-out'
            elif status in (0, 4):
                punch_type = 'check-in'
            else:
                punch_type = 'check-out'
            
            record = {
                'employeeId': str(user_id),
                'employeeName': name,
                'timestamp': rec.timestamp.isoformat(),
                'punchType': punch_type,
                'method': 'zk-manual-fetch',
                'status': 'success',
                'deviceId': ip,
                'rawData': {
                    'status': status,
                    'punch': punch,
                }
            }
            records.append(record)
        
        # Re-enable device
        try:
            conn.enable_device()
            print("▶  Device re-enabled\n")
        except:
            pass
        
        # Show summary
        print(f"{'='*60}")
        print(f"Summary")
        print(f"{'='*60}")
        print(f"Total records fetched: {len(records)}")
        
        # Group by date
        by_date = {}
        for r in records:
            date = r['timestamp'][:10]
            by_date[date] = by_date.get(date, 0) + 1
        
        print(f"\nRecords by date:")
        for date in sorted(by_date.keys()):
            print(f"  {date}: {by_date[date]} punches")
        
        # Group by employee
        by_emp = {}
        for r in records:
            emp = r['employeeId']
            by_emp[emp] = by_emp.get(emp, 0) + 1
        
        print(f"\nRecords by employee:")
        for emp in sorted(by_emp.keys()):
            name = next((r['employeeName'] for r in records if r['employeeId'] == emp), emp)
            print(f"  {emp} ({name}): {by_emp[emp]} punches")
        
        print(f"\n{'='*60}\n")
        
        # Ask to save
        print("Do you want to save these records to ADMS storage?")
        print("This will add them to adms_punches.json so they can be synced to ERP.")
        response = input("Save? (yes/no): ").strip().lower()
        
        if response in ('yes', 'y'):
            # Load existing ADMS punches
            existing = storage.load_adms_punches()
            
            # Check for duplicates
            existing_timestamps = {(r['employeeId'], r['timestamp']) for r in existing}
            new_records = []
            duplicates = 0
            
            for r in records:
                key = (r['employeeId'], r['timestamp'])
                if key not in existing_timestamps:
                    new_records.append(r)
                else:
                    duplicates += 1
            
            if new_records:
                existing.extend(new_records)
                storage.save_adms_punches(existing[-10000:])  # Keep last 10k
                print(f"\n✅ Saved {len(new_records)} new records to ADMS storage")
                if duplicates > 0:
                    print(f"⏩ Skipped {duplicates} duplicate records")
                print(f"\nThese records will now be included in ERP sync.")
            else:
                print(f"\n⏩ All {len(records)} records already exist in storage (duplicates)")
        else:
            print("\n❌ Records not saved")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if conn:
            try:
                conn.disconnect()
                print("\n🔌 Disconnected from device")
            except:
                pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: Missing required arguments")
        print("\nUsage: python3 fetch_adms_history.py <device_ip> [days_back]")
        print("\nExamples:")
        print("  python3 fetch_adms_history.py 172.20.10.4 3")
        print("  python3 fetch_adms_history.py 192.168.1.201 7")
        sys.exit(1)
    
    ip = sys.argv[1]
    days_back = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    success = fetch_historical_punches(ip, days_back)
    
    if success:
        print("\n✅ Done! Historical punches have been fetched.")
        print("\nNext steps:")
        print("1. Go to the web app")
        print("2. Navigate to Data & Reports tab")
        print("3. Select your ADMS device")
        print("4. Click 'Fetch Data' to see all records")
        print("5. Click 'Send to ERP' to sync them")
    else:
        print("\n❌ Failed to fetch historical punches")
        print("\nTroubleshooting:")
        print("1. Verify device IP is correct")
        print("2. Check device is reachable: ping", ip)
        print("3. Try different port: python3 fetch_adms_history.py", ip, "3 5005")
        print("4. Check if device supports ZK protocol polling")
