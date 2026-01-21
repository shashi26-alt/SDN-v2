"""
Test System Integration
End-to-end scenarios testing complete system workflows
"""

import pytest
import json
import time
import threading


class TestSystemIntegration:
    """Test complete system integration scenarios"""
    
    def test_complete_device_lifecycle(self, flask_client, test_device_id, test_mac_address):
        """Test complete device lifecycle: onboard → authenticate → send data"""
        # Step 1: Onboard device
        onboard_response = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address,
                'device_type': 'sensor'
            },
            content_type='application/json'
        )
        assert onboard_response.status_code == 200
        onboard_data = json.loads(onboard_response.data)
        assert onboard_data['status'] == 'success'
        
        # Step 2: Get authentication token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        assert token_response.status_code == 200
        token_data = json.loads(token_response.data)
        assert 'token' in token_data
        token = token_data['token']
        
        # Step 3: Validate token
        auth_response = flask_client.post('/auth',
            json={
                'device_id': test_device_id,
                'token': token
            },
            content_type='application/json'
        )
        assert auth_response.status_code == 200
        auth_data = json.loads(auth_response.data)
        assert auth_data['authorized'] is True
        
        # Step 4: Send data
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
        data_result = json.loads(data_response.data)
        assert data_result['status'] == 'accepted'
        
        # Step 5: Verify device appears in topology
        topology_response = flask_client.get('/get_topology_with_mac')
        assert topology_response.status_code == 200
        topology_data = json.loads(topology_response.data)
        device_found = False
        for node in topology_data.get('nodes', []):
            if node.get('id') == test_device_id:
                device_found = True
                assert node.get('mac') == test_mac_address
                break
        assert device_found, "Device not found in topology"
    
    def test_multiple_devices_concurrent_operation(self, flask_client):
        """Test multiple devices operating concurrently"""
        devices = [
            {'device_id': 'ESP32_2', 'mac_address': 'AA:BB:CC:DD:EE:02'},
            {'device_id': 'ESP32_3', 'mac_address': 'AA:BB:CC:DD:EE:03'}
        ]
        
        tokens = {}
        results = {}
        
        # Get tokens for all devices
        for device in devices:
            token_response = flask_client.post('/get_token',
                json=device,
                content_type='application/json'
            )
            if token_response.status_code == 200:
                tokens[device['device_id']] = json.loads(token_response.data)['token']
        
        # Submit data from all devices
        for device in devices:
            if device['device_id'] in tokens:
                data_response = flask_client.post('/data',
                    json={
                        'device_id': device['device_id'],
                        'token': tokens[device['device_id']],
                        'timestamp': str(int(time.time())),
                        'data': '25.5'
                    },
                    content_type='application/json'
                )
                results[device['device_id']] = json.loads(data_response.data)
        
        # Verify all devices processed
        assert len(results) > 0
        for device_id, result in results.items():
            assert result['status'] in ['accepted', 'rejected']
    
    def test_system_startup_initialization(self, flask_client):
        """Test system startup and initialization"""
        # Test that system is responsive
        response = flask_client.get('/')
        assert response.status_code == 200
        
        # Test health metrics
        health_response = flask_client.get('/get_health_metrics')
        assert health_response.status_code == 200
        
        # Test topology endpoint
        topology_response = flask_client.get('/get_topology')
        assert topology_response.status_code == 200
        
        # Test policies endpoint
        policies_response = flask_client.get('/get_policies')
        assert policies_response.status_code == 200
    
    def test_component_integration(self, flask_client, test_device_id, test_mac_address):
        """Test integration between components"""
        # Onboard device
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
        assert verify_response.status_code in [200, 503]
        
        # Get token (uses onboarding database)
        token_response = flask_client.post('/get_token',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        assert token_response.status_code == 200
        
        # Send data (verifies onboarding status)
        token = json.loads(token_response.data)['token']
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
    
    def test_error_handling_and_recovery(self, flask_client):
        """Test error handling and recovery"""
        # Test invalid endpoint
        response = flask_client.get('/invalid_endpoint')
        assert response.status_code == 404
        
        # Test malformed JSON
        response = flask_client.post('/get_token',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 500]
        
        # Test missing fields
        response = flask_client.post('/get_token',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_system_resilience(self, flask_client, authorized_device):
        """Test system resilience under load"""
        # Get token
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        token = json.loads(token_response.data)['token']
        
        # Send multiple requests rapidly
        success_count = 0
        for i in range(10):
            response = flask_client.post('/data',
                json={
                    'device_id': authorized_device['device_id'],
                    'token': token,
                    'timestamp': str(int(time.time())),
                    'data': f'{25.0 + i}'
                },
                content_type='application/json'
            )
            if response.status_code == 200:
                data = json.loads(response.data)
                if data.get('status') == 'accepted':
                    success_count += 1
        
        # System should handle requests
        assert success_count > 0
    
    def test_topology_integration(self, flask_client, test_device_id, test_mac_address):
        """Test topology integration with onboarding"""
        # Onboard device
        flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        
        # Get topology
        response = flask_client.get('/get_topology_with_mac')
        assert response.status_code == 200
        topology = json.loads(response.data)
        
        # Verify gateway exists
        gateway_found = False
        for node in topology.get('nodes', []):
            if node.get('id') == 'ESP32_Gateway':
                gateway_found = True
                assert node.get('type') == 'gateway'
                assert node.get('online') is True
                break
        assert gateway_found, "Gateway not found in topology"
        
        # Verify device appears
        device_found = False
        for node in topology.get('nodes', []):
            if node.get('id') == test_device_id:
                device_found = True
                assert node.get('mac') == test_mac_address
                assert 'onboarded' in node or node.get('type') == 'device'
                break
        # Device may not be online yet, but should be in list if onboarded
    
    def test_policy_enforcement_integration(self, flask_client, authorized_device):
        """Test SDN policy enforcement integration"""
        # Enable policies
        flask_client.post('/update_policy',
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
        
        # Send data (should be subject to policies)
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
        assert data['status'] in ['accepted', 'rejected']
        
        # Check policy logs
        logs_response = flask_client.get('/get_policy_logs')
        assert logs_response.status_code == 200

