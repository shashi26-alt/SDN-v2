"""
Mitigation Rule Generator Module
Generates automatic mitigation rules from threat intelligence
"""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MitigationGenerator:
    """Generates mitigation rules from threat intelligence"""
    
    def __init__(self, sdn_policy_engine=None):
        """
        Initialize mitigation generator
        
        Args:
            sdn_policy_engine: SDN policy engine instance (optional)
        """
        self.sdn_policy_engine = sdn_policy_engine
        self.generated_rules = []  # Track generated rules
    
    def generate_rules_from_threats(self, threats: List[Dict]) -> List[Dict]:
        """
        Generate mitigation rules from threat intelligence
        
        Args:
            threats: List of threat intelligence dictionaries
            
        Returns:
            List of mitigation rule dictionaries
        """
        rules = []
        
        # Group threats by IP
        ip_threats = {}
        for threat in threats:
            src_ip = threat.get('source_ip')
            if not src_ip:
                continue
            
            if src_ip not in ip_threats:
                ip_threats[src_ip] = []
            ip_threats[src_ip].append(threat)
        
        # Generate rules for each IP
        for ip_address, ip_threat_list in ip_threats.items():
            rule = self._generate_rule_for_ip(ip_address, ip_threat_list)
            if rule:
                rules.append(rule)
        
        # Store generated rules
        self.generated_rules.extend(rules)
        
        # Apply rules to SDN controller if available
        if self.sdn_policy_engine:
            for rule in rules:
                self._apply_rule(rule)
        
        return rules
    
    def _generate_rule_for_ip(self, ip_address: str, threats: List[Dict]) -> Dict:
        """
        Generate mitigation rule for an IP address
        
        Args:
            ip_address: IP address
            threats: List of threats from this IP
            
        Returns:
            Mitigation rule dictionary
        """
        # Count threat types
        threat_types = {}
        for threat in threats:
            event_type = threat.get('event_type', 'unknown')
            threat_types[event_type] = threat_types.get(event_type, 0) + 1
        
        # Determine rule type based on threat severity
        high_severity_events = ['cowrie.login.success', 'cowrie.session.file_download']
        has_high_severity = any(event in threat_types for event in high_severity_events)
        
        if has_high_severity or len(threats) > 5:
            # Deny all traffic from this IP
            rule = {
                'type': 'deny',
                'match_fields': {
                    'ipv4_src': ip_address
                },
                'priority': 200,
                'reason': f"High severity threats: {len(threats)} events",
                'threat_count': len(threats),
                'threat_types': threat_types,
                'generated_at': datetime.utcnow().isoformat()
            }
        elif len(threats) > 2:
            # Redirect to honeypot (already there, but keep monitoring)
            rule = {
                'type': 'redirect',
                'match_fields': {
                    'ipv4_src': ip_address
                },
                'priority': 150,
                'reason': f"Multiple threats detected: {len(threats)} events",
                'threat_count': len(threats),
                'threat_types': threat_types,
                'generated_at': datetime.utcnow().isoformat()
            }
        else:
            # Low severity, just log
            rule = {
                'type': 'monitor',
                'match_fields': {
                    'ipv4_src': ip_address
                },
                'priority': 100,
                'reason': f"Threats detected: {len(threats)} events",
                'threat_count': len(threats),
                'threat_types': threat_types,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        logger.info(f"Generated {rule['type']} rule for {ip_address}: {rule['reason']}")
        return rule
    
    def _apply_rule(self, rule: Dict):
        """
        Apply mitigation rule to SDN controller
        
        Args:
            rule: Mitigation rule dictionary
        """
        if not self.sdn_policy_engine:
            return
        
        try:
            match_fields = rule['match_fields']
            rule_type = rule['type']
            
            # Extract device_id if available (from IP mapping)
            # For now, use IP as identifier
            device_id = match_fields.get('ipv4_src', 'unknown')
            
            if rule_type == 'deny':
                self.sdn_policy_engine.apply_policy(
                    device_id=device_id,
                    action='deny',
                    match_fields=match_fields,
                    priority=rule.get('priority', 200)
                )
            elif rule_type == 'redirect':
                self.sdn_policy_engine.apply_policy(
                    device_id=device_id,
                    action='redirect',
                    match_fields=match_fields,
                    priority=rule.get('priority', 150)
                )
            
            logger.info(f"Applied {rule_type} rule for {device_id}")
            
        except Exception as e:
            logger.error(f"Failed to apply rule: {e}")
    
    def get_generated_rules(self) -> List[Dict]:
        """
        Get all generated rules
        
        Returns:
            List of rule dictionaries
        """
        return self.generated_rules
    
    def set_sdn_policy_engine(self, sdn_policy_engine):
        """
        Set SDN policy engine reference
        
        Args:
            sdn_policy_engine: SDN policy engine instance
        """
        self.sdn_policy_engine = sdn_policy_engine
        logger.info("SDN policy engine connected")

