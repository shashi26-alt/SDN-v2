"""
Simple DDoS Detector Module
Heuristic-based DDoS attack detection using traffic pattern analysis
"""

import logging
from collections import deque
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimpleDDoSDetector:
    """
    Simple heuristic-based DDoS detector
    Detects DDoS attacks using traffic rate thresholds and pattern analysis
    """
    
    def __init__(self):
        """Initialize the DDoS detector"""
        # Detection thresholds
        self.packet_rate_threshold = 1000.0  # packets per second
        self.byte_rate_threshold = 10000000.0  # 10 MB/s
        self.duration_threshold = 10.0  # seconds
        self.pps_threshold = 1000.0  # packets per second
        
        # Traffic history for pattern analysis
        self.traffic_history = deque(maxlen=1000)  # Store last 1000 packets
        self.attack_history = deque(maxlen=100)  # Store detected attacks
        
        # Statistics
        self.total_packets = 0
        self.detected_attacks = 0
        self.false_positives = 0
        
        logger.info("SimpleDDoSDetector initialized")
    
    def detect(self, packet: Optional[Dict] = None, **kwargs) -> Dict:
        """
        Detect DDoS attack from packet or traffic statistics
        
        Args:
            packet: Packet information dictionary with keys:
                - size: Packet size in bytes
                - protocol: Protocol number (6=TCP, 17=UDP, etc.)
                - rate: Traffic rate
                - pps: Packets per second
                - duration: Attack duration in seconds
            **kwargs: Additional packet attributes
        
        Returns:
            Dictionary with detection results:
                - is_attack: Boolean indicating if attack detected
                - attack_type: Type of attack ('ddos', 'flood', 'volume', None)
                - confidence: Confidence score (0.0-1.0)
                - reason: Reason for detection
                - severity: Severity level ('low', 'medium', 'high')
        """
        # Merge packet dict with kwargs
        if packet is None:
            packet = {}
        packet = {**packet, **kwargs}
        
        self.total_packets += 1
        
        # Extract packet attributes
        size = packet.get('size', 0)
        protocol = packet.get('protocol', 0)
        rate = packet.get('rate', 0.0)
        pps = packet.get('pps', 0.0)
        duration = packet.get('duration', 0.0)
        
        # Store in history
        self.traffic_history.append({
            'size': size,
            'protocol': protocol,
            'rate': rate,
            'pps': pps,
            'timestamp': datetime.utcnow()
        })
        
        # Detection logic
        is_attack = False
        attack_type = None
        confidence = 0.0
        reason = ""
        severity = "low"
        
        # Check packet rate (packets per second)
        if pps > self.pps_threshold * 10:  # 10x threshold
            is_attack = True
            attack_type = 'ddos'
            confidence = 0.95
            reason = f"Extremely high packet rate: {pps:.2f} pps (threshold: {self.pps_threshold} pps)"
            severity = 'high'
        elif pps > self.pps_threshold * 5:  # 5x threshold
            is_attack = True
            attack_type = 'ddos'
            confidence = 0.85
            reason = f"Very high packet rate: {pps:.2f} pps (threshold: {self.pps_threshold} pps)"
            severity = 'high'
        elif pps > self.pps_threshold:  # Above threshold
            is_attack = True
            attack_type = 'ddos'
            confidence = 0.70
            reason = f"High packet rate: {pps:.2f} pps (threshold: {self.pps_threshold} pps)"
            severity = 'medium'
        
        # Check byte rate (volume attack)
        byte_rate = rate * size if rate > 0 and size > 0 else 0
        if byte_rate > self.byte_rate_threshold * 10:  # 10x threshold
            is_attack = True
            attack_type = 'volume'
            confidence = max(confidence, 0.90)
            reason = f"Extremely high byte rate: {byte_rate:.2f} Bps (threshold: {self.byte_rate_threshold} Bps)"
            severity = 'high'
        elif byte_rate > self.byte_rate_threshold * 5:  # 5x threshold
            is_attack = True
            attack_type = 'volume'
            confidence = max(confidence, 0.80)
            reason = f"Very high byte rate: {byte_rate:.2f} Bps (threshold: {self.byte_rate_threshold} Bps)"
            severity = 'high'
        elif byte_rate > self.byte_rate_threshold:  # Above threshold
            if not is_attack:
                is_attack = True
                attack_type = 'volume'
                confidence = 0.65
                reason = f"High byte rate: {byte_rate:.2f} Bps (threshold: {self.byte_rate_threshold} Bps)"
                severity = 'medium'
        
        # Check duration (sustained attack)
        if duration > self.duration_threshold * 2:  # 2x threshold
            if is_attack:
                confidence = min(confidence + 0.10, 1.0)  # Increase confidence for sustained attacks
                reason += f" (sustained for {duration:.2f}s)"
                if severity == 'medium':
                    severity = 'high'
        
        # Check for flood pattern (many small packets)
        if size < 100 and pps > self.pps_threshold * 2:
            if not is_attack:
                is_attack = True
                attack_type = 'flood'
                confidence = 0.75
                reason = f"Flood pattern detected: {pps:.2f} pps with small packets ({size} bytes)"
                severity = 'medium'
        
        # Record detection
        if is_attack:
            self.detected_attacks += 1
            self.attack_history.append({
                'attack_type': attack_type,
                'confidence': confidence,
                'reason': reason,
                'severity': severity,
                'timestamp': datetime.utcnow(),
                'packet_info': {
                    'size': size,
                    'protocol': protocol,
                    'rate': rate,
                    'pps': pps,
                    'duration': duration
                }
            })
            logger.warning(f"DDoS attack detected: {reason}")
        
        # Calculate attack score (0-100) from confidence
        attack_score = confidence * 100 if is_attack else 0.0
        
        # Build indicators list
        indicators = []
        if reason:
            indicators.append(reason)
        if is_attack:
            if attack_type == 'ddos':
                indicators.append(f"High packet rate: {pps:.2f} pps")
            elif attack_type == 'volume':
                byte_rate = rate * size if rate > 0 and size > 0 else 0
                indicators.append(f"High byte rate: {byte_rate:.2f} Bps")
            elif attack_type == 'flood':
                indicators.append(f"Flood pattern: {pps:.2f} pps with small packets")
        
        return {
            'is_attack': is_attack,
            'attack_type': attack_type,
            'confidence': confidence,
            'attack_score': attack_score,
            'reason': reason,
            'severity': severity,
            'indicators': indicators,
            'packet_info': {
                'size': size,
                'protocol': protocol,
                'rate': rate,
                'pps': pps,
                'duration': duration
            }
        }
    
    def analyze(self, packet: Dict) -> Dict:
        """
        Alias for detect() method for compatibility
        
        Args:
            packet: Packet information dictionary
        
        Returns:
            Detection result dictionary
        """
        return self.detect(packet=packet)
    
    def get_statistics(self) -> Dict:
        """
        Get detector statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_packets': self.total_packets,
            'detected_attacks': self.detected_attacks,
            'false_positives': self.false_positives,
            'detection_rate': self.detected_attacks / max(self.total_packets, 1) * 100,
            'recent_attacks': len(self.attack_history),
            'thresholds': {
                'packet_rate': self.packet_rate_threshold,
                'byte_rate': self.byte_rate_threshold,
                'duration': self.duration_threshold,
                'pps': self.pps_threshold
            }
        }
    
    def get_recent_attacks(self, limit: int = 10) -> list:
        """
        Get recent attack detections
        
        Args:
            limit: Maximum number of attacks to return
        
        Returns:
            List of recent attack dictionaries
        """
        return list(self.attack_history)[-limit:]
    
    def reset_statistics(self):
        """Reset detector statistics"""
        self.total_packets = 0
        self.detected_attacks = 0
        self.false_positives = 0
        self.traffic_history.clear()
        self.attack_history.clear()
        logger.info("DDoS detector statistics reset")
    
    def update_thresholds(self, **kwargs):
        """
        Update detection thresholds
        
        Args:
            **kwargs: Threshold values to update:
                - packet_rate_threshold: Packets per second threshold
                - byte_rate_threshold: Bytes per second threshold
                - duration_threshold: Duration threshold in seconds
                - pps_threshold: Packets per second threshold
        """
        if 'packet_rate_threshold' in kwargs:
            self.packet_rate_threshold = kwargs['packet_rate_threshold']
        if 'byte_rate_threshold' in kwargs:
            self.byte_rate_threshold = kwargs['byte_rate_threshold']
        if 'duration_threshold' in kwargs:
            self.duration_threshold = kwargs['duration_threshold']
        if 'pps_threshold' in kwargs:
            self.pps_threshold = kwargs['pps_threshold']
        logger.info(f"Updated thresholds: {kwargs}")

