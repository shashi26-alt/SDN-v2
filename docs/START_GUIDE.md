# Zero Trust SDN Framework - Quick Start Guide

## Automatic System Startup

The `start.sh` script automatically starts all components of the Zero Trust SDN Framework.

### Usage

```bash
./start.sh
```

Or:

```bash
bash start.sh
```

### What the Script Does

1. **Checks Prerequisites**
   - Python 3.8+ availability
   - Required dependencies (Flask, etc.)
   - Optional dependencies (Ryu, Docker)

2. **Sets Up Environment**
   - Creates necessary directories (certs, logs, honeypot_data)
   - Checks for virtual environment

3. **Starts Components**
   - ✅ Flask Controller (Web Dashboard & API) - **Always started**
   - ✅ Ryu SDN Controller - **Started if available**
   - ✅ Zero Trust Integration Framework - **Started if available**
   - ✅ Virtual IoT Devices - **Optional, asks for confirmation**

4. **Monitors System**
   - Monitors all running processes
   - Shows status of each component
   - Handles graceful shutdown on Ctrl+C

### Components Started

#### Flask Controller (Required)
- **Port:** 5000
- **URL:** http://localhost:5000
- **Status:** Always started
- **Logs:** `logs/controller.log`

#### Ryu SDN Controller (Optional)
- **Port:** 6653 (OpenFlow)
- **Status:** Started if Ryu is installed
- **Install:** `pip install ryu eventlet`
- **Logs:** `logs/ryu.log`

#### Zero Trust Framework (Optional)
- **Status:** Started if `zero_trust_integration.py` exists
- **Logs:** `logs/zero_trust.log`

#### Virtual IoT Devices (Optional)
- **Status:** Asks for confirmation
- **Logs:** `logs/mininet.log`

### Stopping the System

Press `Ctrl+C` to stop all components gracefully.

The script will:
1. Stop Flask Controller
2. Stop Ryu SDN Controller (if running)
3. Stop Zero Trust Framework (if running)
4. Stop Virtual Devices (if running)
5. Clean up all processes

### Access Points

Once started, access:

- **Web Dashboard:** http://localhost:5000
- **API Endpoints:** http://localhost:5000/api/*
- **SDN Controller:** Port 6653 (if Ryu is running)

### Troubleshooting

#### Controller Not Starting
- Check if port 5000 is already in use
- Check `logs/controller.log` for errors
- Ensure Flask is installed: `pip install flask`

#### Ryu Not Starting
- Install Ryu: `pip install ryu eventlet`
- Check `logs/ryu.log` for errors
- Ensure you have OpenFlow-compatible switch (or use Mininet)

#### Zero Trust Framework Not Starting
- Ensure `zero_trust_integration.py` exists
- Check `logs/zero_trust.log` for errors
- Verify all dependencies are installed

### Manual Component Start

If you prefer to start components manually:

```bash
# Terminal 1: Flask Controller
python3 controller.py

# Terminal 2: Ryu SDN Controller (if installed)
ryu-manager ryu_controller/sdn_policy_engine.py

# Terminal 3: Zero Trust Framework (optional)
python3 zero_trust_integration.py

# Terminal 4: Virtual Devices (optional)
python3 mininet_topology.py
```

### System Requirements

- Python 3.8+
- Flask 3.0+
- SQLite3 (built-in)
- cryptography (for PKI)
- Optional: Ryu, Docker, TensorFlow

### Next Steps

1. Access the dashboard at http://localhost:5000
2. Onboard devices using the Certificates tab
3. Monitor trust scores in the Trust Scores tab
4. View honeypot status in the Honeypot tab
5. Configure SDN policies in the Security tab

---

**Note:** The script handles optional dependencies gracefully. The system will work even if Ryu or Docker are not installed, but some features will be limited.

