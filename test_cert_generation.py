#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Certificate Generation
Verifies that the CA can generate device certificates
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("Testing Certificate Generation")
print("=" * 60)
print()

try:
    from identity_manager.device_onboarding import DeviceOnboarding
    
    print("Initializing DeviceOnboarding...")
    onboarding = DeviceOnboarding(certs_dir="certs", db_path="identity.db")
    print("[OK] DeviceOnboarding initialized")
    print()
    
    # Test device info
    test_device_id = "TEST_ESP32_001"
    test_mac = "AA:BB:CC:DD:EE:01"
    
    print(f"Testing certificate generation for:")
    print(f"  Device ID: {test_device_id}")
    print(f"  MAC Address: {test_mac}")
    print()
    
    # Attempt to onboard test device
    result = onboarding.onboard_device(
        device_id=test_device_id,
        mac_address=test_mac,
        device_type="sensor",
        device_info="Test device for certificate validation"
    )
    
    print("Onboarding Result:")
    print("-" * 60)
    print(f"  Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        print(f"  Device ID: {result.get('device_id')}")
        print(f"  MAC Address: {result.get('mac_address')}")
        print(f"  Certificate: {result.get('certificate_path')}")
        print(f"  Private Key: {result.get('key_path')}")
        print(f"  Fingerprint: {result.get('device_fingerprint')}")
        print(f"  Profiling: {result.get('profiling')}")
        print()
        
        # Verify certificate file exists
        cert_path = result.get('certificate_path')
        key_path = result.get('key_path')
        
        if cert_path and os.path.exists(cert_path):
            print(f"[SUCCESS] Certificate file created: {cert_path}")
        else:
            print(f"[ERROR] Certificate file not found: {cert_path}")
            
        if key_path and os.path.exists(key_path):
            print(f"[SUCCESS] Private key file created: {key_path}")
        else:
            print(f"[ERROR] Private key file not found: {key_path}")
            
        print()
        print("[SUCCESS] Certificate generation is working!")
        print()
        print("Your system is now ready for device onboarding!")
        
    else:
        print(f"  Message: {result.get('message')}")
        print()
        print("[ERROR] Certificate generation failed")
        sys.exit(1)
        
    print("-" * 60)
    print()
    
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
