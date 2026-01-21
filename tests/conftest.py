"""
Pytest configuration and fixtures for system tests
"""

import pytest
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from controller import app as flask_app


@pytest.fixture(scope="session")
def test_dir():
    """Create temporary test directory"""
    test_dir = tempfile.mkdtemp(prefix="iot_test_")
    yield test_dir
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_certs_dir(test_dir):
    """Create temporary certificates directory"""
    certs_dir = os.path.join(test_dir, "test_certs")
    os.makedirs(certs_dir, exist_ok=True)
    return certs_dir


@pytest.fixture(scope="session")
def test_db_path(test_dir):
    """Create temporary database path"""
    return os.path.join(test_dir, "test_identity.db")


@pytest.fixture(scope="session")
def test_pending_db_path(test_dir):
    """Create temporary pending devices database path"""
    return os.path.join(test_dir, "test_pending_devices.db")


@pytest.fixture(scope="function")
def flask_client():
    """Create Flask test client"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def test_device_id():
    """Generate test device ID"""
    import uuid
    return f"TEST_DEVICE_{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture(scope="function")
def test_mac_address():
    """Generate test MAC address"""
    import random
    return ":".join([f"{random.randint(0, 255):02X}" for _ in range(6)])


@pytest.fixture(scope="function")
def clean_onboarding_system(test_certs_dir, test_db_path):
    """Clean onboarding system for testing"""
    # Import here to avoid issues if modules not available
    try:
        from identity_manager.device_onboarding import DeviceOnboarding
        
        # Create fresh onboarding instance
        onboarding = DeviceOnboarding(
            certs_dir=test_certs_dir,
            db_path=test_db_path
        )
        
        yield onboarding
        
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        if os.path.exists(test_certs_dir):
            shutil.rmtree(test_certs_dir, ignore_errors=True)
    except ImportError:
        pytest.skip("Device onboarding not available")


@pytest.fixture(scope="function")
def clean_pending_devices(test_pending_db_path):
    """Clean pending devices manager for testing"""
    try:
        from network_monitor.pending_devices import PendingDeviceManager
        
        # Remove existing database if any
        if os.path.exists(test_pending_db_path):
            os.remove(test_pending_db_path)
        
        manager = PendingDeviceManager(db_path=test_pending_db_path)
        
        yield manager
        
        # Cleanup
        if os.path.exists(test_pending_db_path):
            os.remove(test_pending_db_path)
    except ImportError:
        pytest.skip("Pending devices manager not available")


@pytest.fixture(scope="function")
def clean_auto_onboarding_service(clean_onboarding_system, clean_pending_devices):
    """Clean auto-onboarding service for testing"""
    try:
        from network_monitor.auto_onboarding_service import AutoOnboardingService
        
        service = AutoOnboardingService(
            onboarding_module=clean_onboarding_system,
            identity_db=clean_onboarding_system.identity_db if clean_onboarding_system else None
        )
        
        yield service
        
        # Stop service if running
        if service.is_running():
            service.stop()
    except ImportError:
        pytest.skip("Auto-onboarding service not available")


@pytest.fixture(scope="function")
def authorized_device():
    """Create authorized device data"""
    return {
        "device_id": "ESP32_2",
        "mac_address": "AA:BB:CC:DD:EE:02"
    }


@pytest.fixture(scope="function")
def unauthorized_device():
    """Create unauthorized device data"""
    return {
        "device_id": "ESP32_4",
        "mac_address": "AA:BB:CC:DD:EE:04"
    }


@pytest.fixture(scope="function")
def sample_sensor_data():
    """Create sample sensor data"""
    import time
    return {
        "device_id": "ESP32_2",
        "token": None,  # Will be set in tests
        "timestamp": str(int(time.time())),
        "data": "25.5",
        "size": 100,
        "protocol": 6,
        "src_port": 8080,
        "dst_port": 5000
    }

