# Automatic WiFi Device Onboarding System Documentation

## Overview

The Automatic WiFi Device Onboarding System enables automatic detection and secure onboarding of new IoT devices when they connect to the Raspberry Pi WiFi network. The system monitors WiFi association events, generates unique device identifiers, creates pending approval requests, and provides an admin dashboard for device approval.

## Features

- **Automatic Device Detection**: Monitors WiFi network for new device connections via hostapd logs and ARP table
- **Secure Device ID Generation**: Creates unique device IDs using MAC address prefix + random key for enhanced security
- **Pending Approval Workflow**: New devices are marked as "pending" until admin approval
- **Admin Dashboard**: Web-based interface for reviewing and approving/rejecting devices
- **Automatic Onboarding**: On approval, triggers full onboarding process with certificate generation
- **Background Monitoring**: Continuous network monitoring service running in background
- **Approval History**: Complete audit trail of all device approval/rejection actions

## Architecture

### Components

1. **WiFi Detector** (`network_monitor/wifi_detector.py`)
   - Monitors hostapd log files for WiFi association events
   - Falls back to ARP table monitoring if logs unavailable
   - Detects new MAC addresses on the network
   - Tracks known devices to avoid duplicates

2. **Device ID Generator** (`network_monitor/device_id_generator.py`)
   - Generates unique device IDs from MAC addresses
   - Format: `DEV_<MAC_PREFIX>_<RANDOM_KEY>`
   - Example: `DEV_AA_BB_CC_A3F2K9`
   - Ensures uniqueness and security through random key component

3. **Pending Devices Manager** (`network_monitor/pending_devices.py`)
   - Manages pending device approval requests
   - SQLite database for persistence
   - Tracks device status: pending, approved, rejected, onboarded
   - Maintains approval history

4. **Auto-Onboarding Service** (`network_monitor/auto_onboarding_service.py`)
   - Main service orchestrating the onboarding workflow
   - Background thread for continuous monitoring
   - Integrates with DeviceOnboarding for certificate provisioning
   - Handles approval/rejection workflows

5. **Controller Integration** (`controller.py`)
   - API endpoints for device approval management
   - Dashboard integration
   - Service initialization and lifecycle management

6. **Admin Dashboard** (`templates/dashboard.html`)
   - "Device Approval" tab for managing pending devices
   - Real-time device list with approve/reject actions
   - Approval history viewer

## Installation

The system is automatically initialized when the controller starts. No additional installation steps are required.

### Prerequisites

- Raspberry Pi with WiFi AP mode configured
- hostapd running (for WiFi AP) or ARP table access
- Python 3.10+
- Required Python packages (already in requirements.txt)

## Configuration

### Network Monitor Configuration

Edit `network_monitor/config.py` to customize settings:

```python
# WiFi interface name
WIFI_INTERFACE = 'wlan0'  # Default WiFi AP interface

# hostapd log paths (searched in order)
HOSTAPD_LOG_PATHS = [
    '/var/log/hostapd.log',
    '/var/log/hostapd/hostapd.log',
    '/tmp/hostapd.log',
    'logs/hostapd.log'
]

# Monitoring interval (seconds)
MONITORING_INTERVAL = 2

# Device ID generation
DEVICE_ID_PREFIX = 'DEV'
DEVICE_ID_RANDOM_LENGTH = 6
DEVICE_ID_SEPARATOR = '_'

# Database path
PENDING_DEVICES_DB = 'pending_devices.db'
```

### Environment Variables

You can override configuration via environment variables:

```bash
export WIFI_INTERFACE=wlan0
export MONITORING_INTERVAL=2
```

## Usage

### Automatic Workflow

1. **Device Connects**: New IoT device connects to Raspberry Pi WiFi network
2. **Detection**: System automatically detects new MAC address
3. **ID Generation**: Unique device ID generated (MAC prefix + random key)
4. **Pending Entry**: Device added to pending approval list
5. **Admin Review**: Admin sees device in "Device Approval" dashboard tab
6. **Approval**: Admin approves or rejects device
7. **Onboarding**: If approved, automatic onboarding triggered:
   - Certificate generation
   - Database entry
   - Behavioral profiling started
   - Device can now authenticate

### Manual Device Addition

You can still manually onboard devices using the existing `/onboard` endpoint:

```bash
curl -X POST http://localhost:5000/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_5",
    "mac_address": "AA:BB:CC:DD:EE:05",
    "device_type": "sensor"
  }'
```

## API Endpoints

### Get Pending Devices

**GET** `/api/pending_devices`

Returns list of devices awaiting approval.

**Response:**
```json
{
  "status": "success",
  "devices": [
    {
      "id": 1,
      "mac_address": "AA:BB:CC:DD:EE:01",
      "device_id": "DEV_AA_BB_CC_A3F2K9",
      "detected_at": "2024-01-15 10:30:00",
      "status": "pending",
      "device_type": null,
      "device_info": null
    }
  ]
}
```

### Approve Device

**POST** `/api/approve_device`

Approves a pending device and triggers onboarding.

**Request:**
```json
{
  "mac_address": "AA:BB:CC:DD:EE:01",
  "admin_notes": "Approved for testing"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Device approved and onboarded successfully",
  "device_id": "DEV_AA_BB_CC_A3F2K9",
  "onboarding_result": {
    "status": "success",
    "certificate_path": "certs/DEV_AA_BB_CC_A3F2K9_cert.pem",
    "key_path": "certs/DEV_AA_BB_CC_A3F2K9_key.pem",
    "ca_certificate": "-----BEGIN CERTIFICATE-----\n..."
  }
}
```

### Reject Device

**POST** `/api/reject_device`

Rejects a pending device.

**Request:**
```json
{
  "mac_address": "AA:BB:CC:DD:EE:01",
  "admin_notes": "Unknown device, rejected"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Device rejected successfully"
}
```

### Get Device History

**GET** `/api/device_history?mac_address=<optional>&limit=100`

Returns device approval history.

**Query Parameters:**
- `mac_address` (optional): Filter by specific MAC address
- `limit` (optional): Maximum number of records (default: 100)

**Response:**
```json
{
  "status": "success",
  "history": [
    {
      "id": 1,
      "mac_address": "AA:BB:CC:DD:EE:01",
      "device_id": "DEV_AA_BB_CC_A3F2K9",
      "action": "approved",
      "timestamp": "2024-01-15 10:35:00",
      "admin_notes": "Approved for testing"
    }
  ]
}
```

## Admin Dashboard

### Accessing the Dashboard

1. Open web browser
2. Navigate to `http://<raspberry-pi-ip>:5000`
3. Click on "Device Approval" tab

### Dashboard Features

#### Pending Devices Section

- Lists all devices awaiting approval
- Shows device ID, MAC address, and detection timestamp
- Approve/Reject buttons for each device
- Auto-refreshes every 5 seconds when tab is active

#### Device History Section

- Complete audit trail of all approval actions
- Shows timestamp, device ID, MAC address, action (approved/rejected), and admin notes
- Color-coded status badges

### Approving a Device

1. Navigate to "Device Approval" tab
2. Review pending device information
3. Click "Approve" button
4. Confirm approval in popup dialog
5. Device is automatically onboarded with certificate generation
6. Device appears in main topology view

### Rejecting a Device

1. Navigate to "Device Approval" tab
2. Review pending device information
3. Click "Reject" button
4. Confirm rejection in popup dialog
5. Device is marked as rejected and removed from pending list

## Technical Details

### WiFi Detection Methods

The system uses multiple methods to detect new devices:

1. **hostapd Log Monitoring** (Primary)
   - Monitors `/var/log/hostapd.log` for association events
   - Parses log entries: `wlan0: STA <MAC> IEEE 802.11: authenticated`
   - Real-time detection as devices connect

2. **ARP Table Monitoring** (Fallback)
   - Checks ARP table for connected devices
   - Used when hostapd logs unavailable
   - Less real-time but still effective

### Device ID Generation Algorithm

1. Extract MAC address prefix (first 3 octets)
2. Normalize to uppercase format: `AA:BB:CC`
3. Generate random alphanumeric key (6 characters)
4. Combine: `DEV_AA_BB_CC_<RANDOM_KEY>`
5. Ensure uniqueness by checking against existing IDs

**Example:**
- MAC: `AA:BB:CC:DD:EE:FF`
- Prefix: `AA_BB_CC`
- Random Key: `A3F2K9`
- Device ID: `DEV_AA_BB_CC_A3F2K9`

### Database Schema

#### pending_devices Table

```sql
CREATE TABLE pending_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT UNIQUE NOT NULL,
    device_id TEXT NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    onboarded_at TIMESTAMP,
    device_type TEXT,
    device_info TEXT,
    admin_notes TEXT
)
```

#### device_history Table

```sql
CREATE TABLE device_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT NOT NULL,
    device_id TEXT,
    action TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin_notes TEXT
)
```

### Service Lifecycle

1. **Initialization**: Service starts when controller initializes
2. **Device Loading**: Loads known devices from identity database
3. **Monitoring Loop**: Continuous background monitoring (2-second intervals)
4. **Event Handling**: New device detection triggers pending entry creation
5. **Approval Processing**: Admin approval triggers onboarding workflow

## Troubleshooting

### Devices Not Detected

**Problem**: New devices connecting but not appearing in pending list

**Solutions**:
1. Check hostapd log file exists and is readable:
   ```bash
   ls -l /var/log/hostapd.log
   sudo chmod 644 /var/log/hostapd.log
   ```

2. Verify WiFi interface name in config:
   ```python
   WIFI_INTERFACE = 'wlan0'  # Check actual interface name
   ```

3. Check ARP table access:
   ```bash
   arp -n -i wlan0
   ```

4. Review service logs in controller output

### Approval Not Working

**Problem**: Approve button doesn't trigger onboarding

**Solutions**:
1. Check browser console for JavaScript errors
2. Verify API endpoint is accessible:
   ```bash
   curl http://localhost:5000/api/pending_devices
   ```

3. Check controller logs for errors
4. Verify onboarding module is initialized

### Certificate Generation Fails

**Problem**: Device approved but certificate generation fails

**Solutions**:
1. Check `certs/` directory permissions:
   ```bash
   ls -ld certs/
   chmod 755 certs/
   ```

2. Verify cryptography package installed:
   ```bash
   pip install cryptography
   ```

3. Check CA certificate exists:
   ```bash
   ls -l certs/ca_cert.pem
   ```

### Service Not Starting

**Problem**: Auto-onboarding service not initializing

**Solutions**:
1. Check controller startup logs for errors
2. Verify all dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

3. Check database file permissions:
   ```bash
   ls -l pending_devices.db
   ```

## Security Considerations

1. **Device ID Security**: Random key component prevents MAC address enumeration
2. **Approval Required**: All devices require admin approval before onboarding
3. **Certificate-Based Auth**: Approved devices receive X.509 certificates
4. **Audit Trail**: Complete history of all approval actions
5. **Network Isolation**: Pending devices are not fully onboarded until approved

## Best Practices

1. **Regular Review**: Check pending devices regularly
2. **Documentation**: Add admin notes when approving/rejecting devices
3. **Monitoring**: Monitor approval history for suspicious patterns
4. **Network Security**: Ensure WiFi AP is properly secured
5. **Backup**: Regularly backup `pending_devices.db` and `identity.db`

## Integration with Existing System

The automatic onboarding system integrates seamlessly with existing components:

- **DeviceOnboarding**: Uses existing onboarding module for certificate generation
- **Identity Database**: Shares device information with identity management
- **Controller**: Extends existing Flask controller with new endpoints
- **Dashboard**: Adds new tab to existing dashboard interface
- **Topology**: Approved devices appear in network topology view

## Future Enhancements

Potential improvements for future versions:

1. **Device Fingerprinting**: Identify device type from network traffic patterns
2. **Auto-Approval Rules**: Configurable rules for automatic approval
3. **Email Notifications**: Alert admins when new devices detected
4. **Device Profiles**: Pre-configured device profiles for common IoT devices
5. **Bulk Operations**: Approve/reject multiple devices at once
6. **Time-Based Policies**: Auto-reject devices detected outside business hours

## Support

For issues or questions:

1. Check controller logs: `logs/controller.log`
2. Review system logs: `journalctl -u hostapd`
3. Test API endpoints manually using curl
4. Verify network configuration and permissions

## Changelog

### Version 1.0.0 (Initial Release)

- Automatic WiFi device detection
- Device ID generation with MAC + random key
- Pending approval workflow
- Admin dashboard integration
- API endpoints for device management
- Approval history tracking
- Integration with existing onboarding system

