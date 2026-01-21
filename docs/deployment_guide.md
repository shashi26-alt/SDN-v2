# Raspberry Pi 4 Deployment Guide

## Zero Trust SDN Framework for SOHO IoT Networks

This guide provides instructions for deploying the Zero Trust SDN Framework on a Raspberry Pi 4.

## Prerequisites

- Raspberry Pi 4 (4GB RAM recommended, 8GB preferred)
- MicroSD card (32GB minimum, Class 10 or better)
- Raspberry Pi OS (64-bit recommended)
- Internet connection
- SDN-compatible switch (optional, for physical deployment)

## System Requirements

- Python 3.8 or higher
- Docker (for honeypot deployment)
- OpenSSL
- SQLite3
- Git

## Installation Steps

### 1. Install Base System

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv git openssl sqlite3 docker.io

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group (optional, to run docker without sudo)
sudo usermod -aG docker $USER
```

### 2. Install Ryu SDN Controller

```bash
# Install Ryu
pip3 install ryu eventlet

# Verify installation
ryu-manager --version
```

### 3. Clone and Setup Project

```bash
# Clone repository
cd ~
git clone <repository-url> IOT-project
cd IOT-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure System

```bash
# Create necessary directories
mkdir -p certs honeypot_data logs

# Set permissions
chmod 755 certs honeypot_data logs
```

### 5. Automated Setup (Recommended)

Use the provided setup script for automated installation:

```bash
cd ~/IOT-project
sudo bash scripts/raspberry_pi_setup.sh
```

The script will:
- Update system packages
- Install all required dependencies (Python, Docker, Ryu, etc.)
- Create necessary directories
- Install and configure systemd services
- Set up firewall rules
- Configure permissions

**Note**: The script assumes the project is located at `/home/pi/IOT-project`. If different, specify the path:
```bash
sudo bash scripts/raspberry_pi_setup.sh /path/to/IOT-project
```

### 6. Start Services

#### Option A: Using Systemd Services (After Automated Setup)

After running the setup script, services are ready to start:

```bash
# Start Ryu SDN Controller
sudo systemctl start ryu-sdn-controller
sudo systemctl enable ryu-sdn-controller

# Start Zero Trust Framework
sudo systemctl start zero-trust-sdn
sudo systemctl enable zero-trust-sdn

# Start Flask Controller (if separate)
sudo systemctl start flask-controller
sudo systemctl enable flask-controller
```

Check service status:
```bash
sudo systemctl status ryu-sdn-controller
sudo systemctl status zero-trust-sdn
```

#### Option B: Manual Setup

If you prefer manual setup, create service files:

**Ryu SDN Controller Service** (`/etc/systemd/system/ryu-sdn-controller.service`):

```ini
[Unit]
Description=Ryu SDN Controller for Zero Trust Framework
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/IOT-project
Environment="PATH=/home/pi/IOT-project/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/pi/IOT-project/venv/bin/ryu-manager --ofp-tcp-listen-port 6653 /home/pi/IOT-project/ryu_controller/sdn_policy_engine.py
Restart=always
RestartSec=10
StandardOutput=append:/home/pi/IOT-project/logs/ryu.log
StandardError=append:/home/pi/IOT-project/logs/ryu.log

[Install]
WantedBy=multi-user.target
```

**Zero Trust Framework Service** (`/etc/systemd/system/zero-trust-sdn.service`):

```ini
[Unit]
Description=Zero Trust SDN Framework
After=network.target docker.service ryu-sdn-controller.service
Wants=network-online.target docker.service ryu-sdn-controller.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/IOT-project
Environment="PATH=/home/pi/IOT-project/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/pi/IOT-project/venv/bin/python3 /home/pi/IOT-project/zero_trust_integration.py
Restart=always
RestartSec=10
StandardOutput=append:/home/pi/IOT-project/logs/zero_trust.log
StandardError=append:/home/pi/IOT-project/logs/zero_trust.log

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ryu-sdn-controller
sudo systemctl enable zero-trust-sdn
sudo systemctl start ryu-sdn-controller
sudo systemctl start zero-trust-sdn
```

#### Option C: Manual Start (Development/Testing)

For development or testing, start services manually:

**Terminal 1 - Ryu SDN Controller**:
```bash
cd ~/IOT-project
source venv/bin/activate
ryu-manager --ofp-tcp-listen-port 6653 ryu_controller/sdn_policy_engine.py
```

**Terminal 2 - Zero Trust Framework**:
```bash
cd ~/IOT-project
source venv/bin/activate
python3 zero_trust_integration.py
```

**Terminal 3 - Flask Controller** (if needed):
```bash
cd ~/IOT-project
source venv/bin/activate
python3 controller.py
```

## Configuration

### Network Configuration

1. Configure Raspberry Pi as SDN controller:
   - Set static IP address (recommended: 192.168.1.100)
   - Configure firewall rules (ports 5000, 6653, 22)
   - Enable SSH access

2. Connect SDN switch:
   - Connect switch to Raspberry Pi via Ethernet
   - Configure switch to connect to controller IP (default: 6653)
   - For Mininet testing: `sudo mn --controller=remote,ip=192.168.1.100,port=6653`

### SDN Controller Configuration

The Ryu SDN Controller is configured to:
- Listen on port 6653 (OpenFlow standard)
- Run the `SDNPolicyEngine` application
- Connect to Identity, Trust, and Analyst modules
- Support dynamic policy enforcement

**Key Features**:
- **Policy Translation**: Receives high-level policies from Identity module and translates to granular OpenFlow rules
- **Threat Alert Handling**: Listens for alerts from Analyst module and dynamically installs rules
- **Traffic Orchestration**: Uses Traffic Orchestrator for intelligent policy decisions based on multiple factors

### Zero Trust Framework Configuration

The framework integrates:
- **Identity Manager**: Device onboarding and certificate management
- **Trust Evaluator**: Dynamic trust scoring and policy adaptation
- **Heuristic Analyst**: Anomaly detection and threat alerts
- **Honeypot Manager**: Threat intelligence collection
- **Traffic Orchestrator**: Central policy decision engine

**Background Threads**:
- Honeypot Monitor: Every 10 seconds
- Device Attestation: Every 5 minutes
- Policy Adapter: Every 1 minute
- Analyst Monitor: Every 30 seconds

### Performance Optimization

For Raspberry Pi 4, consider:

1. **Overclocking** (optional):
   ```bash
   # Edit /boot/config.txt
   sudo nano /boot/config.txt
   # Add: over_voltage=2, arm_freq=2000
   ```

2. **Swap space**:
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

3. **Disable unnecessary services**:
   ```bash
   sudo systemctl disable bluetooth
   sudo systemctl disable avahi-daemon
   ```

## Monitoring

### Check System Status

```bash
# Check service status
sudo systemctl status zero-trust-sdn.service

# Check Docker containers
docker ps

# Check logs
tail -f logs/zero_trust.log
```

### Access Dashboard

The web dashboard should be accessible at:
```
http://<raspberry-pi-ip>:5000
```

## Troubleshooting

### Common Issues

1. **Docker not starting**:
   ```bash
   sudo systemctl restart docker
   ```

2. **Ryu controller not connecting**:
   - Check firewall rules
   - Verify switch configuration
   - Check controller IP address

3. **High CPU usage**:
   - Reduce honeypot logging verbosity
   - Adjust polling intervals
   - Disable unnecessary features

4. **Certificate errors**:
   ```bash
   # Regenerate CA
   rm -rf certs/*
   python3 -c "from identity_manager.certificate_manager import CertificateManager; cm = CertificateManager(); print('CA created')"
   ```

## Maintenance

### Regular Tasks

1. **Update system**:
   ```bash
   sudo apt update && sudo apt upgrade
   ```

2. **Backup database**:
   ```bash
   cp identity.db backups/identity_$(date +%Y%m%d).db
   ```

3. **Clean logs**:
   ```bash
   find logs/ -name "*.log" -mtime +30 -delete
   ```

## Performance Benchmarks

Expected performance on Raspberry Pi 4:

- Flow processing: ~1000 flows/second
- Device onboarding: < 5 seconds
- Trust score calculation: < 100ms
- Policy adaptation: < 500ms
- Honeypot log parsing: ~100 entries/second

## Security Considerations

1. **Change default passwords**
2. **Enable firewall**:
   ```bash
   sudo ufw enable
   sudo ufw allow 5000/tcp  # Dashboard
   sudo ufw allow 6653/tcp   # OpenFlow
   ```

3. **Use SSH keys** instead of passwords
4. **Regular security updates**
5. **Monitor system logs**

## New Features

### Policy Translation from Identity Module

The SDN controller now automatically receives and translates high-level policy definitions from the Identity module into granular OpenFlow rules. This ensures least-privilege access enforcement.

**How it works**:
1. Identity module generates policy from behavioral baseline
2. Policy sent to SDN Policy Engine via `apply_policy_from_identity()`
3. Each policy rule translated to OpenFlow match fields
4. Rules installed on all connected switches

### Threat Alert Integration

The system now listens for threat alerts from the Analyst module and dynamically installs OpenFlow rules to redirect suspicious traffic.

**How it works**:
1. Analyst module detects anomalies
2. Background thread (`monitor_analyst_alerts`) polls for alerts
3. Alerts trigger `handle_analyst_alert()` in SDN Policy Engine
4. Dynamic rules installed to redirect traffic to honeypot

### Traffic Orchestration

A new Traffic Orchestrator component makes intelligent policy decisions based on multiple real-time variables:
- Device identity and authentication
- Current trust scores
- Active threat intelligence
- Recent security alerts

**How it works**:
1. Traffic Orchestrator gathers all relevant factors
2. Makes intelligent decision (allow/deny/redirect/quarantine)
3. Applies decision through SDN Policy Engine
4. Maintains audit trail of decisions

See `docs/IMPLEMENTATION_FEATURES.md` for detailed documentation.

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review documentation in `docs/`
- Run integration tests: `python3 -m pytest integration_test/`
- See implementation features: `docs/IMPLEMENTATION_FEATURES.md`

