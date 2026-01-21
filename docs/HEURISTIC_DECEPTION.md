# Heuristic-Based Anomaly Detection with Honeypot Integration

## Overview

The Heuristic-Deception system is an integrated security solution that combines lightweight anomaly detection with an active deception environment. The system periodically polls flow statistics from network switches, compares them against baseline profiles, and automatically redirects suspicious traffic to honeypots for threat intelligence gathering. This creates an adaptive defense system that becomes more effective over time.

## Key Innovation

The innovation is the **tight integration** of lightweight anomaly detection with an active deception environment. The heuristic analysis acts as a tripwire that triggers the honeypot to capture high-fidelity threat intelligence. This intelligence is then used to create confirmed, high-confidence mitigation rules, creating a more adaptive defense system than either component could achieve alone.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Heuristic-Deception System                     │
└─────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Flow       │ │  Anomaly     │ │  Baseline   │
│  Statistics  │ │  Detector    │ │  Manager    │
│  Polling     │ │              │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                 │                 │
       └─────────┬───────┴─────────────────┘
                 │
                 ↓
         ┌──────────────┐
         │   Alert      │
         │  Generation  │
         └──────┬───────┘
                 │
                 ↓
         ┌──────────────┐
         │   Policy     │
         │   Engine     │
         └──────┬───────┘
                 │
                 ↓
         ┌──────────────┐
         │   Traffic    │
         │ Redirection  │
         │  to Honeypot │
         └──────┬───────┘
                 │
                 ↓
         ┌──────────────┐
         │   Honeypot   │
         │  (Container) │
         └──────┬───────┘
                 │
                 ↓
         ┌──────────────┐
         │   Threat     │
         │ Intelligence │
         └──────┬───────┘
                 │
                 ↓
         ┌──────────────┐
         │  Mitigation  │
         │   Rules      │
         └──────┬───────┘
                 │
                 ↓
         ┌──────────────┐
         │  Permanent   │
         │  Mitigation   │
         └──────────────┘
```

## Components

### 1. Flow Statistics Polling

**File**: `heuristic_analyst/flow_analyzer.py`

**Purpose**: Periodically polls flow statistics from network switches using Ryu.

**Key Features**:
- Polls every 10 seconds (configurable)
- Supports multiple switches via `FlowAnalyzerManager`
- Maps MAC addresses to device IDs via Identity module
- Aggregates statistics across switches per device

**Statistics Collected**:
- Packet counts
- Byte counts
- Packets per second (pps)
- Bytes per second (bps)
- Unique destinations
- Unique ports
- Flow duration

**Implementation**:
```python
# FlowAnalyzerManager manages multiple switches
flow_analyzer_manager = FlowAnalyzerManager(
    identity_module=onboarding,
    polling_interval=10
)

# Add switches as they connect
flow_analyzer_manager.add_switch(dpid, datapath)

# Start polling
flow_analyzer_manager.start_polling()
```

### 2. Baseline Management

**File**: `heuristic_analyst/baseline_manager.py`

**Purpose**: Manages behavioral baselines for devices.

**Baseline Metrics**:
- Average packets per second
- Average bytes per second
- Common destinations (top 10)
- Common ports (top 10)
- Traffic patterns

**Baseline Establishment**:
- Baselines created during device onboarding
- Updated adaptively using exponential moving average
- Stored in identity database

**Usage**:
```python
# Get baseline for device
baseline = baseline_manager.get_baseline(device_id)

# Update baseline with new metrics
baseline_manager.update_baseline(device_id, new_metrics)
```

### 3. Anomaly Detection

**File**: `heuristic_analyst/anomaly_detector.py`

**Purpose**: Detects anomalies by comparing current traffic metrics against baselines.

**Detection Rules**:

#### DoS Attack Detection
```python
if current_pps > baseline_pps * 10:
    severity = 'high'
    anomaly_type = 'dos'
elif current_pps > baseline_pps * 5:
    severity = 'high'
    anomaly_type = 'dos'
elif current_pps > baseline_pps * 2:
    severity = 'medium'
    anomaly_type = 'dos'
```

#### Volume Attack Detection
```python
if current_bps > baseline_bps * 10:
    severity = 'high'
    anomaly_type = 'volume_attack'
```

#### Network Scanning Detection
```python
if unique_destinations > baseline_destinations * 5 and unique_destinations > 20:
    severity = 'medium'
    anomaly_type = 'scanning'
```

#### Port Scanning Detection
```python
if unique_ports > baseline_ports * 3 and unique_ports > 10:
    severity = 'medium'
    anomaly_type = 'port_scanning'
```

**Severity Scoring**:
- **High (70+)**: Immediate action required
- **Medium (40-69)**: Monitor and redirect
- **Low (20-39)**: Log and observe
- **None (<20)**: Normal traffic

### 4. Alert Generation and Policy Engine Integration

**File**: `zero_trust_integration.py` - `poll_flow_statistics()` thread

**Purpose**: Real-time anomaly detection and alert generation.

**Process**:
1. Polls flow statistics every 10 seconds
2. Gets aggregated stats for all devices (60-second window)
3. Loads baseline for each device
4. Compares current stats against baseline
5. Triggers alert if anomaly detected
6. Sends alert to Policy Engine

**Alert Flow**:
```python
# Detect anomaly
anomaly_result = anomaly_detector.detect_anomalies(device_id, stats)

if anomaly_result['is_anomaly']:
    # Handle alert
    handle_analyst_alert(
        device_id,
        anomaly_result['anomaly_type'],
        anomaly_result['severity']
    )
    
    # Use traffic orchestrator for policy decision
    traffic_orchestrator.orchestrate_policy(
        device_id,
        threat_intelligence={
            'severity': severity,
            'alert_type': alert_type,
            'indicators': anomaly_result['indicators']
        }
    )
```

### 5. Traffic Redirection to Honeypot

**File**: `ryu_controller/sdn_policy_engine.py` - `handle_analyst_alert()`

**Purpose**: Automatically redirects suspicious traffic to honeypot.

**Implementation**:
- When alert received, Policy Engine applies redirect policy
- OpenFlow rules installed with high priority (150)
- Traffic from suspicious device redirected to honeypot port
- Device unaware of redirection (transparent)

**OpenFlow Rule**:
```python
match = {
    'eth_src': device_mac_address
}
action = OUTPUT(port=honeypot_port)  # Default: port 3
priority = 150
```

### 6. Honeypot Deployment

**File**: `honeypot_manager/honeypot_deployer.py`

**Purpose**: Deploys and manages containerized honeypots.

**Honeypot Type**: Cowrie (SSH/Telnet honeypot)

**Features**:
- Docker-based deployment
- Lightweight containers
- Emulates vulnerable IoT services
- Ports: 2222 (SSH), 8080 (HTTP)
- Data storage: `honeypot_data/cowrie/`

**Deployment**:
```python
honeypot_deployer = HoneypotDeployer(honeypot_type='cowrie')
honeypot_deployer.deploy()  # Creates and starts container
```

### 7. Honeypot Log Parsing

**File**: `honeypot_manager/log_parser.py`

**Purpose**: Parses honeypot logs to extract threat intelligence.

**Intelligence Extracted**:
- **Attacker IPs**: Source IP addresses
- **Commands Used**: Commands executed by attackers
- **Event Types**: Login attempts, file downloads, etc.
- **Timestamps**: When attacks occurred
- **Usernames/Passwords**: Credentials used (if login attempts)

**Log Formats Supported**:
- JSON logs (Cowrie default)
- Text logs (fallback)

**Parsing**:
```python
log_parser = HoneypotLogParser(honeypot_type='cowrie')
threats = log_parser.parse_logs(log_content)

# Extract specific intelligence
ips = log_parser.extract_ips()
commands = log_parser.extract_commands()
```

### 8. Threat Intelligence Processing

**File**: `honeypot_manager/threat_intelligence.py`

**Purpose**: Processes threat intelligence and determines mitigation actions.

**Threat Analysis**:
- **High Severity**: Login success, file downloads → Block IP
- **Medium Severity**: Command execution → Monitor
- **Low Severity**: Login attempts → Log

**Malicious Command Detection**:
```python
malicious_keywords = ['rm', 'delete', 'format', 'dd', 'mkfs', 'shutdown', 'reboot']
if any(keyword in command for keyword in malicious_keywords):
    severity = 'high'
```

### 9. Mitigation Rule Generation

**File**: `honeypot_manager/mitigation_generator.py`

**Purpose**: Generates mitigation rules from threat intelligence.

**Rule Types**:

#### DENY Rule (High Severity)
```python
rule = {
    'type': 'deny',
    'match_fields': {'ipv4_src': attacker_ip},
    'priority': 200,
    'reason': 'High severity threats detected'
}
```

#### REDIRECT Rule (Medium Severity)
```python
rule = {
    'type': 'redirect',
    'match_fields': {'ipv4_src': attacker_ip},
    'priority': 150,
    'reason': 'Multiple threats detected'
}
```

#### MONITOR Rule (Low Severity)
```python
rule = {
    'type': 'monitor',
    'match_fields': {'ipv4_src': attacker_ip},
    'priority': 100,
    'reason': 'Threats detected'
}
```

**Rule Application**:
- Rules automatically applied to SDN Policy Engine
- OpenFlow rules installed on switches
- Permanent until manually removed

## Complete Feedback Loop

### Step-by-Step Flow

1. **Flow Statistics Polling** (Every 10 seconds)
   - FlowAnalyzerManager polls all switches
   - Collects flow statistics for all devices
   - Aggregates statistics across switches

2. **Baseline Comparison** (Real-time)
   - Gets baseline for each device
   - Compares current stats against baseline
   - Calculates deviation ratios

3. **Anomaly Detection** (Real-time)
   - Detects DoS, scanning, volume attacks
   - Assigns severity levels
   - Generates anomaly alerts

4. **Alert Handling** (Immediate)
   - Alert sent to Policy Engine
   - Trust score reduced
   - Policy orchestration triggered

5. **Traffic Redirection** (Immediate)
   - OpenFlow rules installed
   - Traffic redirected to honeypot
   - Device unaware of redirection

6. **Honeypot Capture** (Ongoing)
   - Attacker interacts with honeypot
   - All interactions logged
   - High-fidelity intelligence captured

7. **Log Parsing** (Every 10 seconds)
   - Honeypot logs monitored
   - Threat intelligence extracted
   - IPs, commands, patterns identified

8. **Threat Analysis** (Real-time)
   - Severity assessment
   - Malicious behavior detection
   - Threat classification

9. **Mitigation Rule Generation** (Real-time)
   - Rules generated based on threat severity
   - DENY for high severity
   - REDIRECT/MONITOR for medium/low

10. **Rule Application** (Immediate)
    - Rules applied to Policy Engine
    - OpenFlow rules installed
    - Permanent mitigation active

11. **Threat Blocked** (Ongoing)
    - Future traffic from attacker blocked
    - System protected from confirmed threats
    - Adaptive defense improved

## Configuration

### Flow Polling Configuration

**File**: `zero_trust_integration.py`

```python
config = {
    'flow_polling_interval': 10,  # Seconds between polls
    'anomaly_window': 60,         # Time window for stats (seconds)
    'honeypot_type': 'cowrie'     # Honeypot type
}
```

### Anomaly Detection Thresholds

**File**: `heuristic_analyst/anomaly_detector.py`

```python
# DoS Detection
DOS_THRESHOLD_HIGH = 10.0    # 10x baseline
DOS_THRESHOLD_MEDIUM = 5.0   # 5x baseline
DOS_THRESHOLD_LOW = 2.0       # 2x baseline

# Scanning Detection
SCAN_DEST_THRESHOLD = 5.0     # 5x baseline destinations
SCAN_PORT_THRESHOLD = 3.0     # 3x baseline ports
SCAN_MIN_DEST = 20            # Minimum unique destinations
SCAN_MIN_PORT = 10            # Minimum unique ports
```

### Honeypot Configuration

**File**: `honeypot_manager/honeypot_deployer.py`

```python
honeypot_config = {
    'type': 'cowrie',
    'ssh_port': 2222,
    'http_port': 8080,
    'data_dir': 'honeypot_data/cowrie'
}
```

## Usage Examples

### Starting the System

```python
from zero_trust_integration import ZeroTrustFramework

# Initialize framework
framework = ZeroTrustFramework(
    config={
        'flow_polling_interval': 10,
        'honeypot_type': 'cowrie'
    }
)

# Set SDN policy engine (after Ryu controller starts)
framework.set_sdn_policy_engine(sdn_policy_engine)

# Start framework
framework.start()

# System now:
# - Polls flow statistics every 10 seconds
# - Detects anomalies in real-time
# - Redirects suspicious traffic to honeypot
# - Parses honeypot logs
# - Generates mitigation rules
```

### Monitoring Flow Statistics

```python
# Get flow statistics for all devices
all_stats = framework.flow_analyzer_manager.get_all_device_stats(window_seconds=60)

for device_id, stats in all_stats.items():
    print(f"Device: {device_id}")
    print(f"  Packets/sec: {stats['packets_per_second']:.2f}")
    print(f"  Bytes/sec: {stats['bytes_per_second']:.2f}")
    print(f"  Unique destinations: {stats['unique_destinations']}")
    print(f"  Unique ports: {stats['unique_ports']}")
```

### Checking Threat Intelligence

```python
# Get threat intelligence statistics
stats = framework.threat_intelligence.get_statistics()

print(f"Total threats: {stats['total_threats']}")
print(f"Unique IPs: {stats['unique_ips']}")
print(f"Blocked IPs: {stats['blocked_ips']}")
print(f"Mitigation rules: {stats['mitigation_rules']}")

# Get recent threats
recent_threats = framework.threat_intelligence.get_recent_threats(limit=10)
for threat in recent_threats:
    print(f"IP: {threat['source_ip']}, Type: {threat['event_type']}")
```

### Viewing Mitigation Rules

```python
# Get all generated mitigation rules
rules = framework.mitigation_generator.get_generated_rules()

for rule in rules:
    print(f"Type: {rule['type']}")
    print(f"IP: {rule['match_fields']['ipv4_src']}")
    print(f"Reason: {rule['reason']}")
    print(f"Priority: {rule['priority']}")
```

## Testing

### Test Anomaly Detection

1. **Generate High Packet Rate**:
   ```python
   # Simulate DoS attack by sending high packet rate
   # System should detect anomaly and redirect to honeypot
   ```

2. **Generate Scanning Behavior**:
   ```python
   # Simulate port scanning by connecting to many ports
   # System should detect scanning and redirect to honeypot
   ```

3. **Verify Honeypot Capture**:
   ```python
   # Check honeypot logs
   logs = honeypot_deployer.get_logs(tail=100)
   # Verify attacker IP and commands captured
   ```

4. **Verify Mitigation Rules**:
   ```python
   # Check that mitigation rules were generated
   rules = mitigation_generator.get_generated_rules()
   # Verify rules applied to Policy Engine
   ```

## Troubleshooting

### Flow Statistics Not Being Collected

**Symptoms**: No flow statistics in `get_all_device_stats()`

**Solutions**:
1. Verify switches are connected to SDN controller
2. Check FlowAnalyzerManager has switches added
3. Verify polling is started: `flow_analyzer_manager.start_polling()`
4. Check Ryu controller logs for flow stats replies

### Anomalies Not Detected

**Symptoms**: Traffic anomalies not triggering alerts

**Solutions**:
1. Verify baselines exist for devices
2. Check anomaly detection thresholds
3. Verify flow statistics are being collected
4. Check `poll_flow_statistics()` thread is running

### Honeypot Not Capturing Traffic

**Symptoms**: No logs in honeypot despite redirection

**Solutions**:
1. Verify honeypot container is running
2. Check honeypot ports are accessible
3. Verify OpenFlow redirect rules installed
4. Check honeypot logs: `honeypot_deployer.get_logs()`

### Mitigation Rules Not Applied

**Symptoms**: Rules generated but not blocking traffic

**Solutions**:
1. Verify SDN Policy Engine connected to MitigationGenerator
2. Check OpenFlow rules installed on switches
3. Verify rule priorities are correct
4. Check Policy Engine logs for rule application

## Performance Considerations

### Polling Interval

- **Default**: 10 seconds
- **Lower interval**: More responsive but higher CPU usage
- **Higher interval**: Lower CPU usage but slower detection

### Statistics Window

- **Default**: 60 seconds
- **Shorter window**: More sensitive to short-term spikes
- **Longer window**: Smoother but slower to detect anomalies

### Honeypot Resources

- **CPU**: Minimal (lightweight containers)
- **Memory**: ~100-200MB per honeypot
- **Storage**: Logs grow over time, consider rotation

## Security Considerations

### Honeypot Isolation

- Honeypots should be isolated from production network
- Use separate VLAN or network segment
- Limit honeypot access to prevent lateral movement

### Log Security

- Honeypot logs contain sensitive information
- Encrypt logs at rest
- Limit log access to authorized personnel
- Rotate logs regularly

### False Positives

- Baseline establishment critical for accuracy
- Tune thresholds based on network characteristics
- Monitor and adjust detection rules

## Future Enhancements

1. **Machine Learning Integration**: Use ML models for anomaly detection
2. **Distributed Honeypots**: Deploy honeypots across network segments
3. **Threat Intelligence Sharing**: Share intelligence with other systems
4. **Automated Response**: More sophisticated automated responses
5. **Visualization**: Dashboard for threat intelligence and mitigation rules

## References

- Architecture Documentation: `docs/ARCHITECTURE.md`
- Implementation Features: `docs/IMPLEMENTATION_FEATURES.md`
- Source Code: `heuristic_analyst/`, `honeypot_manager/`, `zero_trust_integration.py`

