"""
Policy Generator Module
Generates least-privilege policies based on behavioral baseline
"""

import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class PolicyGenerator:
    """Generates least-privilege access policies"""
    
    def __init__(self):
        """Initialize policy generator"""
        pass
    
    def generate_least_privilege_policy(self, device_id: str, baseline: Dict) -> Dict:
        """
        Generate least-privilege policy from behavioral baseline
        
        Args:
            device_id: Device identifier
            baseline: Behavioral baseline dictionary
            
        Returns:
            Policy dictionary
        """
        policy = {
            'device_id': device_id,
            'action': 'allow',
            'rules': []
        }
        
        # Allow access to common destinations
        common_destinations = baseline.get('common_destinations', {})
        for dst_ip, count in list(common_destinations.items())[:5]:  # Top 5 destinations
            policy['rules'].append({
                'type': 'allow',
                'match': {
                    'ipv4_dst': dst_ip
                },
                'priority': 100
            })
        
        # Allow access to common ports
        common_ports = baseline.get('common_ports', {})
        for port, count in list(common_ports.items())[:5]:  # Top 5 ports
            policy['rules'].append({
                'type': 'allow',
                'match': {
                    'tcp_dst': port
                },
                'priority': 100
            })
        
        # Set rate limits based on baseline
        baseline_pps = baseline.get('packets_per_second', 1.0)
        policy['rate_limit'] = {
            'packets_per_second': baseline_pps * 1.5,  # 1.5x baseline
            'bytes_per_second': baseline.get('bytes_per_second', 1000) * 1.5
        }
        
        # Default deny rule
        policy['rules'].append({
            'type': 'deny',
            'match': {},
            'priority': 0
        })
        
        logger.info(f"Generated least-privilege policy for {device_id}: {len(policy['rules'])} rules")
        
        return policy
    
    def policy_to_json(self, policy: Dict) -> str:
        """
        Convert policy to JSON string
        
        Args:
            policy: Policy dictionary
            
        Returns:
            JSON string
        """
        return json.dumps(policy, indent=2)
    
    def policy_from_json(self, policy_json: str) -> Dict:
        """
        Parse policy from JSON string
        
        Args:
            policy_json: JSON string
            
        Returns:
            Policy dictionary
        """
        return json.loads(policy_json)

