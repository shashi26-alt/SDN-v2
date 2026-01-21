# Raspberry Pi Deployment Checklist

Use this checklist to ensure a complete and successful deployment.

## Pre-Deployment

- [ ] Raspberry Pi 4 (4GB+ RAM) ready
- [ ] MicroSD card (32GB+) with Raspberry Pi OS installed
- [ ] Power supply connected (5V 3A recommended)
- [ ] Network connection (Ethernet or WiFi) configured
- [ ] SSH access enabled
- [ ] Project files copied to Raspberry Pi (`~/IOT-project`)

## System Setup

- [ ] System updated (`sudo apt update && sudo apt upgrade`)
- [ ] Base packages installed (Python, pip, git, etc.)
- [ ] Docker installed and running
- [ ] User added to docker group
- [ ] Static IP configured (recommended)
- [ ] Firewall configured (UFW)

## Project Setup

- [ ] Project directory exists (`~/IOT-project`)
- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] Virtual environment activated
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Ryu SDN Controller installed
- [ ] TensorFlow installed (optional, for ML features)
- [ ] Required directories created (certs, logs, honeypot_data)

## Service Installation

- [ ] Deployment script run (`sudo bash scripts/deploy_raspberry_pi.sh`)
- [ ] Systemd services installed:
  - [ ] `ryu-sdn-controller.service`
  - [ ] `zero-trust-sdn.service`
  - [ ] `flask-controller.service`
- [ ] Services enabled for auto-start on boot

## Verification

- [ ] Verification script run (`bash scripts/verify_deployment.sh`)
- [ ] All services started successfully
- [ ] Port 5000 (Flask) listening
- [ ] Port 6653 (OpenFlow) listening
- [ ] Dashboard accessible (`http://<pi-ip>:5000`)
- [ ] No critical errors in logs

## Testing

- [ ] Dashboard loads correctly
- [ ] API endpoints responding
- [ ] Services restart after reboot
- [ ] Logs being written correctly
- [ ] Docker containers can be created (if using honeypots)

## ESP32 Configuration

- [ ] ESP32 gateway firmware updated with Raspberry Pi IP
- [ ] ESP32 nodes configured with gateway SSID
- [ ] Devices can connect to gateway
- [ ] Devices can authenticate with controller
- [ ] Data flowing from devices to controller

## Security

- [ ] Firewall rules configured
- [ ] Default passwords changed
- [ ] SSH keys configured (recommended)
- [ ] Unnecessary services disabled
- [ ] Regular updates scheduled

## Monitoring

- [ ] Log rotation configured
- [ ] Backup strategy in place
- [ ] Monitoring tools installed (optional)
- [ ] Alert notifications configured (optional)

## Documentation

- [ ] Network topology documented
- [ ] IP addresses recorded
- [ ] Device IDs documented
- [ ] Configuration changes noted
- [ ] Issues encountered documented

## Post-Deployment

- [ ] System running stable for 24 hours
- [ ] All features tested
- [ ] Performance acceptable
- [ ] Backup tested and verified
- [ ] Team members trained (if applicable)

## Troubleshooting Reference

**Common Issues:**
- Service won't start → Check logs: `sudo journalctl -u <service>`
- Port in use → Find process: `sudo lsof -i :5000`
- Permission errors → Fix ownership: `sudo chown -R pi:pi ~/IOT-project`
- Docker issues → Restart Docker: `sudo systemctl restart docker`

**Log Locations:**
- Controller: `~/IOT-project/logs/controller.log`
- Ryu: `~/IOT-project/logs/ryu.log`
- Zero Trust: `~/IOT-project/logs/zero_trust.log`

**Useful Commands:**
```bash
# Check service status
sudo systemctl status flask-controller

# View logs
tail -f ~/IOT-project/logs/controller.log

# Restart service
sudo systemctl restart flask-controller

# Check system resources
htop
```

---

**Deployment Date**: _______________

**Deployed By**: _______________

**Raspberry Pi Model**: _______________

**Raspberry Pi IP**: _______________

**Notes**: 
_________________________________________________
_________________________________________________
_________________________________________________

