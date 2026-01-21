"""
Baseline Manager Module
Manages behavioral baselines for devices
"""

import logging
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BaselineManager:
    """Manages behavioral baselines for anomaly detection"""
    
    def __init__(self, identity_db=None):
        """
        Initialize baseline manager
        
        Args:
            identity_db: Identity database instance (optional)
        """
        self.identity_db = identity_db
        self.baselines = {}  # {device_id: baseline}
    
    def load_baseline(self, device_id: str) -> Optional[Dict]:
        """
        Load baseline for a device from database
        
        Args:
            device_id: Device identifier
            
        Returns:
            Baseline dictionary or None
        """
        if self.identity_db:
            baseline_json = self.identity_db.get_behavioral_baseline(device_id)
            if baseline_json:
                try:
                    baseline = json.loads(baseline_json)
                    self.baselines[device_id] = baseline
                    return baseline
                except Exception as e:
                    logger.error(f"Failed to parse baseline for {device_id}: {e}")
        
        return self.baselines.get(device_id)
    
    def set_baseline(self, device_id: str, baseline: Dict):
        """
        Set baseline for a device
        
        Args:
            device_id: Device identifier
            baseline: Baseline dictionary
        """
        self.baselines[device_id] = baseline
        logger.info(f"Baseline set for {device_id}")
    
    def get_baseline(self, device_id: str) -> Optional[Dict]:
        """
        Get baseline for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Baseline dictionary or None
        """
        # Try to load from database if not in memory
        if device_id not in self.baselines and self.identity_db:
            return self.load_baseline(device_id)
        
        return self.baselines.get(device_id)
    
    def update_baseline(self, device_id: str, new_metrics: Dict):
        """
        Update baseline with new metrics (adaptive baseline)
        
        Args:
            device_id: Device identifier
            new_metrics: New metrics to incorporate
        """
        baseline = self.get_baseline(device_id)
        if not baseline:
            # Create new baseline
            self.set_baseline(device_id, new_metrics)
            return
        
        # Update baseline with exponential moving average
        alpha = 0.1  # Smoothing factor
        
        baseline['packets_per_second'] = (
            alpha * new_metrics.get('packets_per_second', 0) +
            (1 - alpha) * baseline.get('packets_per_second', 0)
        )
        
        baseline['bytes_per_second'] = (
            alpha * new_metrics.get('bytes_per_second', 0) +
            (1 - alpha) * baseline.get('bytes_per_second', 0)
        )
        
        # Update common destinations (merge)
        new_destinations = new_metrics.get('common_destinations', {})
        baseline_destinations = baseline.get('common_destinations', {})
        
        for dst, count in new_destinations.items():
            if dst in baseline_destinations:
                baseline_destinations[dst] = int(
                    alpha * count + (1 - alpha) * baseline_destinations[dst]
                )
            else:
                baseline_destinations[dst] = count
        
        baseline['common_destinations'] = dict(sorted(
            baseline_destinations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        # Update common ports (merge)
        new_ports = new_metrics.get('common_ports', {})
        baseline_ports = baseline.get('common_ports', {})
        
        for port, count in new_ports.items():
            if port in baseline_ports:
                baseline_ports[port] = int(
                    alpha * count + (1 - alpha) * baseline_ports[port]
                )
            else:
                baseline_ports[port] = count
        
        baseline['common_ports'] = dict(sorted(
            baseline_ports.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        self.set_baseline(device_id, baseline)
        logger.info(f"Baseline updated for {device_id}")

