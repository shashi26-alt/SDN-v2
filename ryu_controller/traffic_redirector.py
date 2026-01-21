"""
Traffic Redirection Module
Handles redirection of suspicious traffic to honeypot network
"""

import logging
from datetime import datetime
from .openflow_rules import OpenFlowRuleGenerator

logger = logging.getLogger(__name__)

class TrafficRedirector:
    """Manages traffic redirection to honeypots"""
    
    def __init__(self, datapath, honeypot_port=3):
        """
        Initialize traffic redirector
        
        Args:
            datapath: Ryu datapath object
            honeypot_port: Port number where honeypot is connected
        """
        self.datapath = datapath
        self.honeypot_port = honeypot_port
        self.rule_generator = OpenFlowRuleGenerator(datapath)
        # Track active redirects with metadata: {device_id: {'match_fields': {...}, 'timestamp': ..., 'reason': ...}}
        self.active_redirects = {}
        
    def redirect_to_honeypot(self, device_id, match_fields, priority=150, reason=None):
        """
        Redirect traffic from a device to the honeypot
        
        Args:
            device_id: Identifier of the device
            match_fields: Match fields to identify device traffic
            priority: Rule priority
            reason: Reason for redirection (optional)
            
        Returns:
            True if redirect successful, False otherwise
        """
        try:
            # Create redirect rule
            flow_mod = self.rule_generator.create_redirect_rule(
                match_fields=match_fields,
                output_port=self.honeypot_port,
                priority=priority,
                cookie=self._device_cookie(device_id)
            )
            
            # Install rule
            self.rule_generator.install_rule(flow_mod)
            
            # Track active redirect with metadata
            self.active_redirects[device_id] = {
                'match_fields': match_fields,
                'timestamp': datetime.utcnow().isoformat(),
                'reason': reason or 'suspicious_activity',
                'priority': priority
            }
            
            logger.warning(f"Redirected traffic from {device_id} to honeypot (port {self.honeypot_port}, reason: {reason})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to redirect traffic for {device_id}: {e}")
            return False
    
    def remove_redirect(self, device_id):
        """
        Remove redirect rule for a device
        
        Args:
            device_id: Identifier of the device
        """
        if device_id not in self.active_redirects:
            logger.warning(f"No active redirect found for {device_id}")
            return
        
        try:
            redirect_info = self.active_redirects[device_id]
            match_fields = redirect_info.get('match_fields', {})
            flow_mod = self.rule_generator.delete_rule(
                match_fields=match_fields,
                cookie=self._device_cookie(device_id)
            )
            
            self.rule_generator.install_rule(flow_mod)
            del self.active_redirects[device_id]
            
            logger.info(f"Removed redirect for {device_id}")
            
        except Exception as e:
            logger.error(f"Failed to remove redirect for {device_id}: {e}")
    
    def get_redirected_devices(self):
        """
        Get list of all devices with active redirects and their metadata
        
        Returns:
            Dictionary of {device_id: redirect_metadata}
        """
        return self.active_redirects.copy()
    
    def is_redirected(self, device_id):
        """
        Check if a device's traffic is currently being redirected
        
        Args:
            device_id: Identifier of the device
            
        Returns:
            True if redirected, False otherwise
        """
        return device_id in self.active_redirects
    
    def get_active_redirects(self):
        """
        Get list of all devices with active redirects
        
        Returns:
            List of device IDs
        """
        return list(self.active_redirects.keys())
    
    def _device_cookie(self, device_id):
        """
        Generate a cookie value for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Cookie value (hash of device_id)
        """
        return hash(device_id) & 0xFFFFFFFFFFFFFFFF  # 64-bit cookie

