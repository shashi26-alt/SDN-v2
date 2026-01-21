# 🚀 IoT Security Framework - Single Script Launcher

## Quick Start

Run the entire IoT Security Framework with a single command:

### Option 1: Python Script (Recommended)
```bash
python3 run_iot_framework.py
```

### Option 2: Bash Script
```bash
./start.sh
```

## What the Launcher Does

The launcher script automatically:

1. **🔍 Checks System Requirements**
   - Verifies Python 3.8+ is installed
   - Checks for required files

2. **🔧 Sets Up Environment**
   - Creates virtual environment (if needed)
   - Installs all dependencies from `requirements.txt`
   - Verifies ML model files

3. **🚀 Starts All Components**
   - Launches Flask SDN Controller with ML engine
   - Starts virtual ESP32 devices simulation
   - Initializes network topology

4. **📊 Monitors System**
   - Checks component health
   - Displays real-time status
   - Shows connection statistics

5. **🌐 Provides Access Info**
   - Dashboard URL: `http://localhost:5000`
   - API endpoints documentation
   - Usage instructions

## Features Included

- ✅ **ML-based Attack Detection** - Real-time DDoS detection
- ✅ **SDN Controller** - Token-based authentication
- ✅ **Virtual IoT Devices** - ESP32 simulation
- ✅ **Web Dashboard** - Interactive monitoring interface
- ✅ **Network Topology** - Visual device connections
- ✅ **Security Policies** - Dynamic policy enforcement
- ✅ **Real-time Monitoring** - Live updates every 5 seconds

## Dashboard Access

Once running, open your browser to:
```
http://localhost:5000
```

### Dashboard Tabs:
- **Overview**: Network status and topology visualization
- **Devices**: Connected ESP32 devices and controls
- **Security**: SDN policies and security alerts
- **ML Engine**: Attack detection and ML statistics
- **Analytics**: Network performance metrics

## Stopping the Framework

Press `Ctrl+C` to gracefully stop all components.

## Troubleshooting

### If the launcher fails:

1. **Check Python version**:
   ```bash
   python3 --version
   ```
   Must be 3.8 or higher.

2. **Install dependencies manually**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check file permissions**:
   ```bash
   chmod +x run_iot_framework.py
   chmod +x start.sh
   ```

4. **Verify all files exist**:
   - `controller.py`
   - `ml_security_engine.py`
   - `mininet_topology.py`
   - `requirements.txt`
   - `models/` directory with ML models

### Common Issues:

- **Port 5000 already in use**: Stop other Flask applications
- **Permission denied**: Run with `sudo` if needed
- **ML model not found**: Framework will still run but attack detection may be limited

## Manual Start (Alternative)

If the launcher doesn't work, you can start components manually:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start controller** (in background):
   ```bash
   python3 controller.py &
   ```

3. **Start virtual devices**:
   ```bash
   python3 mininet_topology.py
   ```

4. **Access dashboard**: `http://localhost:5000`

## System Requirements

- **Python**: 3.8 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 1GB free space
- **Network**: Local network access for virtual devices

## API Endpoints

- `GET /ml/status` - ML engine status
- `GET /ml/detections` - Recent attack detections
- `GET /get_data` - Device data
- `GET /get_topology_with_mac` - Network topology
- `POST /ml/analyze_packet` - Analyze specific packet

## Support

For issues or questions:
1. Check the terminal output for error messages
2. Verify all dependencies are installed
3. Ensure no other services are using port 5000
4. Check file permissions and Python version
