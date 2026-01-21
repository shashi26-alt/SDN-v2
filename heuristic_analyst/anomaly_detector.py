"""
Anomaly Detector Module
Heuristic-based anomaly detection using flow statistics
"""

import logging
import time
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Detects anomalies using heuristic rules"""
    
    def __init__(self):
        """Initialize anomaly detector"""
        self.baselines = {}  # {device_id: baseline_metrics}
        self.alert_history = []  # Store recent alerts
        
    def set_baseline(self, device_id: str, baseline: Dict):
        """
        Set baseline for a device
        
        Args:
            device_id: Device identifier
            baseline: Baseline metrics dictionary
        """
        self.baselines[device_id] = baseline
        logger.info(f"Baseline set for {device_id}")
    
    def detect_anomalies(self, device_id: str, current_stats: Dict) -> Dict:
        """
        Detect anomalies in device behavior
        
        Args:
            device_id: Device identifier
            current_stats: Current flow statistics
            
        Returns:
            Anomaly detection result
        """
        if not current_stats:
            return {
                'is_anomaly': False,
                'anomaly_type': None,
                'severity': None,
                'indicators': []
            }
        
        baseline = self.baselines.get(device_id)
        if not baseline:
            # No baseline available, use default thresholds
            return self._detect_without_baseline(device_id, current_stats)
        
        anomalies = []
        severity_score = 0
        
        # Check packet rate anomaly
        current_pps = current_stats.get('packets_per_second', 0)
        baseline_pps = baseline.get('packets_per_second', 1.0)
        
        if baseline_pps > 0:
            pps_ratio = current_pps / baseline_pps
            if pps_ratio > 10.0:  # 10x normal
                anomalies.append({
                    'type': 'dos',
                    'indicator': f'Extremely high packet rate: {current_pps:.2f} pps (baseline: {baseline_pps:.2f})',
                    'severity': 'high'
                })
                severity_score += 50
            elif pps_ratio > 5.0:  # 5x normal
                anomalies.append({
                    'type': 'dos',
                    'indicator': f'Very high packet rate: {current_pps:.2f} pps (baseline: {baseline_pps:.2f})',
                    'severity': 'high'
                })
                severity_score += 30
            elif pps_ratio > 2.0:  # 2x normal
                anomalies.append({
                    'type': 'dos',
                    'indicator': f'High packet rate: {current_pps:.2f} pps (baseline: {baseline_pps:.2f})',
                    'severity': 'medium'
                })
                severity_score += 15
        
        # Check byte rate anomaly
        current_bps = current_stats.get('bytes_per_second', 0)
        baseline_bps = baseline.get('bytes_per_second', 1000.0)
        
        if baseline_bps > 0:
            bps_ratio = current_bps / baseline_bps
            if bps_ratio > 10.0:
                anomalies.append({
                    'type': 'volume_attack',
                    'indicator': f'Extremely high byte rate: {current_bps:.2f} Bps (baseline: {baseline_bps:.2f})',
                    'severity': 'high'
                })
                severity_score += 40
        
        # Check for scanning behavior (many unique destinations/ports)
        unique_destinations = current_stats.get('unique_destinations', 0)
        baseline_destinations = baseline.get('common_destinations', {})
        baseline_dest_count = len(baseline_destinations)
        
        if unique_destinations > baseline_dest_count * 5 and unique_destinations > 20:
            anomalies.append({
                'type': 'scanning',
                'indicator': f'Scanning behavior: {unique_destinations} unique destinations (baseline: {baseline_dest_count})',
                'severity': 'medium'
            })
            severity_score += 25
        
        unique_ports = current_stats.get('unique_ports', 0)
        baseline_ports = baseline.get('common_ports', {})
        baseline_port_count = len(baseline_ports)
        
        if unique_ports > baseline_port_count * 3 and unique_ports > 10:
            anomalies.append({
                'type': 'port_scanning',
                'indicator': f'Port scanning: {unique_ports} unique ports (baseline: {baseline_port_count})',
                'severity': 'medium'
            })
            severity_score += 20
        
        # Determine overall severity
        if severity_score >= 70:
            overall_severity = 'high'
        elif severity_score >= 40:
            overall_severity = 'medium'
        elif severity_score >= 20:
            overall_severity = 'low'
        else:
            overall_severity = None
        
        # Determine anomaly type
        if anomalies:
            # Get most severe anomaly type
            anomaly_types = [a['type'] for a in anomalies]
            if 'dos' in anomaly_types or 'volume_attack' in anomaly_types:
                anomaly_type = 'dos'
            elif 'scanning' in anomaly_types or 'port_scanning' in anomaly_types:
                anomaly_type = 'scanning'
            else:
                anomaly_type = 'anomaly'
        else:
            anomaly_type = None
        
        result = {
            'is_anomaly': len(anomalies) > 0,
            'anomaly_type': anomaly_type,
            'severity': overall_severity,
            'severity_score': severity_score,
            'indicators': [a['indicator'] for a in anomalies],
            'anomalies': anomalies
        }
        
        if result['is_anomaly']:
            logger.warning(f"Anomaly detected for {device_id}: {anomaly_type} (severity: {overall_severity})")
            self.alert_history.append({
                'device_id': device_id,
                'timestamp': time.time(),
                **result
            })
            # Keep only last 100 alerts
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]
        
        return result
    
    def _detect_without_baseline(self, device_id: str, current_stats: Dict) -> Dict:
        """
        Detect anomalies without baseline (use absolute thresholds)
        
        Args:
            device_id: Device identifier
            current_stats: Current flow statistics
            
        Returns:
            Anomaly detection result
        """
        anomalies = []
        severity_score = 0
        
        # Absolute thresholds
        pps = current_stats.get('packets_per_second', 0)
        if pps > 10000:  # Very high packet rate
            anomalies.append({
                'type': 'dos',
                'indicator': f'Extremely high packet rate: {pps:.2f} pps',
                'severity': 'high'
            })
            severity_score += 50
        elif pps > 5000:
            anomalies.append({
                'type': 'dos',
                'indicator': f'Very high packet rate: {pps:.2f} pps',
                'severity': 'high'
            })
            severity_score += 30
        
        bps = current_stats.get('bytes_per_second', 0)
        if bps > 10000000:  # 10 MB/s
            anomalies.append({
                'type': 'volume_attack',
                'indicator': f'Extremely high byte rate: {bps:.2f} Bps',
                'severity': 'high'
            })
            severity_score += 40
        
        unique_destinations = current_stats.get('unique_destinations', 0)
        if unique_destinations > 50:
            anomalies.append({
                'type': 'scanning',
                'indicator': f'Scanning behavior: {unique_destinations} unique destinations',
                'severity': 'medium'
            })
            severity_score += 25
        
        unique_ports = current_stats.get('unique_ports', 0)
        if unique_ports > 20:
            anomalies.append({
                'type': 'port_scanning',
                'indicator': f'Port scanning: {unique_ports} unique ports',
                'severity': 'medium'
            })
            severity_score += 20
        
        if severity_score >= 70:
            overall_severity = 'high'
        elif severity_score >= 40:
            overall_severity = 'medium'
        elif severity_score >= 20:
            overall_severity = 'low'
        else:
            overall_severity = None
        
        anomaly_type = anomalies[0]['type'] if anomalies else None
        
        return {
            'is_anomaly': len(anomalies) > 0,
            'anomaly_type': anomaly_type,
            'severity': overall_severity,
            'severity_score': severity_score,
            'indicators': [a['indicator'] for a in anomalies],
            'anomalies': anomalies
        }
    
    def get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """
        Get recent alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert dictionaries
        """
        return self.alert_history[-limit:]

