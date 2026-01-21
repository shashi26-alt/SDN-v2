"""
Device Attestation Module
Continuous device integrity verification
"""

import logging
import time
import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DeviceAttestation:
    """Manages device attestation for continuous verification"""
    
    def __init__(self, attestation_interval: int = 300):  # 5 minutes default
        """
        Initialize device attestation
        
        Args:
            attestation_interval: Interval in seconds between attestation checks
        """
        self.attestation_interval = attestation_interval
        self.device_attestations = {}  # {device_id: {'last_check': timestamp, 'status': str, 'certificate_valid': bool}}
        self.attestation_history = {}  # {device_id: [(timestamp, status, result)]}
        self.running = False
    
    def start_attestation(self, device_id: str):
        """
        Start attestation for a device
        
        Args:
            device_id: Device identifier
        """
        self.device_attestations[device_id] = {
            'last_check': None,
            'status': 'pending',
            'certificate_valid': None,
            'heartbeat_received': False,
            'last_heartbeat': None
        }
        logger.info(f"Attestation started for {device_id}")
    
    def perform_attestation(self, device_id: str, certificate_path: Optional[str] = None,
                          certificate_manager=None) -> Dict:
        """
        Perform attestation check for a device
        
        Args:
            device_id: Device identifier
            certificate_path: Path to device certificate
            certificate_manager: Certificate manager instance (optional)
            
        Returns:
            Attestation result dictionary
        """
        if device_id not in self.device_attestations:
            self.start_attestation(device_id)
        
        attestation_data = self.device_attestations[device_id]
        current_time = time.time()
        
        result = {
            'device_id': device_id,
            'timestamp': datetime.utcnow().isoformat(),
            'passed': True,
            'checks': {}
        }
        
        # Check 1: Certificate validity
        if certificate_manager and certificate_path:
            cert_valid = certificate_manager.verify_certificate(certificate_path)
            result['checks']['certificate'] = {
                'passed': cert_valid,
                'message': 'Certificate valid' if cert_valid else 'Certificate invalid or expired'
            }
            attestation_data['certificate_valid'] = cert_valid
            if not cert_valid:
                result['passed'] = False
        else:
            result['checks']['certificate'] = {
                'passed': True,
                'message': 'Certificate check skipped (no certificate manager)'
            }
        
        # Check 2: Heartbeat (device is alive and responding)
        last_heartbeat = attestation_data.get('last_heartbeat')
        if last_heartbeat:
            time_since_heartbeat = current_time - last_heartbeat
            heartbeat_valid = time_since_heartbeat < (self.attestation_interval * 2)
            result['checks']['heartbeat'] = {
                'passed': heartbeat_valid,
                'message': f'Heartbeat received {time_since_heartbeat:.0f}s ago' if heartbeat_valid else 'No recent heartbeat'
            }
            if not heartbeat_valid:
                result['passed'] = False
        else:
            result['checks']['heartbeat'] = {
                'passed': False,
                'message': 'No heartbeat received'
            }
            result['passed'] = False
        
        # Check 3: Time since last check (device should be checked regularly)
        last_check = attestation_data.get('last_check')
        if last_check:
            time_since_check = current_time - last_check
            check_frequency_ok = time_since_check < (self.attestation_interval * 3)
            result['checks']['frequency'] = {
                'passed': check_frequency_ok,
                'message': f'Last check {time_since_check:.0f}s ago'
            }
        else:
            result['checks']['frequency'] = {
                'passed': True,
                'message': 'First attestation check'
            }
        
        # Update attestation data
        attestation_data['last_check'] = current_time
        attestation_data['status'] = 'passed' if result['passed'] else 'failed'
        
        # Record in history
        self._record_attestation(device_id, result)
        
        if result['passed']:
            logger.info(f"Attestation passed for {device_id}")
        else:
            logger.warning(f"Attestation failed for {device_id}: {result['checks']}")
        
        return result
    
    def record_heartbeat(self, device_id: str):
        """
        Record heartbeat from a device
        
        Args:
            device_id: Device identifier
        """
        if device_id not in self.device_attestations:
            self.start_attestation(device_id)
        
        self.device_attestations[device_id]['heartbeat_received'] = True
        self.device_attestations[device_id]['last_heartbeat'] = time.time()
        
        logger.debug(f"Heartbeat received from {device_id}")
    
    def get_attestation_status(self, device_id: str) -> Optional[Dict]:
        """
        Get attestation status for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Attestation status dictionary or None
        """
        if device_id not in self.device_attestations:
            return None
        
        data = self.device_attestations[device_id]
        current_time = time.time()
        
        status = {
            'device_id': device_id,
            'status': data['status'],
            'last_check': data.get('last_check'),
            'time_since_check': current_time - data.get('last_check', 0) if data.get('last_check') else None,
            'certificate_valid': data.get('certificate_valid'),
            'heartbeat_received': data.get('heartbeat_received', False),
            'last_heartbeat': data.get('last_heartbeat'),
            'time_since_heartbeat': current_time - data.get('last_heartbeat', 0) if data.get('last_heartbeat') else None
        }
        
        return status
    
    def get_attestation_history(self, device_id: str, limit: int = 50) -> list:
        """
        Get attestation history for a device
        
        Args:
            device_id: Device identifier
            limit: Maximum number of history entries
            
        Returns:
            List of attestation result dictionaries
        """
        if device_id not in self.attestation_history:
            return []
        
        return self.attestation_history[device_id][-limit:]
    
    def _record_attestation(self, device_id: str, result: Dict):
        """
        Record attestation result in history
        
        Args:
            device_id: Device identifier
            result: Attestation result dictionary
        """
        if device_id not in self.attestation_history:
            self.attestation_history[device_id] = []
        
        self.attestation_history[device_id].append(result)
        
        # Keep only last 1000 entries
        if len(self.attestation_history[device_id]) > 1000:
            self.attestation_history[device_id] = self.attestation_history[device_id][-1000:]
    
    def get_all_attestation_statuses(self) -> Dict[str, Dict]:
        """
        Get attestation status for all devices
        
        Returns:
            Dictionary mapping device_id to attestation status
        """
        return {
            device_id: self.get_attestation_status(device_id)
            for device_id in self.device_attestations.keys()
        }

