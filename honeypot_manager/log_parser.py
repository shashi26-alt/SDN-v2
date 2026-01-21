"""
Honeypot Log Parser Module
Parses honeypot logs to extract threat intelligence
"""

import logging
import json
import re
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class HoneypotLogParser:
    """Parses honeypot logs to extract threat intelligence"""
    
    def __init__(self, honeypot_type: str = "cowrie"):
        """
        Initialize log parser
        
        Args:
            honeypot_type: Type of honeypot ('cowrie', 'dionaea', etc.)
        """
        self.honeypot_type = honeypot_type
        self.threat_intelligence = []  # Store extracted intelligence
    
    def parse_logs(self, log_content: str) -> List[Dict]:
        """
        Parse honeypot logs and extract threat intelligence
        
        Args:
            log_content: Log content as string
            
        Returns:
            List of threat intelligence dictionaries
        """
        if self.honeypot_type == "cowrie":
            return self._parse_cowrie_logs(log_content)
        else:
            logger.warning(f"Unknown honeypot type: {self.honeypot_type}")
            return []
    
    def _parse_cowrie_logs(self, log_content: str) -> List[Dict]:
        """
        Parse Cowrie honeypot logs
        
        Args:
            log_content: Log content as string
            
        Returns:
            List of threat intelligence dictionaries
        """
        threats = []
        lines = log_content.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            # Try to parse JSON log entries
            threat = self._parse_cowrie_json_line(line)
            if threat:
                threats.append(threat)
                continue
            
            # Try to parse text log entries
            threat = self._parse_cowrie_text_line(line)
            if threat:
                threats.append(threat)
        
        # Store in threat intelligence
        self.threat_intelligence.extend(threats)
        
        # Keep only last 1000 entries
        if len(self.threat_intelligence) > 1000:
            self.threat_intelligence = self.threat_intelligence[-1000:]
        
        return threats
    
    def _parse_cowrie_json_line(self, line: str) -> Optional[Dict]:
        """
        Parse Cowrie JSON log line
        
        Args:
            line: Log line
            
        Returns:
            Threat intelligence dictionary or None
        """
        try:
            # Try to parse as JSON
            data = json.loads(line)
            
            # Extract relevant information
            event_id = data.get('eventid', '')
            src_ip = data.get('src_ip', '')
            timestamp = data.get('timestamp', datetime.utcnow().isoformat())
            
            threat = {
                'timestamp': timestamp,
                'source_ip': src_ip,
                'event_type': event_id,
                'honeypot_type': 'cowrie'
            }
            
            # Extract additional information based on event type
            if event_id == 'cowrie.login.success' or event_id == 'cowrie.login.failed':
                threat['username'] = data.get('username', '')
                threat['password'] = data.get('password', '')
                threat['message'] = f"Login attempt: {data.get('username', 'unknown')}"
            
            elif event_id == 'cowrie.command.input':
                threat['command'] = data.get('input', '')
                threat['message'] = f"Command executed: {data.get('input', '')}"
            
            elif event_id == 'cowrie.session.file_download':
                threat['url'] = data.get('url', '')
                threat['outfile'] = data.get('outfile', '')
                threat['message'] = f"File download: {data.get('url', '')}"
            
            elif event_id == 'cowrie.client.version':
                threat['version'] = data.get('version', '')
                threat['message'] = f"Client version: {data.get('version', '')}"
            
            else:
                threat['message'] = f"Event: {event_id}"
                threat['raw_data'] = data
            
            return threat
            
        except (json.JSONDecodeError, KeyError):
            return None
    
    def _parse_cowrie_text_line(self, line: str) -> Optional[Dict]:
        """
        Parse Cowrie text log line
        
        Args:
            line: Log line
            
        Returns:
            Threat intelligence dictionary or None
        """
        # Pattern for IP address
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        
        # Extract IP addresses
        ips = re.findall(ip_pattern, line)
        if not ips:
            return None
        
        src_ip = ips[0]
        
        # Extract commands (common patterns)
        command_patterns = [
            r'command[:\s]+([^\n]+)',
            r'executed[:\s]+([^\n]+)',
            r'cmd[:\s]+([^\n]+)'
        ]
        
        command = None
        for pattern in command_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                command = match.group(1).strip()
                break
        
        threat = {
            'timestamp': datetime.utcnow().isoformat(),
            'source_ip': src_ip,
            'event_type': 'unknown',
            'honeypot_type': 'cowrie',
            'message': line[:200]  # First 200 chars
        }
        
        if command:
            threat['command'] = command
            threat['event_type'] = 'command'
            threat['message'] = f"Command: {command}"
        
        return threat
    
    def extract_ips(self) -> List[str]:
        """
        Extract unique IP addresses from threat intelligence
        
        Returns:
            List of unique IP addresses
        """
        ips = set()
        for threat in self.threat_intelligence:
            if 'source_ip' in threat:
                ips.add(threat['source_ip'])
        return list(ips)
    
    def extract_commands(self) -> List[str]:
        """
        Extract commands from threat intelligence
        
        Returns:
            List of unique commands
        """
        commands = set()
        for threat in self.threat_intelligence:
            if 'command' in threat:
                commands.add(threat['command'])
        return list(commands)
    
    def get_recent_threats(self, limit: int = 50) -> List[Dict]:
        """
        Get recent threat intelligence
        
        Args:
            limit: Maximum number of threats to return
            
        Returns:
            List of threat dictionaries
        """
        return self.threat_intelligence[-limit:]
    
    def get_threats_by_ip(self, ip_address: str) -> List[Dict]:
        """
        Get threats from a specific IP address
        
        Args:
            ip_address: IP address
            
        Returns:
            List of threat dictionaries
        """
        return [
            threat for threat in self.threat_intelligence
            if threat.get('source_ip') == ip_address
        ]
    
    def get_statistics(self) -> Dict:
        """
        Get threat intelligence statistics
        
        Returns:
            Statistics dictionary
        """
        total_threats = len(self.threat_intelligence)
        unique_ips = len(self.extract_ips())
        unique_commands = len(self.extract_commands())
        
        # Count by event type
        event_types = {}
        for threat in self.threat_intelligence:
            event_type = threat.get('event_type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            'total_threats': total_threats,
            'unique_ips': unique_ips,
            'unique_commands': unique_commands,
            'event_types': event_types
        }

