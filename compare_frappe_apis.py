#!/usr/bin/env python3
"""
Quick test script to compare API responses between two Frappe instances
"""

import urllib.request
import urllib.error
import json
import sys

def test_frappe_endpoint(url, api_key, test_name):
    """Test a Frappe endpoint and show detailed results"""
    
    print(f"\n{'='*100}")
    print(f"TESTING: {test_name}")
    print(f"{'='*100}")
    
    # Clean URL
    if not url.startswith('http'):
        url = 'http://' + url
    if url.endswith('/'):
        url = url[:-1]
    
    print(f"Base URL: {url}")
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    
    # Test 1: Get employee list
    print(f"\n{'-'*100}")
    print("TEST 1: Fetching Employee List")
    print(f"{'-'*100}")
    
    try:
        api_url = f"{url}/api/resource/Employee?fields=[%22name%22,%22employee_name%22,%22attendance_device_id%22]&limit_page_length=5"
        print(f"URL: {api_url}")
        
        req = urllib.request.Request(api_url, method='GET')
        req.add_header('Authorization', f'token {api_key}')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"✓ Status: {response.status}")
            print(f"✓ Response Headers: {dict(response.headers)}")
            print(f"✓ Employee Count: {len(data.get('data', []))}")
            print(f"✓ Sample Data:")
            print(json.dumps(data, indent=2))
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"✗ HTTP Error {e.code}: {e.reason}")
        print(f"✗ Error Body: {error_body}")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    # Test 2: Create a test checkin
    print(f"\n{'-'*100}")
    print("TEST 2: Creating Test Employee Checkin")
    print(f"{'-'*100}")
    
    try:
        from datetime import datetime
        
        test_record = {
            'doctype': 'Employee Checkin',
            'employee': 'HR-EMP-00001',  # Use a test employee ID
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'log_type': 'IN',
            'device_id': 'Test Device'
        }
        
        api_url = f"{url}/api/resource/Employee%20Checkin"
        print(f"URL: {api_url}")
        print(f"Payload: {json.dumps(test_record, indent=2)}")
        
        data = json.dumps(test_record).encode('utf-8')
        req = urllib.request.Request(api_url, data=data, method='POST')
        req.add_header('Authorization', f'token {api_key}')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            print(f"✓ Status: {response.status}")
            print(f"✓ Response Headers: {dict(response.headers)}")
            print(f"✓ Response Body:")
            print(response_data)
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"✗ HTTP Error {e.code}: {e.reason}")
        print(f"✗ URL: {e.url}")
        print(f"✗ Response Headers: {dict(e.headers)}")
        print(f"✗ Error Body:")
        print(error_body)
        
        # Try to parse error as JSON
        try:
            error_json = json.loads(error_body)
            print(f"\n✗ Parsed Error:")
            print(json.dumps(error_json, indent=2))
        except:
            pass
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"{'='*100}\n")


if __name__ == "__main__":
    print("\n" + "="*100)
    print("FRAPPE API COMPARISON TEST")
    print("="*100)
    
    # Test configuration
    WORKING_URL = "https://auriga-demo.frappe.cloud/"
    WORKING_KEY = input("Enter API key for auriga-demo.frappe.cloud: ").strip()
    
    FAILING_URL = "https://kapilahr.m.frappe.cloud/"
    FAILING_KEY = input("Enter API key for kapilahr.m.frappe.cloud: ").strip()
    
    # Test both endpoints
    test_frappe_endpoint(WORKING_URL, WORKING_KEY, "WORKING INSTANCE (auriga-demo)")
    test_frappe_endpoint(FAILING_URL, FAILING_KEY, "FAILING INSTANCE (kapilahr.m)")
    
    print("\n" + "="*100)
    print("COMPARISON COMPLETE")
    print("="*100)
    print("\nLook for differences in:")
    print("  1. HTTP status codes")
    print("  2. Error messages")
    print("  3. Response headers")
    print("  4. API endpoint availability")
    print("="*100 + "\n")
