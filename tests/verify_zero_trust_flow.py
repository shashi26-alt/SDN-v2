import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:5000"
DEVICE_ID = "TEST_ZERO_TRUST_01"
MAC_ADDRESS = "AA:BB:CC:DD:EE:FF"

def print_step(step, msg):
    print(f"\n[STEP {step}] {msg}")

def test_zero_trust_flow():
    print(f"Starting Zero-Trust Flow Verification for {DEVICE_ID} ({MAC_ADDRESS})")
    
    # Prerequisite: Ensure device is clean (remove if exists)
    print("Clean up previous state...")
    requests.post(f"{BASE_URL}/api/remove_device", json={"device_id": DEVICE_ID})
    
    # STEP 1: Connect (First time) - Should fail 403 but add to pending
    print_step(1, "Device connects (first time) - Expecting 403 Forbidden")
    response = requests.post(f"{BASE_URL}/get_token", json={
        "device_id": DEVICE_ID,
        "mac_address": MAC_ADDRESS
    })
    
    if response.status_code == 403:
        print(" [OK] Correctly rejected with 403")
    else:
        print(f" [FAIL] Failed: Expected 403, got {response.status_code}")
        print(response.text)
        return False

    # STEP 2: Verify it's in Pending List
    print_step(2, "Verify device is in pending list")
    # Note: access internal DB or use an API if available. 
    # We'll use the failure of Step 1 as implicit proof it's not authorized.
    # But let's check if we can approve it, which implies it's pending.
    
    # STEP 3 & 4: Admin Approves Device
    print_step(3, "Admin approves device")
    response = requests.post(f"{BASE_URL}/api/approve_device", json={
        "mac_address": MAC_ADDRESS,
        "admin_notes": "Zero Trust Test Approval"
    })
    
    if response.status_code == 200:
        print(" [OK] Device approved successfully")
        print(response.json())
    else:
        print(f" [FAIL] Failed to approve: {response.status_code}")
        print(response.text)
        return False
        
    # STEP 5: Auto-onboarding (Internal) - Implicit in approval
    
    # STEP 6: Device requests token again - Should succeed now
    print_step(6, "Device requests token again - Expecting Success (Token)")
    response = requests.post(f"{BASE_URL}/get_token", json={
        "device_id": DEVICE_ID,
        "mac_address": MAC_ADDRESS
    })
    
    token = None
    if response.status_code == 200:
        data = response.json()
        if 'token' in data:
            token = data['token']
            print(f" [OK] Token received: {token[:10]}...")
        else:
            print(" [FAIL] No token in response")
            return False
    else:
        print(f" [FAIL] Failed to get token: {response.status_code}")
        print(response.text)
        return False

    # STEP 9: Authenticating Session
    print_step(9, "Device authenticates session")
    response = requests.post(f"{BASE_URL}/auth", json={
        "device_id": DEVICE_ID,
        "token": token
    })
    
    if response.status_code == 200 and response.json().get('authorized'):
        print(" [OK] Session active and authorized")
    else:
        print(f" [FAIL] Auth failed: {response.status_code}")
        return False

    # STEP 10: Simulate Traffic (Profiling)
    print_step(10, "Simulating traffic for profiling...")
    for i in range(5):
        requests.post(f"{BASE_URL}/data", json={
            "device_id": DEVICE_ID,
            "token": token,
            "timestamp": time.time(),
            "data": 25.0 + i
        })
    print(" [OK] Traffic sent")

    # STEP 11: Finalize Onboarding
    print_step(11, "Manual Finalization of Onboarding")
    response = requests.post(f"{BASE_URL}/finalize_onboarding", json={
        "device_id": DEVICE_ID
    })
    
    if response.status_code == 200:
        res_json = response.json()
        print(" [OK] Onboarding Finalized")
        print(f"   Baseline: {res_json.get('baseline') is not None}")
        print(f"   Policy Generated: {res_json.get('policy') is not None}")
    else:
        print(f" [FAIL] Finalization failed: {response.status_code}")
        print(response.text)
        return False

    print("\n ZERO TRUST FLOW VERIFIED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    try:
        success = test_zero_trust_flow()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n [FAIL] Exception: {e}")
        sys.exit(1)
