# Raspberry Pi Quick Start Guide

## 🚀 Fast Deployment (5 Minutes)

### Step 1: Copy Project to Raspberry Pi

```bash
# On your computer, copy project to Raspberry Pi
scp -r IOT-project pi@<raspberry-pi-ip>:~/

# Or use USB drive, or clone from repository
```

### Step 2: SSH into Raspberry Pi

```bash
ssh pi@<raspberry-pi-ip>
```

### Step 3: Run Deployment Script

```bash
cd ~/IOT-project
sudo bash scripts/deploy_raspberry_pi.sh
```

**That's it!** The script will:
- ✅ Install all dependencies
- ✅ Set up virtual environment
- ✅ Configure Docker
- ✅ Install systemd services
- ✅ Set up firewall

### Step 4: Start Services

```bash
# Start all services
sudo systemctl start ryu-sdn-controller
sudo systemctl start zero-trust-sdn
sudo systemctl start flask-controller

# Enable auto-start on boot
sudo systemctl enable ryu-sdn-controller
sudo systemctl enable zero-trust-sdn
sudo systemctl enable flask-controller
```

### Step 5: Verify Deployment

```bash
# Run verification script
bash scripts/verify_deployment.sh

# Check service status
sudo systemctl status flask-controller
```

### Step 6: Access Dashboard

Open browser and go to:
```
http://<raspberry-pi-ip>:5000
```

## 📋 What Gets Installed

- **Python 3.8+** with virtual environment
- **Docker** for honeypot containers
- **Ryu SDN Controller** (port 6653)
- **Zero Trust Framework** (background service)
- **Flask Controller** (port 5000, web dashboard)
- **All Python dependencies** from requirements.txt

## 🔧 Common Commands

```bash
# Check service status
sudo systemctl status flask-controller

# View logs
tail -f ~/IOT-project/logs/controller.log
tail -f ~/IOT-project/logs/ryu.log

# Restart service
sudo systemctl restart flask-controller

# Stop service
sudo systemctl stop flask-controller

# Check if dashboard is accessible
curl http://localhost:5000
```

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u flask-controller -n 50

# Check for errors
grep -i error ~/IOT-project/logs/*.log
```

### Port Already in Use
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Kill the process
sudo kill <PID>
```

### Can't Access Dashboard
```bash
# Check firewall
sudo ufw status

# Allow port 5000
sudo ufw allow 5000/tcp

# Check if service is running
sudo systemctl status flask-controller
```

## 📚 Full Documentation

For detailed information, see:
- `docs/RASPBERRY_PI_DEPLOYMENT.md` - Complete deployment guide
- `docs/deployment_guide.md` - General deployment information
- `README.md` - Project overview

## ✅ Next Steps

1. **Configure ESP32 Devices**: Update gateway firmware with Raspberry Pi IP
2. **Test Connection**: Verify devices can connect
3. **Monitor Dashboard**: Check real-time status
4. **Test Security**: Trigger alerts and verify responses

---

**Need Help?** Check logs in `~/IOT-project/logs/` directory

