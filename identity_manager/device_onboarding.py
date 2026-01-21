"""
Secure Device Onboarding Module
Handles secure onboarding process with certificate provisioning and behavioral profiling
"""

import logging
import time
import threading
from typing import Dict, Optional

import json
from .certificate_manager import CertificateManager
from .identity_database import IdentityDatabase
from .behavioral_profiler import BehavioralProfiler
from .policy_generator import PolicyGenerator

logger = logging.getLogger(__name__)

class DeviceOnboarding:
    """Manages secure device onboarding process"""
    
    def __init__(self, certs_dir="certs", db_path="identity.db", sdn_policy_engine=None):
        """
        Initialize device onboarding system
        
        Args:
            certs_dir: Directory for certificates
            db_path: Path to identity database
            sdn_policy_engine: SDN policy engine instance (optional, for policy application)
        """
        self.cert_manager = CertificateManager(certs_dir=certs_dir)
        self.identity_db = IdentityDatabase(db_path=db_path)
        self.profiler = BehavioralProfiler(profiling_duration=300)  # 5 minutes
        self.policy_generator = PolicyGenerator()
        self.sdn_policy_engine = sdn_policy_engine
        
        # Automatic finalization monitoring
        self.monitoring_enabled = True
        self.monitoring_thread = None
        self.monitoring_interval = 30  # Check every 30 seconds
        self.min_traffic_packets = 5  # Minimum packets required for baseline
        
        # Start monitoring thread
        self._start_profiling_monitor()
        
        logger.info("Device onboarding system initialized")
    
    def onboard_device(self, device_id: str, mac_address: str, device_type: str = None,
                     device_info: str = None) -> Dict:
        """
        Onboard a new device with secure certificate provisioning
        
        Args:
            device_id: Device identifier
            mac_address: Device MAC address
            device_type: Type of device
            device_info: Additional device information
            
        Returns:
            Onboarding result dictionary with certificate paths and status
        """
        try:
            logger.info(f"Starting onboarding for device {device_id} ({mac_address})...")
            
            # Check if device already exists
            existing = self.identity_db.get_device(device_id)
            if existing:
                logger.warning(f"Device {device_id} already onboarded")
                return {
                    'status': 'error',
                    'message': 'Device already onboarded',
                    'device_id': device_id
                }
            
            # Create physical identity fingerprint
            import hashlib
            from datetime import datetime
            physical_identity_data = {
                'mac_address': mac_address,
                'device_type': device_type,
                'first_seen': datetime.utcnow().isoformat(),
                'onboarding_timestamp': datetime.utcnow().isoformat()
            }
            physical_identity_json = json.dumps(physical_identity_data)
            
            # Generate device fingerprint (hash of MAC + device type + timestamp)
            fingerprint_data = f"{mac_address}:{device_type}:{physical_identity_data['first_seen']}"
            device_fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
            
            # Generate certificate with physical identity linking
            cert_path, key_path = self.cert_manager.generate_device_certificate(
                device_id, mac_address
            )
            
            # Add device to database with physical identity information
            success = self.identity_db.add_device(
                device_id=device_id,
                mac_address=mac_address,
                certificate_path=cert_path,
                key_path=key_path,
                device_type=device_type,
                device_info=device_info,
                physical_identity=physical_identity_json,
                device_fingerprint=device_fingerprint
            )
            
            if not success:
                raise Exception("Failed to add device to database")
            
            # Start behavioral profiling
            self.profiler.start_profiling(device_id)
            
            # Get CA certificate for device
            ca_cert = self.cert_manager.get_ca_certificate()
            
            result = {
                'status': 'success',
                'device_id': device_id,
                'mac_address': mac_address,
                'certificate_path': cert_path,
                'key_path': key_path,
                'ca_certificate': ca_cert,
                'profiling': True,
                'device_fingerprint': device_fingerprint,
                'physical_identity_linked': True,
                'message': 'Device onboarded successfully. Physical identity linked to network credential. Behavioral profiling started.'
            }
            
            logger.info(f"Device {device_id} onboarded successfully")
            return result
            
        except Exception as e:
            logger.error(f"Onboarding failed for {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'device_id': device_id
            }
    
    def record_traffic(self, device_id: str, packet_info: Dict):
        """
        Record traffic for behavioral profiling
        
        Args:
            device_id: Device identifier
            packet_info: Packet information dictionary
        """
        self.profiler.record_traffic(device_id, packet_info)
        self.identity_db.update_last_seen(device_id)
    
    def finalize_onboarding(self, device_id: str) -> Dict:
        """
        Finalize onboarding by establishing baseline and generating policy
        
        Args:
            device_id: Device identifier
            
        Returns:
            Finalization result with baseline and policy
        """
        try:
            # Finish profiling
            baseline = self.profiler.finish_profiling(device_id)
            if not baseline:
                return {
                    'status': 'error',
                    'message': 'No profiling data available'
                }
            
            # Save baseline to database
            baseline_json = json.dumps(baseline)
            self.identity_db.save_behavioral_baseline(device_id, baseline_json)
            
            # Generate least-privilege policy
            policy = self.policy_generator.generate_least_privilege_policy(device_id, baseline)
            policy_json = self.policy_generator.policy_to_json(policy)
            self.identity_db.save_device_policy(device_id, policy_json)
            
            # Apply policy to SDN controller if available
            if self.sdn_policy_engine:
                try:
                    self.sdn_policy_engine.apply_policy_from_identity(device_id, policy)
                    logger.info(f"Policy applied to SDN controller for {device_id}")
                except Exception as e:
                    logger.error(f"Failed to apply policy to SDN controller for {device_id}: {e}")
            
            result = {
                'status': 'success',
                'device_id': device_id,
                'baseline': baseline,
                'policy': policy,
                'message': 'Onboarding finalized. Baseline and policy generated.'
            }
            
            logger.info(f"Onboarding finalized for {device_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to finalize onboarding for {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """
        Get device information
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device information dictionary or None
        """
        return self.identity_db.get_device(device_id)
    
    def get_device_id_from_mac(self, mac_address: str) -> Optional[str]:
        """
        Get device ID from MAC address
        
        Args:
            mac_address: MAC address
            
        Returns:
            Device ID or None
        """
        device = self.identity_db.get_device_by_mac(mac_address)
        if device:
            return device['device_id']
        return None
    
    def verify_device_certificate(self, device_id: str) -> bool:
        """
        Verify device certificate
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if certificate is valid, False otherwise
        """
        device = self.identity_db.get_device(device_id)
        if not device or not device.get('certificate_path'):
            return False
        
        return self.cert_manager.verify_certificate(device['certificate_path'])
    
    def revoke_device(self, device_id: str) -> bool:
        """
        Revoke device access
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Revoke certificate
            self.cert_manager.revoke_certificate(device_id)
            
            # Update device status
            self.identity_db.update_device_status(device_id, 'revoked')
            
            # Remove policy from SDN controller if available
            if self.sdn_policy_engine:
                try:
                    self.sdn_policy_engine.remove_policy(device_id)
                    logger.info(f"Policy removed from SDN controller for {device_id}")
                except Exception as e:
                    logger.error(f"Failed to remove policy from SDN controller for {device_id}: {e}")
            
            logger.info(f"Device {device_id} revoked")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke device {device_id}: {e}")
            return False
    
    def set_sdn_policy_engine(self, sdn_policy_engine):
        """
        Set SDN policy engine reference for policy application
        
        Args:
            sdn_policy_engine: SDN policy engine instance
        """
        self.sdn_policy_engine = sdn_policy_engine
        logger.info("SDN policy engine connected to device onboarding")
    
    def update_policy_for_device(self, device_id: str) -> bool:
        """
        Update policy for a device based on current baseline
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current baseline
            baseline_json = self.identity_db.get_behavioral_baseline(device_id)
            if not baseline_json:
                logger.warning(f"No baseline found for {device_id}")
                return False
            
            import json
            baseline = json.loads(baseline_json)
            
            # Generate updated policy
            policy = self.policy_generator.generate_least_privilege_policy(device_id, baseline)
            policy_json = self.policy_generator.policy_to_json(policy)
            self.identity_db.save_device_policy(device_id, policy_json)
            
            # Apply to SDN controller
            if self.sdn_policy_engine:
                try:
                    self.sdn_policy_engine.apply_policy_from_identity(device_id, policy)
                    logger.info(f"Policy updated for {device_id}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to update policy in SDN controller for {device_id}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update policy for {device_id}: {e}")
            return False
    
    def _start_profiling_monitor(self):
        """Start background thread to monitor and auto-finalize profiling"""
        if not self.monitoring_enabled:
            return
        
        def monitoring_loop():
            """Background loop to check for expired profiling periods"""
            while self.monitoring_enabled:
                try:
                    # Get all devices currently being profiled
                    active_devices = self.profiler.get_active_profiling_devices()
                    
                    for device_id in active_devices:
                        # Check if profiling period has expired
                        if self.profiler.is_profiling_expired(device_id):
                            # Check if we have minimum traffic data
                            profile_status = self.profiler.get_profiling_status(device_id)
                            if profile_status and profile_status.get('packet_count', 0) >= self.min_traffic_packets:
                                logger.info(f"Profiling period expired for {device_id}, auto-finalizing onboarding...")
                                try:
                                    result = self.finalize_onboarding(device_id)
                                    if result.get('status') == 'success':
                                        logger.info(f"Successfully auto-finalized onboarding for {device_id}")
                                    else:
                                        logger.warning(f"Auto-finalization failed for {device_id}: {result.get('message')}")
                                except Exception as e:
                                    logger.error(f"Error during auto-finalization for {device_id}: {e}")
                            else:
                                # Not enough traffic, but period expired - finalize anyway with what we have
                                packet_count = profile_status.get('packet_count', 0) if profile_status else 0
                                logger.warning(f"Profiling expired for {device_id} with insufficient traffic ({packet_count} packets), finalizing anyway...")
                                try:
                                    result = self.finalize_onboarding(device_id)
                                    if result.get('status') == 'success':
                                        logger.info(f"Successfully auto-finalized onboarding for {device_id} (with limited traffic)")
                                    else:
                                        logger.warning(f"Auto-finalization failed for {device_id}: {result.get('message')}")
                                except Exception as e:
                                    logger.error(f"Error during auto-finalization for {device_id}: {e}")
                    
                    # Sleep until next check
                    time.sleep(self.monitoring_interval)
                    
                except Exception as e:
                    logger.error(f"Error in profiling monitor loop: {e}")
                    time.sleep(self.monitoring_interval)
        
        self.monitoring_thread = threading.Thread(
            target=monitoring_loop,
            daemon=True,
            name="OnboardingProfilingMonitor"
        )
        self.monitoring_thread.start()
        logger.info("Profiling monitor thread started")
    
    def stop_monitoring(self):
        """Stop the profiling monitor thread"""
        self.monitoring_enabled = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Profiling monitor thread stopped")

