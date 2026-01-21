# SecureIoT-SDN - Architecture Documentation

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Layered Architecture](#layered-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Security Architecture](#security-architecture)
6. [Network Architecture](#network-architecture)
7. [Deployment Architecture](#deployment-architecture)

---

## System Architecture Overview

### Architecture Principles

The SecureIoT-SDN framework is built on the following architectural principles:

1. **Zero Trust Security**: Never trust, always verify
2. **Software-Defined Networking**: Centralized network control
3. **Microservices Design**: Modular, independent components
4. **Event-Driven Architecture**: Asynchronous processing
5. **Defense in Depth**: Multiple security layers

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Management Layer                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Web Dashboard (Flask)                      │  │
│  │  • Real-time monitoring                                  │  │
│  │  • Device management                                      │  │
│  │  • Policy configuration                                  │  │
│  │  • Security alerts                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      Control Plane Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Flask      │  │   Ryu SDN    │  │   ML Security │         │
│  │  Controller  │  │  Controller  │  │    Engine    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         ↕                ↕                    ↕                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Identity   │  │    Trust     │  │   Heuristic  │         │
│  │   Manager    │  │  Evaluator   │  │   Analyst    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         ↕                ↕                    ↕                 │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │   Honeypot   │  │    Policy    │                            │
│  │   Manager    │  │   Adapter    │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Zero Trust Integration Framework                 │  │
│  │         (Orchestrates all components)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ OpenFlow/HTTP
┌─────────────────────────────────────────────────────────────────┐
│                        Data Plane Layer                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SDN Switch (OpenFlow)                       │  │
│  │  • Flow table management                                 │  │
│  │  • Packet forwarding                                     │  │
│  │  • Policy enforcement                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ WiFi/Ethernet
┌─────────────────────────────────────────────────────────────────┐
│                        Gateway Layer                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         ESP32 Gateway (Dual Mode: AP + STA)              │  │
│  │  • WiFi Access Point for nodes                           │  │
│  │  • Station mode to controller                            │  │
│  │  • Data forwarding                                       │  │
│  │  • Protocol translation                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ WiFi
┌─────────────────────────────────────────────────────────────────┐
│                       IoT Device Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ ESP32    │  │ ESP32    │  │ ESP32    │  │ ESP32    │      │
│  │ Node 1   │  │ Node 2   │  │ Node 3   │  │ Node N   │      │
│  │          │  │          │  │          │  │          │      │
│  │ Sensors: │  │ Sensors: │  │ Sensors: │  │ Sensors: │      │
│  │ • Temp   │  │ • Motion │  │ • Light │  │ • Custom │      │
│  │ • Humid  │  │ • PIR    │  │ • DHT22 │  │          │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layered Architecture

### Layer 1: IoT Device Layer

**Purpose**: Physical IoT devices that collect and transmit data

**Components**:
- ESP32 microcontrollers
- Various sensors (temperature, motion, light, etc.)
- Firmware: `esp32/node.ino`

**Responsibilities**:
- Sensor data collection
- WiFi connectivity
- Token-based authentication
- Periodic data transmission (every 5 seconds)
- MAC address identification

**Protocols**:
- WiFi 802.11 (b/g/n)
- HTTP/JSON for data transmission
- TCP/IP stack

**Characteristics**:
- Low power consumption
- Limited processing capability
- Battery or USB powered
- Range: ~100 meters (indoor)

### Layer 2: Gateway Layer

**Purpose**: Bridge between IoT devices and controller

**Components**:
- ESP32 Gateway device
- Firmware: `esp32/gateway.ino`

**Responsibilities**:
- WiFi Access Point (AP) for nodes
- Station (STA) mode to connect to controller network
- Data forwarding between nodes and controller
- Protocol translation
- Network isolation

**Network Configuration**:
- AP Mode:
  - SSID: "ESP32-AP"
  - IP: 192.168.4.1 (fixed)
  - Subnet: 192.168.4.0/24
- STA Mode:
  - Connects to existing WiFi
  - Gets IP via DHCP
  - Forwards to controller

**Dual Mode Operation**:
```cpp
WiFi.mode(WIFI_AP_STA);  // Both modes simultaneously
WiFi.softAP(ap_ssid, ap_password);  // Start AP
WiFi.begin(sta_ssid, sta_password);  // Connect to WiFi
```

### Layer 3: Data Plane Layer (SDN Switch)

**Purpose**: Software-defined network switching and forwarding

**Components**:
- OpenFlow-compatible switch
- Flow tables
- Packet forwarding engine

**Responsibilities**:
- Packet forwarding based on flow rules
- Policy enforcement (allow/deny/redirect/quarantine)
- Traffic redirection to honeypot
- Flow statistics collection

**OpenFlow Protocol**:
- Version: 1.3
- Controller connection: TCP port 6653
- Flow table operations:
  - Install rules
  - Delete rules
  - Modify rules
  - Query statistics

**Flow Rule Structure**:
```
Match Fields:
  - Source MAC
  - Destination MAC
  - Source IP
  - Destination IP
  - Source Port
  - Destination Port
  - Protocol

Actions:
  - OUTPUT: Forward to port
  - DROP: Discard packet
  - REDIRECT: Send to honeypot
  - QUARANTINE: Isolate device
```

### Layer 4: Control Plane Layer

**Purpose**: Centralized network control and security management

#### 4.1 Flask Controller

**File**: `controller.py`

**Responsibilities**:
- Web server (Flask)
- REST API endpoints
- Token generation and validation
- Device authorization management
- Rate limiting enforcement
- Session timeout management
- Dashboard serving

**Key Modules**:
- Token management
- Device authorization
- Rate limiting
- SDN policy coordination
- ML engine integration

#### 4.2 Ryu SDN Controller

**File**: `ryu_controller/sdn_policy_engine.py`

**Responsibilities**:
- OpenFlow protocol handling
- Switch connection management
- Flow rule generation and installation
- Policy enforcement
- Traffic redirection
- **Policy translation from Identity module to OpenFlow rules**
- **Threat alert handling from Analyst module**
- **Dynamic rule installation based on threat intelligence**

**Key Components**:
- `SDNPolicyEngine`: Main Ryu application
- `OpenFlowRuleGenerator`: Rule generation
- `TrafficRedirector`: Honeypot redirection
- `TrafficOrchestrator`: Central intelligent orchestration engine

**Policy Types**:
- **ALLOW**: Normal forwarding
- **DENY**: Block traffic
- **REDIRECT**: Send to honeypot
- **QUARANTINE**: Isolate device

**Policy Translation**:
The SDN Policy Engine receives high-level policy definitions from the Identity module and translates them into granular OpenFlow rules:

```python
# High-level policy from Identity module
policy = {
    'device_id': 'ESP32_2',
    'action': 'allow',
    'rules': [
        {'type': 'allow', 'match': {'ipv4_dst': '192.168.1.100'}, 'priority': 100},
        {'type': 'allow', 'match': {'tcp_dst': 80}, 'priority': 100},
        {'type': 'deny', 'match': {}, 'priority': 0}  # Default deny
    ]
}

# Translated to OpenFlow rules:
# - Rule 1: Allow traffic from device MAC to 192.168.1.100
# - Rule 2: Allow TCP traffic from device MAC to port 80
# - Rule 3: Deny all other traffic from device MAC
```

**Threat Alert Handling**:
When the Analyst module detects anomalies, the SDN Policy Engine:
1. Receives alert via `handle_analyst_alert(device_id, alert_type, severity)`
2. Dynamically installs OpenFlow rules to redirect suspicious traffic to honeypot
3. Applies mitigation actions based on confirmed threat intelligence
4. Updates trust scores through the Trust module

**Methods**:
- `apply_policy_from_identity(device_id, policy)`: Translates high-level policies from Identity module to granular OpenFlow rules
- `handle_analyst_alert(device_id, alert_type, severity)`: Handles threat alerts and applies dynamic rules
- `set_analyst_module(analyst_module)`: Connects to Analyst module for threat detection
- `set_identity_module(identity_module)`: Connects to Identity module for policy definitions
- `set_trust_module(trust_module)`: Connects to Trust module for trust-based decisions

#### 4.3 ML Security Engine

**File**: `ml_security_engine.py`

**Responsibilities**:
- Load TensorFlow models
- Real-time packet analysis
- Attack detection and classification
- Statistics tracking
- Health monitoring

**Models**:
- DDoS detection model
- Attack classification
- Confidence scoring

**Features Analyzed**:
- Packet size
- Protocol type
- Port numbers
- Packet rates (bps, pps)
- TCP flags
- Window size
- TTL values

#### 4.4 Identity Manager

**Directory**: `identity_manager/`

**Components**:
- `certificate_manager.py`: PKI operations
- `identity_database.py`: Device database
- `device_onboarding.py`: Onboarding workflow
- `behavioral_profiler.py`: Traffic profiling
- `policy_generator.py`: Policy generation

**Responsibilities**:
- Certificate Authority (CA) management
- Device certificate generation (X.509)
- Identity database (SQLite)
- Behavioral baseline establishment
- Least-privilege policy generation

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

CREATE TABLE behavioral_baselines (
    device_id TEXT PRIMARY KEY,
    avg_packet_size REAL,
    avg_packet_rate REAL,
    common_ports TEXT,
    traffic_pattern TEXT,
    established_at TIMESTAMP
);
```

#### 4.5 Trust Evaluator

**Directory**: `trust_evaluator/`

**Components**:
- `trust_scorer.py`: Trust calculation
- `device_attestation.py`: Certificate attestation
- `policy_adapter.py`: Policy adaptation

**Responsibilities**:
- Dynamic trust score calculation (0-100)
- Device attestation verification
- Trust-based policy adaptation
- Score history tracking

**Trust Score Factors**:
```
Initial Score: 70

Adjustments:
- Behavioral Anomaly: -10 to -30
- Attestation Failure: -20
- Security Alert (Low): -5
- Security Alert (Medium): -10
- Security Alert (High): -15
- Time Decay: -1 per day of inactivity

Final Score: Clamped to 0-100
```

**Trust Levels**:
- **High (80-100)**: Full access, normal policies
- **Medium (50-79)**: Restricted access, enhanced monitoring
- **Low (20-49)**: Limited access, strict policies
- **Critical (0-19)**: Quarantined, no access

#### 4.6 Heuristic Analyst

**Directory**: `heuristic_analyst/`

**Components**:
- `flow_analyzer.py`: Flow statistics analysis
- `anomaly_detector.py`: Heuristic detection
- `baseline_manager.py`: Baseline management

**Responsibilities**:
- Poll Ryu flow statistics periodically (every 10 seconds)
- Compare real-time traffic metrics against baseline profiles
- Detect anomalies using heuristics (DoS, scanning, volume attacks)
- Generate security alerts and send to Policy Engine
- Map MAC addresses to device IDs via Identity module

**Components**:
- `FlowAnalyzer`: Polls flow statistics from individual switches
- `FlowAnalyzerManager`: Manages multiple FlowAnalyzers for multiple switches
- `AnomalyDetector`: Compares current stats against baselines
- `BaselineManager`: Manages behavioral baselines for devices

**Detection Rules**:
```python
# DoS Detection
if packet_rate > 1000 pps:
    alert = "DoS Attack Detected"
    severity = "high"

# Scanning Detection
if unique_dest_ports > 50 in 1 minute:
    alert = "Port Scanning Detected"
    severity = "medium"

# Volume Attack
if data_transfer > 10 MB in 1 minute:
    alert = "Volume Attack Detected"
    severity = "high"
```

#### 4.7 Honeypot Manager

**Directory**: `honeypot_manager/`

**Components**:
- `docker_manager.py`: Container management
- `honeypot_deployer.py`: Honeypot deployment
- `log_parser.py`: Log parsing
- `threat_intelligence.py`: Threat extraction
- `mitigation_generator.py`: Rule generation

**Responsibilities**:
- Deploy Cowrie honeypot (Docker)
- Parse honeypot logs
- Extract threat intelligence (IPs, commands)
- Generate mitigation rules
- Integrate with SDN controller

**Honeypot Configuration**:
- Type: Cowrie (SSH/Telnet honeypot)
- Ports: 2222 (SSH), 8080 (HTTP)
- Data Storage: `honeypot_data/cowrie/`
- Log Format: JSON

#### 4.8 Traffic Orchestrator

**File**: `ryu_controller/traffic_orchestrator.py`

**Purpose**: Central intelligent orchestration engine for dynamic and multifaceted traffic orchestration

**Responsibilities**:
- Make intelligent policy decisions based on multiple real-time variables
- Consider device identity, trust scores, and threat intelligence simultaneously
- Enforce various security policies (allow, deny, redirect, quarantine)
- Provide unified interface for policy decisions
- Maintain audit trail of policy decisions

**Decision Factors**:
- Device identity and authentication status
- Current trust score (0-100)
- Active threat intelligence from Analyst module
- Recent security alerts and their severity
- Threat level assessment (none, low, medium, high, critical)

**Policy Decision Logic**:
1. Critical threat level → QUARANTINE
2. High threat level → REDIRECT or QUARANTINE (based on trust)
3. Trust score < 30 → QUARANTINE
4. Trust score < 50 → DENY
5. Medium threat level → REDIRECT
6. Trust score < 70 → REDIRECT
7. Low threat level → ALLOW (with monitoring)
8. Trust score >= 70 → ALLOW

**Methods**:
- `orchestrate_policy(device_id, threat_intelligence)`: Makes intelligent policy decision
- `get_decision_history(device_id, limit)`: Retrieves policy decision audit trail

#### 4.9 Zero Trust Integration

**File**: `zero_trust_integration.py`

**Purpose**: Orchestrates all components

**Responsibilities**:
- Initialize all modules
- Coordinate component interactions
- Background monitoring threads
- Event handling
- Status reporting
- Connect Analyst module to SDN Policy Engine
- Integrate Traffic Orchestrator for intelligent policy decisions

**Background Threads**:
1. **Honeypot Monitor**: Monitors honeypot logs every 10 seconds
2. **Attestation Thread**: Performs device attestation every 5 minutes
3. **Policy Adapter**: Adapts policies every 1 minute
4. **Analyst Monitor**: Monitors analyst alerts and triggers policy orchestration every 30 seconds

**Analyst Module Integration**:
- Connects Analyst module to SDN Policy Engine via `set_analyst_module()`
- Background thread polls for recent alerts from AnomalyDetector
- When anomalies detected, calls `handle_analyst_alert()` to trigger dynamic rule installation
- Uses Traffic Orchestrator for intelligent policy decisions based on threat intelligence

### Layer 5: Management Layer

**Purpose**: User interface and system management

**Components**:
- Web Dashboard (`templates/dashboard.html`)
- REST API endpoints
- Real-time updates (AJAX)

**Features**:
- Device overview and management
- Network topology visualization
- Security alerts display
- ML engine statistics
- SDN policy controls
- Trust score visualization
- Certificate management

**Technologies**:
- HTML5/CSS3
- JavaScript (vanilla)
- vis-network.js (topology)
- AJAX for real-time updates

---

## Component Architecture

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Zero Trust Framework                      │
│                    (Orchestrator)                            │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ↓              ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Identity   │ │    Trust     │ │   Heuristic  │ │   Honeypot   │
│   Manager    │ │  Evaluator   │ │   Analyst    │ │   Manager    │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │
       │                │                │                │
       │  Policy Defs   │  Trust Scores  │  Threat Alerts │  Threat Intel
       │                │                │                │
       ↓                ↓                ↓                ↓
┌─────────────────────────────────────────────────────────────┐
│              Traffic Orchestrator                            │
│  • Intelligent Policy Decisions                              │
│  • Multi-factor Analysis                                     │
│  • Dynamic Policy Enforcement                                │
└─────────────────────────────────────────────────────────────┘
       │                │                │                │
       ↓                ↓                ↓                ↓
┌─────────────────────────────────────────────────────────────┐
│                    Flask Controller                          │
│  • Token Management                                          │
│  • Device Authorization                                      │
│  • Rate Limiting                                             │
│  • API Endpoints                                             │
└─────────────────────────────────────────────────────────────┘
         │              │              │
         ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Ryu SDN    │ │   ML Security │ │   Dashboard  │
│  Controller  │ │    Engine     │ │              │
│              │ │                │ │              │
│  • Policy    │ │  • Attack      │ │  • Real-time │
│    Engine    │ │    Detection   │ │    Monitoring│
│  • OpenFlow  │ │  • ML Models   │ │  • Alerts    │
│    Rules     │ │                │ │  • Topology  │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Component Communication Patterns

#### 1. Synchronous Communication (HTTP/REST)
- Device → Controller: Token requests, data submission
- Dashboard → Controller: API calls for status
- Controller → ML Engine: Packet analysis

#### 2. Asynchronous Communication (Events)
- Heuristic Analyst → Trust Scorer: Anomaly alerts
- Trust Scorer → Policy Adapter: Trust score changes
- Honeypot Manager → Mitigation Generator: Threat intelligence

#### 3. Database Communication (SQLite)
- Identity Manager ↔ Identity Database
- Trust Scorer ↔ Score History
- Behavioral Profiler ↔ Baselines

#### 4. OpenFlow Protocol
- Ryu Controller ↔ SDN Switch
- Flow rule installation
- Statistics polling

---

## Data Flow Architecture

### 1. Device Onboarding Flow

```
┌──────────┐
│ ESP32    │
│ Device   │
└────┬─────┘
     │ 1. Connect to Gateway AP
     ↓
┌──────────┐
│ Gateway  │
└────┬─────┘
     │ 2. Forward onboarding request
     ↓
┌──────────┐
│ Flask    │
│Controller│
└────┬─────┘
     │ 3. Validate device authorization
     ↓
┌──────────┐
│Identity  │
│Manager   │
└────┬─────┘
     │ 4. Generate certificate
     │ 5. Create identity record
     │ 6. Establish baseline
     ↓
┌──────────┐
│Trust     │
│Scorer    │
└────┬─────┘
     │ 7. Initialize trust score (70)
     ↓
┌──────────┐
│Controller│
└────┬─────┘
     │ 8. Issue token
     ↓
┌──────────┐
│ Device   │
│ Ready    │
└──────────┘
```

### 2. Data Transmission Flow

```
┌──────────┐
│ ESP32    │
│ Node     │
└────┬─────┘
     │ 1. Collect sensor data
     │ 2. Create packet with token
     ↓
┌──────────┐
│ Gateway  │
└────┬─────┘
     │ 3. Forward to controller
     ↓
┌──────────┐
│ Flask    │
│Controller│
└────┬─────┘
     │ 4. Validate token
     │ 5. Check session timeout
     │ 6. Check rate limit
     │ 7. Check authorization
     ↓
┌──────────┐
│   ML     │
│  Engine  │
└────┬─────┘
     │ 8. Analyze packet
     │ 9. Detect attacks
     ↓
┌──────────┐
│   SDN    │
│  Policy  │
│  Engine  │
└────┬─────┘
     │ 10. Enforce policies
     │ 11. Apply flow rules
     ↓
┌──────────┐
│  Trust   │
│  Scorer  │
└────┬─────┘
     │ 12. Update trust score
     ↓
┌──────────┐
│Response  │
│Accept/   │
│Reject    │
└──────────┘
```

### 3. Heuristic-Deception Feedback Loop (Threat Detection and Mitigation)

This flow demonstrates the complete integrated heuristic-deception system:

```
┌──────────┐
│  SDN     │
│ Switches │
└────┬─────┘
     │
     │ 1. Flow statistics collected
     │    (periodic polling every 10 seconds)
     ↓
┌──────────────────┐
│ FlowAnalyzer     │
│ Manager          │
│ • Polls all      │
│   switches       │
│ • Aggregates     │
│   statistics     │
└────┬─────────────┘
     │
     │ 2. Get flow stats for all devices
     │    (window: 60 seconds)
     ↓
┌──────────────────┐
│ AnomalyDetector  │
│ • Compare against│
│   baseline       │
│ • Detect DoS,    │
│   scanning, etc. │
└────┬─────────────┘
     │
     │ 3. Anomaly detected
     │    (DoS, scanning, volume attack)
     ↓
┌──────────┐      ┌──────────┐
│Heuristic │      │   ML     │
│ Analyst  │ ←──→ │  Engine  │
└────┬─────┘      └──────────┘
     │
     │ 4. Alert generated
     │    (via poll_flow_statistics thread)
     ↓
┌──────────┐
│  Trust   │
│  Scorer  │
└────┬─────┘
     │ 2. Reduce trust score
     ↓
┌──────────────────────────┐
│   Traffic Orchestrator    │
│  • Analyzes trust score   │
│  • Considers threat level │
│  • Makes policy decision  │
└────┬──────────────────────┘
     │ 3. Orchestrate policy
     ↓
┌──────────┐
│   SDN    │
│  Policy  │
│  Engine  │
└────┬─────┘
     │ 4. handle_analyst_alert()
     │    → Redirect to honeypot
     ↓
┌──────────┐
│ Honeypot │
│ (Cowrie) │
└────┬─────┘
     │ 5. Capture attack
     │    (attacker interacts with honeypot)
     ↓
┌──────────┐
│ Threat   │
│Intel     │
│          │
│ • Parse  │
│   logs   │
│ • Extract│
│   IPs    │
│ • Extract│
│   commands│
└────┬─────┘
     │ 6. Extract IOCs
     │    (via monitor_honeypot_logs thread)
     ↓
┌──────────┐
│Mitigation│
│Generator │
└────┬─────┘
     │ 7. Generate blocking rules
     ↓
┌──────────┐
│   SDN    │
│  Policy  │
│  Engine  │
└────┬─────┘
     │ 8. Install rules dynamically
     ↓
┌──────────┐
│  Policy  │
│ Adapter  │
└────┬─────┘
     │ 9. Update device policies
     │    (permanent mitigation rules)
     ↓
┌──────────┐
│ Threat   │
│ Blocked  │
│          │
│ • IP     │
│   blocked│
│ • Rules  │
│   applied│
│ • Future │
│   traffic│
│   denied │
└──────────┘
```

**Key Innovation**: The tight integration between lightweight anomaly detection (heuristic analysis) and active deception environment (honeypot). The heuristic analysis acts as a tripwire that triggers the honeypot to capture high-fidelity threat intelligence. This intelligence is then used to create confirmed, high-confidence mitigation rules, creating a more adaptive defense system than either component could achieve alone.

### 4. Policy Translation and Application Flow

```
┌──────────┐
│ Identity │
│  Module  │
└────┬─────┘
     │ 1. Generate least-privilege policy
     │    from behavioral baseline
     ↓
┌──────────┐
│  Policy  │
│Generator │
└────┬─────┘
     │ 2. High-level policy definition
     │    {
     │      'device_id': 'ESP32_2',
     │      'rules': [
     │        {'type': 'allow', 'match': {'ipv4_dst': '192.168.1.100'}},
     │        {'type': 'deny', 'match': {}}
     │      ]
     │    }
     ↓
┌──────────┐
│   SDN    │
│  Policy  │
│  Engine  │
└────┬─────┘
     │ 3. apply_policy_from_identity()
     │    • Get device MAC from Identity module
     │    • Translate each rule to OpenFlow match fields
     │    • Install granular OpenFlow rules
     ↓
┌──────────┐
│ OpenFlow │
│  Switch  │
└────┬─────┘
     │ 4. Flow rules installed:
     │    • Rule 1: eth_src=MAC, ipv4_dst=192.168.1.100 → ALLOW
     │    • Rule 2: eth_src=MAC → DENY (default)
     ↓
┌──────────┐
│  Policy  │
│ Enforced │
└──────────┘
```

---

## Security Architecture

### Security Layers

#### Layer 1: Device Authentication
- **Token-based**: UUID tokens, 5-minute expiry
- **PKI-based**: X.509 certificates (optional)
- **MAC address**: Device identification

#### Layer 2: Authorization
- **Device whitelist**: Pre-authorized devices
- **Dynamic revocation**: Real-time access control
- **Trust-based access**: Trust score determines access level

#### Layer 3: Rate Limiting
- **Per-device limits**: 60 packets/minute
- **Sliding window**: 60-second window
- **Automatic blocking**: When limit exceeded

#### Layer 4: Session Management
- **Timeout**: 5-minute sessions
- **Token invalidation**: Automatic on timeout
- **Activity tracking**: Last activity timestamp

#### Layer 5: Network Security
- **SDN policies**: Packet inspection, traffic shaping
- **Traffic redirection**: Suspicious traffic to honeypot
- **Quarantine**: Isolate compromised devices

#### Layer 6: Attack Detection
- **ML-based**: TensorFlow models for DDoS detection
- **Heuristic-based**: Rule-based anomaly detection
- **Behavioral analysis**: Baseline comparison

#### Layer 7: Threat Intelligence
- **Honeypot**: Active threat capture
- **Log analysis**: Threat extraction
- **Automatic mitigation**: Rule generation

### Zero Trust Principles Implementation

1. **Never Trust, Always Verify**
   - Every packet validated
   - Continuous authentication
   - Token validation on each request

2. **Least Privilege Access**
   - Trust-based access levels
   - Policy adaptation based on trust
   - Device-specific policies

3. **Assume Breach**
   - Honeypot for threat detection
   - Continuous monitoring
   - Automatic isolation

4. **Continuous Verification**
   - Periodic attestation (every 5 minutes)
   - Trust score updates
   - Behavioral monitoring

5. **Micro-segmentation**
   - Device isolation
   - Traffic redirection
   - Quarantine zones

---

## Network Architecture

### Network Topology

```
                    Internet
                       │
                       ↓
              ┌────────────────┐
              │   Router/AP     │
              │  (192.168.1.1)  │
              └────────┬────────┘
                       │ WiFi/Ethernet
                       ↓
        ┌──────────────┴──────────────┐
        │                              │
        ↓                              ↓
┌───────────────┐            ┌───────────────┐
│ Controller    │            │ ESP32 Gateway │
│ Server        │            │               │
│(192.168.1.100)│            │ AP: 192.168.4.1│
│               │            │ STA: DHCP     │
└───────────────┘            └───────┬───────┘
                                     │ WiFi AP
                                     │ "ESP32-AP"
                                     ↓
                        ┌────────────┴────────────┐
                        │                         │
                        ↓                         ↓
                ┌──────────────┐         ┌──────────────┐
                │ ESP32 Node 1 │         │ ESP32 Node 2 │
                │ (192.168.4.X)│         │ (192.168.4.Y)│
                └──────────────┘         └──────────────┘
```

### IP Address Allocation

**Controller Network** (192.168.1.0/24):
- Router: 192.168.1.1
- Controller: 192.168.1.100 (static recommended)
- Gateway (STA): DHCP from router

**Gateway AP Network** (192.168.4.0/24):
- Gateway (AP): 192.168.4.1 (fixed)
- Nodes: 192.168.4.2-254 (DHCP from gateway)

### Protocol Stack

```
Application Layer
    │
    ├── HTTP/JSON (Device ↔ Controller)
    ├── OpenFlow 1.3 (Controller ↔ Switch)
    └── REST API (Dashboard ↔ Controller)
    │
Transport Layer
    │
    ├── TCP (HTTP, OpenFlow)
    └── UDP (Optional for stats)
    │
Network Layer
    │
    └── IP (IPv4)
    │
Data Link Layer
    │
    ├── WiFi 802.11 (Device ↔ Gateway)
    └── Ethernet (Gateway ↔ Controller)
    │
Physical Layer
    │
    ├── 2.4 GHz WiFi
    └── Ethernet cable
```

---

## Deployment Architecture

### Development Deployment

```
Developer Machine
    │
    ├── Python 3.8+
    ├── Flask Controller
    ├── ML Engine
    ├── Virtual ESP32 devices (Mininet)
    └── Web Dashboard
```

### Production Deployment (Raspberry Pi)

```
Raspberry Pi 4
    │
    ├── Systemd Services
    │   ├── Flask Controller (port 5000)
    │   ├── Ryu SDN Controller (port 6653)
    │   └── Zero Trust Framework
    │
    ├── Docker
    │   └── Cowrie Honeypot
    │
    ├── SQLite Database
    │   └── identity.db
    │
    └── File System
        ├── certs/ (Certificates)
        ├── models/ (ML models)
        ├── logs/ (Log files)
        └── honeypot_data/ (Honeypot logs)
```

### Cloud Deployment

```
Cloud Provider (AWS/Azure/GCP)
    │
    ├── Compute Instance
    │   ├── Flask Controller
    │   ├── ML Engine
    │   └── Zero Trust Framework
    │
    ├── Container Service
    │   └── Honeypot containers
    │
    ├── Database Service
    │   └── Device identity database
    │
    └── Load Balancer
        └── Distribute traffic
```

### Hybrid Deployment

```
On-Premise Gateway
    │
    └── ESP32 Gateway
        └── Local IoT devices

Cloud Controller
    │
    └── Centralized control
        └── Multiple gateways
```

---

## Scalability Architecture

### Horizontal Scaling

- **Multiple Controllers**: Load balance across instances
- **Database Replication**: SQLite → PostgreSQL
- **Redis Cache**: Token caching
- **Message Queue**: Async processing (RabbitMQ/Kafka)

### Vertical Scaling

- **Raspberry Pi 4**: 4GB → 8GB RAM
- **Server Upgrade**: More CPU/RAM
- **SSD Storage**: Faster I/O
- **GPU**: ML model acceleration

---

## Performance Architecture

### Optimization Strategies

1. **Caching**: Token cache, trust score cache
2. **Async Processing**: Background threads for heavy operations
3. **Database Indexing**: Fast device lookups
4. **Connection Pooling**: Reuse database connections
5. **Batch Processing**: Group similar operations

### Performance Metrics

- **Token Generation**: < 10ms
- **Packet Analysis**: < 50ms (ML)
- **Policy Enforcement**: < 5ms
- **Trust Score Update**: < 20ms
- **Dashboard Load**: < 500ms

---
