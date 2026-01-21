"""
Threat Intelligence Module
Manages and processes threat intelligence from honeypots
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from honeypot_manager.log_parser import HoneypotLogParser

logger = logging.getLogger(__name__)

class ThreatIntelligence:
    """Manages threat intelligence from honeypots"""
    
    def __init__(self, ip_to_device_mapper=None):
        """
        Initialize threat intelligence manager
        
        Args:
            ip_to_device_mapper: Function to map IP address to device_id (optional)
        """
        self.log_parser = HoneypotLogParser()
        self.blocked_ips = {}  # {ip: {'blocked_at': timestamp, 'reason': reason}}
        self.mitigation_rules = []  # List of mitigation rules generated
        self.device_activities = {}  # {device_id: [threat_events]}
        self.ip_to_device_mapper = ip_to_device_mapper  # Function to map IP -> device_id
    
    def process_logs(self, log_content: str) -> List[Dict]:
        """
        Process honeypot logs and extract threat intelligence
        
        Args:
            log_content: Log content as string
            
        Returns:
            List of threat intelligence dictionaries
        """
        threats = self.log_parser.parse_logs(log_content)
        
        # Map IP addresses to device IDs and associate threats with devices
        for threat in threats:
            src_ip = threat.get('source_ip')
            if src_ip and self.ip_to_device_mapper:
                try:
                    device_id = self.ip_to_device_mapper(src_ip)
                    if device_id:
                        threat['device_id'] = device_id
                        # Store in device activities
                        if device_id not in self.device_activities:
                            self.device_activities[device_id] = []
                        self.device_activities[device_id].append(threat)
                        # Keep only last 1000 activities per device
                        if len(self.device_activities[device_id]) > 1000:
                            self.device_activities[device_id] = self.device_activities[device_id][-1000:]
                except Exception as e:
                    logger.debug(f"Failed to map IP {src_ip} to device_id: {e}")
            
            # Analyze threats and generate mitigation rules
            self._analyze_threat(threat)
        
        return threats
    
    def get_device_activity(self, device_id: str, limit: int = 100) -> List[Dict]:
        """
        Get honeypot activity for a specific device
        
        Args:
            device_id: Device identifier
            limit: Maximum number of activities to return
            
        Returns:
            List of threat dictionaries for the device
        """
        activities = self.device_activities.get(device_id, [])
        return activities[-limit:] if limit else activities
    
    def get_device_activity_count(self, device_id: str) -> int:
        """
        Get count of honeypot activities for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Number of activities
        """
        return len(self.device_activities.get(device_id, []))
    
    def _analyze_threat(self, threat: Dict):
        """
        Analyze a threat and determine if mitigation is needed
        
        Args:
            threat: Threat intelligence dictionary
        """
        src_ip = threat.get('source_ip')
        if not src_ip:
            return
        
        event_type = threat.get('event_type', '')
        
        # Determine threat severity
        severity = 'low'
        if event_type in ['cowrie.login.success', 'cowrie.session.file_download']:
            severity = 'high'
        elif event_type in ['cowrie.command.input']:
            # Check for malicious commands
            command = threat.get('command', '').lower()
            malicious_keywords = ['rm', 'delete', 'format', 'dd', 'mkfs', 'shutdown', 'reboot']
            if any(keyword in command for keyword in malicious_keywords):
                severity = 'high'
            else:
                severity = 'medium'
        
        # Block IP if high severity
        if severity == 'high':
            self.block_ip(src_ip, f"High severity threat: {event_type}")
            logger.warning(f"Blocked IP {src_ip} due to {event_type}")
    
    def block_ip(self, ip_address: str, reason: str):
        """
        Block an IP address
        
        Args:
            ip_address: IP address to block
            reason: Reason for blocking
        """
        self.blocked_ips[ip_address] = {
            'blocked_at': datetime.utcnow().isoformat(),
            'reason': reason
        }
        
        # Generate mitigation rule
        rule = {
            'type': 'deny',
            'match_fields': {
                'ipv4_src': ip_address
            },
            'priority': 200,
            'reason': reason,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        self.mitigation_rules.append(rule)
        logger.info(f"Generated mitigation rule for {ip_address}: {reason}")
    
    def is_blocked(self, ip_address: str) -> bool:
        """
        Check if an IP address is blocked
        
        Args:
            ip_address: IP address to check
            
        Returns:
            True if blocked, False otherwise
        """
        return ip_address in self.blocked_ips
    
    def get_blocked_ips(self) -> List[str]:
        """
        Get list of blocked IP addresses
        
        Returns:
            List of blocked IP addresses
        """
        return list(self.blocked_ips.keys())
    
    def get_mitigation_rules(self) -> List[Dict]:
        """
        Get all mitigation rules
        
        Returns:
            List of mitigation rule dictionaries
        """
        return self.mitigation_rules
    
    def get_recent_threats(self, limit: int = 50) -> List[Dict]:
        """
        Get recent threats
        
        Args:
            limit: Maximum number of threats to return
            
        Returns:
            List of threat dictionaries
        """
        return self.log_parser.get_recent_threats(limit)
    
    def get_statistics(self) -> Dict:
        """
        Get threat intelligence statistics
        
        Returns:
            Statistics dictionary
        """
        stats = self.log_parser.get_statistics()
        stats['blocked_ips'] = len(self.blocked_ips)
        stats['mitigation_rules'] = len(self.mitigation_rules)
        return stats

