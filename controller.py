def get_pending_manager():
    """Return a pending device manager if available."""
    if auto_onboarding_service and hasattr(auto_onboarding_service, "pending_manager"):
        return auto_onboarding_service.pending_manager
    return pending_manager

"""
IoT Security Framework Controller
Advanced IoT Security Framework with Software-Defined Networking
"""

import matplotlib
matplotlib.use('Agg')
from flask import Flask, request, render_template, send_file, jsonify
import json
import matplotlib.pyplot as plt
import io
import time
import uuid
from datetime import datetime
import random
import threading
import os
import logging

# Try to import DeviceOnboarding, but make it optional
try:
    from identity_manager.device_onboarding import DeviceOnboarding
    ONBOARDING_AVAILABLE = True
except ImportError as e:
    ONBOARDING_AVAILABLE = False
    print(f"⚠️  Device onboarding not available: {e}")
    print("   System will use static device authorization")
    DeviceOnboarding = None

# Try to import Auto-Onboarding Service, but make it optional
try:
    from network_monitor.auto_onboarding_service import AutoOnboardingService
    from network_monitor.pending_devices import PendingDeviceManager
    AUTO_ONBOARDING_AVAILABLE = True
    PENDING_MANAGER_AVAILABLE = True
except ImportError as e:
    AUTO_ONBOARDING_AVAILABLE = False
    PENDING_MANAGER_AVAILABLE = False
    print(f"⚠️  Auto-onboarding service not available: {e}")
    AutoOnboardingService = None
    PendingDeviceManager = None

# Try to import ML engine, but make it optional
try:
    from ml_security_engine import initialize_ml_engine, get_ml_engine
    # Check if TensorFlow is actually available
    try:
        import tensorflow as tf
        ML_ENGINE_AVAILABLE = True
    except ImportError:
        ML_ENGINE_AVAILABLE = False
        print("⚠️  TensorFlow not available. ML model features will be limited.")
        print("   System will run with heuristic-based detection")
except ImportError as e:
    ML_ENGINE_AVAILABLE = False
    print(f"⚠️  ML engine not available: {e}")
    print("   System will run without ML-based detection")
    # Create dummy functions
    def initialize_ml_engine():
        return None
    def get_ml_engine():
        return None

app = Flask(__name__)

# Device authorization (static for now, can be dynamic)
authorized_devices = {}
device_data = {}
timestamps = []
last_seen = {}
device_tokens = {}  # {device_id: {"token": token, "last_activity": timestamp}}
packet_counts = {}  # For rate limiting
SESSION_TIMEOUT = 300  # 5 minutes
RATE_LIMIT = 60  # Max 60 packets per minute per device

# Track failed token requests for manual approval
failed_token_requests = {}  # {device_id: {"mac_address": mac, "last_request": timestamp, "count": count}}

# Store MAC addresses dynamically
mac_addresses = {
    # MAC addresses will be populated dynamically as devices connect
}

# SDN Policies
sdn_policies = {
    "packet_inspection": False,
    "traffic_shaping": False,
    "dynamic_routing": False
}

# Simulated policy logs
policy_logs = []

# Simulated SDN metrics
sdn_metrics = {
    "control_plane_latency": 0,  # ms
    "data_plane_throughput": 0,  # Mbps
    "policy_enforcement_rate": 0  # %
}

# Suspicious device alerts for dashboard
suspicious_device_alerts = []  # List of alert dictionaries

# Initialize ML Security Engine
ml_engine = None
ml_monitoring_active = False

# Security flag: disallow insecure auto-authorization unless explicitly enabled
ALLOW_INSECURE_AUTO_AUTH = os.getenv("ALLOW_INSECURE_AUTO_AUTH", "false").lower() == "true"

# Initialize Device Onboarding System
onboarding = None
if ONBOARDING_AVAILABLE:
    try:
        certs_dir = os.path.join(os.path.dirname(__file__), 'certs')
        db_path = os.path.join(os.path.dirname(__file__), 'identity.db')
        onboarding = DeviceOnboarding(certs_dir=certs_dir, db_path=db_path)
        print("✅ Device onboarding system initialized")
    except Exception as e:
        print(f"⚠️  Failed to initialize device onboarding: {e}")
        print("   System will use static device authorization")
        onboarding = None
        ONBOARDING_AVAILABLE = False
else:
    print("⚠️  Device onboarding not available - using static authorization")

# Hydrate authorized_devices from database if available (Persistence Fix)
if ONBOARDING_AVAILABLE and onboarding:
    try:
        print("🔄 Hydrating authorized devices from database...")
        stored_devices = onboarding.identity_db.get_all_devices()
        count = 0
        for device in stored_devices:
            # If device is active or has a valid certificate, authorized it
            if device.get('status') == 'active' or device.get('certificate_path'):
                device_id = device['device_id']
                authorized_devices[device_id] = True
                
                # Restore MAC address
                if device.get('mac_address'):
                    mac_addresses[device_id] = device['mac_address']
                
                # Restore last_seen if available (to prevent immediate timeout)
                if device.get('last_seen'):
                    try:
                        # Handle both string (ISO) and float/int timestamps
                        ls_val = device['last_seen']
                        if isinstance(ls_val, str):
                            import datetime as dt_module
                            # Naive parse just for restoration
                            ls_time = time.mktime(dt_module.datetime.fromisoformat(ls_val.replace('Z', '+00:00')).timetuple())
                            last_seen[device_id] = ls_time
                        else:
                            last_seen[device_id] = float(ls_val)
                    except Exception:
                        last_seen[device_id] = time.time()
                
                # Initialize data structures
                if device_id not in device_data:
                    device_data[device_id] = []
                if device_id not in packet_counts:
                    packet_counts[device_id] = []
                    
                count += 1
        print(f"✅ Restored {count} authorized devices from persistent storage")
    except Exception as e:
        print(f"⚠️  Failed to hydrate authorized devices: {e}")

# Initialize Auto-Onboarding Service
auto_onboarding_service = None
pending_manager = None
if AUTO_ONBOARDING_AVAILABLE:
    try:
        auto_onboarding_service = AutoOnboardingService(
            onboarding_module=onboarding,  # may be None; service still manages pending list
            identity_db=onboarding.identity_db if onboarding else None
        )
        pending_manager = auto_onboarding_service.pending_manager
        # Start the service
        auto_onboarding_service.start()
        print("✅ Auto-onboarding service initialized and started")
    except Exception as e:
        print(f"⚠️  Failed to initialize auto-onboarding service: {e}")
        auto_onboarding_service = None
        if PENDING_MANAGER_AVAILABLE:
            try:
                pending_manager = PendingDeviceManager()
                print("ℹ️  Fallback pending device manager initialized")
            except Exception as pe:
                print(f"⚠️  Failed to initialize fallback pending device manager: {pe}")
                pending_manager = None
        AUTO_ONBOARDING_AVAILABLE = False
elif PENDING_MANAGER_AVAILABLE:
    try:
        pending_manager = PendingDeviceManager()
        print("ℹ️  Pending device manager initialized (no auto-onboarding service)")
    except Exception as pe:
        print(f"⚠️  Failed to initialize pending device manager: {pe}")


@app.route('/ml/health')
def ml_health():
    """Get ML engine health status"""
    if not ML_ENGINE_AVAILABLE:
        return json.dumps({
            'status': 'unavailable',
            'message': 'ML engine not available (TensorFlow not installed)'
        }), 503
    
    try:
        global ml_engine
        if not ml_engine:
            return json.dumps({
                'status': 'error',
                'message': 'ML engine not initialized'
            }), 503

        network_stats = getattr(ml_engine, 'network_stats', {})
        is_loaded = getattr(ml_engine, 'is_loaded', False)
        
        health_data = {
            'status': 'healthy' if is_loaded else 'error',
            'uptime': network_stats.get('uptime'),
            'last_health_check': network_stats.get('last_health_check'),
            'model_status': network_stats.get('model_status'),
            'total_packets_processed': network_stats.get('total_packets'),
            'detection_accuracy': network_stats.get('detection_accuracy')
        }

        return json.dumps(health_data), 200 if is_loaded else 503

    except Exception as e:
        app.logger.error(f"Health check error: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

def is_maintenance_window():
    current_hour = datetime.now().hour
    return 2 <= current_hour < 3  # Simulated maintenance window

def simulate_policy_enforcement(device_id):
    if sdn_policies["packet_inspection"] and random.random() > 0.8:
        policy_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Blocked packet from {device_id} due to packet inspection policy")
        return False
    if sdn_policies["traffic_shaping"] and random.random() > 0.9:
        policy_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Delayed packet from {device_id} due to traffic shaping policy")
        time.sleep(0.1)  # Simulate delay
    if sdn_policies["dynamic_routing"]:
        policy_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Rerouted packet from {device_id} via dynamic routing policy")
    return True

def update_sdn_metrics():
    """Update SDN metrics with real data from Ryu controller if available"""
    # TODO: Integrate with Ryu controller to get real SDN metrics
    # For now, keep metrics at 0 if no real data is available
    # Real metrics would come from Ryu controller API or flow statistics
    pass

@app.route('/onboard', methods=['POST'])
def onboard_device():
    """
    Onboard a new IoT device with certificate provisioning
    
    Request JSON:
    {
        "device_id": "DEVICE_ID",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "device_type": "sensor" (optional),
        "device_info": "Additional info" (optional)
    }
    
    Returns:
        Onboarding result with certificate paths and CA certificate
    """
    if not ONBOARDING_AVAILABLE or not onboarding:
        return json.dumps({
            'status': 'error',
            'message': 'Device onboarding system not available'
        }), 503
    
    try:
        data = request.json
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        device_type = data.get('device_type')
        device_info = data.get('device_info')
        
        if not device_id or not mac_address:
            return json.dumps({
                'status': 'error',
                'message': 'Missing device_id or mac_address'
            }), 400
        
        # Onboard the device
        result = onboarding.onboard_device(
            device_id=device_id,
            mac_address=mac_address,
            device_type=device_type,
            device_info=device_info
        )
        
        if result['status'] == 'success':
            # Store MAC address for topology
            mac_addresses[device_id] = mac_address
            # Initialize device tracking
            if device_id not in device_data:
                device_data[device_id] = []
            if device_id not in last_seen:
                last_seen[device_id] = time.time()
            if device_id not in packet_counts:
                packet_counts[device_id] = []
            
            app.logger.info(f"Device {device_id} onboarded. Profiling will auto-finalize after 5 minutes.")
            return json.dumps(result), 200
        else:
            return json.dumps(result), 400
            
    except Exception as e:
        app.logger.error(f"Onboarding error: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/finalize_onboarding', methods=['POST'])
def finalize_onboarding():
    """
    Manually finalize onboarding for a device (establish baseline and generate policy)
    
    Request JSON:
    {
        "device_id": "DEVICE_ID"
    }
    
    Returns:
        Finalization result with baseline and policy
    """
    if not ONBOARDING_AVAILABLE or not onboarding:
        return json.dumps({
            'status': 'error',
            'message': 'Device onboarding system not available'
        }), 503
    
    try:
        data = request.json
        device_id = data.get('device_id')
        
        if not device_id:
            return json.dumps({
                'status': 'error',
                'message': 'Missing device_id'
            }), 400
        
        # Finalize onboarding
        result = onboarding.finalize_onboarding(device_id)
        
        if result['status'] == 'success':
            app.logger.info(f"Onboarding finalized for {device_id}. Baseline and policy generated.")
            return json.dumps(result), 200
        else:
            return json.dumps(result), 400
            
    except Exception as e:
        app.logger.error(f"Finalization error: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get_profiling_status', methods=['GET'])
def get_profiling_status():
    """
    Get profiling status for a device
    
    Query parameters:
        device_id: Device identifier
    
    Returns:
        Profiling status information
    """
    if not ONBOARDING_AVAILABLE or not onboarding:
        return json.dumps({
            'status': 'error',
            'message': 'Device onboarding system not available'
        }), 503
    
    try:
        device_id = request.args.get('device_id')
        
        if not device_id:
            return json.dumps({
                'status': 'error',
                'message': 'Missing device_id parameter'
            }), 400
        
        # Get profiling status
        profiler = onboarding.profiler
        profile_status = profiler.get_profiling_status(device_id)
        
        if profile_status:
            elapsed = profile_status.get('elapsed_time', 0)
            remaining = max(0, profiler.profiling_duration - elapsed)
            return json.dumps({
                'status': 'success',
                'device_id': device_id,
                'is_profiling': True,
                'elapsed_time': elapsed,
                'remaining_time': remaining,
                'packet_count': profile_status.get('packet_count', 0),
                'byte_count': profile_status.get('byte_count', 0)
            }), 200
        else:
            # Check if device has baseline (profiling completed)
            baseline = profiler.get_baseline(device_id)
            if baseline:
                return json.dumps({
                    'status': 'success',
                    'device_id': device_id,
                    'is_profiling': False,
                    'baseline_established': True,
                    'baseline': baseline
                }), 200
            else:
                return json.dumps({
                    'status': 'success',
                    'device_id': device_id,
                    'is_profiling': False,
                    'baseline_established': False,
                    'message': 'Device not currently being profiled'
                }), 200
            
    except Exception as e:
        app.logger.error(f"Error getting profiling status: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get_token', methods=['POST'])
def get_token():
    """
    Get authentication token for device
    
    First checks if device is onboarded (certificate-based).
    Falls back to static authorized_devices list for backward compatibility.
    Auto-authorizes new devices if they provide a valid MAC address.
    """
    try:
        data = request.json
        if not data:
            app.logger.error("Token request: No JSON data received")
            return json.dumps({'error': 'Invalid JSON data'}), 400
    except Exception as e:
        app.logger.error(f"Token request: JSON parsing error: {e}")
        return json.dumps({'error': 'Invalid JSON format'}), 400
    
    device_id = data.get('device_id')
    mac_address = data.get('mac_address')  # Get MAC address from request
    
    if not device_id:
        app.logger.warning("Token request missing device_id")
        app.logger.warning(f"Received data: {data}")
        return json.dumps({'error': 'Missing device_id'}), 400
    
    app.logger.info(f"Token request from device_id: {device_id}, MAC: {mac_address}")
    app.logger.debug(f"Full request data: {data}")
    
    # Normalize MAC for downstream checks
    if isinstance(mac_address, str):
        mac_address = mac_address.strip()
    device_authorized = False
    pending_device = None
    
    # Check if device is onboarded (certificate-based authentication)
    if ONBOARDING_AVAILABLE and onboarding:
        try:
            device_info = onboarding.get_device_info(device_id)
            if device_info:
                # Device is onboarded - verify certificate
                if onboarding.verify_device_certificate(device_id):
                    device_authorized = True
                    # Update MAC address from database if not provided
                    if not mac_address and device_info.get('mac_address'):
                        mac_address = device_info['mac_address']
                    app.logger.info(f"Device {device_id} authorized via certificate-based onboarding")
                else:
                    app.logger.warning(f"Device {device_id} certificate verification failed")
        except Exception as e:
            app.logger.error(f"Error checking onboarding database: {e}")
    
    # Check identity database entry if certificate check did not authorize
    if not device_authorized and ONBOARDING_AVAILABLE and onboarding and hasattr(onboarding, "identity_db"):
        try:
            identity_record = onboarding.identity_db.get_device(device_id)
            if not identity_record and mac_address:
                identity_record = onboarding.identity_db.get_device_by_mac(mac_address)
            if identity_record:
                status = identity_record.get('status', 'active')
                if status == 'revoked':
                    app.logger.warning(f"Device {device_id} found in identity DB but status is revoked")
                else:
                    device_authorized = True
                    if not mac_address and identity_record.get('mac_address'):
                        mac_address = identity_record['mac_address']
                    app.logger.info(f"Device {device_id} authorized via identity database (status={status})")
        except Exception as e:
            app.logger.error(f"Error checking identity database: {e}")
    
    # Enforce pending-approval workflow if pending manager is available
    if not device_authorized:
        pending_manager = get_pending_manager()
        if pending_manager:
            try:
                if mac_address:
                    pending_device = pending_manager.get_device_by_mac(mac_address)
                if pending_device:
                    pending_status = pending_device.get('status')
                    if pending_status == pending_manager.STATUS_PENDING:
                        app.logger.warning(f"Device {device_id} ({mac_address}) is pending approval")
                        return json.dumps({'error': 'Device pending approval'}), 403
                    if pending_status == pending_manager.STATUS_REJECTED:
                        app.logger.warning(f"Device {device_id} ({mac_address}) was rejected")
                        return json.dumps({'error': 'Device rejected'}), 403
                    if pending_status in (pending_manager.STATUS_APPROVED, pending_manager.STATUS_ONBOARDED):
                        device_authorized = True
                        app.logger.info(f"Device {device_id} authorized after approval (status={pending_status})")
            except Exception as e:
                app.logger.error(f"Error checking pending device status: {e}")
    
    # Fallback to static authorized_devices list
    if not device_authorized:
        device_authorized = authorized_devices.get(device_id, False)
        if device_authorized:
            app.logger.info(f"Device {device_id} authorized via static authorized_devices list")
    
    # Auto-authorize new devices only when explicitly allowed for testing
    if not device_authorized and ALLOW_INSECURE_AUTO_AUTH:
        if mac_address:
            # Validate MAC address format (more flexible check)
            # ESP8266/ESP32 MAC: "AA:BB:CC:DD:EE:FF" or "AA-BB-CC-DD-EE-FF" or "AABBCCDDEEFF"
            mac_clean = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
            is_valid_mac = len(mac_clean) == 12 and all(c in '0123456789ABCDEF' for c in mac_clean)
            
            if is_valid_mac:
                # Auto-add to authorized_devices for easy onboarding
                authorized_devices[device_id] = True
                device_authorized = True
                app.logger.info(f"✅ Auto-authorized new device {device_id} with MAC {mac_address}")
                # Initialize device tracking structures
                if device_id not in device_data:
                    device_data[device_id] = []
                if device_id not in last_seen:
                    last_seen[device_id] = 0
                if device_id not in packet_counts:
                    packet_counts[device_id] = []
            else:
                app.logger.warning(f"Invalid MAC address format: {mac_address} (cleaned: {mac_clean}, length: {len(mac_clean)})")
        else:
            app.logger.warning(f"⚠️  No MAC address provided for device {device_id}; cannot auto-authorize even though ALLOW_INSECURE_AUTO_AUTH is enabled")
    
    if not device_authorized:
        # Ensure the device is present in pending list so the dashboard can show it
        manager = get_pending_manager()
        if manager and mac_address:
            try:
                existing_pending = manager.get_device_by_mac(mac_address)
                if not existing_pending:
                    added = manager.add_pending_device(
                        mac_address=mac_address,
                        device_id=device_id,
                        device_type=None,
                        device_info=None
                    )
                    if added:
                        app.logger.info(f"Device {device_id} ({mac_address}) added to pending approval from token flow")
                else:
                    app.logger.debug(f"Device {device_id} ({mac_address}) already present in pending list")
            except Exception as e:
                app.logger.error(f"Failed to add device to pending list: {e}")

        # Track failed request for dashboard display
        if device_id not in failed_token_requests:
            failed_token_requests[device_id] = {
                "mac_address": mac_address or "Unknown",
                "first_request": time.time(),
                "last_request": time.time(),
                "count": 1
            }
        else:
            failed_token_requests[device_id]["last_request"] = time.time()
            failed_token_requests[device_id]["count"] += 1
            if mac_address and failed_token_requests[device_id]["mac_address"] == "Unknown":
                failed_token_requests[device_id]["mac_address"] = mac_address
        
        app.logger.warning(f"❌ Device {device_id} not authorized - token request rejected")
        app.logger.warning(f"   MAC provided: {mac_address}")
        app.logger.warning(f"   MAC type: {type(mac_address)}")
        app.logger.warning(f"   Device exists in authorized_devices: {device_id in authorized_devices}")
        app.logger.warning(f"   Current authorized_devices keys: {list(authorized_devices.keys())}")
        return json.dumps({'error': 'Device not authorized'}), 403
    
    # Generate token for authorized device
    token = str(uuid.uuid4())
    device_tokens[device_id] = {"token": token, "last_activity": time.time()}
    if mac_address:  # Store the MAC address if provided
        mac_addresses[device_id] = mac_address
    
    app.logger.info(f"Token generated successfully for device {device_id}")
    return json.dumps({'token': token})

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    device_id = data.get('device_id')
    token = data.get('token')
    if not device_id or not token:
        return json.dumps({'error': 'Missing device_id or token'}), 400

    if device_id not in device_tokens or device_tokens[device_id]["token"] != token:
        return json.dumps({'device_id': device_id, 'authorized': False})

    current_time = time.time()
    last_activity = device_tokens[device_id]["last_activity"]
    if current_time - last_activity > SESSION_TIMEOUT:
        device_tokens.pop(device_id)
        return json.dumps({'device_id': device_id, 'authorized': False})

    device_tokens[device_id]["last_activity"] = current_time

    # Start per-device ML monitoring on first successful auth in this session
    if ML_ENGINE_AVAILABLE:
        global ml_engine, ml_monitoring_active
        if ml_engine is None:
            ml_engine = initialize_ml_engine()
        if ml_engine and hasattr(ml_engine, 'is_loaded') and ml_engine.is_loaded and not ml_monitoring_active:
            # Begin background monitoring
            if hasattr(ml_engine, 'start_monitoring'):
                ml_engine.start_monitoring()
            ml_monitoring_active = True
    return json.dumps({'device_id': device_id, 'authorized': True})

@app.route('/data', methods=['POST'])
def data():
    """
    Receive data from IoT device
    
    Verifies device is onboarded or in authorized list before accepting data.
    """
    data = request.json
    device_id = data.get('device_id')
    token = data.get('token')
    packet_time = data.get('timestamp')
    data_value = data.get('data', 0)

    if not device_id or not token or not packet_time:
        return json.dumps({'status': 'rejected', 'reason': 'Missing required fields'})

    # Verify token
    if device_id not in device_tokens or device_tokens[device_id]["token"] != token:
        return json.dumps({'status': 'rejected', 'reason': 'Invalid token'})
    
    # Verify device is authorized (onboarded or in static list)
    device_authorized = False
    if ONBOARDING_AVAILABLE and onboarding:
        try:
            device_info = onboarding.get_device_info(device_id)
            if device_info and device_info.get('status') != 'revoked':
                # Device is onboarded and not revoked
                device_authorized = True
                # Update last_seen in database
                onboarding.identity_db.update_last_seen(device_id)
        except Exception as e:
            app.logger.error(f"Error checking device authorization: {e}")
    
    # Fallback to static authorized_devices list
    if not device_authorized:
        device_authorized = authorized_devices.get(device_id, False)
    
    if not device_authorized:
        return json.dumps({'status': 'rejected', 'reason': 'Device not authorized'})

    current_time = time.time()
    last_activity = device_tokens[device_id]["last_activity"]
    if current_time - last_activity > SESSION_TIMEOUT:
        device_tokens.pop(device_id)
        return json.dumps({'status': 'rejected'})

    if is_maintenance_window():
        return json.dumps({'status': 'rejected', 'reason': 'Maintenance window'})

    packet_counts[device_id].append(current_time)
    packet_counts[device_id] = [t for t in packet_counts[device_id] if current_time - t <= 60]
    if len(packet_counts[device_id]) > RATE_LIMIT:
        return json.dumps({'status': 'rejected', 'reason': 'Rate limit exceeded'})

    # Apply SDN policies
    if not simulate_policy_enforcement(device_id):
        return json.dumps({'status': 'rejected', 'reason': 'SDN policy violation'})

    device_tokens[device_id]["last_activity"] = current_time
    last_seen[device_id] = current_time
    device_data[device_id].append(1)
    if len(timestamps) == 0 or current_time - timestamps[-1] > 1:
        timestamps.append(current_time)
    # Feed packet to ML engine for anomaly detection with device context
    global ml_engine
    try:
        if ml_engine and ml_engine.is_loaded:
            result = ml_engine.predict_attack({
                'device_id': device_id,
                'size': data.get('size', 0),
                'protocol': data.get('protocol', 6),
                'src_port': data.get('src_port', 0),
                'dst_port': data.get('dst_port', 0),
                'rate': data.get('rate', 0.0),
                'duration': data.get('duration', 0.0),
                'bps': data.get('bps', 0.0),
                'pps': data.get('pps', 0.0),
                'tcp_flags': data.get('tcp_flags', 0),
                'window_size': data.get('window_size', 0),
                'ttl': data.get('ttl', 64),
                'fragment_offset': data.get('fragment_offset', 0),
                'ip_length': data.get('ip_length', 0),
                'tcp_length': data.get('tcp_length', 0),
                'udp_length': data.get('udp_length', 0)
            })
            
            # Check if ML detected high-confidence attack and trigger redirection
            if result and result.get('is_attack', False) and result.get('confidence', 0) > 0.8:
                # High confidence attack detected - create alert
                severity = 'high' if result.get('confidence', 0) > 0.9 else 'medium'
                create_suspicious_device_alert(
                    device_id=device_id,
                    reason='ml_detection',
                    severity=severity,
                    redirected=True
                )
                app.logger.warning(f"High-confidence ML attack detected for {device_id}: {result.get('attack_type')}")
    except Exception as e:
        # Non-fatal for data ingestion; continue normally
        app.logger.warning(f"ML prediction error (non-fatal): {str(e)}")

    return json.dumps({'status': 'accepted'})

def generate_graph():
    plt.figure(figsize=(8, 4))
    has_data = False
    for device in device_data:
        if len(device_data[device]) > 0:
            plt.plot(timestamps[-len(device_data[device]):], device_data[device], label=device)
            has_data = True
    if has_data:
        plt.xlabel('Time (s)')
        plt.ylabel('Packets Received')
        plt.legend()
        plt.grid(True)
    else:
        plt.text(0.5, 0.5, 'No data to display', horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

@app.route('/')
def dashboard():
    return render_template('dashboard.html', devices=authorized_devices, data={k: sum(v) for k, v in device_data.items()})

@app.route('/graph')
def graph():
    return send_file(generate_graph(), mimetype='image/png')

@app.route('/get_data')
def get_data():
    current_time = time.time()
    data = {}
    for device in device_data:
        packet_count = sum(device_data[device])
        device_packet_counts = [t for t in packet_counts[device] if current_time - t <= 60]
        rate_limit_status = f"{len(device_packet_counts)}/{RATE_LIMIT}"
        blocked_reason = "Maintenance window" if is_maintenance_window() else None
        data[device] = {
            "packets": packet_count,
            "rate_limit_status": rate_limit_status,
            "blocked_reason": blocked_reason
        }
    return json.dumps(data)

@app.route('/update', methods=['POST'])
def update_auth():
    device_id = request.form['device_id']
    action = request.form['action']
    authorized_devices[device_id] = (action == 'authorize')
    if action == 'revoke' and device_id in device_tokens:
        device_tokens.pop(device_id)
    return dashboard()

@app.route('/api/failed_token_requests', methods=['GET'])
def get_failed_token_requests():
    """
    Get list of devices that requested tokens but were rejected
    
    Returns:
        List of failed token requests for manual approval
    """
    try:
        current_time = time.time()
        devices = []
        
        for device_id, info in failed_token_requests.items():
            # Only show requests from last 24 hours
            if current_time - info["last_request"] < 86400:
                devices.append({
                    "device_id": device_id,
                    "mac_address": info["mac_address"],
                    "first_request": info["first_request"],
                    "last_request": info["last_request"],
                    "request_count": info["count"],
                    "time_since_last": int(current_time - info["last_request"])
                })
        
        # Sort by most recent first
        devices.sort(key=lambda x: x["last_request"], reverse=True)
        
        return json.dumps({
            'status': 'success',
            'devices': devices
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting failed token requests: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e),
            'devices': []
        }), 500

@app.route('/api/authorize_device', methods=['POST'])
def api_authorize_device():
    """
    API endpoint to authorize or revoke a device
    
    Request JSON:
    {
        "device_id": "ESP32_5",
        "mac_address": "AA:BB:CC:DD:EE:FF" (optional),
        "action": "authorize" or "revoke" (optional, default: "authorize")
    }
    
    Returns:
        Authorization result
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        mac_address = data.get('mac_address')
        
        if not device_id:
            return json.dumps({
                'status': 'error',
                'message': 'Missing device_id'
            }), 400
        
        # Check if action is 'revoke'
        action = data.get('action', 'authorize')
        
        if action == 'revoke':
            # Revoke device authorization
            authorized_devices[device_id] = False
            
            # Remove device tokens
            if device_id in device_tokens:
                del device_tokens[device_id]
            
            app.logger.info(f"Device {device_id} revoked via API")
            
            return json.dumps({
                'status': 'success',
                'message': f'Device {device_id} revoked successfully',
                'device_id': device_id
            }), 200
        else:
            # Authorize device
            authorized_devices[device_id] = True
            
            # Initialize device tracking structures
            if device_id not in device_data:
                device_data[device_id] = []
            if device_id not in last_seen:
                last_seen[device_id] = time.time()
            if device_id not in packet_counts:
                packet_counts[device_id] = []
            
            # Store MAC address if provided
            if mac_address:
                mac_addresses[device_id] = mac_address
            
            # Remove from failed requests if it was there
            if device_id in failed_token_requests:
                del failed_token_requests[device_id]
            
            app.logger.info(f"Device {device_id} manually authorized via API")
            
            return json.dumps({
                'status': 'success',
                'message': f'Device {device_id} authorized successfully',
                'device_id': device_id
            }), 200
        
    except Exception as e:
        app.logger.error(f"Error authorizing device: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/update_policy', methods=['POST'])
def update_policy():
    policy = request.form['policy']
    action = request.form['action']
    sdn_policies[policy] = (action == 'enable')
    policy_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {policy.replace('_', ' ').title()} policy {'enabled' if action == 'enable' else 'disabled'}")
    return dashboard()

@app.route('/get_topology')
def get_topology():
    return json.dumps(last_seen)

@app.route('/get_topology_with_mac')
def get_topology_with_mac():
    """
    Get network topology with MAC addresses
    
    Uses onboarding database to get device list, merges with last_seen tracking.
    """
    current_time = time.time()
    topology = {
        "nodes": [],
        "edges": []
    }
    
    # Add gateway node (always online/connected)
    topology["nodes"].append({
        "id": "ESP32_Gateway",
        "label": "Gateway",
        "mac": mac_addresses.get("ESP32_Gateway", "A0:B1:C2:D3:E4:F5"),
        "online": True,
        "status": "active",
        "type": "gateway",
        "last_seen": current_time,
        "packets": 0
    })
    
    # Get devices from onboarding database if available
    devices_from_db = {}
    if ONBOARDING_AVAILABLE and onboarding:
        try:
            db_devices = onboarding.identity_db.get_all_devices()
            for device in db_devices:
                devices_from_db[device['device_id']] = device
                # Store MAC address if not already stored
                if device['device_id'] not in mac_addresses and device.get('mac_address'):
                    mac_addresses[device['device_id']] = device['mac_address']
        except Exception as e:
            app.logger.error(f"Error getting devices from database: {e}")
    
    # Merge database devices with last_seen tracking and authorized devices
    # Include authorized devices so they appear in topology even before sending data
    all_device_ids = set(list(last_seen.keys()) + list(devices_from_db.keys()) + list(authorized_devices.keys()))
    
    # Add ESP32 device nodes and edges to gateway
    for device_id in all_device_ids:
        # Skip gateway (already added)
        if device_id == "ESP32_Gateway":
            continue
            
        # Get last_seen time (from tracking or database)
        last_seen_time = last_seen.get(device_id, 0)
        
        # If device is authorized but not in last_seen, initialize it
        if device_id in authorized_devices and device_id not in last_seen:
            last_seen[device_id] = current_time  # Mark as just seen
            last_seen_time = current_time
            # Initialize other tracking structures if needed
            if device_id not in device_data:
                device_data[device_id] = []
            if device_id not in packet_counts:
                packet_counts[device_id] = []
        
        if device_id in devices_from_db and devices_from_db[device_id].get('last_seen'):
            # Try to parse database timestamp if available
            try:
                db_timestamp = devices_from_db[device_id]['last_seen']
                if isinstance(db_timestamp, str):
                    from datetime import datetime
                    db_time = datetime.fromisoformat(db_timestamp.replace('Z', '+00:00'))
                    last_seen_time = db_time.timestamp()
                elif db_timestamp:
                    last_seen_time = float(db_timestamp)
            except:
                pass
        
        online = (current_time - last_seen_time) < 10
        
        # Get device info from database if available
        device_info = devices_from_db.get(device_id, {})
        device_status = device_info.get('status', 'active' if online else 'inactive')
        
        # Get MAC address (from database, mac_addresses dict, or default)
        mac = (mac_addresses.get(device_id) or 
               device_info.get('mac_address') or 
               "Unknown")
        
        topology["nodes"].append({
            "id": device_id,
            "label": device_id,
            "mac": mac,
            "online": online,
            "status": device_status,
            "type": "device",
            "last_seen": last_seen_time,
            "packets": sum(device_data.get(device_id, [])),
            "onboarded": device_id in devices_from_db
        })
        
        # Only add edge if device is online/connected
        if online and device_status != 'revoked':
            topology["edges"].append({
                "from": device_id,
                "to": "ESP32_Gateway"
            })
    
    return json.dumps(topology)

@app.route('/verify_certificate', methods=['POST'])
def verify_certificate():
    """
    Verify device certificate
    
    Request JSON:
    {
        "device_id": "DEVICE_ID"
    }
    
    Returns:
        Certificate verification status
    """
    if not ONBOARDING_AVAILABLE or not onboarding:
        return json.dumps({
            'status': 'error',
            'message': 'Device onboarding system not available'
        }), 503
    
    try:
        data = request.json
        device_id = data.get('device_id')
        
        if not device_id:
            return json.dumps({
                'status': 'error',
                'message': 'Missing device_id'
            }), 400
        
        # Verify certificate
        is_valid = onboarding.verify_device_certificate(device_id)
        device_info = onboarding.get_device_info(device_id)
        
        return json.dumps({
            'status': 'success',
            'device_id': device_id,
            'certificate_valid': is_valid,
            'device_status': device_info.get('status') if device_info else None,
            'onboarded_at': device_info.get('onboarded_at') if device_info else None
        }), 200
        
    except Exception as e:
        app.logger.error(f"Certificate verification error: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/pending_devices', methods=['GET'])
def get_pending_devices():
    """
    Get list of pending devices awaiting approval
    
    Returns:
        List of pending devices
    """
    manager = get_pending_manager()
    if not manager:
        return json.dumps({
            'status': 'error',
            'message': 'Pending device manager not available',
            'devices': []
        }), 503
    
    try:
        pending_devices = manager.get_pending_devices()
        return json.dumps({
            'status': 'success',
            'devices': pending_devices
        }), 200
    except Exception as e:
        app.logger.error(f"Error getting pending devices: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e),
            'devices': []
        }), 500

@app.route('/api/approve_device', methods=['POST'])
def approve_device():
    """
    Approve a pending device and trigger onboarding
    
    Request JSON:
    {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "admin_notes": "Optional notes" (optional)
    }
    
    Returns:
        Approval and onboarding result
    """
    manager = get_pending_manager()
    if not manager:
        return json.dumps({
            'status': 'error',
            'message': 'Pending device manager not available'
        }), 503
    
    try:
        data = request.json
        mac_address = data.get('mac_address')
        admin_notes = data.get('admin_notes')
        
        if not mac_address:
            return json.dumps({
                'status': 'error',
                'message': 'Missing mac_address'
            }), 400
        
        # If full service is available, use it
        if auto_onboarding_service:
            # Get pending device info before approval
            pending_device = manager.get_device_by_mac(mac_address)
            if not pending_device:
                return json.dumps({
                    'status': 'error',
                    'message': 'Device not found in pending list'
                }), 400
            
            device_id = pending_device.get('device_id')
            
            # Approve and onboard
            result = auto_onboarding_service.approve_and_onboard(mac_address, admin_notes)
            if result.get('status') == 'success':
                # Set up tracking structures so device appears in topology
                authorized_devices[device_id] = True
                if device_id not in device_data:
                    device_data[device_id] = []
                if device_id not in last_seen:
                    last_seen[device_id] = time.time()
                if device_id not in packet_counts:
                    packet_counts[device_id] = []
                if mac_address:
                    mac_addresses[device_id] = mac_address
                
                app.logger.info(f"Device {device_id} ({mac_address}) approved and added to topology tracking")
                return json.dumps(result), 200
            else:
                return json.dumps(result), 400
        
        # Fallback: approve via pending manager and optionally onboard
        pending_device = manager.get_device_by_mac(mac_address)
        if not pending_device:
            return json.dumps({
                'status': 'error',
                'message': 'Device not found in pending list'
            }), 400
        
        if not manager.approve_device(mac_address, admin_notes):
            return json.dumps({
                'status': 'error',
                'message': 'Failed to approve device'
            }), 400
        
        device_id = pending_device.get('device_id')
        # Allow device to proceed through token/auth flow
        authorized_devices[device_id] = True
        if device_id not in device_data:
            device_data[device_id] = []
        if device_id not in last_seen:
            last_seen[device_id] = time.time()
        if device_id not in packet_counts:
            packet_counts[device_id] = []
        if mac_address:
            mac_addresses[device_id] = mac_address
        
        # Attempt onboarding if module available
        onboarding_result = None
        if onboarding:
            try:
                onboarding_result = onboarding.onboard_device(
                    device_id=device_id,
                    mac_address=mac_address,
                    device_type=pending_device.get('device_type'),
                    device_info=pending_device.get('device_info')
                )
                if onboarding_result.get('status') == 'success':
                    manager.mark_onboarded(mac_address)
            except Exception as e:
                app.logger.error(f"Onboarding error during fallback approval: {e}")
                onboarding_result = {'status': 'error', 'message': str(e)}
        
        return json.dumps({
            'status': 'success',
            'message': 'Device approved',
            'onboarding_result': onboarding_result
        }), 200
            
    except Exception as e:
        app.logger.error(f"Error approving device: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/reject_device', methods=['POST'])
def reject_device():
    """
    Reject a pending device
    
    Request JSON:
    {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "admin_notes": "Optional notes" (optional)
    }
    
    Returns:
        Rejection result
    """
    manager = get_pending_manager()
    if not manager:
        return json.dumps({
            'status': 'error',
            'message': 'Pending device manager not available'
        }), 503
    
    try:
        data = request.json
        mac_address = data.get('mac_address')
        admin_notes = data.get('admin_notes')
        
        if not mac_address:
            return json.dumps({
                'status': 'error',
                'message': 'Missing mac_address'
            }), 400
        
        # Reject device
        if auto_onboarding_service:
            success = auto_onboarding_service.reject_device(mac_address, admin_notes)
        else:
            success = manager.reject_device(mac_address, admin_notes)
        
        if success:
            return json.dumps({
                'status': 'success',
                'message': 'Device rejected successfully'
            }), 200
        else:
            return json.dumps({
                'status': 'error',
                'message': 'Failed to reject device (device not found or not pending)'
            }), 400
            
    except Exception as e:
        app.logger.error(f"Error rejecting device: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/device_history', methods=['GET'])
def get_device_history():
    """
    Get device approval history
    
    Query parameters:
        mac_address: Optional MAC address filter
        limit: Maximum number of records (default: 100)
    
    Returns:
        Device approval history
    """
    manager = get_pending_manager()
    if not manager:
        return json.dumps({
            'status': 'error',
            'message': 'Pending device manager not available',
            'history': []
        }), 503
    
    try:
        mac_address = request.args.get('mac_address')
        limit = int(request.args.get('limit', 100))
        
        if auto_onboarding_service:
            history = auto_onboarding_service.get_device_history(mac_address, limit)
        else:
            history = manager.get_device_history(mac_address, limit)
        
        return json.dumps({
            'status': 'success',
            'history': history
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting device history: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e),
            'history': []
        }), 500

@app.route('/api/device_history/clear', methods=['POST'])
def clear_device_history():
    """Clear device approval history"""
    manager = get_pending_manager()
    if not manager:
        return json.dumps({
            'status': 'error',
            'message': 'Pending device manager not available'
        }), 503
    
    try:
        success = False
        if auto_onboarding_service:
            success = auto_onboarding_service.clear_device_history()
        else:
            success = manager.clear_device_history()
            
        if success:
            return json.dumps({'status': 'success'}), 200
        else:
            return json.dumps({
                'status': 'error',
                'message': 'Failed to clear history'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error clearing device history: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get_health_metrics')
def get_health_metrics():
    """Get real device health metrics based on actual device status"""
    current_time = time.time()
    health_data = {}
    for device in device_data:
        last_seen_time = last_seen.get(device, 0)
        online = (current_time - last_seen_time) < 10  # Device is online if seen in last 10 seconds
        
        if online and last_seen_time > 0:
            # Calculate real uptime from last_seen timestamp
            uptime_seconds = int(current_time - last_seen_time)
            health_data[device] = {
                "online": True,
                "uptime": uptime_seconds,
                "last_seen": last_seen_time,
                "status": "online"
            }
        else:
            health_data[device] = {
                "online": False,
                "uptime": 0,
                "last_seen": last_seen_time if last_seen_time > 0 else None,
                "status": "offline"
            }
    return json.dumps(health_data)

@app.route('/get_policy_logs')
def get_policy_logs():
    return json.dumps(policy_logs[-10:])  # Return last 10 logs


@app.route('/toggle_policy/<policy>', methods=['POST'])
def toggle_policy(policy):
    """Toggle a named SDN policy and return its new state as JSON"""
    if policy not in sdn_policies:
        return json.dumps({'error': 'Unknown policy'}), 400

    # flip the policy
    sdn_policies[policy] = not sdn_policies[policy]
    state = sdn_policies[policy]
    policy_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {policy.replace('_', ' ').title()} policy {'enabled' if state else 'disabled'}")
    return json.dumps({'enabled': state})


@app.route('/clear_policy_logs', methods=['POST'])
def clear_policy_logs():
    """Clear policy logs (useful for UI testing)"""
    policy_logs.clear()
    return json.dumps({'status': 'ok'})


@app.route('/get_security_alerts')
def get_security_alerts():
    """Return recent security alerts. For now, convert policy logs into structured alerts.

    Each alert contains: message, timestamp, severity (low/medium/high), optional device
    """
    alerts = []
    for entry in reversed(policy_logs[-20:]):
        # entries look like: [HH:MM:SS] Message
        try:
            ts_part, msg_part = entry.split(']', 1)
            ts = ts_part.strip('[')
            message = msg_part.strip()
        except Exception:
            ts = datetime.now().strftime('%H:%M:%S')
            message = entry

        # simple severity heuristic
        severity = 'low'
        low_keywords = ['delayed', 'routed', 'rerouted']
        high_keywords = ['blocked', 'attack', 'ddos', 'denied']
        if any(k in message.lower() for k in high_keywords):
            severity = 'high'
        elif any(k in message.lower() for k in low_keywords):
            severity = 'medium'

        alerts.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'severity': severity,
            'device': None
        })

    return json.dumps(alerts)


@app.route('/get_policies')
def get_policies():
    """Return current policy states"""
    return json.dumps(sdn_policies)

@app.route('/get_sdn_metrics')
def get_sdn_metrics():
    """Get SDN metrics - returns real data if available, otherwise 0"""
    # Real SDN metrics would be populated from Ryu controller
    # For now, return current metrics (0 if not set from real sources)
    return json.dumps(sdn_metrics)

# ML Security Engine Endpoints
@app.route('/ml/initialize')
def initialize_ml():
    """Initialize the ML security engine"""
    if not ML_ENGINE_AVAILABLE:
        return json.dumps({'status': 'error', 'message': 'ML engine not available (TensorFlow not installed)'})
    
    global ml_engine, ml_monitoring_active
    try:
        # Already initialized and healthy
        if ml_engine and hasattr(ml_engine, 'is_loaded') and ml_engine.is_loaded:
            return json.dumps({'status': 'success', 'message': 'ML engine already running'})

        ml_engine = initialize_ml_engine()
        if ml_engine and hasattr(ml_engine, 'is_loaded') and ml_engine.is_loaded:
            ml_monitoring_active = True
            if hasattr(ml_engine, 'start_monitoring'):
                ml_engine.start_monitoring()
            return json.dumps({'status': 'success', 'message': 'ML engine initialized and monitoring started'})
        else:
            return json.dumps({'status': 'error', 'message': 'Failed to initialize ML engine'})
    except Exception as e:
        return json.dumps({'status': 'error', 'message': f'ML initialization failed: {str(e)}'})

@app.route('/ml/status')
def ml_status():
    """Get ML engine status"""
    if not ML_ENGINE_AVAILABLE:
        return json.dumps({
            'status': 'unavailable',
            'monitoring': False,
            'message': 'ML engine not available (TensorFlow not installed)'
        })
    
    global ml_engine, ml_monitoring_active
    
    # Auto-initialize if not running
    if not ml_engine:
        try:
            ml_engine = initialize_ml_engine()
            if ml_engine and hasattr(ml_engine, 'is_loaded') and ml_engine.is_loaded:
                ml_monitoring_active = True
                if hasattr(ml_engine, 'start_monitoring'):
                    ml_engine.start_monitoring()
                app.logger.info("ML engine auto-initialized from status endpoint")
        except Exception as e:
            app.logger.error(f"Auto-initialization failed in status: {e}")
    
    if ml_engine and hasattr(ml_engine, 'is_loaded') and ml_engine.is_loaded:
        stats = {}
        if hasattr(ml_engine, 'get_attack_statistics'):
            stats = ml_engine.get_attack_statistics()
        return json.dumps({
            'status': 'active',
            'monitoring': ml_monitoring_active,
            'statistics': stats
        })
    else:
        return json.dumps({'status': 'inactive', 'monitoring': False})

@app.route('/ml/detections')
def ml_detections():
    """Get recent attack detections"""
    if not ML_ENGINE_AVAILABLE:
        return json.dumps({
            'error': 'ML engine not available',
            'status': 'error',
            'message': 'TensorFlow not installed'
        }), 503
    
    try:
        global ml_engine, ml_monitoring_active
        
        # Auto-initialize if not running
        if not ml_engine:
            try:
                ml_engine = initialize_ml_engine()
                if ml_engine and hasattr(ml_engine, 'is_loaded') and ml_engine.is_loaded:
                    ml_monitoring_active = True
                    if hasattr(ml_engine, 'start_monitoring'):
                        ml_engine.start_monitoring()
                    app.logger.info("ML engine auto-initialized from detections endpoint")
            except Exception as e:
                app.logger.error(f"Auto-initialization failed in detections: {e}")
                return json.dumps({
                    'error': 'ML engine initialization failed',
                    'status': 'error',
                    'message': str(e)
                }), 503

        if not ml_engine:
            return json.dumps({'error': 'ML engine not initialized', 'status': 'error'}), 503

        if not hasattr(ml_engine, 'is_loaded') or not ml_engine.is_loaded:
            return json.dumps({'error': 'ML model not loaded', 'status': 'error'}), 503

        if hasattr(ml_engine, 'attack_detections'):
            all_detections = list(ml_engine.attack_detections)[-20:]  # Get last 20 detections
            # Filter to only high-confidence attacks (>70% confidence)
            detections = [
                d for d in all_detections 
                if d.get('is_attack', False) and d.get('confidence', 0.0) > 0.7
            ]
        else:
            detections = []

        # Ensure all data is JSON serializable
        clean_detections = []
        for d in detections:
            clean_det = {
                'timestamp': d.get('timestamp'),
                'is_attack': bool(d.get('is_attack', False)),
                'attack_type': str(d.get('attack_type', 'Unknown')),
                'confidence': float(d.get('confidence', 0.0))
            }
            if 'device_id' in d:
                clean_det['device_id'] = str(d.get('device_id'))
            if 'details' in d:
                clean_det['details'] = str(d.get('details'))
            clean_detections.append(clean_det)

        # Get statistics safely
        stats = {}
        if hasattr(ml_engine, 'get_attack_statistics'):
            try:
                stats = ml_engine.get_attack_statistics()
            except Exception as e:
                app.logger.warning(f"Error getting attack statistics: {e}")
                stats = {}
        
        return json.dumps({
            'status': 'success',
            'detections': clean_detections,
            'stats': stats
        }), 200
    except Exception as e:
        app.logger.error(f"Error in /ml/detections: {str(e)}")
        return json.dumps({
            'error': 'Internal server error',
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/ml/analyze_packet', methods=['POST'])
def analyze_packet():
    """Analyze a specific packet for attacks"""
    if not ML_ENGINE_AVAILABLE:
        return json.dumps({'error': 'ML engine not available (TensorFlow not installed)'})
    
    global ml_engine
    if not ml_engine or not hasattr(ml_engine, 'is_loaded') or not ml_engine.is_loaded:
        return json.dumps({'error': 'ML engine not initialized'})
    
    try:
        packet_data = request.json
        if hasattr(ml_engine, 'predict_attack'):
            result = ml_engine.predict_attack(packet_data)
            return json.dumps(result)
        else:
            return json.dumps({'error': 'ML engine does not support packet analysis'})
    except Exception as e:
        return json.dumps({'error': f'Analysis failed: {str(e)}'})

@app.route('/api/network/statistics')
def network_statistics():
    """Get comprehensive real network statistics"""
    try:
        current_time = time.time()
        stats = {}
        
        # Get ML engine statistics if available
        global ml_engine
        if ml_engine and hasattr(ml_engine, 'get_attack_statistics'):
            try:
                ml_stats = ml_engine.get_attack_statistics()
                stats['ml_engine'] = {
                    'total_packets': ml_stats.get('total_packets', 0),
                    'attack_packets': ml_stats.get('attack_packets', 0),
                    'normal_packets': ml_stats.get('normal_packets', 0),
                    'attack_rate': ml_stats.get('attack_rate', 0.0),
                    'detection_accuracy': ml_stats.get('detection_accuracy', 0.0),
                    'processing_rate': ml_stats.get('processing_rate', 0.0),
                    'model_confidence': ml_stats.get('model_confidence', 0.0)
                }
            except Exception as e:
                app.logger.warning(f"Error getting ML statistics: {e}")
                stats['ml_engine'] = {}
        else:
            stats['ml_engine'] = {}
        
        # Get device-specific statistics
        device_stats = {}
        for device_id in device_data:
            # Real packet count from device_data
            packet_count = sum(device_data.get(device_id, []))
            
            # Calculate real traffic rate (packets per minute)
            device_packet_timestamps = packet_counts.get(device_id, [])
            recent_packets = [t for t in device_packet_timestamps if current_time - t <= 60]
            packets_per_minute = len(recent_packets)
            
            # Device online/offline status
            last_seen_time = last_seen.get(device_id, 0)
            is_online = (current_time - last_seen_time) < 10
            
            device_stats[device_id] = {
                'total_packets': packet_count,
                'packets_per_minute': packets_per_minute,
                'is_online': is_online,
                'last_seen': last_seen_time if last_seen_time > 0 else None,
                'uptime_seconds': int(current_time - last_seen_time) if is_online and last_seen_time > 0 else 0
            }
        
        stats['devices'] = device_stats
        
        # Overall network statistics
        total_devices = len(device_data)
        online_devices = sum(1 for d in device_data if (current_time - last_seen.get(d, 0)) < 10)
        total_network_packets = sum(sum(device_data.get(d, [])) for d in device_data)
        
        stats['network'] = {
            'total_devices': total_devices,
            'online_devices': online_devices,
            'offline_devices': total_devices - online_devices,
            'total_network_packets': total_network_packets
        }
        
        return json.dumps({
            'status': 'success',
            'statistics': stats
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in /api/network/statistics: {str(e)}")
        return json.dumps({
            'error': 'Internal server error',
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/ml/statistics')
def ml_statistics():
    """Get comprehensive ML statistics"""
    if not ML_ENGINE_AVAILABLE:
        return json.dumps({'error': 'ML engine not available (TensorFlow not installed)'})
    
    global ml_engine
    if ml_engine and hasattr(ml_engine, 'is_loaded') and ml_engine.is_loaded:
        if hasattr(ml_engine, 'get_attack_statistics'):
            try:
                stats = ml_engine.get_attack_statistics()
                return json.dumps(stats)
            except Exception as e:
                app.logger.error(f"Error getting ML statistics: {e}")
                return json.dumps({'error': f'Failed to get statistics: {str(e)}'})
        else:
            return json.dumps({'error': 'ML engine statistics not available'})
    else:
        return json.dumps({'error': 'ML engine not available'})

def start_ml_engine():
    """Initialize and start the ML engine on app startup"""
    if not ML_ENGINE_AVAILABLE:
        print("⚠️  ML engine not available (TensorFlow not installed)")
        print("   System will run with heuristic-based detection only")
        return False
        
    global ml_engine, ml_monitoring_active
    try:
        print("🚀 Initializing ML Security Engine...")
        ml_engine = initialize_ml_engine()
        if ml_engine and hasattr(ml_engine, 'is_loaded') and ml_engine.is_loaded:
            ml_monitoring_active = True
            if hasattr(ml_engine, 'start_monitoring'):
                ml_engine.start_monitoring()
            print("✅ ML Security Engine initialized and monitoring started")
            return True
        else:
            print("⚠️  ML engine initialization skipped (using heuristic detection)")
            return False
    except Exception as e:
        print(f"⚠️  ML initialization failed: {str(e)}")
        print("   System will run with heuristic-based detection only")
        return False

# Suspicious Device Alert Management
def create_suspicious_device_alert(device_id, reason, severity, redirected=True):
    """
    Create a suspicious device alert
    
    Args:
        device_id: Device identifier
        reason: Reason for alert ('ml_detection', 'anomaly', 'trust_score', etc.)
        severity: Alert severity ('low', 'medium', 'high')
        redirected: Whether device was redirected to honeypot
    """
    # Check if alert already exists for this device
    existing_alert = None
    for alert in suspicious_device_alerts:
        if alert.get('device_id') == device_id and alert.get('redirected'):
            existing_alert = alert
            break
    
    if existing_alert:
        # Update existing alert
        existing_alert['timestamp'] = datetime.now().isoformat()
        existing_alert['reason'] = reason
        existing_alert['severity'] = severity
        return existing_alert
    
    alert = {
        'device_id': device_id,
        'timestamp': datetime.now().isoformat(),
        'reason': reason,
        'severity': severity,
        'redirected': redirected,
        'honeypot_activity_count': 0
    }
    suspicious_device_alerts.append(alert)
    # Keep only last 100 alerts
    if len(suspicious_device_alerts) > 100:
        suspicious_device_alerts[:] = suspicious_device_alerts[-100:]
    return alert

def update_alert_activity_counts():
    """Periodically update honeypot activity counts for alerts"""
    # Try to get threat_intelligence if available
    threat_intelligence = None
    try:
        # Check if threat_intelligence is available in global scope or can be imported
        from honeypot_manager.threat_intelligence import ThreatIntelligence
        # Note: threat_intelligence instance would need to be initialized elsewhere
        # For now, we'll update counts if we can access it
        pass
    except ImportError:
        pass
    
    # Update activity counts for each alert
    for alert in suspicious_device_alerts:
        device_id = alert.get('device_id')
        if device_id and threat_intelligence:
            try:
                activity_count = threat_intelligence.get_device_activity_count(device_id)
                alert['honeypot_activity_count'] = activity_count
            except Exception as e:
                app.logger.debug(f"Failed to update activity count for {device_id}: {e}")

def start_activity_count_updater():
    """Start background thread to periodically update honeypot activity counts"""
    def activity_count_loop():
        """Background loop to update activity counts"""
        while True:
            try:
                update_alert_activity_counts()
                time.sleep(10)  # Update every 10 seconds
            except Exception as e:
                app.logger.error(f"Activity count updater error: {e}")
                time.sleep(30)  # Wait longer on error
    
    updater_thread = threading.Thread(
        target=activity_count_loop,
        name="ActivityCountUpdater",
        daemon=True
    )
    updater_thread.start()
    app.logger.info("✅ Activity count updater thread started")

@app.route('/api/alerts/suspicious_devices', methods=['GET'])
def get_suspicious_device_alerts():
    """
    Get all suspicious device alerts
    
    Returns:
        JSON list of alerts
    """
    # Update activity counts from honeypot if available
    # This would ideally get from threat_intelligence.device_activities
    # For now, activity counts are updated when honeypot logs are processed
    
    return json.dumps({
        'status': 'success',
        'alerts': suspicious_device_alerts[-50:]  # Return last 50 alerts
    }), 200

@app.route('/api/alerts/create', methods=['POST'])
def create_alert():
    """
    Create a new suspicious device alert
    
    Request JSON:
    {
        "device_id": "DEVICE_ID",
        "reason": "ml_detection",
        "severity": "high",
        "redirected": true
    }
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        reason = data.get('reason', 'unknown')
        severity = data.get('severity', 'medium')
        redirected = data.get('redirected', True)
        
        if not device_id:
            return json.dumps({
                'status': 'error',
                'message': 'Missing device_id'
            }), 400
        
        alert = create_suspicious_device_alert(device_id, reason, severity, redirected)
        
        return json.dumps({
            'status': 'success',
            'alert': alert
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error creating alert: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    """Clear old alerts"""
    suspicious_device_alerts.clear()
    return json.dumps({'status': 'success', 'message': 'Alerts cleared'}), 200

@app.route('/api/alerts/update_activity', methods=['POST'])
def update_alert_activity():
    """
    Update activity count for a device alert
    
    Request JSON:
    {
        "device_id": "DEVICE_ID",
        "activity_count": 5
    }
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        activity_count = data.get('activity_count', 0)
        
        if not device_id:
            return json.dumps({
                'status': 'error',
                'message': 'Missing device_id'
            }), 400
        
        # Update activity count in alerts
        updated = False
        for alert in suspicious_device_alerts:
            if alert.get('device_id') == device_id:
                alert['honeypot_activity_count'] = activity_count
                updated = True
                break
        
        return json.dumps({
            'status': 'success',
            'updated': updated
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error updating alert activity: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/honeypot/status', methods=['GET'])
def get_honeypot_status():
    """
    Get honeypot container status and information
    
    Returns:
        JSON with honeypot status, threats, blocked IPs, and mitigation rules
    """
    try:
        # Try to import and check honeypot status
        try:
            from honeypot_manager.honeypot_deployer import HoneypotDeployer
            from honeypot_manager.docker_manager import DOCKER_AVAILABLE
            
            if not DOCKER_AVAILABLE:
                return json.dumps({
                    'status': 'stopped',
                    'message': 'Docker not available',
                    'threats': [],
                    'blocked_ips': [],
                    'mitigation_rules': []
                }), 200
            
            deployer = HoneypotDeployer()
            container_status = deployer.get_status()
            is_running = deployer.is_running()
            
            # Get threats from threat intelligence if available
            threats = []
            blocked_ips = []
            mitigation_rules = []
            
            try:
                from honeypot_manager.threat_intelligence import ThreatIntelligence
                # Try to get threat intelligence instance
                # This would need to be initialized elsewhere or passed in
                # For now, return empty lists
            except Exception:
                pass
            
            return json.dumps({
                'status': 'running' if is_running else 'stopped',
                'container_status': container_status or 'not_found',
                'running': is_running,
                'threats': threats,
                'blocked_ips': blocked_ips,
                'mitigation_rules': mitigation_rules
            }), 200
            
        except ImportError:
            # Honeypot manager not available
            return json.dumps({
                'status': 'stopped',
                'message': 'Honeypot manager not available',
                'threats': [],
                'blocked_ips': [],
                'mitigation_rules': []
            }), 200
            
    except Exception as e:
        app.logger.error(f"Error getting honeypot status: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e),
            'threats': [],
            'blocked_ips': [],
            'mitigation_rules': []
        }), 500

@app.route('/api/honeypot/redirected_devices', methods=['GET'])
def get_redirected_devices():
    """
    Get list of all currently redirected devices
    
    Returns:
        JSON list of redirected devices with metadata
    """
    try:
        # Get redirected devices from alerts
        redirected_devices = []
        for alert in suspicious_device_alerts:
            if alert.get('redirected', False):
                redirected_devices.append({
                    'device_id': alert.get('device_id'),
                    'timestamp': alert.get('timestamp'),
                    'reason': alert.get('reason'),
                    'severity': alert.get('severity'),
                    'activity_count': alert.get('honeypot_activity_count', 0)
                })
        
        # Check honeypot container status
        container_running = False
        try:
            from honeypot_manager.honeypot_deployer import HoneypotDeployer
            from honeypot_manager.docker_manager import DOCKER_AVAILABLE
            if DOCKER_AVAILABLE:
                deployer = HoneypotDeployer()
                container_running = deployer.is_running()
        except Exception:
            pass
        
        return json.dumps({
            'status': 'success',
            'devices': redirected_devices,
            'redirected_count': len(redirected_devices),
            'container_running': container_running,
            'total_threats': len([a for a in suspicious_device_alerts if a.get('honeypot_activity_count', 0) > 0])
        }), 200
    except Exception as e:
        app.logger.error(f"Error getting redirected devices: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e),
            'devices': []
        }), 500

@app.route('/api/honeypot/device/<device_id>/activity', methods=['GET'])
def get_device_honeypot_activity(device_id):
    """
    Get honeypot activity for a specific device
    
    Args:
        device_id: Device identifier
    """
    try:
        limit = int(request.args.get('limit', 100))
        
        # Get activity count from alert if it exists
        # The activity count is updated by the honeypot monitoring thread via API
        activity_count = 0
        activities = []
        
        for alert in suspicious_device_alerts:
            if alert.get('device_id') == device_id:
                activity_count = alert.get('honeypot_activity_count', 0)
                break
        
        return json.dumps({
            'status': 'success',
            'device_id': device_id,
            'activities': activities,
            'count': activity_count
        }), 200
    except Exception as e:
        app.logger.error(f"Error getting device activity: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e),
            'activities': []
        }), 500

@app.route('/api/honeypot/device/<device_id>/remove_redirect', methods=['POST'])
def remove_device_redirect(device_id):
    """
    Manually remove redirect for a device (admin action)
    
    Args:
        device_id: Device identifier
    """
    try:
        # This would need to call SDN policy engine to remove redirect
        # For now, just return success
        return json.dumps({
            'status': 'success',
            'message': f'Redirect removed for {device_id}'
        }), 200
    except Exception as e:
        app.logger.error(f"Error removing redirect: {e}")
        return json.dumps({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Start ML engine before running the app (optional)
    start_ml_engine()
    
    # Start activity count updater thread
    start_activity_count_updater()
    
    # Run the Flask app
    print("🌐 Starting Flask Controller on http://0.0.0.0:5000")
    try:
        app.run(host='0.0.0.0', port=5000, use_reloader=False, debug=False, threaded=True)  # disable reloader to prevent duplicate ML engine initialization
    except KeyboardInterrupt:
        print("\n🛑 Flask Controller stopped by user")
    except Exception as e:
        print(f"❌ Flask Controller error: {e}")
        import traceback
        traceback.print_exc()
        raise