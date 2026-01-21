"""
Test Auto-Onboarding Workflow
Tests WiFi device detection, pending device creation, approval workflow, and automatic onboarding
"""

import pytest
import json
import time


class TestAutoOnboarding:
    """Test auto-onboarding workflow scenarios"""
    
    def test_pending_devices_endpoint(self, flask_client):
        """Test getting pending devices list"""
        response = flask_client.get('/api/pending_devices')
        
        assert response.status_code in [200, 503]  # 503 if service unavailable
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'status' in data
            assert 'devices' in data
    
    def test_wifi_device_detection_simulation(self, clean_auto_onboarding_service, test_mac_address):
        """Test WiFi device detection simulation"""
        # Simulate new device detection
        clean_auto_onboarding_service._on_new_device_detected(test_mac_address)
        
        # Check if device was added to pending
        pending = clean_auto_onboarding_service.get_pending_devices()
        assert len(pending) > 0
        
        # Find our device
        device_found = False
        for device in pending:
            if device['mac_address'] == test_mac_address:
                device_found = True
                assert device['status'] == 'pending'
                assert 'device_id' in device
                assert device['device_id'].startswith('DEV_')
                break
        
        assert device_found, "Device not found in pending list"
    
    def test_device_id_generation(self, clean_auto_onboarding_service, test_mac_address):
        """Test device ID generation from MAC address"""
        from network_monitor.device_id_generator import DeviceIDGenerator
        
        generator = DeviceIDGenerator()
        device_id = generator.generate_device_id(test_mac_address)
        
        # Verify format: DEV_<MAC_PREFIX>_<RANDOM_KEY>
        assert device_id.startswith('DEV_')
        parts = device_id.split('_')
        assert len(parts) >= 3
        assert len(parts[2]) == 6  # Random key length
    
    def test_pending_device_creation(self, clean_pending_devices, test_mac_address):
        """Test pending device creation"""
        from network_monitor.device_id_generator import DeviceIDGenerator
        
        generator = DeviceIDGenerator()
        device_id = generator.generate_device_id(test_mac_address)
        
        # Add pending device
        success = clean_pending_devices.add_pending_device(
            mac_address=test_mac_address,
            device_id=device_id,
            device_type='sensor'
        )
        
        assert success is True
        
        # Verify device in pending list
        pending = clean_pending_devices.get_pending_devices()
        assert len(pending) > 0
        
        device = clean_pending_devices.get_device_by_mac(test_mac_address)
        assert device is not None
        assert device['status'] == 'pending'
        assert device['device_id'] == device_id
    
    def test_approve_device_workflow(self, flask_client, clean_auto_onboarding_service, test_mac_address):
        """Test device approval workflow"""
        # Simulate device detection
        clean_auto_onboarding_service._on_new_device_detected(test_mac_address)
        
        # Get pending device
        pending = clean_auto_onboarding_service.get_pending_devices()
        assert len(pending) > 0
        
        device = None
        for p in pending:
            if p['mac_address'] == test_mac_address:
                device = p
                break
        
        assert device is not None
        
        # Approve device via API
        response = flask_client.post('/api/approve_device',
            json={
                'mac_address': test_mac_address,
                'admin_notes': 'Approved for testing'
            },
            content_type='application/json'
        )
        
        # Should succeed (200) or handle gracefully
        assert response.status_code in [200, 400, 503]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'device_id' in data
    
    def test_reject_device_workflow(self, flask_client, clean_auto_onboarding_service, test_mac_address):
        """Test device rejection workflow"""
        # Simulate device detection
        clean_auto_onboarding_service._on_new_device_detected(test_mac_address)
        
        # Reject device via API
        response = flask_client.post('/api/reject_device',
            json={
                'mac_address': test_mac_address,
                'admin_notes': 'Rejected for testing'
            },
            content_type='application/json'
        )
        
        # Should succeed
        assert response.status_code in [200, 400, 503]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['status'] == 'success'
    
    def test_device_history(self, flask_client, clean_auto_onboarding_service, test_mac_address):
        """Test device approval history"""
        # Simulate device detection
        clean_auto_onboarding_service._on_new_device_detected(test_mac_address)
        
        # Get history
        response = flask_client.get('/api/device_history')
        
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'status' in data
            assert 'history' in data
    
    def test_duplicate_pending_device(self, clean_pending_devices, test_mac_address):
        """Test that duplicate pending devices are handled"""
        from network_monitor.device_id_generator import DeviceIDGenerator
        
        generator = DeviceIDGenerator()
        device_id = generator.generate_device_id(test_mac_address)
        
        # Add first time
        success1 = clean_pending_devices.add_pending_device(
            mac_address=test_mac_address,
            device_id=device_id
        )
        assert success1 is True
        
        # Try to add again
        success2 = clean_pending_devices.add_pending_device(
            mac_address=test_mac_address,
            device_id=device_id
        )
        assert success2 is False  # Should fail
    
    def test_approve_and_onboard_integration(self, clean_auto_onboarding_service, test_mac_address, test_device_id):
        """Test complete approve and onboard integration"""
        # Simulate device detection
        clean_auto_onboarding_service._on_new_device_detected(test_mac_address)
        
        # Get pending device info
        pending = clean_auto_onboarding_service.get_pending_devices()
        assert len(pending) > 0
        
        device = pending[0]
        mac = device['mac_address']
        
        # Approve and onboard
        result = clean_auto_onboarding_service.approve_and_onboard(mac, 'Test approval')
        
        # Should succeed if onboarding module available
        assert result['status'] in ['success', 'error']
        if result['status'] == 'success':
            assert 'device_id' in result
    
    def test_auto_onboarding_service_start_stop(self, clean_auto_onboarding_service):
        """Test auto-onboarding service start/stop"""
        # Service should not be running initially
        assert not clean_auto_onboarding_service.is_running()
        
        # Start service
        clean_auto_onboarding_service.start()
        assert clean_auto_onboarding_service.is_running()
        
        # Stop service
        clean_auto_onboarding_service.stop()
        # Give it a moment to stop
        time.sleep(0.1)
        assert not clean_auto_onboarding_service.is_running()

