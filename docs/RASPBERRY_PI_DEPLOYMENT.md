# Raspberry Pi Deployment Guide

## Complete Deployment Guide for Zero Trust SDN Framework on Raspberry Pi

This guide provides step-by-step instructions for deploying the entire IoT Security Framework on a Raspberry Pi for real-world testing.

## Prerequisites

### Hardware Requirements
- **Raspberry Pi 4** (4GB RAM minimum, 8GB recommended)
- **MicroSD Card** (32GB minimum, Class 10 or better)
- **Power Supply** (Official Raspberry Pi 5V 3A USB-C power supply recommended)
- **Network Connection** (Ethernet or WiFi)
- **Optional**: SDN-compatible switch for physical network testing

### Software Requirements
- **Raspberry Pi OS** (64-bit recommended, based on Debian)
- **Internet Connection** (for package installation)
- **SSH Access** (for remote deployment)

## Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
# Clone or copy project to Raspberry Pi
cd ~
# If project is already there, skip this step
# Otherwise, copy project files to ~/IOT-project

# Run deployment script
cd ~/IOT-project
sudo bash scripts/deploy_raspberry_pi.sh
```

The script will:
- Update system packages
- Install all dependencies
- Set up virtual environment
- Configure Docker
- Install systemd services
- Configure firewall
- Set proper permissions

### Option 2: Manual Deployment

Follow the detailed steps below for manual installation.

## Detailed Installation Steps

### 1. Initial System Setup

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install base packages
sudo apt install -y python3 python3-pip python3-venv git openssl sqlite3 \
    docker.io docker-compose build-essential libssl-dev libffi-dev \
    python3-dev curl wget ufw
```

### 2. Configure Docker

```bash
# Start and enable Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group (replace 'pi' with your username)
sudo usermod -aG docker pi

# Log out and back in for group changes to take effect
```

### 3. Set Up Project

```bash
# Navigate to home directory
cd ~

# If project is not already there, copy/clone it
# For example, if you have it on a USB drive:
# cp -r /media/usb/IOT-project ~/IOT-project

cd ~/IOT-project

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 4. Install Python Dependencies

**Important for ARM/Raspberry Pi**: TensorFlow installation may take time and may require specific versions.

```bash
# Install TensorFlow (ARM-compatible)
# Option 1: TensorFlow CPU (recommended for Pi)
pip install tensorflow-cpu

# Option 2: Standard TensorFlow (may be slower)
# pip install tensorflow

# Install other dependencies
pip install -r requirements.txt

# Install Ryu SDN Controller
pip install ryu eventlet
```

**Note**: If TensorFlow installation fails or is too slow, the system will run with heuristic-based detection only.

### 5. Create Required Directories

```bash
mkdir -p certs honeypot_data logs data/models data/logs data/certs
chmod 755 certs honeypot_data logs
```

### 6. Install Systemd Services

The deployment script automatically creates these services. For manual installation:

```bash
# Copy service files (adjust paths as needed)
sudo cp scripts/ryu-sdn-controller.service /etc/systemd/system/
sudo cp scripts/zero-trust-sdn.service /etc/systemd/system/
sudo cp scripts/flask-controller.service /etc/systemd/system/

# Edit service files to match your project path
sudo nano /etc/systemd/system/ryu-sdn-controller.service
# Update paths: /home/pi/IOT-project

# Reload systemd
sudo systemctl daemon-reload
```

### 7. Configure Network

#### Static IP (Recommended)

```bash
# Edit network configuration
sudo nano /etc/dhcpcd.conf

# Add (adjust IP address as needed):
# interface eth0
# static ip_address=192.168.1.100/24
# static routers=192.168.1.1
# static domain_name_servers=8.8.8.8 8.8.4.4

# Restart networking
sudo systemctl restart dhcpcd
```

#### Firewall Configuration

```bash
# Enable firewall
sudo ufw enable

# Allow required ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp   # Flask Controller
sudo ufw allow 6653/tcp   # OpenFlow Controller

# Check status
sudo ufw status
```

### 8. Start Services

```bash
# Start services in order
sudo systemctl start ryu-sdn-controller
sudo systemctl start zero-trust-sdn
sudo systemctl start flask-controller

# Enable services to start on boot
sudo systemctl enable ryu-sdn-controller
sudo systemctl enable zero-trust-sdn
sudo systemctl enable flask-controller

# Check status
sudo systemctl status ryu-sdn-controller
sudo systemctl status zero-trust-sdn
sudo systemctl status flask-controller
```

## Verification

### Check Service Status

```bash
# Check all services
sudo systemctl status ryu-sdn-controller zero-trust-sdn flask-controller

# Check if ports are listening
sudo netstat -tuln | grep -E ':(5000|6653)'
```

### Access Dashboard

Open a web browser and navigate to:
```
http://<raspberry-pi-ip>:5000
```

Or from the Raspberry Pi itself:
```
http://localhost:5000
```

### Check Logs

```bash
# View logs
tail -f ~/IOT-project/logs/controller.log
tail -f ~/IOT-project/logs/ryu.log
tail -f ~/IOT-project/logs/zero_trust.log

# Check for errors
grep -i error ~/IOT-project/logs/*.log
```

## Configuration

### Network Configuration

1. **Controller IP**: Update ESP32 gateway code with Raspberry Pi IP address
2. **Port Configuration**: Default ports (5000, 6653) can be changed in service files
3. **Firewall Rules**: Adjust UFW rules if using different ports

### Performance Optimization

For better performance on Raspberry Pi:

```bash
# Increase swap space (if needed)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# Optional: Overclock (use with caution)
sudo nano /boot/config.txt
# Add: over_voltage=2, arm_freq=2000
```

### ML Model Configuration

If ML models are not loading:

1. Check model files exist:
   ```bash
   ls -la ~/IOT-project/data/models/
   ```

2. Verify TensorFlow installation:
   ```bash
   source ~/IOT-project/venv/bin/activate
   python3 -c "import tensorflow as tf; print(tf.__version__)"
   ```

3. System will fall back to heuristic detection if ML is unavailable

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status <service-name>

# View logs
sudo journalctl -u <service-name> -n 50

# Check for Python errors
~/IOT-project/venv/bin/python3 ~/IOT-project/controller.py
```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :5000
sudo lsof -i :6653

# Kill process (replace PID)
sudo kill <PID>
```

### Docker Issues

```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Check Docker group membership
groups
# Should include 'docker'
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R pi:pi ~/IOT-project

# Fix permissions
chmod 755 ~/IOT-project/certs
chmod 755 ~/IOT-project/logs
```

### High CPU/Memory Usage

```bash
# Monitor resources
htop

# Check process usage
ps aux | grep python

# Reduce ML model complexity or disable ML features
# Edit controller.py to skip ML initialization
```

## Maintenance

### Regular Updates

```bash
# Update system
sudo apt update && sudo apt upgrade

# Update Python packages
cd ~/IOT-project
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Backup

```bash
# Backup database
cp ~/IOT-project/identity.db ~/backups/identity_$(date +%Y%m%d).db

# Backup certificates
tar -czf ~/backups/certs_$(date +%Y%m%d).tar.gz ~/IOT-project/certs/
```

### Log Rotation

```bash
# Clean old logs (older than 30 days)
find ~/IOT-project/logs/ -name "*.log" -mtime +30 -delete
```

## Production Deployment Checklist

- [ ] System updated and secured
- [ ] Static IP configured
- [ ] Firewall rules configured
- [ ] All services installed and enabled
- [ ] Services start on boot
- [ ] Dashboard accessible from network
- [ ] Logs directory has proper permissions
- [ ] Docker configured and user added to docker group
- [ ] Backup strategy in place
- [ ] Monitoring configured (optional)
- [ ] ESP32 devices configured with correct IP
- [ ] Network topology verified

## Access Information

After deployment:

- **Web Dashboard**: `http://<raspberry-pi-ip>:5000`
- **API Endpoints**: `http://<raspberry-pi-ip>:5000/api/*`
- **SDN Controller**: Port 6653 (OpenFlow)
- **SSH Access**: Port 22

## Support

For issues:
1. Check logs in `~/IOT-project/logs/`
2. Review service status: `sudo systemctl status <service>`
3. Check system resources: `htop`
4. Review this documentation
5. Check project README.md

## Next Steps

1. **Configure ESP32 Devices**: Update gateway and node firmware with Raspberry Pi IP
2. **Test Connectivity**: Verify devices can connect to controller
3. **Monitor Dashboard**: Check real-time device status and alerts
4. **Test Security Features**: Trigger alerts and verify honeypot redirection
5. **Performance Tuning**: Optimize for your specific use case

---

**Deployment Date**: Record when you deployed
**Raspberry Pi Model**: Record your Pi model and RAM
**Network Configuration**: Document your network setup
**Issues Encountered**: Keep notes for future reference

