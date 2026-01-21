# Secure IoT Device Onboarding Implementation Documentation

## Overview

This document describes the complete implementation of secure onboarding features for the IoT Zero Trust Framework. The implementation includes automatic behavioral profiling, traffic recording, physical identity linking, and automatic policy generation.

**Date**: 2024
**Status**: Complete

---

## Features Implemented

### 1. Automatic Finalization After Profiling Period

**Description**: The system now automatically finalizes device onboarding after the behavioral profiling period (5 minutes) expires, establishing a baseline and generating least-privilege policies without manual intervention.

**Key Components**:
- Background monitoring thread that checks every 30 seconds
- Automatic baseline establishment from observed traffic patterns
- Policy generation and application to SDN controller
- Handles edge cases (insufficient traffic, device disconnects)

**Benefits**:
- Zero-touch policy generation
- Consistent security posture for all devices
- Reduced administrative overhead

---

### 2. Traffic Recording Integration

**Description**: The SDN Policy Engine now automatically records all traffic from devices during the profiling period, enabling accurate behavioral baseline establishment.

**Key Components**:
- Packet capture and analysis in SDN Policy Engine
- Extraction of IP addresses, ports, protocols, and packet sizes
- Real-time traffic recording during profiling
- Integration with behavioral profiler

**Benefits**:
- Accurate behavioral baselines
- Real-time traffic observation
- Automatic policy generation based on actual device behavior

---

### 3. Physical Identity Linking

**Description**: Enhanced PKI onboarding that explicitly links a device's physical identity (MAC address, device type, first seen timestamp) with its network credentials (certificate).

**Key Components**:
- Device fingerprint generation (SHA-256 hash of MAC + type + timestamp)
- Physical identity metadata storage in database
- Certificate generation with physical identity linking
- Simplified onboarding process for non-technical users

**Benefits**:
- Strong binding between physical device and network credential
- Foundation for Zero Trust architecture
- User-friendly onboarding process
- Audit trail of device physical characteristics

---

### 4. Enhanced Database Schema

**Description**: Extended the SQLite identity database to support physical identity information and device fingerprinting.

**New Database Fields**:
- `physical_identity` (TEXT): JSON metadata containing MAC, device type, timestamps
- `device_fingerprint` (TEXT): SHA-256 hash fingerprint for device identification
- `first_seen` (TIMESTAMP): First time device was detected/onboarded

**Migration**: Automatic migration function handles existing databases gracefully.

---

## File Changes

### Modified Files

#### 1. `identity_manager/device_onboarding.py`

**Changes**:
- Added automatic finalization monitoring thread
- Enhanced `onboard_device()` to create physical identity and fingerprint
- Added `_start_profiling_monitor()` method for background monitoring
- Added `stop_monitoring()` method for graceful shutdown
- Updated onboarding result to include physical identity information

**New Methods**:
- `_start_profiling_monitor()`: Starts background thread for automatic finalization
- `stop_monitoring()`: Stops the monitoring thread

**Modified Methods**:
- `onboard_device()`: Now creates physical identity and device fingerprint
- `__init__()`: Initializes monitoring thread automatically

**Key Code Additions**:
```python
# Automatic finalization monitoring
self.monitoring_enabled = True
self.monitoring_thread = None
self.monitoring_interval = 30  # Check every 30 seconds
self.min_traffic_packets = 5  # Minimum packets required for baseline
```

---

#### 2. `identity_manager/behavioral_profiler.py`

**Changes**:
- Added methods to check profiling expiration status
- Added method to get profiling status for a device
- Added method to get list of actively profiled devices
- Added method to get elapsed profiling time

**New Methods**:
- `is_profiling_expired(device_id)`: Checks if profiling period has expired
- `get_active_profiling_devices()`: Returns list of devices being profiled
- `get_profiling_elapsed_time(device_id)`: Gets elapsed time for profiling
- `get_profiling_status(device_id)`: Gets detailed profiling status

**Import Fix**:
- Added `Optional` to type imports

---

#### 3. `identity_manager/identity_database.py`

**Changes**:
- Extended database schema with new columns
- Added database migration function
- Enhanced `add_device()` method to support physical identity
- Improved first_seen timestamp handling

**New Database Columns**:
- `physical_identity` (TEXT)
- `device_fingerprint` (TEXT)
- `first_seen` (TIMESTAMP)

**New Methods**:
- `_migrate_database(conn)`: Automatically migrates existing databases

**Modified Methods**:
- `add_device()`: Now accepts and stores physical identity information
- `_init_database()`: Includes migration call

---

#### 4. `ryu_controller/sdn_policy_engine.py`

**Changes**:
- Added traffic recording integration
- Added onboarding module reference
- Enhanced packet processing to extract traffic information
- Records traffic for devices in active profiling

**New Methods**:
- `set_onboarding_module(onboarding_module)`: Connects onboarding module for traffic recording

**Modified Methods**:
- `packet_in_handler()`: Now extracts and records traffic information
- `__init__()`: Initializes onboarding_module reference

**Key Code Additions**:
```python
# Record traffic for behavioral profiling if device is being profiled
if device_id and self.onboarding_module:
    packet_info = {
        'size': len(msg.data),
        'src_mac': eth_src,
        'dst_mac': eth_dst,
        'dst_ip': ip_pkt.dst,  # If IP packet
        'dst_port': tcp_pkt.dst_port,  # If TCP/UDP
        'protocol': ip_pkt.proto
    }
    self.onboarding_module.record_traffic(device_id, packet_info)
```

**Import Changes**:
- Added `tcp` and `udp` to packet imports

---

#### 5. `zero_trust_integration.py`

**Changes**:
- Connected onboarding module to SDN Policy Engine for traffic recording
- Ensures all components are properly integrated

**Modified Methods**:
- `set_sdn_policy_engine()`: Now calls `set_onboarding_module()` on SDN Policy Engine

**Key Code Addition**:
```python
self.sdn_policy_engine.set_onboarding_module(self.onboarding)  # For traffic recording
```

---

#### 6. `controller.py`

**Changes**:
- Added new API endpoints for onboarding management
- Enhanced onboarding response logging
- Added profiling status endpoint

**New API Endpoints**:
- `POST /finalize_onboarding`: Manually finalize onboarding for a device
- `GET /get_profiling_status?device_id=...`: Get current profiling status

**Modified Endpoints**:
- `POST /onboard`: Enhanced logging to indicate auto-finalization

**New Endpoint Details**:

**POST /finalize_onboarding**
```json
Request:
{
    "device_id": "ESP32_2"
}

Response:
{
    "status": "success",
    "device_id": "ESP32_2",
    "baseline": {...},
    "policy": {...},
    "message": "Onboarding finalized. Baseline and policy generated."
}
```

**GET /get_profiling_status**
```
Query Parameters:
- device_id: Device identifier (required)

Response (if profiling):
{
    "status": "success",
    "device_id": "ESP32_2",
    "is_profiling": true,
    "elapsed_time": 120.5,
    "remaining_time": 179.5,
    "packet_count": 45,
    "byte_count": 10240
}

Response (if completed):
{
    "status": "success",
    "device_id": "ESP32_2",
    "is_profiling": false,
    "baseline_established": true,
    "baseline": {...}
}
```

---

## Workflow

### Complete Onboarding Flow

1. **Device Detection/Onboarding Request**
   - Device connects to network or admin initiates onboarding
   - System generates unique device ID
   - Creates physical identity fingerprint

2. **Certificate Generation**
   - PKI certificate generated with device identity
   - Physical identity linked to network credential
   - Certificate stored in database

3. **Behavioral Profiling Starts**
   - Profiling begins automatically (5-minute period)
   - Traffic recording activated
   - SDN Policy Engine captures all packets

4. **Traffic Observation**
   - All device traffic recorded during profiling
   - Packet information extracted (IP, ports, protocols, sizes)
   - Behavioral patterns observed

5. **Automatic Finalization** (after 5 minutes)
   - Monitoring thread detects profiling period expiration
   - Baseline established from observed traffic
   - Least-privilege policy generated
   - Policy applied to SDN controller

6. **Policy Enforcement**
   - SDN Policy Engine enforces generated policies
   - Device operates with least-privilege access
   - Continuous monitoring for anomalies

---

## Database Schema

### Devices Table

```sql
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    mac_address TEXT UNIQUE NOT NULL,
    certificate_path TEXT,
    key_path TEXT,
    onboarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,
    status TEXT DEFAULT 'active',
    device_type TEXT,
    device_info TEXT,
    physical_identity TEXT,        -- NEW: JSON metadata
    first_seen TIMESTAMP,          -- NEW: First detection time
    device_fingerprint TEXT         -- NEW: SHA-256 fingerprint
)
```

### Behavioral Baselines Table

```sql
CREATE TABLE behavioral_baselines (
    device_id TEXT PRIMARY KEY,
    baseline_data TEXT,
    established_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
)
```

### Device Policies Table

```sql
CREATE TABLE device_policies (
    device_id TEXT PRIMARY KEY,
    policy_data TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
)
```

---

## Configuration

### Profiling Configuration

The profiling duration and monitoring interval can be configured:

```python
# In identity_manager/device_onboarding.py
self.profiler = BehavioralProfiler(profiling_duration=300)  # 5 minutes
self.monitoring_interval = 30  # Check every 30 seconds
self.min_traffic_packets = 5  # Minimum packets for baseline
```

### Physical Identity Format

Physical identity is stored as JSON:

```json
{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "device_type": "sensor",
    "first_seen": "2024-01-15T10:30:00Z",
    "onboarding_timestamp": "2024-01-15T10:30:00Z"
}
```

### Device Fingerprint

Device fingerprint is generated as:
```
SHA256(MAC_ADDRESS:DEVICE_TYPE:FIRST_SEEN_TIMESTAMP)[:16]
```

Example: `a3f2k9b8c7d6e5f4`

---

## API Usage Examples

### Onboard a Device

```bash
curl -X POST http://localhost:5000/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_2",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "device_type": "sensor",
    "device_info": "Temperature sensor"
  }'
```

**Response**:
```json
{
    "status": "success",
    "device_id": "ESP32_2",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "certificate_path": "certs/ESP32_2_cert.pem",
    "key_path": "certs/ESP32_2_key.pem",
    "ca_certificate": "-----BEGIN CERTIFICATE-----\n...",
    "profiling": true,
    "device_fingerprint": "a3f2k9b8c7d6e5f4",
    "physical_identity_linked": true,
    "message": "Device onboarded successfully. Physical identity linked to network credential. Behavioral profiling started."
}
```

### Check Profiling Status

```bash
curl "http://localhost:5000/get_profiling_status?device_id=ESP32_2"
```

### Manually Finalize Onboarding

```bash
curl -X POST http://localhost:5000/finalize_onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_2"
  }'
```

---

## Security Features

### 1. PKI-Based Authentication
- X.509 certificates for device authentication
- Certificate Authority (CA) for trust chain
- Automatic certificate generation and distribution

### 2. Physical Identity Binding
- Strong binding between physical device and network credential
- Device fingerprint prevents device spoofing
- Audit trail of device physical characteristics

### 3. Least-Privilege Policy Generation
- Policies generated from observed behavior
- Only allows traffic patterns seen during profiling
- Default deny for unknown traffic

### 4. Behavioral Baseline
- Establishes normal behavior patterns
- Enables anomaly detection
- Supports adaptive security policies

---

## Monitoring and Logging

### Log Messages

The system logs important events:

```
INFO: Device onboarding system initialized
INFO: Profiling monitor thread started
INFO: Starting onboarding for device ESP32_2 (AA:BB:CC:DD:EE:FF)...
INFO: Device ESP32_2 onboarded successfully
INFO: Started profiling device ESP32_2
INFO: Profiling period expired for ESP32_2, auto-finalizing onboarding...
INFO: Baseline established for ESP32_2: 45 packets, 0.15 pps
INFO: Generated least-privilege policy for ESP32_2: 5 rules
INFO: Policy applied to SDN controller for ESP32_2
INFO: Successfully auto-finalized onboarding for ESP32_2
```

### Monitoring Thread

The monitoring thread:
- Runs every 30 seconds
- Checks all devices in active profiling
- Automatically finalizes when period expires
- Handles errors gracefully

---

## Error Handling

### Insufficient Traffic

If a device has insufficient traffic (< 5 packets) when profiling expires:
- System logs a warning
- Finalizes anyway with available data
- Policy generated from limited observations

### Device Disconnection

If a device disconnects during profiling:
- Profiling continues until period expires
- Baseline generated from available data
- Policy applied when device reconnects

### Database Migration Errors

If database migration fails:
- System logs warning but continues
- New columns may not be available
- System falls back to basic functionality

---

## Testing

### Manual Testing

1. **Test Onboarding**:
   ```python
   from identity_manager.device_onboarding import DeviceOnboarding
   
   onboarding = DeviceOnboarding()
   result = onboarding.onboard_device("TEST_DEVICE", "AA:BB:CC:DD:EE:FF")
   assert result['status'] == 'success'
   ```

2. **Test Profiling**:
   ```python
   # Wait 5 minutes or manually finalize
   result = onboarding.finalize_onboarding("TEST_DEVICE")
   assert result['status'] == 'success'
   assert 'baseline' in result
   assert 'policy' in result
   ```

3. **Test Traffic Recording**:
   ```python
   # Simulate traffic
   packet_info = {
       'size': 100,
       'dst_ip': '192.168.1.1',
       'dst_port': 80,
       'protocol': 6  # TCP
   }
   onboarding.record_traffic("TEST_DEVICE", packet_info)
   ```

### Integration Testing

Run the test suite:
```bash
cd /home/kasun/Documents/IOT-project
python -m pytest tests/test_device_onboarding.py -v
```

---

## Migration Guide

### Upgrading Existing Installations

1. **Backup Database**:
   ```bash
   cp identity.db identity.db.backup
   ```

2. **Run System**:
   - The system automatically migrates the database on startup
   - New columns are added automatically
   - Existing data is preserved

3. **Verify Migration**:
   ```python
   from identity_manager.identity_database import IdentityDatabase
   db = IdentityDatabase()
   # Check that new columns exist
   device = db.get_device("EXISTING_DEVICE")
   # Should work without errors
   ```

---

## Performance Considerations

### Monitoring Thread

- Runs every 30 seconds
- Minimal CPU usage
- Checks only active profiling devices
- Daemon thread (doesn't block shutdown)

### Traffic Recording

- Only records during profiling period
- Minimal overhead (packet parsing)
- Stored in memory during profiling
- Written to database on finalization

### Database Operations

- Migration runs once on startup
- Indexed queries for device lookup
- Efficient baseline storage (JSON)

---

## Future Enhancements

### Potential Improvements

1. **Adaptive Profiling Duration**
   - Adjust duration based on device type
   - Longer profiling for complex devices

2. **Enhanced Fingerprinting**
   - Include more device characteristics
   - Network stack fingerprinting

3. **Policy Refinement**
   - Periodic policy updates based on behavior
   - Machine learning for policy optimization

4. **Multi-Device Profiling**
   - Profile device groups together
   - Cross-device behavior analysis

---

## Troubleshooting

### Profiling Not Finalizing

**Symptoms**: Device remains in profiling state indefinitely

**Solutions**:
1. Check monitoring thread is running: `ps aux | grep OnboardingProfilingMonitor`
2. Check logs for errors
3. Manually finalize: `POST /finalize_onboarding`

### Traffic Not Being Recorded

**Symptoms**: Baseline has no traffic data

**Solutions**:
1. Verify SDN Policy Engine is connected: Check `set_onboarding_module()` called
2. Verify device is in active profiling: `GET /get_profiling_status`
3. Check SDN controller is processing packets

### Database Migration Issues

**Symptoms**: Errors about missing columns

**Solutions**:
1. Check database file permissions
2. Verify SQLite version supports ALTER TABLE
3. Manually add columns if needed

---

## References

### Related Documentation

- `docs/AUTO_ONBOARDING_DOCUMENTATION.md`: Auto-onboarding system
- `docs/ARCHITECTURE.md`: System architecture
- `docs/PROJECT_STRUCTURE.md`: Project structure

### Code Files

- `identity_manager/device_onboarding.py`: Main onboarding logic
- `identity_manager/behavioral_profiler.py`: Behavioral profiling
- `identity_manager/policy_generator.py`: Policy generation
- `ryu_controller/sdn_policy_engine.py`: SDN policy enforcement

---

## Conclusion

This implementation provides a complete, secure onboarding system for IoT devices with:

✅ Automatic behavioral profiling  
✅ Traffic pattern observation  
✅ Least-privilege policy generation  
✅ Physical identity linking  
✅ Zero-touch policy application  
✅ Simplified PKI onboarding  

The system is production-ready and provides a strong foundation for Zero Trust architecture deployment.

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: Implementation Team

