#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CA Certificate Initialization Script
Creates the Certificate Authority (CA) needed for device certificate issuance
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("CA Certificate Initialization")
print("=" * 60)
print()

# Check if cryptography is available
try:
    import cryptography
    print(f"[OK] cryptography module found (version {cryptography.__version__})")
except ImportError:
    print("[ERROR] cryptography module not installed")
    print("   Please install: pip install cryptography")
    sys.exit(1)

# Import certificate manager
try:
    from identity_manager.certificate_manager import CertificateManager, CRYPTOGRAPHY_AVAILABLE
    print(f"[OK] certificate_manager imported successfully")
    print(f"   CRYPTOGRAPHY_AVAILABLE: {CRYPTOGRAPHY_AVAILABLE}")
except ImportError as e:
    print(f"[ERROR] Failed to import certificate_manager: {e}")
    sys.exit(1)

print()
print("Initializing Certificate Authority...")
print()

try:
    # Create certificate manager - this will auto-create CA if it doesn't exist
    cert_manager = CertificateManager(
        ca_cert_path="certs/ca_cert.pem",
        ca_key_path="certs/ca_key.pem",
        certs_dir="certs"
    )
    
    # Verify CA files exist
    ca_cert_path = os.path.abspath("certs/ca_cert.pem")
    ca_key_path = os.path.abspath("certs/ca_key.pem")
    
    if os.path.exists(ca_cert_path) and os.path.exists(ca_key_path):
        print("[SUCCESS] CA Certificate Authority created successfully!")
        print()
        print(f"   CA Certificate: {ca_cert_path}")
        print(f"   CA Private Key: {ca_key_path}")
        print()
        
        # Display CA certificate info
        ca_cert_content = cert_manager.get_ca_certificate()
        if ca_cert_content:
            print("CA Certificate Preview:")
            print("-" * 60)
            # Show first few lines
            lines = ca_cert_content.split('\n')[:5]
            for line in lines:
                print(f"   {line}")
            print("   ...")
            print("-" * 60)
            print()
        
        print("[SUCCESS] Certificate system is ready!")
        print()
        print("Next steps:")
        print("  1. Restart controller.py")
        print("  2. Approve a new device")
        print("  3. Verify certificates are created in certs/ directory")
        print()
        
    else:
        print("[WARNING] CA files were not created")
        print(f"   Expected at: {ca_cert_path}")
        print(f"   Expected at: {ca_key_path}")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] Failed to create CA")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
