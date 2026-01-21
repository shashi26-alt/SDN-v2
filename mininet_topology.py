#!/usr/bin/env python3
"""
Mininet-style Topology for IoT Security Framework Testing
Creates a virtual network topology to test SDN functionality
"""

import time
import threading
import requests
import json
from datetime import datetime

class VirtualSwitch:
    """Virtual SDN Switch"""
    def __init__(self, switch_id):
        self.switch_id = switch_id
        self.ports = {}
        self.flow_table = {}
        self.connected_devices = []
        
    def add_port(self, port_id, device):
        """Add device to switch port"""
        self.ports[port_id] = device
        self.connected_devices.append(device)
        print(f"🔌 Switch {self.switch_id}: Device {device.device_id} connected to port {port_id}")
        
    def process_packet(self, packet):
        """Process packet through switch (simulate SDN forwarding)"""
        # Simulate packet processing delay
        time.sleep(0.001)
        
        # Update flow table
        flow_key = f"{packet['src']}->{packet['dst']}"
        if flow_key not in self.flow_table:
            self.flow_table[flow_key] = {
                'count': 0,
                'last_seen': time.time()
            }
        
        self.flow_table[flow_key]['count'] += 1
        self.flow_table[flow_key]['last_seen'] = time.time()
        
        return True

class VirtualHost:
    """Virtual IoT Device/Host"""
    def __init__(self, device_id, controller_url="http://localhost:5000"):
        self.device_id = device_id
        self.controller_url = controller_url
        self.token = None
        self.mac_address = f"AA:BB:CC:DD:EE:{device_id[-1]}{device_id[-1]}"
        self.switch = None
        self.running = False
        
    def connect_to_switch(self, switch):
        """Connect to virtual switch"""
        self.switch = switch
        switch.add_port(f"port_{self.device_id}", self)
        print(f"📡 {self.device_id} connected to switch {switch.switch_id}")
        
    def authenticate_with_controller(self):
        """Authenticate with SDN controller"""
        try:
            response = requests.post(f"{self.controller_url}/get_token", 
                                  json={"device_id": self.device_id, "mac_address": self.mac_address})
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                print(f"🔐 {self.device_id}: Authenticated with controller")
                return True
            else:
                print(f"❌ {self.device_id}: Authentication failed")
                return False
        except Exception as e:
            print(f"❌ {self.device_id}: Auth error: {e}")
            return False
    
    def send_packet(self, data):
        """Send packet through network"""
        if not self.token:
            return False
            
        # Create packet
        packet = {
            'src': self.device_id,
            'dst': 'controller',
            'data': data,
            'timestamp': time.time(),
            'token': self.token
        }
        
        # Process through switch
        if self.switch:
            self.switch.process_packet(packet)
        
        # Send to controller
        try:
            response = requests.post(f"{self.controller_url}/data", json={
                "device_id": self.device_id,
                "token": self.token,
                "timestamp": str(int(time.time())),
                "data": data
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'accepted':
                    print(f"✅ {self.device_id}: Packet accepted")
                    return True
                else:
                    print(f"❌ {self.device_id}: Packet rejected - {result.get('reason')}")
                    return False
            else:
                print(f"❌ {self.device_id}: Send failed")
                return False
        except Exception as e:
            print(f"❌ {self.device_id}: Send error: {e}")
            return False
    
    def run_device(self, interval=5):
        """Run device simulation"""
        print(f"🚀 Starting {self.device_id}...")
        
        # Authenticate
        if not self.authenticate_with_controller():
            return
        
        self.running = True
        packet_count = 0
        
        while self.running:
            # Generate sensor data
            sensor_data = f"{20 + (packet_count % 10):.1f}"  # Simulated temperature
            
            # Send packet
            self.send_packet(sensor_data)
            packet_count += 1
            
            time.sleep(interval)
    
    def stop_device(self):
        """Stop device"""
        self.running = False
        print(f"🛑 {self.device_id} stopped")

class MininetTopology:
    """Mininet-style network topology"""
    def __init__(self):
        self.switches = {}
        self.hosts = {}
        self.controller_url = "http://localhost:5000"
        
    def add_switch(self, switch_id):
        """Add virtual switch to topology"""
        switch = VirtualSwitch(switch_id)
        self.switches[switch_id] = switch
        print(f"🔧 Added switch: {switch_id}")
        return switch
    
    def add_host(self, host_id):
        """Add virtual host to topology"""
        host = VirtualHost(host_id, self.controller_url)
        self.hosts[host_id] = host
        print(f"📱 Added host: {host_id}")
        return host
    
    def add_link(self, host_id, switch_id):
        """Add link between host and switch"""
        if host_id in self.hosts and switch_id in self.switches:
            self.hosts[host_id].connect_to_switch(self.switches[switch_id])
            print(f"🔗 Linked {host_id} to {switch_id}")
        else:
            print(f"❌ Cannot link {host_id} to {switch_id} - missing components")
    
    def start_network(self):
        """Start the virtual network"""
        print("🌐 Starting Virtual Network...")
        
        # Start all hosts
        threads = []
        for host in self.hosts.values():
            thread = threading.Thread(target=host.run_device, args=(3,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            time.sleep(1)  # Stagger starts
        
        return threads
    
    def stop_network(self):
        """Stop the virtual network"""
        print("🛑 Stopping Virtual Network...")
        for host in self.hosts.values():
            host.stop_device()
    
    def show_topology(self):
        """Display network topology"""
        print("\n📊 Network Topology:")
        print("=" * 30)
        
        for switch_id, switch in self.switches.items():
            print(f"Switch {switch_id}:")
            print(f"  Connected devices: {len(switch.connected_devices)}")
            print(f"  Flow table entries: {len(switch.flow_table)}")
            
            for device in switch.connected_devices:
                print(f"    - {device.device_id} ({device.mac_address})")
        
        print(f"\nTotal hosts: {len(self.hosts)}")
        print(f"Total switches: {len(self.switches)}")
    
    def test_sdn_policies(self):
        """Test SDN policy enforcement"""
        print("\n🧪 Testing SDN Policies...")
        
        # Test rate limiting
        print("Testing rate limiting on first host...")
        host = list(self.hosts.values())[0]
        
        # Send packets rapidly to test rate limiting
        for i in range(70):  # Exceed 60 packets/minute limit
            host.send_packet(f"test_{i}")
            time.sleep(0.1)
        
        # Test session timeout
        print("Testing session timeout...")
        time.sleep(310)  # Wait for 5-minute timeout
        host.send_packet("timeout_test")
    
    def monitor_controller(self):
        """Monitor controller metrics"""
        try:
            response = requests.get(f"{self.controller_url}/get_data")
            if response.status_code == 200:
                data = response.json()
                print("\n📈 Controller Metrics:")
                for device_id, status in data.items():
                    print(f"  {device_id}: {status['packets']} packets")
            
            response = requests.get(f"{self.controller_url}/get_sdn_metrics")
            if response.status_code == 200:
                metrics = response.json()
                print(f"  SDN Latency: {metrics['control_plane_latency']}ms")
                print(f"  Throughput: {metrics['data_plane_throughput']}Mbps")
                print(f"  Policy Enforcement: {metrics['policy_enforcement_rate']}%")
                
        except Exception as e:
            print(f"❌ Controller monitoring error: {e}")

def create_test_topology():
    """Create a test network topology"""
    print("🔧 Creating Mininet-style Test Topology")
    print("=" * 40)
    
    # Create topology
    topology = MininetTopology()
    
    # Add switches
    switch1 = topology.add_switch("s1")
    switch2 = topology.add_switch("s2")
    
    # Add hosts (IoT devices)
    host1 = topology.add_host("ESP32_2")
    host2 = topology.add_host("ESP32_3")
    host3 = topology.add_host("ESP32_4")
    
    # Create network links
    topology.add_link("ESP32_2", "s1")
    topology.add_link("ESP32_3", "s1")
    topology.add_link("ESP32_4", "s2")
    
    # Show topology
    topology.show_topology()
    
    return topology

def main():
    print("🌐 IoT Security Framework Mininet-style SDN Test")
    print("=" * 50)
    
    # Check controller
    try:
        response = requests.get("http://localhost:5000")
        if response.status_code != 200:
            print("❌ IoT Security Controller not running")
            print("Start with: python controller.py")
            return
    except:
        print("❌ Cannot connect to controller")
        return
    
    print("✅ Controller is running")
    
    # Create topology
    topology = create_test_topology()
    
    # Start network
    threads = topology.start_network()
    
    # Monitor for 30 seconds
    print("\n📊 Monitoring network for 30 seconds...")
    for i in range(6):
        topology.monitor_controller()
        time.sleep(5)
    
    # Test SDN policies
    topology.test_sdn_policies()
    
    # Stop network
    topology.stop_network()
    
    print("\n✅ SDN Test Complete!")
    print("🌐 View results at: http://localhost:5000")

if __name__ == "__main__":
    main()
