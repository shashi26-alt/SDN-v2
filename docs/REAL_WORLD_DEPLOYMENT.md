# SecureIoT-SDN - Real-World IoT Device Implementation Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Hardware Requirements](#hardware-requirements)
3. [Software Setup](#software-setup)
4. [Network Configuration](#network-configuration)
5. [ESP32 Gateway Setup](#esp32-gateway-setup)
6. [ESP32 Node Setup](#esp32-node-setup)
7. [Physical Sensor Integration](#physical-sensor-integration)
8. [Controller Deployment](#controller-deployment)
9. [Testing and Verification](#testing-and-verification)
10. [Troubleshooting](#troubleshooting)
11. [Production Deployment](#production-deployment)
12. [Maintenance and Monitoring](#maintenance-and-monitoring)

---

## Introduction

This guide provides step-by-step instructions for implementing the SecureIoT-SDN framework with real-world IoT devices. You'll learn how to:

- Set up ESP32 microcontrollers as gateway and nodes
- Integrate physical sensors (temperature, motion, etc.)
- Deploy the controller on Raspberry Pi or server
- Configure network connectivity
- Test end-to-end functionality
- Deploy in production environments

### Prerequisites

- Basic knowledge of Arduino/ESP32 programming
- Understanding of WiFi networks
- Python programming basics
- Linux command line experience (for controller setup)
- Access to ESP32 development boards
- USB cables for programming

---

## Hardware Requirements

### ESP32 Development Boards

#### Gateway Requirements
- **ESP32 Development Board**: ESP32-WROOM-32 or ESP32-DevKitC
- **Power Supply**: 5V via USB or external power adapter (2A recommended)
- **Antenna**: Built-in PCB antenna (external antenna optional for better range)
- **USB Cable**: For programming and power

#### Node Requirements
- **ESP32 Development Board**: ESP32-WROOM-32 or ESP32-DevKitC
- **Power Supply**: 5V via USB or battery pack (for portable nodes)
- **Sensors**: Based on your use case (see Sensor Integration section)
- **USB Cable**: For programming
- **Breadboard and Jumper Wires**: For sensor connections

### Controller Server Options

#### Option 1: Raspberry Pi 4 (Recommended for SOHO)
- **Model**: Raspberry Pi 4 Model B
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 32GB+ microSD card (Class 10 or better)
- **OS**: Raspberry Pi OS (64-bit)
- **Network**: Ethernet or WiFi

#### Option 2: Linux Server/VM
- **CPU**: 2+ cores
- **RAM**: 4GB minimum
- **Storage**: 20GB+ free space
- **OS**: Ubuntu 20.04+ or Debian 11+
- **Network**: Ethernet connection

#### Option 3: Cloud Instance
- **Provider**: AWS EC2, Azure VM, or GCP Compute Engine
- **Instance**: t3.medium or equivalent
- **OS**: Ubuntu 20.04 LTS
- **Network**: Public IP with security groups configured

### Sensors (Optional)

Common sensors for IoT projects:

- **Temperature**: DS18B20, DHT22, LM35
- **Humidity**: DHT22, DHT11
- **Motion**: PIR sensor (HC-SR501)
- **Light**: LDR (Light Dependent Resistor), BH1750
- **Gas**: MQ-2, MQ-7
- **Distance**: Ultrasonic sensor (HC-SR04)

---

## Software Setup

### 1. Arduino IDE Installation

#### Windows
1. Download Arduino IDE from https://www.arduino.cc/en/software
2. Run installer and follow instructions
3. Install ESP32 board support (see below)

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install arduino

# Or download from website
wget https://downloads.arduino.cc/arduino-ide-latest-linux64.tar.xz
tar -xf arduino-ide-latest-linux64.tar.xz
cd arduino-ide-*
./arduino-ide
```

#### macOS
1. Download Arduino IDE from https://www.arduino.cc/en/software
2. Open .dmg file and drag to Applications
3. Install ESP32 board support (see below)

### 2. ESP32 Board Support Installation

1. Open Arduino IDE
2. Go to **File → Preferences**
3. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click **OK**
5. Go to **Tools → Board → Boards Manager**
6. Search for "ESP32"
7. Install "esp32" by Espressif Systems
8. Wait for installation to complete

### 3. Required Libraries

Install via **Tools → Manage Libraries**:

- **ArduinoJson** (by Benoit Blanchon) - Version 6.x
- **OneWire** (by Paul Stoffregen) - For DS18B20
- **DallasTemperature** (by Miles Burton) - For DS18B20
- **DHT sensor library** (by Adafruit) - For DHT22/DHT11
- **Adafruit Unified Sensor** (by Adafruit) - Required for DHT

### 4. Python Environment Setup

#### Install Python 3.8+
```bash
# Check Python version
python3 --version

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# macOS (using Homebrew)
brew install python3

# Windows: Download from python.org
```

#### Create Virtual Environment
```bash
cd /path/to/IOT-project
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Docker Installation (for Honeypot)

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Log out and back in for group changes
```

#### macOS
```bash
# Install Docker Desktop from docker.com
# Or using Homebrew:
brew install --cask docker
```

#### Windows
- Download Docker Desktop from docker.com
- Install and restart computer

---

## Network Configuration

### Network Topology

```
                    Internet
                       │
                       ↓
              ┌────────────────┐
              │   Router/AP     │
              │  (192.168.1.1)  │
              │  WiFi: YourWiFi │
              └────────┬────────┘
                       │
        ┌──────────────┴──────────────┐
        │                              │
        ↓                              ↓
┌───────────────┐            ┌───────────────┐
│ Controller   │            │ ESP32 Gateway  │
│ Server       │            │               │
│              │            │ AP: ESP32-AP  │
│(192.168.1.100)│            │(192.168.4.1)  │
│              │            │ STA: DHCP     │
└───────────────┘            └───────┬───────┘
                                     │
                                     │ WiFi AP
                                     │ "ESP32-AP"
                                     │ Password: 12345678
                                     ↓
                        ┌────────────┴────────────┐
                        │                         │
                        ↓                         ↓
                ┌──────────────┐         ┌──────────────┐
                │ ESP32 Node 1 │         │ ESP32 Node 2 │
                │(192.168.4.X) │         │(192.168.4.Y) │
                └──────────────┘         └──────────────┘
```

### IP Address Configuration

#### Controller Network (192.168.1.0/24)
- **Router**: 192.168.1.1
- **Controller**: 192.168.1.100 (static IP recommended)
- **Gateway (STA)**: DHCP from router (e.g., 192.168.1.50)

#### Gateway AP Network (192.168.4.0/24)
- **Gateway (AP)**: 192.168.4.1 (fixed)
- **Nodes**: 192.168.4.2-254 (DHCP from gateway)

### Setting Static IP for Controller

#### Linux (NetworkManager)
```bash
sudo nmtui
# Or edit /etc/netplan/50-cloud-init.yaml (Ubuntu)
```

#### Linux (Manual)
```bash
sudo nano /etc/network/interfaces

# Add:
auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 8.8.8.8 8.8.4.4

sudo systemctl restart networking
```

#### Raspberry Pi
```bash
sudo nano /etc/dhcpcd.conf

# Add:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

sudo systemctl restart dhcpcd
```

### Firewall Configuration

#### Linux (UFW)
```bash
sudo ufw allow 5000/tcp  # Flask controller
sudo ufw allow 6653/tcp  # OpenFlow (if using Ryu)
sudo ufw enable
```

#### Linux (iptables)
```bash
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 6653 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

---

## ESP32 Gateway Setup

### 1. Hardware Connection

1. Connect ESP32 to computer via USB cable
2. Ensure proper drivers installed (CP2102 or CH340)

### 2. Configure Gateway Firmware

Open `esp32/gateway.ino` in Arduino IDE and configure:

```cpp
// Access Point Configuration
const char *ap_ssid = "ESP32-AP";           // AP name
const char *ap_password = "12345678";        // AP password (min 8 chars)

// Station Mode Configuration (connects to your WiFi)
const char *sta_ssid = "YourWiFi";          // Your WiFi network name
const char *sta_password = "YourPassword";   // Your WiFi password

// Controller IP Address
const char *controller_ip = "192.168.1.100"; // Controller server IP
```

**Important**: Update `controller_ip` to match your controller's IP address.

### 3. Upload Firmware

1. **Select Board**: Tools → Board → ESP32 Dev Module
2. **Select Port**: Tools → Port → (your ESP32 port, e.g., /dev/ttyUSB0)
3. **Upload**: Click Upload button or Sketch → Upload
4. **Wait**: Wait for "Done uploading" message

### 4. Verify Gateway Operation

1. **Open Serial Monitor**: Tools → Serial Monitor
2. **Set Baud Rate**: 115200
3. **Check Output**: You should see:
   ```
   Gateway AP Started
   Connected to WiFi
   ```

4. **Verify AP**: Look for "ESP32-AP" in WiFi networks on your phone/computer
5. **Verify STA**: Check gateway connected to your WiFi (check router admin panel)

### 5. Gateway Troubleshooting

**Problem**: Gateway not creating AP
- **Solution**: Check `ap_ssid` and `ap_password` in code
- **Solution**: Ensure `WiFi.mode(WIFI_AP_STA)` is set
- **Solution**: Check Serial Monitor for error messages

**Problem**: Gateway not connecting to WiFi
- **Solution**: Verify `sta_ssid` and `sta_password` are correct
- **Solution**: Check WiFi signal strength
- **Solution**: Verify router allows new connections

**Problem**: Gateway not forwarding data
- **Solution**: Verify `controller_ip` is correct
- **Solution**: Check controller is running and accessible
- **Solution**: Test connectivity: `ping 192.168.1.100` from gateway network

---

## ESP32 Node Setup

### 1. Hardware Connection

1. Connect ESP32 to computer via USB cable
2. Connect sensors (see Sensor Integration section)

### 2. Configure Node Firmware

Open `esp32/node.ino` in Arduino IDE and configure:

```cpp
// Gateway AP Configuration
const char *ssid = "ESP32-AP";              // Gateway AP name
const char *password = "12345678";           // Gateway AP password

// Gateway IP (AP mode IP)
const char *controller_ip = "192.168.4.1";  // Gateway IP in AP mode

// Device ID (UNIQUE for each node)
String device_id = "ESP32_2";                // Change for each node!
```

**Critical**: Change `device_id` for each node (ESP32_2, ESP32_3, ESP32_4, etc.)

### 3. Update Controller Authorization

Edit `controller.py` and add device to authorized list:

```python
authorized_devices = {
    "ESP32_2": True,  # Add your device IDs here
    "ESP32_3": True,
    "ESP32_4": True
}
```

### 4. Upload Firmware to Each Node

For each ESP32 node:

1. **Update device_id**: Change in code (ESP32_2, ESP32_3, etc.)
2. **Select Board**: Tools → Board → ESP32 Dev Module
3. **Select Port**: Tools → Port → (your ESP32 port)
4. **Upload**: Click Upload button
5. **Repeat**: For each additional node

### 5. Verify Node Operation

1. **Open Serial Monitor**: Tools → Serial Monitor (115200 baud)
2. **Check Output**: You should see:
   ```
   Connected to Gateway
   Received token: 550e8400-e29b-41d4-a716-446655440000
   Sent: {"device_id":"ESP32_2",...} | Response: 200
   ```

3. **Verify Data**: Check controller logs or dashboard

### 6. Node Troubleshooting

**Problem**: Node not connecting to Gateway AP
- **Solution**: Verify AP name and password match Gateway
- **Solution**: Check Gateway is powered and AP is active
- **Solution**: Reduce distance between node and gateway
- **Solution**: Check Serial Monitor for connection errors

**Problem**: Node not receiving token
- **Solution**: Verify device_id is authorized in controller
- **Solution**: Check Gateway can reach controller
- **Solution**: Verify MAC address is unique

**Problem**: Data not reaching controller
- **Solution**: Check token is valid (not expired)
- **Solution**: Verify rate limit not exceeded
- **Solution**: Check controller logs for errors
- **Solution**: Verify Gateway is forwarding data

---

## Physical Sensor Integration

### Temperature Sensor (DS18B20)

#### Hardware Connection
```
DS18B20 Pinout:
- Red wire (VDD) → 3.3V
- Black wire (GND) → GND
- Yellow wire (DATA) → GPIO 4 (with 4.7kΩ pull-up resistor to 3.3V)
```

#### Code Integration

Add to `esp32/node.ino`:

```cpp
#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 4  // GPIO pin
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
    Serial.begin(115200);
    // ... existing WiFi setup ...
    sensors.begin();
}

void loop() {
    sensors.requestTemperatures();
    float temp = sensors.getTempCByIndex(0);
    
    // Send temperature data
    StaticJsonDocument<200> doc;
    doc["device_id"] = device_id;
    doc["token"] = token;
    doc["timestamp"] = String(millis() / 1000);
    doc["data"] = String(temp);
    doc["sensor_type"] = "temperature";
    
    String json;
    serializeJson(doc, json);
    // ... send to controller ...
    
    delay(5000);
}
```

### Humidity Sensor (DHT22)

#### Hardware Connection
```
DHT22 Pinout:
- VCC → 3.3V
- GND → GND
- DATA → GPIO 2 (with 10kΩ pull-up resistor to 3.3V)
```

#### Code Integration

```cpp
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

void setup() {
    dht.begin();
    // ... existing setup ...
}

void loop() {
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    
    StaticJsonDocument<200> doc;
    doc["device_id"] = device_id;
    doc["token"] = token;
    doc["timestamp"] = String(millis() / 1000);
    doc["temperature"] = String(temperature);
    doc["humidity"] = String(humidity);
    doc["sensor_type"] = "dht22";
    
    // ... send to controller ...
    delay(5000);
}
```

### Motion Sensor (PIR)

#### Hardware Connection
```
PIR Sensor (HC-SR501):
- VCC → 5V (or 3.3V)
- GND → GND
- OUT → GPIO 2
```

#### Code Integration

```cpp
#define PIR_PIN 2

void setup() {
    pinMode(PIR_PIN, INPUT);
    // ... existing setup ...
}

void loop() {
    int motion = digitalRead(PIR_PIN);
    String motion_status = motion ? "MOTION_DETECTED" : "NO_MOTION";
    
    StaticJsonDocument<200> doc;
    doc["device_id"] = device_id;
    doc["token"] = token;
    doc["timestamp"] = String(millis() / 1000);
    doc["data"] = motion_status;
    doc["sensor_type"] = "pir";
    
    // ... send to controller ...
    delay(1000);  // Check more frequently for motion
}
```

### Light Sensor (LDR)

#### Hardware Connection
```
LDR Circuit:
- One leg → 3.3V
- Other leg → GPIO 35 (ADC1) → 10kΩ resistor → GND
```

#### Code Integration

```cpp
#define LDR_PIN 35  // ADC1 pin

void setup() {
    // ... existing setup ...
}

void loop() {
    int light_value = analogRead(LDR_PIN);
    // Convert to percentage (0-100)
    int light_percent = map(light_value, 0, 4095, 0, 100);
    
    StaticJsonDocument<200> doc;
    doc["device_id"] = device_id;
    doc["token"] = token;
    doc["timestamp"] = String(millis() / 1000);
    doc["data"] = String(light_percent);
    doc["sensor_type"] = "ldr";
    
    // ... send to controller ...
    delay(5000);
}
```

### Multiple Sensors on One Node

```cpp
#include <OneWire.h>
#include <DallasTemperature.h>
#include <DHT.h>

#define ONE_WIRE_BUS 4
#define DHTPIN 2
#define DHTTYPE DHT22
#define PIR_PIN 5

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensors(&oneWire);
DHT dht(DHTPIN, DHTTYPE);

void setup() {
    pinMode(PIR_PIN, INPUT);
    tempSensors.begin();
    dht.begin();
    // ... WiFi setup ...
}

void loop() {
    // Read all sensors
    tempSensors.requestTemperatures();
    float temp = tempSensors.getTempCByIndex(0);
    float humidity = dht.readHumidity();
    int motion = digitalRead(PIR_PIN);
    
    // Create JSON with all sensor data
    StaticJsonDocument<400> doc;
    doc["device_id"] = device_id;
    doc["token"] = token;
    doc["timestamp"] = String(millis() / 1000);
    doc["temperature"] = String(temp);
    doc["humidity"] = String(humidity);
    doc["motion"] = motion ? "DETECTED" : "NONE";
    
    // ... send to controller ...
    delay(5000);
}
```

---

## Controller Deployment

### Option 1: Raspberry Pi 4 Deployment

#### 1. Install Raspberry Pi OS

1. Download Raspberry Pi Imager from raspberrypi.org
2. Flash OS to microSD card
3. Enable SSH: Create `ssh` file in boot partition
4. Configure WiFi: Create `wpa_supplicant.conf` in boot partition
5. Boot Raspberry Pi

#### 2. Initial Setup

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv git openssl sqlite3 docker.io

# Start Docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

#### 3. Clone and Setup Project

```bash
cd ~
git clone <repository-url> IOT-project
cd IOT-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 4. Configure Controller

Edit `controller.py`:

```python
# Update authorized devices
authorized_devices = {
    "ESP32_2": True,
    "ESP32_3": True,
    "ESP32_4": True
}

# Configure IP (if needed)
# Controller will bind to 0.0.0.0 (all interfaces)
```

#### 5. Create Systemd Service

Create `/etc/systemd/system/secureiot-sdn.service`:

```ini
[Unit]
Description=SecureIoT-SDN Controller
After=network.target docker.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/IOT-project
Environment="PATH=/home/pi/IOT-project/venv/bin"
ExecStart=/home/pi/IOT-project/venv/bin/python3 controller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable secureiot-sdn.service
sudo systemctl start secureiot-sdn.service

# Check status
sudo systemctl status secureiot-sdn.service
```

### Option 2: Linux Server Deployment

#### 1. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git openssl sqlite3 docker.io
```

#### 2. Setup Project

```bash
cd /opt  # or your preferred directory
git clone <repository-url> IOT-project
cd IOT-project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Run Controller

```bash
# Manual start
python controller.py

# Or use screen/tmux for background
screen -S secureiot
python controller.py
# Press Ctrl+A then D to detach
```

### Option 3: Cloud Deployment (AWS EC2)

#### 1. Launch EC2 Instance

- AMI: Ubuntu 20.04 LTS
- Instance Type: t3.medium
- Security Group: Allow ports 22 (SSH), 5000 (HTTP)

#### 2. Connect and Setup

```bash
# SSH to instance
ssh -i your-key.pem ubuntu@<instance-ip>

# Install dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv git docker.io

# Clone and setup (same as above)
```

#### 3. Configure Security Groups

- Inbound Rules:
  - Port 22: SSH (your IP)
  - Port 5000: HTTP (0.0.0.0/0 or specific IPs)

---

## Testing and Verification

### 1. Gateway Test

**Steps**:
1. Power on Gateway ESP32
2. Open Serial Monitor (115200 baud)
3. Verify output:
   ```
   Gateway AP Started
   Connected to WiFi
   ```
4. Check WiFi: Look for "ESP32-AP" network
5. Verify connectivity: `ping 192.168.4.1` from connected device

### 2. Node Test

**Steps**:
1. Power on Node ESP32
2. Open Serial Monitor (115200 baud)
3. Verify output:
   ```
   Connected to Gateway
   Received token: 550e8400-...
   Sent: {"device_id":"ESP32_2",...} | Response: 200
   ```
4. Check data transmission every 5 seconds

### 3. Controller Test

**Steps**:
1. Start controller: `python controller.py`
2. Check output:
   ```
   Starting Flask Controller on http://0.0.0.0:5000
   ML Security Engine initialized (if TensorFlow available)
   ```
3. Access dashboard: `http://localhost:5000` or `http://<controller-ip>:5000`
4. Verify dashboard loads

### 4. End-to-End Test

**Steps**:
1. **Verify Devices**: Check devices appear in dashboard
2. **Check Data Flow**: Verify packet counts increasing
3. **Test Topology**: Verify topology graph shows connections
4. **Test Authorization**:
   - Revoke device in dashboard
   - Verify device stops sending data
   - Re-authorize device
   - Verify device resumes sending
5. **Test ML Detection**: Send high-rate traffic, verify detection
6. **Test Policies**: Toggle SDN policies, verify enforcement

### 5. Sensor Data Test

**Steps**:
1. Connect sensor to node
2. Upload updated firmware
3. Check Serial Monitor for sensor readings
4. Verify data in dashboard
5. Check data format in controller logs

---

## Troubleshooting

### Common Issues

#### Gateway Issues

**Problem**: Gateway not creating AP
- Check `ap_ssid` and `ap_password` in code
- Verify `WiFi.mode(WIFI_AP_STA)` is set
- Check Serial Monitor for errors

**Problem**: Gateway not connecting to WiFi
- Verify `sta_ssid` and `sta_password`
- Check WiFi signal strength
- Verify router allows connections

#### Node Issues

**Problem**: Node not connecting to Gateway
- Verify AP name and password match
- Check Gateway is powered
- Reduce distance between devices
- Check Serial Monitor for errors

**Problem**: Token request fails
- Verify device_id is authorized
- Check Gateway can reach controller
- Verify MAC address format

#### Controller Issues

**Problem**: Controller not starting
- Check port 5000 availability: `lsof -i :5000`
- Verify all dependencies installed
- Check Python version: `python3 --version`

**Problem**: Devices not appearing
- Verify devices in `authorized_devices`
- Check devices are sending data
- Refresh dashboard page

#### Sensor Issues

**Problem**: Sensor not reading
- Check wiring connections
- Verify GPIO pin numbers
- Check sensor power supply
- Test sensor with simple sketch first

**Problem**: Incorrect sensor values
- Calibrate sensor
- Check sensor datasheet
- Verify pull-up resistors (if needed)

---

## Production Deployment

### Security Hardening

#### 1. Change Default Passwords
```cpp
// Gateway AP password
const char *ap_password = "StrongPassword123!";

// WiFi password (use strong password)
const char *sta_password = "YourStrongWiFiPassword";
```

#### 2. Use HTTPS (Production)
```python
# In controller.py
from flask import Flask
app = Flask(__name__)

# Use SSL context
if __name__ == '__main__':
    context = ('certs/server.crt', 'certs/server.key')
    app.run(host='0.0.0.0', port=5000, ssl_context=context)
```

#### 3. Firewall Rules
```bash
# Only allow necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 5000/tcp  # Controller (restrict to specific IPs)
sudo ufw enable
```

#### 4. Regular Updates
```bash
# Update system regularly
sudo apt update && sudo apt upgrade

# Update Python packages
pip install --upgrade -r requirements.txt
```

### Monitoring

#### 1. Log Management
```bash
# Rotate logs
sudo logrotate -f /etc/logrotate.d/secureiot

# Monitor logs
tail -f logs/controller.log
```

#### 2. System Monitoring
```bash
# Monitor system resources
htop

# Monitor network
iftop

# Monitor disk usage
df -h
```

#### 3. Alerting

Set up alerts for:
- Controller downtime
- High attack rates
- Device disconnections
- Disk space low
- High CPU usage

---

## Maintenance and Monitoring

### Daily Tasks

- Check dashboard for anomalies
- Review security alerts
- Verify all devices online
- Check system logs

### Weekly Tasks

- Review ML detection statistics
- Check honeypot logs
- Verify trust scores
- Update threat intelligence

### Monthly Tasks

- Update system packages
- Review and rotate certificates
- Backup database
- Performance optimization
- Security audit

### Backup Procedures

```bash
# Backup database
cp identity.db backups/identity_$(date +%Y%m%d).db

# Backup certificates
tar -czf backups/certs_$(date +%Y%m%d).tar.gz certs/

# Backup configuration
cp controller.py backups/controller_$(date +%Y%m%d).py
```

---

## Advanced Configurations

### Multiple Gateways

For larger deployments, deploy multiple gateways:

1. Configure each gateway with unique AP name
2. Update controller to handle multiple gateways
3. Load balance across gateways
4. Monitor all gateways from dashboard

### High Availability

1. Deploy multiple controller instances
2. Use load balancer
3. Database replication
4. Failover mechanisms

### Scaling

1. **Horizontal**: Add more controller instances
2. **Vertical**: Upgrade hardware
3. **Database**: Migrate to PostgreSQL
4. **Caching**: Add Redis for tokens

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0

