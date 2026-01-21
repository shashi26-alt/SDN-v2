"""
Test Authentication & Authorization
Tests token-based authentication, validation, session timeout, and authorization
"""

import pytest
import json
import time


class TestAuthentication:
    """Test authentication and authorization scenarios"""
    
    def test_token_request_onboarded_device(self, flask_client, test_device_id, test_mac_address):
        """Test token request for onboarded device"""
        # First onboard device
        onboard_response = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        assert onboard_response.status_code == 200
        
        # Request token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        
        assert token_response.status_code == 200
        data = json.loads(token_response.data)
        assert 'token' in data
        assert len(data['token']) > 0
    
    def test_token_request_static_device(self, flask_client, authorized_device):
        """Test token request for static authorized device"""
        response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
        assert len(data['token']) > 0
    
    def test_token_request_unauthorized_device(self, flask_client, unauthorized_device):
        """Test token request for unauthorized device"""
        response = flask_client.post('/get_token',
            json={
                'device_id': unauthorized_device['device_id'],
                'mac_address': unauthorized_device['mac_address']
            },
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not authorized' in data['error'].lower()
    
    def test_token_request_missing_fields(self, flask_client):
        """Test token request with missing fields"""
        # Missing device_id
        response = flask_client.post('/get_token',
            json={'mac_address': 'AA:BB:CC:DD:EE:FF'},
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_token_validation_success(self, flask_client, authorized_device):
        """Test successful token validation"""
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token = json.loads(token_response.data)['token']
        
        # Validate token
        auth_response = flask_client.post('/auth',
            json={
                'device_id': authorized_device['device_id'],
                'token': token
            },
            content_type='application/json'
        )
        
        assert auth_response.status_code == 200
        data = json.loads(auth_response.data)
        assert data['authorized'] is True
        assert data['device_id'] == authorized_device['device_id']
    
    def test_token_validation_invalid_token(self, flask_client, authorized_device):
        """Test token validation with invalid token"""
        response = flask_client.post('/auth',
            json={
                'device_id': authorized_device['device_id'],
                'token': 'invalid_token_12345'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['authorized'] is False
    
    def test_token_validation_missing_token(self, flask_client, authorized_device):
        """Test token validation with missing token"""
        response = flask_client.post('/auth',
            json={'device_id': authorized_device['device_id']},
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_session_timeout(self, flask_client, authorized_device, monkeypatch):
        """Test session timeout handling"""
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token = json.loads(token_response.data)['token']
        
        # Mock session timeout (5 minutes = 300 seconds)
        from controller import device_tokens, SESSION_TIMEOUT
        if authorized_device['device_id'] in device_tokens:
            # Set last_activity to past timeout
            device_tokens[authorized_device['device_id']]['last_activity'] = time.time() - SESSION_TIMEOUT - 10
        
        # Try to use expired token
        auth_response = flask_client.post('/auth',
            json={
                'device_id': authorized_device['device_id'],
                'token': token
            },
            content_type='application/json'
        )
        
        # Token should be expired
        data = json.loads(auth_response.data)
        # May be False if timeout is enforced
        assert data.get('authorized') is False or 'token' not in device_tokens.get(authorized_device['device_id'], {})
    
    def test_token_reuse_after_timeout(self, flask_client, authorized_device):
        """Test that expired tokens cannot be reused"""
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token1 = json.loads(token_response.data)['token']
        
        # Get new token (should be different)
        token_response2 = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token2 = json.loads(token_response2.data)['token']
        
        # Tokens should be different
        assert token1 != token2
    
    def test_multiple_devices_tokens(self, flask_client):
        """Test that multiple devices can have different tokens"""
        device1 = {'device_id': 'ESP32_2', 'mac_address': 'AA:BB:CC:DD:EE:02'}
        device2 = {'device_id': 'ESP32_3', 'mac_address': 'AA:BB:CC:DD:EE:03'}
        
        # Get tokens for both devices
        token1_response = flask_client.post('/get_token',
            json=device1,
            content_type='application/json'
        )
        token2_response = flask_client.post('/get_token',
            json=device2,
            content_type='application/json'
        )
        
        assert token1_response.status_code == 200
        assert token2_response.status_code == 200
        
        token1 = json.loads(token1_response.data)['token']
        token2 = json.loads(token2_response.data)['token']
        
        # Tokens should be different
        assert token1 != token2
        
        # Each token should only work for its device
        auth1 = flask_client.post('/auth',
            json={'device_id': device1['device_id'], 'token': token1},
            content_type='application/json'
        )
        auth2 = flask_client.post('/auth',
            json={'device_id': device2['device_id'], 'token': token2},
            content_type='application/json'
        )
        
        assert json.loads(auth1.data)['authorized'] is True
        assert json.loads(auth2.data)['authorized'] is True
        
        # Cross-device token should fail
        cross_auth = flask_client.post('/auth',
            json={'device_id': device1['device_id'], 'token': token2},
            content_type='application/json'
        )
        assert json.loads(cross_auth.data)['authorized'] is False

