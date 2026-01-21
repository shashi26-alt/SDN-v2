#!/usr/bin/env python3
"""
IoT Security Framework - Complete Project Launcher
Single script to run the entire IoT Security Framework with ML-based attack detection
"""

import os
import sys
import subprocess
import time
import signal
import threading
import requests
import json
from pathlib import Path

class IoTFrameworkLauncher:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.controller_process = None
        self.mininet_process = None
        self.virtual_env = None
        self.running = True
        
    def print_banner(self):
        """Print the project banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔐 SecureIoT-SDN Framework Launcher 🔐                    ║
║                                                                              ║
║  Advanced IoT Security Framework with Software-Defined Networking          ║
║  • ML-based DDoS Attack Detection                                          ║
║  • Real-time Network Monitoring                                            ║
║  • Token-based Device Authentication                                       ║
║  • SDN Policy Enforcement                                                  ║
║  • Interactive Web Dashboard                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def check_python_version(self):
        """Check if Python version is compatible"""
        if sys.version_info < (3, 8):
            print("❌ Error: Python 3.8 or higher is required")
            print(f"   Current version: {sys.version}")
            return False
        print(f"✅ Python version: {sys.version.split()[0]}")
        return True
        
    def setup_virtual_environment(self):
        """Set up virtual environment if it doesn't exist"""
        venv_path = self.project_dir / "venv"
        
        if not venv_path.exists():
            print("🔧 Creating virtual environment...")
            try:
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                             check=True, capture_output=True)
                print("✅ Virtual environment created")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to create virtual environment: {e}")
                return False
        else:
            print("✅ Virtual environment already exists")
            
        # Determine the correct pip and python paths
        if os.name == 'nt':  # Windows
            self.pip_path = venv_path / "Scripts" / "pip.exe"
            self.python_path = venv_path / "Scripts" / "python.exe"
        else:  # Unix/Linux/macOS
            self.pip_path = venv_path / "bin" / "pip"
            self.python_path = venv_path / "bin" / "python"
            
        return True
        
    def install_dependencies(self):
        """Install required dependencies"""
        requirements_file = self.project_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ Error: requirements.txt not found")
            return False
            
        print("📦 Installing Python dependencies...")
        try:
            subprocess.run([str(self.pip_path), "install", "-r", str(requirements_file)], 
                         check=True, capture_output=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("   Try running: pip install -r requirements.txt")
            return False
            
    def check_model_files(self):
        """Check if ML model files exist"""
        models_dir = self.project_dir / "models"
        model_files = [
            "ddos_model_retrained.keras",
            "ddos_model.keras"
        ]
        
        print("🤖 Checking ML model files...")
        for model_file in model_files:
            model_path = models_dir / model_file
            if model_path.exists():
                print(f"✅ Found model: {model_file}")
                return True
                
        print("⚠️  Warning: No ML model files found in models/ directory")
        print("   The ML engine will still run but may not detect attacks properly")
        return True
        
    def start_controller(self):
        """Start the Flask controller"""
        controller_file = self.project_dir / "controller.py"
        
        if not controller_file.exists():
            print("❌ Error: controller.py not found")
            return False
            
        print("🚀 Starting Flask SDN Controller...")
        try:
            # Start controller in background
            self.controller_process = subprocess.Popen(
                [str(self.python_path), str(controller_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for controller to start
            print("⏳ Waiting for controller to initialize...")
            for i in range(10):  # Wait up to 10 seconds
                try:
                    response = requests.get("http://localhost:5000", timeout=1)
                    if response.status_code == 200:
                        print("✅ Controller started successfully")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    print(f"   Attempt {i+1}/10...")
                    
            print("❌ Controller failed to start within 10 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start controller: {e}")
            return False
            
    def start_virtual_devices(self):
        """Start the Mininet virtual topology"""
        mininet_file = self.project_dir / "mininet_topology.py"
        
        if not mininet_file.exists():
            print("❌ Error: mininet_topology.py not found")
            return False
            
        print("🌐 Starting Virtual IoT Devices...")
        try:
            # Start mininet in background
            self.mininet_process = subprocess.Popen(
                [str(self.python_path), str(mininet_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give devices time to connect
            time.sleep(3)
            print("✅ Virtual devices started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start virtual devices: {e}")
            return False
            
    def check_system_status(self):
        """Check if all components are running"""
        print("\n📊 Checking System Status...")
        
        # Check controller
        try:
            response = requests.get("http://localhost:5000/ml/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ ML Engine: {data['status']}")
                print(f"   Total Packets: {data['statistics']['total_packets']}")
                print(f"   Model Status: {data['statistics']['model_status']}")
            else:
                print("⚠️  ML Engine: Responding but status unclear")
        except requests.exceptions.RequestException:
            print("❌ ML Engine: Not responding")
            
        # Check device data
        try:
            response = requests.get("http://localhost:5000/get_data", timeout=5)
            if response.status_code == 200:
                data = response.json()
                device_count = len(data)
                print(f"✅ Connected Devices: {device_count}")
                for device, info in data.items():
                    print(f"   {device}: {info['packets']} packets")
            else:
                print("⚠️  Device Data: Not available")
        except requests.exceptions.RequestException:
            print("❌ Device Data: Not responding")
            
    def display_access_info(self):
        """Display access information"""
        print("\n" + "="*80)
        print("🎉 IoT Security Framework is now running!")
        print("="*80)
        print("\n🌐 Access the Dashboard:")
        print("   URL: http://localhost:5000")
        print("   Or:  http://127.0.0.1:5000")
        
        print("\n📱 Dashboard Features:")
        print("   • Overview: Real-time network status and topology")
        print("   • Devices: Connected ESP32 devices and controls")
        print("   • Security: SDN policies and security alerts")
        print("   • ML Engine: Attack detection and ML statistics")
        print("   • Analytics: Network performance metrics")
        
        print("\n🔧 API Endpoints:")
        print("   • /ml/status - ML engine status")
        print("   • /ml/detections - Recent attack detections")
        print("   • /get_data - Device data")
        print("   • /get_topology_with_mac - Network topology")
        
        print("\n⌨️  Controls:")
        print("   • Press Ctrl+C to stop the framework")
        print("   • Check terminal for real-time logs")
        
        print("\n" + "="*80)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n🛑 Shutting down IoT Security Framework...")
        self.running = False
        
        if self.mininet_process:
            print("   Stopping virtual devices...")
            self.mininet_process.terminate()
            self.mininet_process.wait(timeout=5)
            
        if self.controller_process:
            print("   Stopping controller...")
            self.controller_process.terminate()
            self.controller_process.wait(timeout=5)
            
        print("✅ Framework stopped successfully")
        sys.exit(0)
        
    def monitor_system(self):
        """Monitor system status periodically"""
        while self.running:
            time.sleep(30)  # Check every 30 seconds
            if self.running:
                print("\n🔄 System Status Check:")
                self.check_system_status()
                
    def run(self):
        """Main execution function"""
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Print banner
            self.print_banner()
            
            # Check Python version
            if not self.check_python_version():
                return False
                
            # Set up virtual environment
            if not self.setup_virtual_environment():
                return False
                
            # Install dependencies
            if not self.install_dependencies():
                return False
                
            # Check model files
            self.check_model_files()
            
            # Start controller
            if not self.start_controller():
                return False
                
            # Start virtual devices
            if not self.start_virtual_devices():
                return False
                
            # Check initial status
            self.check_system_status()
            
            # Display access information
            self.display_access_info()
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
            monitor_thread.start()
            
            # Keep running until interrupted
            print("\n🔄 Framework is running... Press Ctrl+C to stop")
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            self.signal_handler(signal.SIGINT, None)
            
        return True

def main():
    """Main entry point"""
    launcher = IoTFrameworkLauncher()
    success = launcher.run()
    
    if not success:
        print("\n❌ Failed to start IoT Security Framework")
        sys.exit(1)
    else:
        print("\n✅ IoT Security Framework stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
