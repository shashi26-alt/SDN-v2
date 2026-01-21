"""
Behavioral Profiler Module
Establishes behavioral baselines for newly onboarded devices
"""

import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class BehavioralProfiler:
    """Profiles device behavior to establish baseline"""
    
    def __init__(self, profiling_duration=300):  # 5 minutes default
        """
        Initialize behavioral profiler
        
        Args:
            profiling_duration: Duration in seconds to profile device behavior
        """
        self.profiling_duration = profiling_duration
        self.device_profiles = {}  # {device_id: profile_data}
        self.active_profiling = {}  # {device_id: {'start_time': timestamp, 'traffic': []}}
        self.traffic_history = defaultdict(lambda: deque(maxlen=1000))  # Store recent traffic
    
    def start_profiling(self, device_id: str):
        """
        Start profiling a device
        
        Args:
            device_id: Device identifier
        """
        self.active_profiling[device_id] = {
            'start_time': time.time(),
            'traffic': [],
            'packet_count': 0,
            'byte_count': 0,
            'destinations': defaultdict(int),
            'ports': defaultdict(int),
            'protocols': defaultdict(int)
        }
        
        logger.info(f"Started profiling device {device_id}")
    
    def record_traffic(self, device_id: str, packet_info: Dict):
        """
        Record traffic for a device during profiling
        
        Args:
            device_id: Device identifier
            packet_info: Dictionary with packet information
                - size: Packet size in bytes
                - dst_ip: Destination IP
                - dst_port: Destination port
                - protocol: Protocol number
        """
        if device_id not in self.active_profiling:
            return
        
        profile = self.active_profiling[device_id]
        profile['traffic'].append({
            'timestamp': time.time(),
            **packet_info
        })
        
        profile['packet_count'] += 1
        profile['byte_count'] += packet_info.get('size', 0)
        
        if 'dst_ip' in packet_info:
            profile['destinations'][packet_info['dst_ip']] += 1
        if 'dst_port' in packet_info:
            profile['ports'][packet_info['dst_port']] += 1
        if 'protocol' in packet_info:
            profile['protocols'][packet_info['protocol']] += 1
        
        # Also store in history
        self.traffic_history[device_id].append({
            'timestamp': time.time(),
            **packet_info
        })
    
    def finish_profiling(self, device_id: str) -> Dict:
        """
        Finish profiling and generate baseline
        
        Args:
            device_id: Device identifier
            
        Returns:
            Baseline profile dictionary
        """
        if device_id not in self.active_profiling:
            logger.warning(f"No active profiling for {device_id}")
            return None
        
        profile = self.active_profiling[device_id]
        elapsed_time = time.time() - profile['start_time']
        
        # Calculate baseline metrics
        baseline = {
            'device_id': device_id,
            'profiling_duration': elapsed_time,
            'packet_count': profile['packet_count'],
            'byte_count': profile['byte_count'],
            'avg_packet_size': profile['byte_count'] / max(profile['packet_count'], 1),
            'packets_per_second': profile['packet_count'] / max(elapsed_time, 1),
            'bytes_per_second': profile['byte_count'] / max(elapsed_time, 1),
            'common_destinations': dict(sorted(
                profile['destinations'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # Top 10 destinations
            'common_ports': dict(sorted(
                profile['ports'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # Top 10 ports
            'protocols': dict(profile['protocols']),
            'established_at': datetime.utcnow().isoformat()
        }
        
        # Store baseline
        self.device_profiles[device_id] = baseline
        
        # Remove from active profiling
        del self.active_profiling[device_id]
        
        logger.info(f"Baseline established for {device_id}: {baseline['packet_count']} packets, {baseline['packets_per_second']:.2f} pps")
        
        return baseline
    
    def get_baseline(self, device_id: str) -> Dict:
        """
        Get baseline for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Baseline profile dictionary or None
        """
        return self.device_profiles.get(device_id)
    
    def is_profiling_expired(self, device_id: str) -> bool:
        """
        Check if profiling period has expired for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if profiling period has expired, False otherwise
        """
        if device_id not in self.active_profiling:
            return False
        
        profile = self.active_profiling[device_id]
        elapsed_time = time.time() - profile['start_time']
        return elapsed_time >= self.profiling_duration
    
    def get_active_profiling_devices(self) -> List[str]:
        """
        Get list of device IDs currently being profiled
        
        Returns:
            List of device IDs in active profiling
        """
        return list(self.active_profiling.keys())
    
    def get_profiling_elapsed_time(self, device_id: str) -> float:
        """
        Get elapsed time for a device's profiling
        
        Args:
            device_id: Device identifier
            
        Returns:
            Elapsed time in seconds, or 0 if not profiling
        """
        if device_id not in self.active_profiling:
            return 0.0
        
        profile = self.active_profiling[device_id]
        return time.time() - profile['start_time']
    
    def get_profiling_status(self, device_id: str) -> Optional[Dict]:
        """
        Get current profiling status for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Dictionary with profiling status (packet_count, byte_count, elapsed_time) or None
        """
        if device_id not in self.active_profiling:
            return None
        
        profile = self.active_profiling[device_id]
        return {
            'packet_count': profile.get('packet_count', 0),
            'byte_count': profile.get('byte_count', 0),
            'elapsed_time': time.time() - profile['start_time'],
            'start_time': profile['start_time']
        }
    
    def check_anomaly(self, device_id: str, current_metrics: Dict) -> Dict:
        """
        Check if current behavior deviates from baseline
        
        Args:
            device_id: Device identifier
            current_metrics: Current traffic metrics
            
        Returns:
            Anomaly detection result with score and indicators
        """
        baseline = self.get_baseline(device_id)
        if not baseline:
            return {
                'is_anomaly': False,
                'score': 0,
                'reason': 'No baseline available'
            }
        
        anomaly_score = 0
        indicators = []
        
        # Check packet rate
        current_pps = current_metrics.get('packets_per_second', 0)
        baseline_pps = baseline.get('packets_per_second', 0)
        if baseline_pps > 0:
            pps_ratio = current_pps / baseline_pps
            if pps_ratio > 2.0:  # 2x normal rate
                anomaly_score += 30
                indicators.append(f"High packet rate: {current_pps:.2f} pps (baseline: {baseline_pps:.2f})")
            elif pps_ratio > 5.0:  # 5x normal rate
                anomaly_score += 50
                indicators.append(f"Very high packet rate: {current_pps:.2f} pps (baseline: {baseline_pps:.2f})")
        
        # Check byte rate
        current_bps = current_metrics.get('bytes_per_second', 0)
        baseline_bps = baseline.get('bytes_per_second', 0)
        if baseline_bps > 0:
            bps_ratio = current_bps / baseline_bps
            if bps_ratio > 2.0:
                anomaly_score += 20
                indicators.append(f"High byte rate: {current_bps:.2f} Bps (baseline: {baseline_bps:.2f})")
        
        # Check for new destinations
        current_destinations = set(current_metrics.get('destinations', {}).keys())
        baseline_destinations = set(baseline.get('common_destinations', {}).keys())
        new_destinations = current_destinations - baseline_destinations
        if len(new_destinations) > 5:
            anomaly_score += 25
            indicators.append(f"Many new destinations: {len(new_destinations)}")
        
        # Check for new ports
        current_ports = set(current_metrics.get('ports', {}).keys())
        baseline_ports = set(baseline.get('common_ports', {}).keys())
        new_ports = current_ports - baseline_ports
        if len(new_ports) > 10:
            anomaly_score += 15
            indicators.append(f"Many new ports: {len(new_ports)}")
        
        return {
            'is_anomaly': anomaly_score > 50,
            'score': anomaly_score,
            'indicators': indicators,
            'baseline': baseline
        }

