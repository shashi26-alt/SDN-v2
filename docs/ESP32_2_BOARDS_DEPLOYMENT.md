# Real-World Deployment Guide: 2 ESP Boards

## 🎯 Overview

This guide will help you deploy the IoT Security Framework with **2 ESP32/ESP8266 boards** in a real-world scenario. You'll set up:
- **1 ESP board as Gateway** (connects to your WiFi and creates AP for nodes)
- **1 ESP board as Node** (connects to gateway and sends sensor data)
- **Controller** (runs on your computer or Raspberry Pi)

---

## 📋 Prerequisites

### Hardware Required
- ✅ 2x ESP32 or ESP8266 development boards
- ✅ 2x USB cables (for programming and power)
- ✅ Computer (Windows/Mac/Linux) for controller
- ✅ WiFi router/access point
- ✅ Optional: Sensors (DHT22, DS18B20, etc.)

### Software Required
- ✅ Arduino IDE (latest version)
- ✅ Python 3.8+ (for controller)
- ✅ USB drivers for ESP32 (CP2102 or CH340)

---

## 🚀 Step-by-Step Deployment

### **PHASE 1: Controller Setup** (15 minutes)

#### Step 1.1: Install Python Dependencies

```bash
# Navigate to project directory
cd IOT-project-main

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 1.2: Find Your Computer's IP Address

**Windows:**
```cmd
ipconfig
# Look for "IPv4 Address" under your WiFi adapter
# Example: 192.168.1.105
```

**Linux/Mac:**
```bash
ifconfig
# or
ip addr show
# Look for inet address under wlan0 or eth0
# Example: 192.168.1.105
```

**📝 Write down your IP address - you'll need it for ESP32 configuration!**

#### Step 1.3: Start the Controller

```bash
# Make sure virtual environment is activated
python controller.py
```

You should see:
```
Starting Flask Controller on http://0.0.0.0:5000
Device onboarding system initialized
```

**✅ Keep this terminal window open!**

#### Step 1.4: Verify Controller is Running

Open your web browser and go to:
```
http://localhost:5000
```

You should see the dashboard. If yes, controller is working! ✅

---

### **PHASE 2: ESP32 Gateway Setup** (20 minutes)

#### Step 2.1: Install Arduino IDE and ESP32 Support

1. **Download Arduino IDE**: https://www.arduino.cc/en/software
2. **Install Arduino IDE**
3. **Add ESP32 Board Support**:
   - Open Arduino IDE
   - Go to **File → Preferences**
   - In "Additional Board Manager URLs", add:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Click **OK**
   - Go to **Tools → Board → Boards Manager**
   - Search for "ESP32"
   - Install "esp32" by Espressif Systems

#### Step 2.2: Install Required Libraries

In Arduino IDE:
- Go to **Tools → Manage Libraries**
- Install:
  - **ArduinoJson** (by Benoit Blanchon) - Version 6.x
  - **HTTPClient** (usually included with ESP32)

#### Step 2.3: Configure Gateway Code

1. **Open gateway code**: `esp32/gateway.ino` or `esp8266/gateway_node.ino`

2. **Update these settings**:

```cpp
// WiFi Access Point (for nodes to connect)
const char *ap_ssid = "ESP32-AP";        // You can change this
const char *ap_password = "12345678";     // Minimum 8 characters

// Your WiFi Network (gateway connects to this)
const char *sta_ssid = "YOUR_WIFI_NAME";      // ⚠️ CHANGE THIS!
const char *sta_password = "YOUR_WIFI_PASSWORD"; // ⚠️ CHANGE THIS!

// Controller IP (your computer's IP from Step 1.2)
const char *controller_ip = "192.168.1.105";  // ⚠️ CHANGE THIS!
```

**Important**: Replace:
- `YOUR_WIFI_NAME` with your actual WiFi network name
- `YOUR_WIFI_PASSWORD` with your WiFi password
- `192.168.1.105` with your computer's IP address from Step 1.2

#### Step 2.4: Upload Gateway Firmware

1. **Connect ESP32 #1** to computer via USB
2. **Select Board**: Tools → Board → ESP32 Dev Module (or ESP8266 if using ESP8266)
3. **Select Port**: Tools → Port → (your ESP32 port, e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)
4. **Upload**: Click Upload button (→) or Sketch → Upload
5. **Wait** for "Done uploading" message

#### Step 2.5: Verify Gateway Operation

1. **Open Serial Monitor**: Tools → Serial Monitor
2. **Set Baud Rate**: 115200
3. **Check Output**: You should see:
   ```
   Gateway AP Started
   Connected to WiFi
   ```

4. **Verify Access Point**: 
   - Look for "ESP32-AP" in your phone/computer's WiFi networks
   - You should see it as an available network

5. **Verify WiFi Connection**:
   - Check your router's admin panel
   - Gateway should appear as a connected device

**✅ Gateway is ready!**

---

### **PHASE 3: ESP32 Node Setup** (15 minutes)

#### Step 3.1: Configure Node Code

1. **Open node code**: `esp32/node.ino` or `esp8266/node.ino`

2. **Update these settings**:

```cpp
// Gateway AP Configuration (must match gateway settings)
const char *ssid = "ESP32-AP";           // Must match gateway AP name
const char *password = "12345678";        // Must match gateway AP password

// Gateway IP (when connecting to gateway AP)
const char *controller_ip = "192.168.4.1"; // Gateway's AP IP (usually 192.168.4.1)

// Device ID (UNIQUE for each node)
String device_id = "ESP32_Node1";         // ⚠️ CHANGE THIS for each node!
```

**Important**: 
- `ssid` and `password` must match the gateway AP settings
- `device_id` must be unique for each node (e.g., "ESP32_Node1", "ESP32_Node2")

#### Step 3.2: Upload Node Firmware

1. **Connect ESP32 #2** to computer via USB
2. **Select Board**: Tools → Board → ESP32 Dev Module
3. **Select Port**: Tools → Port → (your ESP32 port)
4. **Upload**: Click Upload button
5. **Wait** for "Done uploading" message

#### Step 3.3: Verify Node Operation

1. **Open Serial Monitor**: Tools → Serial Monitor (115200 baud)
2. **Check Output**: You should see:
   ```
   Connected to Gateway
   Received token: 550e8400-e29b-41d4-a716-446655440000
   Sent: {"device_id":"ESP32_Node1",...} | Response: 200
   ```

3. **Check Data Transmission**: 
   - You should see "Sent: ... Response: 200" every 5 seconds
   - This means data is being sent successfully!

**✅ Node is ready!**

---

### **PHASE 4: Device Onboarding** (5 minutes)

#### Step 4.1: Check Pending Devices

1. **Open Dashboard**: http://localhost:5000
2. **Click "Device Approval" tab**
3. **Check for pending devices**: Your ESP32 node should appear in the pending list

#### Step 4.2: Approve Device

1. **Find your device** in the pending list (shows MAC address and device ID)
2. **Click "Approve" button**
3. **Confirm approval** in the popup
4. **Device will be onboarded automatically**:
   - Certificate generated
   - Behavioral profiling started
   - Device added to system

#### Step 4.3: Verify Device is Onboarded

1. **Check Dashboard**: Device should appear in the main topology view
2. **Check Data Flow**: You should see packet counts increasing
3. **Check Logs**: Controller terminal should show device activity

**✅ Device is onboarded!**

---

### **PHASE 5: Testing & Verification** (10 minutes)

#### Test 1: Data Transmission

1. **Check Serial Monitor** (Node ESP32):
   - Should show "Sent: ... Response: 200" every 5 seconds

2. **Check Dashboard**:
   - Device should show in topology
   - Packet count should be increasing
   - Last seen timestamp should update

#### Test 2: Dashboard Functionality

1. **View Topology**: Check network graph shows your device
2. **View Metrics**: Check packet counts, data rates
3. **View Logs**: Check for any errors or warnings

#### Test 3: Security Features

1. **Revoke Device** (in dashboard):
   - Device should stop sending data
   - Status should change to "revoked"

2. **Re-approve Device**:
   - Device should resume sending data
   - Status should change to "active"

#### Test 4: Behavioral Profiling

1. **Wait 5 minutes** after device approval
2. **Check logs**: System should automatically finalize onboarding
3. **Check baseline**: Device should have behavioral baseline established
4. **Check policy**: Least-privilege policy should be generated

**✅ All tests passed!**

---

## 🔧 Configuration Summary

### Network Topology

```
┌─────────────────┐
│  Your WiFi AP   │
│  (192.168.1.1)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ↓         ↓
┌─────────┐ ┌──────────────┐
│Computer │ │ ESP32 Gateway│
│(Controller)│ │              │
│192.168.1.X│ │ AP: ESP32-AP │
│          │ │ STA: DHCP    │
└─────────┘ └──────┬───────┘
                   │
                   │ WiFi AP
                   │ "ESP32-AP"
                   │
                   ↓
            ┌──────────────┐
            │ ESP32 Node 1 │
            │(192.168.4.X) │
            └──────────────┘
```

### IP Address Configuration

- **Controller (Computer)**: `192.168.1.X` (from your router DHCP)
- **Gateway (STA mode)**: `192.168.1.X` (from your router DHCP)
- **Gateway (AP mode)**: `192.168.4.1` (fixed)
- **Node**: `192.168.4.X` (DHCP from gateway)

---

## 🐛 Troubleshooting

### Problem: Gateway not creating AP

**Solutions**:
- ✅ Check `ap_ssid` and `ap_password` in gateway code
- ✅ Verify `WiFi.mode(WIFI_AP_STA)` is set
- ✅ Check Serial Monitor for error messages
- ✅ Try resetting ESP32 (press reset button)

### Problem: Gateway not connecting to WiFi

**Solutions**:
- ✅ Verify `sta_ssid` and `sta_password` are correct
- ✅ Check WiFi signal strength
- ✅ Verify router allows new connections
- ✅ Check Serial Monitor for connection errors

### Problem: Node not connecting to Gateway

**Solutions**:
- ✅ Verify AP name and password match gateway settings
- ✅ Check Gateway is powered and AP is active (look for "ESP32-AP" network)
- ✅ Reduce distance between node and gateway
- ✅ Check Serial Monitor for connection errors
- ✅ Try resetting both devices

### Problem: Node not receiving token

**Solutions**:
- ✅ Verify device_id is unique
- ✅ Check Gateway can reach controller (ping controller IP from gateway network)
- ✅ Verify controller is running (check http://localhost:5000)
- ✅ Check controller logs for errors

### Problem: Data not reaching controller

**Solutions**:
- ✅ Check token is valid (not expired)
- ✅ Verify Gateway is forwarding data (check Serial Monitor)
- ✅ Check controller logs for errors
- ✅ Verify firewall allows port 5000
- ✅ Test controller endpoint: `curl http://localhost:5000/api/devices`

### Problem: Controller not starting

**Solutions**:
- ✅ Check port 5000 is not in use: `netstat -an | grep 5000`
- ✅ Verify all dependencies installed: `pip list`
- ✅ Check Python version: `python3 --version` (need 3.8+)
- ✅ Check for errors in terminal output

### Problem: Device not appearing in dashboard

**Solutions**:
- ✅ Check device is sending data (Serial Monitor)
- ✅ Verify device is approved in "Device Approval" tab
- ✅ Refresh dashboard page
- ✅ Check browser console for JavaScript errors
- ✅ Verify controller is receiving data (check logs)

---

## 📊 Monitoring Your System

### Real-Time Monitoring

1. **Dashboard**: http://localhost:5000
   - View device status
   - Monitor packet counts
   - Check for alerts

2. **Serial Monitor** (ESP32):
   - Monitor device activity
   - Check connection status
   - View data transmission

3. **Controller Logs**:
   - Check terminal output
   - View error messages
   - Monitor system activity

### Key Metrics to Watch

- ✅ **Device Status**: Active/Inactive
- ✅ **Packet Count**: Should increase over time
- ✅ **Last Seen**: Should update regularly
- ✅ **Connection Status**: Should show "Connected"
- ✅ **Token Status**: Should be valid

---

## 🔒 Security Best Practices

### 1. Change Default Passwords

```cpp
// In gateway.ino
const char *ap_password = "YourStrongPassword123!"; // Change from "12345678"
```

### 2. Use Strong WiFi Password

Ensure your WiFi network uses WPA2/WPA3 encryption.

### 3. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 5000/tcp  # Controller
sudo ufw enable
```

### 4. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
pip install --upgrade -r requirements.txt
```

---

## 📈 Next Steps

### Adding More Devices

1. **Configure additional ESP32 nodes**:
   - Use unique `device_id` for each
   - Upload firmware to each device
   - Approve in dashboard

### Adding Sensors

1. **Connect sensors** to ESP32 node:
   - DHT22 (temperature/humidity)
   - DS18B20 (temperature)
   - PIR (motion)
   - LDR (light)

2. **Update node code** to read sensors (see `docs/REAL_WORLD_DEPLOYMENT.md`)

3. **Upload updated firmware**

### Production Deployment

1. **Deploy controller on Raspberry Pi** (see `docs/RASPBERRY_PI_DEPLOYMENT.md`)
2. **Set up systemd services** for auto-start
3. **Configure static IP** for controller
4. **Set up monitoring** and alerting
5. **Regular backups** of database and certificates

---

## 📝 Quick Reference

### Important Files

- **Gateway Code**: `esp32/gateway.ino` or `esp8266/gateway_node.ino`
- **Node Code**: `esp32/node.ino` or `esp8266/node.ino`
- **Controller**: `controller.py`
- **Configuration**: Update IP addresses in ESP32 code

### Important IPs

- **Controller**: Your computer's IP (from `ipconfig`/`ifconfig`)
- **Gateway AP**: `192.168.4.1` (fixed)
- **Gateway STA**: DHCP from your router

### Important Ports

- **Controller**: `5000` (HTTP)
- **OpenFlow**: `6653` (if using SDN)

### Default Credentials

- **Gateway AP**: SSID: `ESP32-AP`, Password: `12345678`
- **Change these in production!**

---

## ✅ Deployment Checklist

- [ ] Controller installed and running
- [ ] Computer IP address identified
- [ ] Gateway ESP32 configured and uploaded
- [ ] Gateway creating AP ("ESP32-AP" visible)
- [ ] Gateway connected to WiFi
- [ ] Node ESP32 configured and uploaded
- [ ] Node connected to Gateway AP
- [ ] Node receiving token
- [ ] Node sending data (Response: 200)
- [ ] Device appears in dashboard
- [ ] Device approved in dashboard
- [ ] Data flowing in dashboard
- [ ] Behavioral profiling working (wait 5 minutes)
- [ ] All tests passed

---

## 🆘 Getting Help

### Check Logs

```bash
# Controller logs
tail -f logs/controller.log

# Check for errors
grep -i error logs/*.log
```

### Common Issues

1. **Port already in use**: Kill process using port 5000
2. **Firewall blocking**: Allow port 5000
3. **WiFi connection issues**: Check credentials and signal strength
4. **Device not appearing**: Check device approval tab

### Documentation

- **Full Deployment Guide**: `docs/REAL_WORLD_DEPLOYMENT.md`
- **Raspberry Pi Guide**: `docs/RASPBERRY_PI_DEPLOYMENT.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Project README**: `README.md`

---

## 🎉 Success!

If you've completed all steps and see:
- ✅ Devices in dashboard
- ✅ Data flowing
- ✅ No errors in logs

**Congratulations! Your IoT Security Framework is deployed and working!** 🚀

---

**Last Updated**: 2024
**Version**: 1.0.0

