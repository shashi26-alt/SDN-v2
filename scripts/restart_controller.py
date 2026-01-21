#!/usr/bin/env python3
"""
Restart Controller Script
Restarts the Flask controller to load the updated ML engine
"""

import subprocess
import time
import requests
import signal
import os
import sys

def find_controller_process():
    """Find the running controller process"""
    try:
        result = subprocess.run(['pgrep', '-f', 'controller.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return [int(pid) for pid in pids if pid]
    except:
        pass
    return []

def stop_controller():
    """Stop the running controller"""
    print("🛑 Stopping controller...")
    pids = find_controller_process()
    
    if pids:
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"   Sent SIGTERM to PID {pid}")
            except ProcessLookupError:
                print(f"   Process {pid} already stopped")
            except Exception as e:
                print(f"   Error stopping PID {pid}: {e}")
        
        # Wait for processes to stop
        time.sleep(3)
        
        # Check if still running
        remaining_pids = find_controller_process()
        if remaining_pids:
            print("   Force killing remaining processes...")
            for pid in remaining_pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                    print(f"   Force killed PID {pid}")
                except:
                    pass
    else:
        print("   No controller process found")

def start_controller():
    """Start the controller"""
    print("🚀 Starting controller...")
    try:
        # Start controller in background
        process = subprocess.Popen([sys.executable, 'controller.py'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Wait for controller to start
        print("   Waiting for controller to initialize...")
        for i in range(10):
            try:
                response = requests.get("http://localhost:5000", timeout=1)
                if response.status_code == 200:
                    print("   ✅ Controller started successfully")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
                print(f"   Attempt {i+1}/10...")
        
        print("   ❌ Controller failed to start within 10 seconds")
        return False
        
    except Exception as e:
        print(f"   ❌ Failed to start controller: {e}")
        return False

def test_ml_engine():
    """Test the ML engine"""
    print("\n🧪 Testing ML Engine...")
    try:
        # Test normal packet
        normal_response = requests.post("http://localhost:5000/ml/analyze_packet",
                                      json={
                                          "device_id": "ESP32_2",
                                          "size": 64,
                                          "rate": 1.0,
                                          "bps": 1000,
                                          "pps": 1.0,
                                          "duration": 1.0,
                                          "tcp_flags": 16
                                      })
        
        if normal_response.status_code == 200:
            normal_data = normal_response.json()
            print(f"   Normal packet: {normal_data.get('prediction', 'Unknown')}")
        
        # Test attack packet
        attack_response = requests.post("http://localhost:5000/ml/analyze_packet",
                                      json={
                                          "device_id": "ESP32_2",
                                          "size": 1500,
                                          "rate": 10000.0,
                                          "bps": 100000000,
                                          "pps": 10000.0,
                                          "duration": 0.001,
                                          "tcp_flags": 2,
                                          "window_size": 0,
                                          "ttl": 1
                                      })
        
        if attack_response.status_code == 200:
            attack_data = attack_response.json()
            print(f"   Attack packet: {attack_data.get('prediction', 'Unknown')} "
                  f"(Attack: {attack_data.get('is_attack', False)}, "
                  f"Confidence: {attack_data.get('confidence', 0):.2f})")
            
            if attack_data.get('is_attack', False):
                print("   ✅ ML Engine is detecting attacks!")
                return True
            else:
                print("   ⚠️  ML Engine is not detecting attacks")
                return False
        
    except Exception as e:
        print(f"   ❌ Error testing ML engine: {e}")
        return False

def main():
    print("🔄 Restarting IoT Security Framework Controller...")
    print("="*60)
    
    # Stop controller
    stop_controller()
    time.sleep(2)
    
    # Start controller
    if start_controller():
        time.sleep(3)
        
        # Test ML engine
        if test_ml_engine():
            print("\n🎉 Controller restarted successfully with working ML engine!")
        else:
            print("\n⚠️  Controller restarted but ML engine may need attention")
    else:
        print("\n❌ Failed to restart controller")

if __name__ == "__main__":
    main()
