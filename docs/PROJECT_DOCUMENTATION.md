# SecureIoT-SDN - Complete Project Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Core Features](#core-features)
4. [Component Details](#component-details)
5. [API Reference](#api-reference)
6. [Real-World Implementation](#real-world-implementation)
7. [Deployment Guide](#deployment-guide)
8. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What is SecureIoT-SDN?

**SecureIoT-SDN** is a comprehensive, enterprise-grade IoT security framework that combines Software-Defined Networking (SDN) with Zero Trust security principles. It provides advanced protection for IoT devices through multiple security layers including:

- **ML-based Attack Detection**: Real-time DDoS and anomaly detection using machine learning
- **Zero Trust Architecture**: Continuous verification and least-privilege access control
- **SDN Policy Enforcement**: Dynamic network policies and traffic management
- **PKI-based Identity Management**: Certificate-based device authentication
- **Honeypot Integration**: Active threat detection and intelligence gathering
- **Trust Scoring System**: Dynamic trust evaluation based on device behavior

### Key Use Cases

1. **Smart Home Security**: Protect home IoT devices (cameras, sensors, smart appliances)
2. **Industrial IoT (IIoT)**: Secure manufacturing and industrial automation systems
3. **Healthcare IoT**: Protect medical devices and patient monitoring systems
4. **Smart City Infrastructure**: Secure traffic sensors, environmental monitors, and public services
5. **Research & Education**: Educational platform for IoT security and SDN concepts

### Technology Stack

#### Backend
- **Python 3.8+**: Core application language
- **Flask 3.0+**: Web framework and REST API
- **TensorFlow 2.14+**: Machine learning engine for attack detection
- **Ryu 4.34+**: SDN controller framework (OpenFlow 1.3)
- **SQLite3**: Lightweight device identity database
- **Docker**: Container management for honeypots

#### Frontend
- **HTML5/CSS3**: Modern dashboard interface
- **JavaScript**: Real-time updates and interactivity
- **vis-network.js**: Network topology visualization

#### IoT Hardware
- **ESP32**: WiFi-enabled microcontrollers for devices and gateway
- **Arduino IDE**: Firmware development environment
- **Raspberry Pi 4**: Controller deployment platform

#### Security Libraries
- **cryptography**: PKI and certificate management
- **pyOpenSSL**: X.509 certificate operations

---

## System Architecture

### High-Level Architecture

The system is organized into four main layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Management Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Web Dashboard (Flask)                               │  │
│  │  - Real-time monitoring                               │  │
│  │  - Device management                                  │  │
│  │  - Policy configuration                               │  │
│  │  - Security alerts                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Flask        │  │ Ryu SDN      │  │ ML Security  │       │
│  │ Controller   │  │ Controller   │  │ Engine       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Identity     │  │ Trust        │  │ Heuristic    │       │
│  │ Manager      │  │ Evaluator    │  │ Analyst      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Honeypot     │  │ Policy       │                        │
│  │ Manager      │  │ Adapter      │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Gateway Layer                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ESP32 Gateway (Dual Mode: AP + STA)                 │  │
│  │  - WiFi Access Point for nodes                       │  │
│  │  - Station mode to connect to controller              │  │
│  │  - Data forwarding                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    IoT Device Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ ESP32    │  │ ESP32    │  │ ESP32    │  │ ESP32    │     │
│  │ Node 1   │  │ Node 2   │  │ Node 3   │  │ Node N   │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

#### 1. Device Onboarding Flow

```
ESP32 Node → Gateway → Controller
    ↓
Request Token (with MAC address)
    ↓
Controller validates device authorization
    ↓
Generate X.509 certificate (PKI mode)
    ↓
Issue authentication token
    ↓
Establish behavioral baseline
    ↓
Device ready for data transmission
```

#### 2. Data Transmission Flow

```
ESP32 Node → Gateway → Controller
    ↓
Send data packet with token
    ↓
Controller validates:
  - Token validity
  - Session timeout
  - Rate limiting
  - Device authorization
    ↓
ML Engine analyzes packet
    ↓
SDN Policy Engine enforces policies
    ↓
Trust Scorer updates device trust
    ↓
Response: Accept/Reject
```

#### 3. Threat Detection Flow

```
Suspicious Traffic Detected
    ↓
Heuristic Analyst flags anomaly
    ↓
ML Engine confirms attack
    ↓
Trust Scorer reduces trust score
    ↓
SDN Policy Engine redirects to honeypot
    ↓
Honeypot captures attack details
    ↓
Threat Intelligence extracts IOCs
    ↓
Mitigation Generator creates blocking rules
    ↓
Policy Adapter updates device access
```

### Component Interaction

#### Core Components

1. **Flask Controller** (`controller.py`)
   - Main web server and API endpoint
   - Token management and validation
   - Device authorization
   - Rate limiting enforcement
   - Dashboard serving

2. **ML Security Engine** (`ml_security_engine.py`)
   - DDoS attack detection using TensorFlow models
   - Real-time packet analysis
   - Attack classification
   - Statistics tracking

3. **Ryu SDN Controller** (`ryu_controller/sdn_policy_engine.py`)
   - OpenFlow 1.3 protocol support
   - Dynamic policy enforcement
   - Traffic redirection
   - Flow table management

4. **Identity Manager** (`identity_manager/`)
   - Certificate Authority (CA) management
   - Device certificate generation
   - Identity database (SQLite)
   - Behavioral profiling
   - Policy generation

5. **Trust Evaluator** (`trust_evaluator/`)
   - Dynamic trust score calculation (0-100)
   - Device attestation
   - Policy adaptation based on trust

6. **Heuristic Analyst** (`heuristic_analyst/`)
   - Flow statistics analysis
   - Anomaly detection
   - Baseline comparison

7. **Honeypot Manager** (`honeypot_manager/`)
   - Cowrie honeypot deployment (Docker)
   - Log parsing and threat extraction
   - Mitigation rule generation

8. **Zero Trust Integration** (`zero_trust_integration.py`)
   - Orchestrates all components
   - Background monitoring threads
   - Component coordination

---

## Core Features

### 1. Token-Based Authentication

**Purpose**: Secure device authentication using dynamically generated tokens

**How It Works**:
- Devices request tokens during initial connection
- Tokens are UUID-based and time-limited (5-minute sessions)
- Each data packet must include a valid token
- Tokens are automatically invalidated after timeout

**Usage**:
```python
# Device requests token
POST /get_token
{
    "device_id": "ESP32_2",
    "mac_address": "AA:BB:CC:DD:EE:FF"
}

# Response
{
    "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Configuration**:
- Session timeout: 300 seconds (configurable in `controller.py`)
- Token format: UUID v4

### 2. ML-Based DDoS Detection

**Purpose**: Real-time detection of DDoS and network attacks using machine learning

**How It Works**:
- Pre-trained TensorFlow models analyze network traffic
- Features extracted from packets: size, protocol, ports, rates, flags
- Models classify traffic as Normal, DDoS, Botnet, or Flood attacks
- Confidence scores and attack statistics tracked

**Usage**:
```python
# Initialize ML engine
POST /ml/initialize

# Check ML status
GET /ml/status

# Get recent detections
GET /ml/detections

# Analyze specific packet
POST /ml/analyze_packet
{
    "device_id": "ESP32_2",
    "size": 1500,
    "protocol": 6,
    "src_port": 12345,
    "dst_port": 80,
    "rate": 1000.0,
    "bps": 1000000.0,
    "pps": 100.0
}
```

**Model Files**:
- `models/ddos_model_retrained.keras`: Main DDoS detection model
- `models/ddos_model.keras`: Alternative model
- Models trained on CIC-DDoS2019 dataset

### 3. SDN Policy Enforcement

**Purpose**: Dynamic network policy enforcement through OpenFlow

**Policies Available**:
- **Packet Inspection**: Deep packet inspection and filtering
- **Traffic Shaping**: Bandwidth limiting and QoS
- **Dynamic Routing**: Intelligent packet routing

**Usage**:
```python
# Toggle policy
POST /toggle_policy/packet_inspection
POST /toggle_policy/traffic_shaping
POST /toggle_policy/dynamic_routing

# Get current policies
GET /get_policies

# Get policy logs
GET /get_policy_logs
```

**SDN Controller**:
- Ryu-based OpenFlow 1.3 controller
- Supports allow, deny, redirect, and quarantine actions
- Real-time flow table updates

### 4. Zero Trust Architecture

**Purpose**: Continuous verification and least-privilege access

**Components**:
- **PKI-based Identity**: X.509 certificates for device identity
- **Continuous Attestation**: Periodic device verification
- **Trust Scoring**: Dynamic trust evaluation (0-100 scale)
- **Policy Adaptation**: Access control based on trust scores

**Trust Score Factors**:
- Behavioral anomalies: -10 to -30 points
- Attestation failures: -20 points
- Security alerts: -5 to -15 points (based on severity)
- Time-based decay: Gradual reduction over time

**Usage**:
```python
# Onboard device with certificate
from identity_manager.device_onboarding import DeviceOnboarding
onboarding = DeviceOnboarding()
result = onboarding.onboard_device(
    device_id="ESP32_2",
    mac_address="AA:BB:CC:DD:EE:FF",
    device_type="sensor"
)

# Get trust score
from trust_evaluator.trust_scorer import TrustScorer
scorer = TrustScorer()
score = scorer.get_trust_score("ESP32_2")
```

### 5. Honeypot Integration

**Purpose**: Active threat detection and intelligence gathering

**How It Works**:
- Suspicious traffic redirected to honeypot (Cowrie)
- Honeypot logs attacker activities
- Threat intelligence extracts IPs, commands, and attack patterns
- Automatic mitigation rules generated

**Usage**:
```python
# Deploy honeypot
from honeypot_manager.honeypot_deployer import HoneypotDeployer
deployer = HoneypotDeployer(honeypot_type="cowrie")
deployer.deploy()

# Check status
status = deployer.get_status()

# Get threat intelligence
from honeypot_manager.threat_intelligence import ThreatIntelligence
ti = ThreatIntelligence()
threats = ti.get_blocked_ips()
```

**Honeypot Ports**:
- SSH: 2222
- HTTP: 8080

### 6. Rate Limiting

**Purpose**: Prevent DoS attacks through packet rate control

**Configuration**:
- Default limit: 60 packets per minute per device
- Sliding window: 60-second window
- Automatic blocking when limit exceeded

**Usage**:
```python
# Rate limit status in dashboard
GET /get_data
# Response includes rate_limit_status for each device
```

### 7. Real-Time Dashboard

**Purpose**: Web-based monitoring and control interface

**Features**:
- **Overview Tab**: Network status, topology visualization
- **Devices Tab**: Connected devices, authorization controls
- **Security Tab**: SDN policies, security alerts
- **ML Engine Tab**: Attack detections, ML statistics
- **Analytics Tab**: Network performance metrics

**Access**:
```
http://localhost:5000
```

### 8. Network Topology Visualization

**Purpose**: Visual representation of device connections

**Features**:
- Interactive network graph (vis-network.js)
- Real-time connection status
- MAC address display
- Gateway-centric topology
- Device packet counts

**Usage**:
```python
GET /get_topology_with_mac
# Returns JSON with nodes and edges
```

---

## Component Details

### Flask Controller (`controller.py`)

**Responsibilities**:
- Web server and REST API
- Token generation and validation
- Device authorization management
- Rate limiting enforcement
- SDN policy coordination
- Dashboard serving

**Key Functions**:
- `get_token()`: Generate authentication tokens
- `auth()`: Validate device tokens
- `data()`: Process device data packets
- `update_auth()`: Authorize/revoke devices
- `toggle_policy()`: Enable/disable SDN policies

### ML Security Engine (`ml_security_engine.py`)

**Responsibilities**:
- Load and manage TensorFlow models
- Real-time packet analysis
- Attack detection and classification
- Statistics tracking
- Health monitoring

**Key Functions**:
- `load_model()`: Load TensorFlow model
- `predict_attack()`: Analyze packet for attacks
- `get_attack_statistics()`: Get detection statistics
- `check_health()`: Monitor engine health

### Identity Manager (`identity_manager/`)

**Components**:
- `certificate_manager.py`: CA and certificate operations
- `identity_database.py`: SQLite device database
- `device_onboarding.py`: Onboarding workflow
- `behavioral_profiler.py`: Traffic pattern analysis
- `policy_generator.py`: Least-privilege policy generation

**Database Schema**:
```sql
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    mac_address TEXT UNIQUE,
    certificate_path TEXT,
    key_path TEXT,
    device_type TEXT,
    device_info TEXT,
    onboarded_at TIMESTAMP,
    last_seen TIMESTAMP
);
```

### Trust Evaluator (`trust_evaluator/`)

**Components**:
- `trust_scorer.py`: Dynamic trust calculation
- `device_attestation.py`: Certificate-based attestation
- `policy_adapter.py`: Trust-based policy adaptation

**Trust Score Calculation**:
```
Initial Score: 70
- Behavioral Anomaly: -10 to -30
- Attestation Failure: -20
- Security Alert: -5 to -15 (severity-based)
- Time Decay: -1 per day of inactivity
Final Score: Clamped to 0-100
```

### Heuristic Analyst (`heuristic_analyst/`)

**Components**:
- `flow_analyzer.py`: Ryu flow statistics polling
- `anomaly_detector.py`: Heuristic-based detection
- `baseline_manager.py`: Behavioral baseline management

**Detection Rules**:
- DoS Detection: High packet rate (>1000 pps)
- Scanning Detection: Multiple destination ports
- Volume Attack: Excessive data transfer (>10MB/min)

### Honeypot Manager (`honeypot_manager/`)

**Components**:
- `docker_manager.py`: Docker container operations
- `honeypot_deployer.py`: Honeypot deployment
- `log_parser.py`: Cowrie log parsing
- `threat_intelligence.py`: Threat extraction
- `mitigation_generator.py`: Automatic rule generation

**Honeypot Types**:
- **Cowrie**: SSH and Telnet honeypot (default)
- Extensible for other honeypots (Dionaea, etc.)

### Ryu SDN Controller (`ryu_controller/`)

**Components**:
- `sdn_policy_engine.py`: Main Ryu application
- `openflow_rules.py`: OpenFlow rule generation
- `traffic_redirector.py`: Honeypot redirection

**OpenFlow Actions**:
- **ALLOW**: Normal forwarding
- **DENY**: Drop packet
- **REDIRECT**: Send to honeypot
- **QUARANTINE**: Isolate device

---

## API Reference

### Authentication Endpoints

#### POST /get_token
Request authentication token for device.

**Request**:
```json
{
    "device_id": "ESP32_2",
    "mac_address": "AA:BB:CC:DD:EE:FF"
}
```

**Response** (200 OK):
```json
{
    "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (403 Forbidden):
```json
{
    "error": "Device not authorized"
}
```

#### POST /auth
Validate device token.

**Request**:
```json
{
    "device_id": "ESP32_2",
    "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:
```json
{
    "device_id": "ESP32_2",
    "authorized": true
}
```

### Data Endpoints

#### POST /data
Submit device data packet.

**Request**:
```json
{
    "device_id": "ESP32_2",
    "token": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "1234567890",
    "data": "25.5",
    "size": 1500,
    "protocol": 6,
    "src_port": 12345,
    "dst_port": 80,
    "rate": 100.0,
    "bps": 100000.0,
    "pps": 10.0
}
```

**Response** (Accepted):
```json
{
    "status": "accepted"
}
```

**Response** (Rejected):
```json
{
    "status": "rejected",
    "reason": "Rate limit exceeded"
}
```

### Dashboard Endpoints

#### GET /
Main dashboard page (HTML).

#### GET /get_data
Get device data and status.

**Response**:
```json
{
    "ESP32_2": {
        "packets": 150,
        "rate_limit_status": "45/60",
        "blocked_reason": null
    },
    "ESP32_3": {
        "packets": 200,
        "rate_limit_status": "60/60",
        "blocked_reason": null
    }
}
```

#### GET /get_topology_with_mac
Get network topology with MAC addresses.

**Response**:
```json
{
    "nodes": [
        {
            "id": "ESP32_Gateway",
            "label": "Gateway",
            "mac": "A0:B1:C2:D3:E4:F5",
            "online": true,
            "last_seen": 1234567890.0,
            "packets": 0
        },
        {
            "id": "ESP32_2",
            "label": "ESP32_2",
            "mac": "AA:BB:CC:DD:EE:22",
            "online": true,
            "last_seen": 1234567890.0,
            "packets": 150
        }
    ],
    "edges": [
        {
            "from": "ESP32_2",
            "to": "ESP32_Gateway"
        }
    ]
}
```

#### GET /get_health_metrics
Get device health metrics.

**Response**:
```json
{
    "ESP32_2": {
        "cpu_usage": 45,
        "memory_usage": 60,
        "uptime": 3600
    }
}
```

### SDN Policy Endpoints

#### POST /toggle_policy/<policy>
Toggle SDN policy on/off.

**Policies**: `packet_inspection`, `traffic_shaping`, `dynamic_routing`

**Response**:
```json
{
    "enabled": true
}
```

#### GET /get_policies
Get current policy states.

**Response**:
```json
{
    "packet_inspection": false,
    "traffic_shaping": true,
    "dynamic_routing": false
}
```

#### GET /get_policy_logs
Get recent policy enforcement logs.

**Response**:
```json
[
    "[14:30:15] Packet Inspection policy enabled",
    "[14:30:20] Blocked packet from ESP32_2 due to packet inspection policy"
]
```

#### GET /get_sdn_metrics
Get SDN control plane metrics.

**Response**:
```json
{
    "control_plane_latency": 25,
    "data_plane_throughput": 500,
    "policy_enforcement_rate": 95
}
```

### ML Engine Endpoints

#### POST /ml/initialize
Initialize ML security engine.

**Response**:
```json
{
    "status": "success",
    "message": "ML engine initialized and monitoring started"
}
```

#### GET /ml/status
Get ML engine status.

**Response**:
```json
{
    "status": "active",
    "monitoring": true,
    "statistics": {
        "total_packets": 10000,
        "attack_packets": 150,
        "normal_packets": 9850,
        "attack_rate": 1.5,
        "detection_rate": 98.5,
        "model_status": "loaded"
    }
}
```

#### GET /ml/detections
Get recent attack detections.

**Response**:
```json
{
    "status": "success",
    "detections": [
        {
            "timestamp": "2024-01-15T14:30:00",
            "is_attack": true,
            "attack_type": "DDoS Attack",
            "confidence": 0.95,
            "device_id": "ESP32_2",
            "details": "High packet rate detected"
        }
    ],
    "stats": {
        "total_packets": 10000,
        "attack_packets": 150
    }
}
```

#### POST /ml/analyze_packet
Analyze specific packet for attacks.

**Request**:
```json
{
    "device_id": "ESP32_2",
    "size": 1500,
    "protocol": 6,
    "src_port": 12345,
    "dst_port": 80,
    "rate": 1000.0,
    "duration": 10.0,
    "bps": 1000000.0,
    "pps": 100.0
}
```

**Response**:
```json
{
    "is_attack": true,
    "attack_type": "DDoS Attack",
    "confidence": 0.92
}
```

#### GET /ml/statistics
Get comprehensive ML statistics.

**Response**:
```json
{
    "total_packets": 10000,
    "attack_packets": 150,
    "normal_packets": 9850,
    "attack_rate": 1.5,
    "detection_rate": 98.5,
    "false_positive_rate": 0.5,
    "model_confidence": 0.95,
    "processing_rate": 1000.0
}
```

#### GET /ml/health
Get ML engine health status.

**Response**:
```json
{
    "status": "healthy",
    "uptime": 3600,
    "last_health_check": "2024-01-15T14:30:00",
    "model_status": "loaded",
    "total_packets_processed": 10000,
    "detection_accuracy": 98.5
}
```

### Device Management Endpoints

#### POST /update
Authorize or revoke device access.

**Request** (form data):
```
device_id=ESP32_2
action=authorize  # or 'revoke'
```

#### GET /get_security_alerts
Get recent security alerts.

**Response**:
```json
[
    {
        "timestamp": "2024-01-15T14:30:00",
        "message": "Blocked packet from ESP32_2 due to packet inspection policy",
        "severity": "high",
        "device": null
    }
]
```

---

## Real-World Implementation

### Hardware Requirements

#### ESP32 Devices
- **ESP32 Development Board** (ESP32-WROOM-32 or similar)
- **USB Cable** for programming
- **Power Supply**: 5V via USB or external power
- **Antenna**: Built-in PCB antenna (or external for better range)

#### Gateway Requirements
- **ESP32 Gateway**: Same as above, but with stable power
- **Network Connection**: WiFi connection to controller network

#### Controller Server
- **Raspberry Pi 4** (4GB RAM minimum, 8GB recommended)
- **OR** Linux server/VM with Python 3.8+
- **Network**: Ethernet or WiFi connection

### Software Setup

#### 1. ESP32 Development Environment

**Install Arduino IDE**:
1. Download from https://www.arduino.cc/en/software
2. Install ESP32 board support:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools → Board → Boards Manager → Search "ESP32" → Install

**Install Required Libraries**:
- ArduinoJson (via Library Manager)
- WiFi and HTTPClient (built-in)

#### 2. Gateway Configuration

Edit `esp32/gateway.ino`:

```cpp
const char *ap_ssid = "ESP32-AP";           // Access Point name
const char *ap_password = "12345678";        // AP password (min 8 chars)
const char *sta_ssid = "YourWiFi";          // Your WiFi network
const char *sta_password = "YourPassword";    // WiFi password
const char *controller_ip = "192.168.1.100"; // Controller IP address
```

**Upload Steps**:
1. Connect ESP32 via USB
2. Select board: Tools → Board → ESP32 Dev Module
3. Select port: Tools → Port → (your ESP32 port)
4. Upload: Sketch → Upload

#### 3. Node Configuration

Edit `esp32/node.ino` for each device:

```cpp
const char *ssid = "ESP32-AP";              // Gateway AP name
const char *password = "12345678";           // Gateway AP password
const char *controller_ip = "192.168.4.1";  // Gateway IP (AP mode)
String device_id = "ESP32_2";                // Unique ID per device
```

**Important**: Change `device_id` for each node (ESP32_2, ESP32_3, ESP32_4, etc.)

**Upload to Each Node**:
1. Connect each ESP32 via USB
2. Update `device_id` in code
3. Upload firmware
4. Disconnect and power via external supply

#### 4. Controller Setup

**Install Dependencies**:
```bash
cd /path/to/IOT-project
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Configure Controller**:
- Update `authorized_devices` in `controller.py`:
```python
authorized_devices = {
    "ESP32_2": True,
    "ESP32_3": True,
    "ESP32_4": True
}
```

**Start Controller**:
```bash
python controller.py
```

### Network Configuration

#### Network Topology

```
[Controller Server] (192.168.1.100)
        |
        | WiFi/Ethernet
        |
[ESP32 Gateway] (192.168.1.XXX)
   AP Mode: 192.168.4.1
        |
        | WiFi AP: "ESP32-AP"
        |
   ┌────┴────┬─────────┬─────────┐
   |         |         |         |
[Node 1]  [Node 2]  [Node 3]  [Node N]
```

#### IP Address Configuration

**Controller**:
- Static IP recommended: `192.168.1.100`
- Or use DHCP and find IP: `ip addr show` (Linux) or `ipconfig` (Windows)

**Gateway**:
- AP Mode IP: `192.168.4.1` (fixed)
- STA Mode: DHCP from your router

**Nodes**:
- Connect to Gateway AP
- Gateway IP: `192.168.4.1`

### Physical Sensor Integration

#### Example: Temperature Sensor (DS18B20)

Modify `esp32/node.ino`:

```cpp
#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 4  // GPIO pin
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
    // ... existing WiFi setup ...
    sensors.begin();
}

void loop() {
    sensors.requestTemperatures();
    float temp = sensors.getTempCByIndex(0);
    
    // Send temperature data
    String payload = "{\"device_id\":\"" + device_id + 
                     "\",\"token\":\"" + token + 
                     "\",\"timestamp\":\"" + String(millis()/1000) + 
                     "\",\"data\":\"" + String(temp) + "\"}";
    // ... send to controller ...
}
```

#### Example: Motion Sensor (PIR)

```cpp
#define PIR_PIN 2  // GPIO pin

void setup() {
    pinMode(PIR_PIN, INPUT);
    // ... existing setup ...
}

void loop() {
    int motion = digitalRead(PIR_PIN);
    String data = motion ? "MOTION_DETECTED" : "NO_MOTION";
    // ... send data ...
}
```

### Testing Procedure

#### 1. Gateway Test
1. Power on Gateway ESP32
2. Check Serial Monitor (115200 baud):
   - Should see "Gateway AP Started"
   - Should see "Connected to WiFi"
3. Verify AP: Look for "ESP32-AP" in WiFi networks

#### 2. Node Test
1. Power on Node ESP32
2. Check Serial Monitor:
   - Should see "Connected to Gateway"
   - Should see "Received token: ..."
3. Verify connection: Check controller logs

#### 3. Controller Test
1. Start controller: `python controller.py`
2. Check output:
   - Should see "Starting Flask Controller on http://0.0.0.0:5000"
   - Should see "ML Security Engine initialized" (if TensorFlow available)
3. Access dashboard: `http://localhost:5000`
4. Verify devices appear in dashboard

#### 4. End-to-End Test
1. Nodes should send data every 5 seconds
2. Dashboard should show:
   - Device status: Online
   - Packet counts increasing
   - Topology graph showing connections
3. Test authorization:
   - Revoke device in dashboard
   - Device should stop sending data
   - Re-authorize: Device should resume

### Troubleshooting Real Devices

#### Gateway Issues

**Problem**: Gateway not creating AP
- **Solution**: Check `ap_ssid` and `ap_password` in code
- **Solution**: Ensure WiFi.mode(WIFI_AP_STA) is set

**Problem**: Gateway not connecting to WiFi
- **Solution**: Verify `sta_ssid` and `sta_password`
- **Solution**: Check router WiFi range

**Problem**: Gateway not forwarding data
- **Solution**: Verify `controller_ip` is correct
- **Solution**: Check controller is running and accessible

#### Node Issues

**Problem**: Node not connecting to Gateway AP
- **Solution**: Verify AP name and password match Gateway
- **Solution**: Check Gateway is powered and AP is active
- **Solution**: Reduce distance between node and gateway

**Problem**: Node not receiving token
- **Solution**: Verify device_id is authorized in controller
- **Solution**: Check Gateway can reach controller
- **Solution**: Verify MAC address is unique

**Problem**: Data not reaching controller
- **Solution**: Check token is valid (not expired)
- **Solution**: Verify rate limit not exceeded
- **Solution**: Check controller logs for errors

#### Controller Issues

**Problem**: Controller not starting
- **Solution**: Check port 5000 is not in use: `lsof -i :5000`
- **Solution**: Verify all dependencies installed
- **Solution**: Check Python version: `python3 --version` (must be 3.8+)

**Problem**: ML engine not loading
- **Solution**: Install TensorFlow: `pip install tensorflow`
- **Solution**: Verify model files exist in `models/` directory
- **Solution**: System will run without ML (heuristic detection only)

**Problem**: Devices not appearing in dashboard
- **Solution**: Verify devices are authorized in `authorized_devices`
- **Solution**: Check devices are sending data
- **Solution**: Refresh dashboard page

---

## Deployment Guide

### Development Deployment

#### Quick Start
```bash
# Clone repository
git clone <repository-url> IOT-project
cd IOT-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start controller
python controller.py
```

#### Using Launcher Script
```bash
# Automatic setup and start
python3 run_iot_framework.py
```

### Production Deployment (Raspberry Pi)

See `raspberry_pi/deployment_guide.md` for detailed instructions.

**Quick Steps**:
1. Install Raspberry Pi OS (64-bit)
2. Install dependencies: `sudo apt install python3-pip docker.io`
3. Clone repository and install Python packages
4. Create systemd service for auto-start
5. Configure network and firewall

### Docker Deployment (Optional)

**Create Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "controller.py"]
```

**Build and Run**:
```bash
docker build -t secureiot-sdn .
docker run -p 5000:5000 secureiot-sdn
```

### Cloud Deployment

#### AWS EC2
1. Launch Ubuntu 20.04 instance
2. Install dependencies
3. Configure security groups (port 5000)
4. Start controller as systemd service

#### Azure IoT Hub Integration
- Use Azure IoT Hub for device management
- Integrate controller with Azure services
- Use Azure ML for enhanced attack detection

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
**Error**: `Address already in use`
**Solution**:
```bash
# Find process using port 5000
lsof -i :5000
# Kill process
kill -9 <PID>
```

#### 2. TensorFlow Import Error
**Error**: `ImportError: cannot import name 'tensorflow'`
**Solution**:
```bash
pip install tensorflow
# Or for CPU-only:
pip install tensorflow-cpu
```

#### 3. Ryu Controller Not Starting
**Error**: `ImportError: cannot import name 'ALREADY_HANDLED' from 'eventlet.wsgi'`
**Solution**:
```bash
# Update eventlet version
pip install --upgrade eventlet==0.33.0
# Or use compatible Ryu version
pip install ryu==4.34
```

#### 4. ESP32 Not Connecting
**Error**: Device not appearing in dashboard
**Solution**:
- Verify WiFi credentials in firmware
- Check device is authorized in `authorized_devices`
- Verify Gateway is running and accessible
- Check Serial Monitor for error messages

#### 5. ML Model Not Loading
**Error**: `Model file not found`
**Solution**:
- Verify model files exist in `models/` directory
- Check file permissions
- System will run with heuristic detection if ML unavailable

### Debug Mode

**Enable Debug Logging**:
```python
# In controller.py, change:
app.run(host='0.0.0.0', port=5000, debug=True)
```

**Check Logs**:
```bash
# Controller logs
tail -f logs/controller.log

# Ryu logs
tail -f logs/ryu.log

# Zero Trust logs
tail -f logs/zero_trust.log
```

### Performance Optimization

#### For Raspberry Pi
1. **Overclock**: Edit `/boot/config.txt`
2. **Increase Swap**: Set to 2GB
3. **Disable Unnecessary Services**: Bluetooth, avahi-daemon
4. **Use SSD**: Instead of SD card for better I/O

#### For High-Volume Deployments
1. **Use Redis**: For token caching
2. **Database Optimization**: Use PostgreSQL instead of SQLite
3. **Load Balancing**: Deploy multiple controller instances
4. **CDN**: For dashboard static assets

---

## Additional Resources

### Documentation Files
- `README.md`: Quick start guide
- `START_GUIDE.md`: System startup instructions
- `IMPLEMENTATION_SUMMARY.md`: Implementation details
- `raspberry_pi/deployment_guide.md`: Raspberry Pi deployment
- `ARCHITECTURE.md`: Detailed architecture (see separate file)
- `FEATURES_GUIDE.md`: Feature usage guide (see separate file)
- `REAL_WORLD_DEPLOYMENT.md`: Real device implementation (see separate file)

### Research Papers
- `docs/NIST.SP.800-207.pdf`: Zero Trust Architecture
- `docs/futureinternet-06-00302.pdf`: SDN for IoT
- `docs/TAF_25-26J-029.pdf`: Framework specification

### External Resources
- [ESP32 Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [Ryu SDN Controller](https://ryu-sdn.org/)
- [TensorFlow Documentation](https://www.tensorflow.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## Support and Contributing

### Getting Help
- Check logs in `logs/` directory
- Review troubleshooting section
- Check GitHub issues
- Review documentation files

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

### License
MIT License - See `LICENSE` file

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0

