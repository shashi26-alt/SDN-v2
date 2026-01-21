"""
Auto-Onboarding Service
Background service that automatically detects new WiFi devices and manages onboarding workflow
"""

import threading
import logging
import time
from typing import Optional, Callable
from .wifi_detector import WiFiDetector
from .device_id_generator import DeviceIDGenerator
from .pending_devices import PendingDeviceManager
from .config import MONITORING_INTERVAL

logger = logging.getLogger(__name__)


class AutoOnboardingService:
    """Automatic device onboarding service"""
    
    def __init__(self, onboarding_module=None, identity_db=None):
        """
        Initialize auto-onboarding service
        
        Args:
            onboarding_module: DeviceOnboarding instance (optional, for direct onboarding)
            identity_db: IdentityDatabase instance (optional, for checking existing devices)
        """
        self.onboarding_module = onboarding_module
        self.identity_db = identity_db
        
        # Initialize components
        self.wifi_detector = WiFiDetector(on_new_device=self._on_new_device_detected)
        self.device_id_generator = DeviceIDGenerator()
        self.pending_manager = PendingDeviceManager()
        
        # Service state
        self.running = False
        self.monitor_thread = None
        
        # Load known devices from database
        self._load_known_devices()
        
        logger.info("Auto-onboarding service initialized")
    
    def _load_known_devices(self):
        """Load known devices from identity database"""
        if self.identity_db:
            try:
                devices = self.identity_db.get_all_devices()
                for device in devices:
                    mac = device.get('mac_address')
                    if mac:
                        self.wifi_detector.add_known_device(mac)
                        logger.debug(f"Loaded known device: {mac}")
            except Exception as e:
                logger.warning(f"Failed to load known devices: {e}")
        
        # Also load from pending devices
        try:
            pending_devices = self.pending_manager.get_all_devices()
            for device in pending_devices:
                mac = device.get('mac_address')
                if mac:
                    self.wifi_detector.add_known_device(mac)
        except Exception as e:
            logger.warning(f"Failed to load pending devices: {e}")
    
    def _on_new_device_detected(self, mac_address: str):
        """
        Callback when new device is detected
        
        Args:
            mac_address: Detected device MAC address
        """
        try:
            logger.info(f"New device detected: {mac_address}")
            
            # Check if device already exists in identity database
            if self.identity_db:
                existing = self.identity_db.get_device_by_mac(mac_address)
                if existing:
                    logger.info(f"Device {mac_address} already onboarded, skipping")
                    return
            
            # Check if already in pending devices
            pending = self.pending_manager.get_device_by_mac(mac_address)
            if pending and pending.get('status') == PendingDeviceManager.STATUS_PENDING:
                logger.info(f"Device {mac_address} already pending approval")
                return
            
            # Generate device ID
            device_id = self.device_id_generator.generate_device_id(mac_address)
            logger.info(f"Generated device ID: {device_id} for MAC: {mac_address}")
            
            # Add to pending devices
            success = self.pending_manager.add_pending_device(
                mac_address=mac_address,
                device_id=device_id,
                device_type=None,  # Could be detected later
                device_info=None
            )
            
            if success:
                logger.info(f"Device {device_id} ({mac_address}) added to pending approval")
            else:
                logger.warning(f"Failed to add device {mac_address} to pending list")
                
        except Exception as e:
            logger.error(f"Error handling new device detection: {e}")
    
    def approve_and_onboard(self, mac_address: str, admin_notes: str = None) -> dict:
        """
        Approve pending device and trigger onboarding
        
        Args:
            mac_address: Device MAC address
            admin_notes: Optional admin notes
            
        Returns:
            Result dictionary with status and details
        """
        try:
            # Get pending device info
            pending_device = self.pending_manager.get_device_by_mac(mac_address)
            if not pending_device:
                return {
                    'status': 'error',
                    'message': 'Device not found in pending list'
                }
            
            if pending_device.get('status') != PendingDeviceManager.STATUS_PENDING:
                return {
                    'status': 'error',
                    'message': f"Device status is {pending_device.get('status')}, not pending"
                }
            
            device_id = pending_device.get('device_id')
            
            # Approve device
            if not self.pending_manager.approve_device(mac_address, admin_notes):
                return {
                    'status': 'error',
                    'message': 'Failed to approve device'
                }
            
            # Trigger onboarding if onboarding module is available
            if self.onboarding_module:
                try:
                    result = self.onboarding_module.onboard_device(
                        device_id=device_id,
                        mac_address=mac_address,
                        device_type=pending_device.get('device_type'),
                        device_info=pending_device.get('device_info')
                    )
                    
                    if result.get('status') == 'success':
                        # Mark as onboarded
                        self.pending_manager.mark_onboarded(mac_address)
                        return {
                            'status': 'success',
                            'message': 'Device approved and onboarded successfully',
                            'device_id': device_id,
                            'onboarding_result': result
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f"Onboarding failed: {result.get('message')}",
                            'device_id': device_id
                        }
                except Exception as e:
                    logger.error(f"Onboarding error: {e}")
                    return {
                        'status': 'error',
                        'message': f"Onboarding exception: {str(e)}",
                        'device_id': device_id
                    }
            else:
                # Onboarding module not available, just approved
                return {
                    'status': 'success',
                    'message': 'Device approved (onboarding module not available)',
                    'device_id': device_id
                }
                
        except Exception as e:
            logger.error(f"Error in approve_and_onboard: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def reject_device(self, mac_address: str, admin_notes: str = None) -> bool:
        """
        Reject pending device
        
        Args:
            mac_address: Device MAC address
            admin_notes: Optional admin notes
            
        Returns:
            True if rejected successfully
        """
        return self.pending_manager.reject_device(mac_address, admin_notes)
    
    def start(self):
        """Start the auto-onboarding service"""
        if self.running:
            logger.warning("Service already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="AutoOnboardingMonitor"
        )
        self.monitor_thread.start()
        logger.info("Auto-onboarding service started")
    
    def stop(self):
        """Stop the auto-onboarding service"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Auto-onboarding service stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting WiFi monitoring loop")
        
        while self.running:
            try:
                # Scan for new devices
                new_devices = self.wifi_detector.scan_once()
                
                # Callback is already set, so new devices are handled automatically
                if new_devices:
                    logger.debug(f"Detected {len(new_devices)} new device(s)")
                
                # Sleep until next scan
                time.sleep(MONITORING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(MONITORING_INTERVAL)
    
    def get_pending_devices(self):
        """Get list of pending devices"""
        return self.pending_manager.get_pending_devices()
    
    def get_device_history(self, mac_address: str = None, limit: int = 100):
        """Get device approval history"""
        return self.pending_manager.get_device_history(mac_address, limit)
    
    def is_running(self) -> bool:
        """Check if service is running"""
        return self.running

