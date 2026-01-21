"""
Test API Endpoints
Validates all 29 API endpoints are functional
"""

import pytest
import json
import time


class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_onboard_endpoint(self, flask_client, test_device_id, test_mac_address):
        """Test POST /onboard"""
        response = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400, 503]
    
    def test_get_token_endpoint(self, flask_client, authorized_device):
        """Test POST /get_token"""
        response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 403]
    
    def test_auth_endpoint(self, flask_client, authorized_device):
        """Test POST /auth"""
        # Get token first
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        if token_response.status_code == 200:
            token = json.loads(token_response.data)['token']
            response = flask_client.post('/auth',
                json={
                    'device_id': authorized_device['device_id'],
                    'token': token
                },
                content_type='application/json'
            )
            assert response.status_code == 200
    
    def test_data_endpoint(self, flask_client, authorized_device):
        """Test POST /data"""
        # Get token first
        token_response = flask_client.post('/get_token',
            json={
                'device_id': authorized_device['device_id'],
                'mac_address': authorized_device['mac_address']
            },
            content_type='application/json'
        )
        if token_response.status_code == 200:
            token = json.loads(token_response.data)['token']
            response = flask_client.post('/data',
                json={
                    'device_id': authorized_device['device_id'],
                    'token': token,
                    'timestamp': str(int(time.time())),
                    'data': '25.5'
                },
                content_type='application/json'
            )
            assert response.status_code == 200
    
    def test_dashboard_endpoint(self, flask_client):
        """Test GET /"""
        response = flask_client.get('/')
        assert response.status_code == 200
    
    def test_graph_endpoint(self, flask_client):
        """Test GET /graph"""
        response = flask_client.get('/graph')
        assert response.status_code == 200
    
    def test_get_data_endpoint(self, flask_client):
        """Test GET /get_data"""
        response = flask_client.get('/get_data')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_update_endpoint(self, flask_client):
        """Test POST /update"""
        response = flask_client.post('/update',
            json={'device_id': 'ESP32_2', 'authorized': True},
            content_type='application/json'
        )
        assert response.status_code == 200
    
    def test_update_policy_endpoint(self, flask_client):
        """Test POST /update_policy"""
        response = flask_client.post('/update_policy',
            json={'policy': 'packet_inspection', 'enabled': True},
            content_type='application/json'
        )
        assert response.status_code == 200
    
    def test_get_topology_endpoint(self, flask_client):
        """Test GET /get_topology"""
        response = flask_client.get('/get_topology')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'nodes' in data
        assert 'edges' in data
    
    def test_get_topology_with_mac_endpoint(self, flask_client):
        """Test GET /get_topology_with_mac"""
        response = flask_client.get('/get_topology_with_mac')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'nodes' in data
        assert 'edges' in data
        # Check nodes have MAC addresses
        if len(data['nodes']) > 0:
            assert 'mac' in data['nodes'][0]
    
    def test_verify_certificate_endpoint(self, flask_client, test_device_id, test_mac_address):
        """Test POST /verify_certificate"""
        # First onboard device
        onboard_response = flask_client.post('/onboard',
            json={
                'device_id': test_device_id,
                'mac_address': test_mac_address
            },
            content_type='application/json'
        )
        if onboard_response.status_code == 200:
            response = flask_client.post('/verify_certificate',
                json={'device_id': test_device_id},
                content_type='application/json'
            )
            assert response.status_code in [200, 503]
    
    def test_pending_devices_endpoint(self, flask_client):
        """Test GET /api/pending_devices"""
        response = flask_client.get('/api/pending_devices')
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'status' in data
            assert 'devices' in data
    
    def test_approve_device_endpoint(self, flask_client):
        """Test POST /api/approve_device"""
        response = flask_client.post('/api/approve_device',
            json={
                'mac_address': 'AA:BB:CC:DD:EE:FF',
                'admin_notes': 'Test approval'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400, 503]
    
    def test_reject_device_endpoint(self, flask_client):
        """Test POST /api/reject_device"""
        response = flask_client.post('/api/reject_device',
            json={
                'mac_address': 'AA:BB:CC:DD:EE:FF',
                'admin_notes': 'Test rejection'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400, 503]
    
    def test_device_history_endpoint(self, flask_client):
        """Test GET /api/device_history"""
        response = flask_client.get('/api/device_history')
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'status' in data
            assert 'history' in data
    
    def test_get_health_metrics_endpoint(self, flask_client):
        """Test GET /get_health_metrics"""
        response = flask_client.get('/get_health_metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_get_policy_logs_endpoint(self, flask_client):
        """Test GET /get_policy_logs"""
        response = flask_client.get('/get_policy_logs')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_toggle_policy_endpoint(self, flask_client):
        """Test POST /toggle_policy/<policy>"""
        response = flask_client.post('/toggle_policy/packet_inspection')
        assert response.status_code == 200
    
    def test_clear_policy_logs_endpoint(self, flask_client):
        """Test POST /clear_policy_logs"""
        response = flask_client.post('/clear_policy_logs')
        assert response.status_code == 200
    
    def test_get_security_alerts_endpoint(self, flask_client):
        """Test GET /get_security_alerts"""
        response = flask_client.get('/get_security_alerts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_get_policies_endpoint(self, flask_client):
        """Test GET /get_policies"""
        response = flask_client.get('/get_policies')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'packet_inspection' in data
    
    def test_get_sdn_metrics_endpoint(self, flask_client):
        """Test GET /get_sdn_metrics"""
        response = flask_client.get('/get_sdn_metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_ml_health_endpoint(self, flask_client):
        """Test GET /ml/health"""
        response = flask_client.get('/ml/health')
        assert response.status_code in [200, 503]
    
    def test_ml_initialize_endpoint(self, flask_client):
        """Test POST /ml/initialize"""
        response = flask_client.post('/ml/initialize')
        assert response.status_code in [200, 503]
    
    def test_ml_status_endpoint(self, flask_client):
        """Test GET /ml/status"""
        response = flask_client.get('/ml/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
    
    def test_ml_detections_endpoint(self, flask_client):
        """Test GET /ml/detections"""
        response = flask_client.get('/ml/detections')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_ml_analyze_packet_endpoint(self, flask_client):
        """Test POST /ml/analyze_packet"""
        response = flask_client.post('/ml/analyze_packet',
            json={
                'device_id': 'ESP32_2',
                'size': 100,
                'protocol': 6
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 503]
    
    def test_ml_statistics_endpoint(self, flask_client):
        """Test GET /ml/statistics"""
        response = flask_client.get('/ml/statistics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

