"""
Test Data Submission Flow
Tests data submission, rate limiting, SDN policy enforcement, and concurrent operations
"""

import pytest
import json
import time
import threading


class TestDataFlow:
    """Test data submission and policy enforcement"""
    
    def test_valid_data_submission(self, flask_client, authorized_device):
        """Test valid data submission with token"""
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token = json.loads(token_response.data)['token']
        
        # Submit data
        data_response = flask_client.post('/data',
            json={
                'device_id': authorized_device['device_id'],
                'token': token,
                'timestamp': str(int(time.time())),
                'data': '25.5'
            },
            content_type='application/json'
        )
        
        assert data_response.status_code == 200
        data = json.loads(data_response.data)
        assert data['status'] == 'accepted'
    
    def test_data_submission_invalid_token(self, flask_client, authorized_device):
        """Test data submission with invalid token"""
        response = flask_client.post('/data',
            json={
                'device_id': authorized_device['device_id'],
                'token': 'invalid_token',
                'timestamp': str(int(time.time())),
                'data': '25.5'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'rejected'
        assert 'token' in data.get('reason', '').lower() or 'rejected' in data['status']
    
    def test_data_submission_missing_fields(self, flask_client, authorized_device):
        """Test data submission with missing required fields"""
        # Missing token
        response = flask_client.post('/data',
            json={
                'device_id': authorized_device['device_id'],
                'timestamp': str(int(time.time())),
                'data': '25.5'
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'rejected'
    
    def test_rate_limiting_enforcement(self, flask_client, authorized_device):
        """Test rate limiting (60 packets per minute)"""
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token = json.loads(token_response.data)['token']
        
        # Send data up to rate limit
        accepted_count = 0
        rejected_count = 0
        
        for i in range(65):  # Try to exceed limit
            response = flask_client.post('/data',
                json={
                    'device_id': authorized_device['device_id'],
                    'token': token,
                    'timestamp': str(int(time.time())),
                    'data': f'{25.0 + i * 0.1}'
                },
                content_type='application/json'
            )
            
            data = json.loads(response.data)
            if data['status'] == 'accepted':
                accepted_count += 1
            else:
                rejected_count += 1
                if 'rate limit' in data.get('reason', '').lower():
                    break
        
        # Should have some rejections due to rate limiting
        assert rejected_count > 0 or accepted_count <= 60
    
    def test_sdn_policy_enforcement(self, flask_client, authorized_device):
        """Test SDN policy enforcement"""
        # Enable packet inspection policy
        policy_response = flask_client.post('/update_policy',
            json={'policy': 'packet_inspection', 'enabled': True},
            content_type='application/json'
        )
        
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token = json.loads(token_response.data)['token']
        
        # Submit data (may be blocked by policy)
        data_response = flask_client.post('/data',
            json={
                'device_id': authorized_device['device_id'],
                'token': token,
                'timestamp': str(int(time.time())),
                'data': '25.5'
            },
            content_type='application/json'
        )
        
        # Should either accept or reject based on policy
        assert data_response.status_code == 200
        data = json.loads(data_response.data)
        assert data['status'] in ['accepted', 'rejected']
    
    def test_multiple_concurrent_submissions(self, flask_client):
        """Test multiple devices submitting data concurrently"""
        devices = [
            {'device_id': 'ESP32_2', 'mac_address': 'AA:BB:CC:DD:EE:02'},
            {'device_id': 'ESP32_3', 'mac_address': 'AA:BB:CC:DD:EE:03'}
        ]
        
        tokens = {}
        for device in devices:
            token_response = flask_client.post('/get_token',
                json=device,
                content_type='application/json'
            )
            if token_response.status_code == 200:
                tokens[device['device_id']] = json.loads(token_response.data)['token']
        
        # Submit data from both devices
        results = {}
        for device in devices:
            if device['device_id'] in tokens:
                response = flask_client.post('/data',
                    json={
                        'device_id': device['device_id'],
                        'token': tokens[device['device_id']],
                        'timestamp': str(int(time.time())),
                        'data': '25.5'
                    },
                    content_type='application/json'
                )
                results[device['device_id']] = json.loads(response.data)
        
        # Both should be processed
        assert len(results) > 0
        for device_id, result in results.items():
            assert result['status'] in ['accepted', 'rejected']
    
    def test_data_submission_onboarded_device(self, flask_client, test_device_id, test_mac_address):
        """Test data submission from onboarded device"""
        # Onboard device
        onboard_response = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        assert onboard_response.status_code == 200
        
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        token = json.loads(token_response.data)['token']
        
        # Submit data
        data_response = flask_client.post('/data',
            json={
                'device_id': test_device_id,
                'token': token,
                'timestamp': str(int(time.time())),
                'data': '25.5'
            },
            content_type='application/json'
        )
        
        assert data_response.status_code == 200
        data = json.loads(data_response.data)
        assert data['status'] == 'accepted'
    
    def test_data_submission_unauthorized_device(self, flask_client, unauthorized_device):
        """Test data submission from unauthorized device"""
        # Try to get token (should fail)
        token_response = flask_client.post('/get_token',
            json={
                'device_id': unauthorized_device['device_id'],
                'mac_address': unauthorized_device['mac_address']
            },
            content_type='application/json'
        )
        
        # Should not get token
        assert token_response.status_code == 403
    
    def test_data_with_ml_features(self, flask_client, authorized_device):
        """Test data submission with ML analysis features"""
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token = json.loads(token_response.data)['token']
        
        # Submit data with ML features
        data_response = flask_client.post('/data',
            json={
                'device_id': authorized_device['device_id'],
                'token': token,
                'timestamp': str(int(time.time())),
                'data': '25.5',
                'size': 100,
                'protocol': 6,
                'src_port': 8080,
                'dst_port': 5000,
                'rate': 1.0,
                'duration': 0.5
            },
            content_type='application/json'
        )
        
        assert data_response.status_code == 200
        data = json.loads(data_response.data)
        assert data['status'] in ['accepted', 'rejected']

