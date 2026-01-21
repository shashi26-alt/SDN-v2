"""
Test Device Onboarding Flow
Tests manual device onboarding, certificate generation, and database operations
"""

import pytest
import os
import json
import time


class TestDeviceOnboarding:
    """Test device onboarding scenarios"""
    
    def test_manual_onboarding_success(self, flask_client, test_device_id, test_mac_address):
        """Test successful manual device onboarding"""
        response = flask_client.post('/onboard', 
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address,
                'device_type': 'sensor',
                'device_info': 'Test sensor device'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['device_id'] == test_device_id
        assert data['mac_address'] == test_mac_address
        assert 'certificate_path' in data
        assert 'key_path' in data
        assert 'ca_certificate' in data
        assert data.get('profiling') is True
    
    def test_duplicate_device_rejection(self, flask_client, test_device_id, test_mac_address):
        """Test that duplicate device onboarding is rejected"""
        # First onboarding
        response1 = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        assert response1.status_code == 200
        
        # Attempt duplicate onboarding
        response2 = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        assert response2.status_code == 400
        data = json.loads(response2.data)
        assert data['status'] == 'error'
        assert 'already onboarded' in data['message'].lower()
    
    def test_onboarding_missing_fields(self, flask_client):
        """Test onboarding with missing required fields"""
        # Missing device_id
        response = flask_client.post('/onboard',
            json={'mac_address': 'AA:BB:CC:DD:EE:FF'},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'missing' in data['message'].lower()
        
        # Missing mac_address
        response = flask_client.post('/onboard',
            json={'device_id': 'TEST_DEVICE'},
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_certificate_generation(self, flask_client, test_device_id, test_mac_address):
        """Test that certificates are generated during onboarding"""
        response = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        cert_path = data.get('certificate_path')
        key_path = data.get('key_path')
        
        # Verify certificate files exist (if paths are absolute)
        if cert_path and os.path.isabs(cert_path):
            assert os.path.exists(cert_path), f"Certificate file not found: {cert_path}"
        if key_path and os.path.isabs(key_path):
            assert os.path.exists(key_path), f"Key file not found: {key_path}"
    
    def test_certificate_verification(self, flask_client, test_device_id, test_mac_address):
        """Test certificate verification endpoint"""
        # First onboard device
        onboard_response = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        assert onboard_response.status_code == 200
        
        # Verify certificate
        verify_response = flask_client.post('/verify_certificate',
            json={'device_id': test_device_id},
            content_type='application/json'
        )
        
        assert verify_response.status_code == 200
        data = json.loads(verify_response.data)
        assert data['status'] == 'success'
        assert data['device_id'] == test_device_id
        assert 'certificate_valid' in data
        assert 'device_status' in data
    
    def test_onboarding_database_entry(self, clean_onboarding_system, test_device_id, test_mac_address):
        """Test that onboarding creates database entry"""
        result = clean_onboarding_system.onboard_device(
            device_id=test_device_id,
            mac_address=test_mac_address,
            device_type='sensor'
        )
        
        assert result['status'] == 'success'
        
        # Verify database entry
        device_info = clean_onboarding_system.get_device_info(test_device_id)
        assert device_info is not None
        assert device_info['device_id'] == test_device_id
        assert device_info['mac_address'] == test_mac_address
        assert device_info['device_type'] == 'sensor'
        assert device_info['status'] == 'active'
    
    def test_onboarding_optional_fields(self, flask_client, test_device_id, test_mac_address):
        """Test onboarding with optional fields"""
        response = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address,
                'device_type': 'actuator',
                'device_info': 'Test actuator with additional info'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_onboarding_system_unavailable(self, flask_client, monkeypatch):
        """Test onboarding when system is unavailable"""
        # Mock unavailable system
        from controller import ONBOARDING_AVAILABLE
        monkeypatch.setattr('controller.ONBOARDING_AVAILABLE', False)
        
        response = flask_client.post('/onboard',
            json={
                'device_id': 'TEST_DEVICE',
                'mac_address': 'AA:BB:CC:DD:EE:FF'
            },
            content_type='application/json'
        )
        
        # Should return 503 or handle gracefully
        assert response.status_code in [400, 503]

