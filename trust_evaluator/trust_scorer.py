"""
Trust Scorer Module
Dynamic trust score calculation based on behavioral and attestation factors
"""

import logging
import time
from typing import Dict, Optional, Callable, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TrustScorer:
    """Calculates and manages dynamic trust scores for devices"""
    
    def __init__(self, initial_score: int = 70, identity_db=None):
        """
        Initialize trust scorer
        
        Args:
            initial_score: Initial trust score for new devices (0-100)
            identity_db: Identity database instance for persistence (optional)
        """
        self.initial_score = initial_score
        self.identity_db = identity_db
        self.device_scores = {}  # {device_id: {'score': int, 'history': [], 'factors': {}}}
        self.score_history = {}  # {device_id: [(timestamp, score, reason)]}
        self.change_callbacks: List[Callable] = []  # Callbacks for trust score changes
        
        # Load existing trust scores from database if available
        if self.identity_db:
            self._load_trust_scores_from_db()
    
    def initialize_device(self, device_id: str, initial_score: Optional[int] = None):
        """
        Initialize trust score for a device
        
        Args:
            device_id: Device identifier
            initial_score: Initial score (default: self.initial_score)
        """
        # Check if device already has a trust score in database
        if self.identity_db:
            db_score = self.identity_db.get_trust_score(device_id)
            if db_score is not None:
                score = db_score
                logger.info(f"Loaded existing trust score from database for {device_id}: {score}")
            else:
                score = initial_score if initial_score is not None else self.initial_score
        else:
            score = initial_score if initial_score is not None else self.initial_score
        
        self.device_scores[device_id] = {
            'score': score,
            'history': [],
            'factors': {
                'behavioral': 0,  # Behavioral anomaly score
                'attestation': 0,  # Attestation failures
                'alerts': 0,  # Security alerts
                'time_based': 0  # Time-based decay
            },
            'last_updated': time.time()
        }
        
        self._record_score_change(device_id, score, "Initialized")
        
        # Persist to database
        if self.identity_db:
            self.identity_db.save_trust_score(device_id, score, "Initialized")
        
        logger.info(f"Trust score initialized for {device_id}: {score}")
    
    def get_trust_score(self, device_id: str) -> Optional[int]:
        """
        Get current trust score for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Trust score (0-100) or None if device not found
        """
        if device_id not in self.device_scores:
            return None
        
        return self.device_scores[device_id]['score']
    
    def adjust_trust_score(self, device_id: str, adjustment: int, reason: str = ""):
        """
        Adjust trust score for a device
        
        Args:
            device_id: Device identifier
            adjustment: Score adjustment (positive or negative)
            reason: Reason for adjustment
        """
        if device_id not in self.device_scores:
            self.initialize_device(device_id)
        
        current_score = self.device_scores[device_id]['score']
        new_score = max(0, min(100, current_score + adjustment))
        
        self.device_scores[device_id]['score'] = new_score
        self.device_scores[device_id]['last_updated'] = time.time()
        
        # Update factors
        if adjustment < 0:
            if 'alert' in reason.lower() or 'anomaly' in reason.lower():
                self.device_scores[device_id]['factors']['alerts'] += abs(adjustment)
            elif 'attestation' in reason.lower():
                self.device_scores[device_id]['factors']['attestation'] += abs(adjustment)
            elif 'behavior' in reason.lower():
                self.device_scores[device_id]['factors']['behavioral'] += abs(adjustment)
        
        self._record_score_change(device_id, new_score, reason)
        
        # Persist to database
        if self.identity_db:
            self.identity_db.save_trust_score(device_id, new_score, reason)
        
        # Notify callbacks of trust score change
        self._notify_score_change(device_id, current_score, new_score, reason)
        
        logger.info(f"Trust score adjusted for {device_id}: {current_score} -> {new_score} ({adjustment:+d}) - {reason}")
        
        return new_score
    
    def set_trust_score(self, device_id: str, score: int, reason: str = ""):
        """
        Set trust score to a specific value
        
        Args:
            device_id: Device identifier
            score: New trust score (0-100)
            reason: Reason for setting score
        """
        if device_id not in self.device_scores:
            self.initialize_device(device_id)
        
        old_score = self.device_scores[device_id]['score']
        new_score = max(0, min(100, score))
        
        self.device_scores[device_id]['score'] = new_score
        self.device_scores[device_id]['last_updated'] = time.time()
        
        self._record_score_change(device_id, new_score, reason)
        
        # Persist to database
        if self.identity_db:
            self.identity_db.save_trust_score(device_id, new_score, reason)
        
        # Notify callbacks of trust score change
        self._notify_score_change(device_id, old_score, new_score, reason)
        
        logger.info(f"Trust score set for {device_id}: {old_score} -> {new_score} - {reason}")
        
        return new_score
    
    def record_behavioral_anomaly(self, device_id: str, severity: str):
        """
        Record behavioral anomaly and adjust trust score
        
        Args:
            device_id: Device identifier
            severity: Anomaly severity ('low', 'medium', 'high')
        """
        adjustments = {
            'low': -5,
            'medium': -15,
            'high': -30
        }
        
        adjustment = adjustments.get(severity, -10)
        self.adjust_trust_score(device_id, adjustment, f"Behavioral anomaly: {severity}")
        
        # Update behavioral factor
        if device_id in self.device_scores:
            self.device_scores[device_id]['factors']['behavioral'] += abs(adjustment)
    
    def record_attestation_failure(self, device_id: str):
        """
        Record device attestation failure
        
        Args:
            device_id: Device identifier
        """
        self.adjust_trust_score(device_id, -20, "Attestation failure")
        
        # Update attestation factor
        if device_id in self.device_scores:
            self.device_scores[device_id]['factors']['attestation'] += 20
    
    def record_security_alert(self, device_id: str, alert_type: str, severity: str):
        """
        Record security alert and adjust trust score
        
        Args:
            device_id: Device identifier
            alert_type: Type of alert
            severity: Alert severity ('low', 'medium', 'high')
        """
        adjustments = {
            'low': -10,
            'medium': -20,
            'high': -40
        }
        
        adjustment = adjustments.get(severity, -15)
        self.adjust_trust_score(device_id, adjustment, f"Security alert: {alert_type} ({severity})")
        
        # Update alerts factor
        if device_id in self.device_scores:
            self.device_scores[device_id]['factors']['alerts'] += abs(adjustment)
    
    def record_positive_behavior(self, device_id: str, reason: str = ""):
        """
        Record positive behavior and increase trust score
        
        Args:
            device_id: Device identifier
            reason: Reason for positive adjustment
        """
        # Small positive adjustment for good behavior
        self.adjust_trust_score(device_id, +2, f"Positive behavior: {reason}")
    
    def get_score_factors(self, device_id: str) -> Dict:
        """
        Get trust score factors for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Dictionary of score factors
        """
        if device_id not in self.device_scores:
            return {}
        
        return self.device_scores[device_id]['factors'].copy()
    
    def get_score_history(self, device_id: str, limit: int = 50) -> list:
        """
        Get trust score history for a device
        
        Args:
            device_id: Device identifier
            limit: Maximum number of history entries
            
        Returns:
            List of (timestamp, score, reason) tuples
        """
        if device_id not in self.score_history:
            return []
        
        return self.score_history[device_id][-limit:]
    
    def _record_score_change(self, device_id: str, score: int, reason: str):
        """
        Record score change in history
        
        Args:
            device_id: Device identifier
            score: New score
            reason: Reason for change
        """
        if device_id not in self.score_history:
            self.score_history[device_id] = []
        
        self.score_history[device_id].append((
            datetime.utcnow().isoformat(),
            score,
            reason
        ))
        
        # Keep only last 1000 entries
        if len(self.score_history[device_id]) > 1000:
            self.score_history[device_id] = self.score_history[device_id][-1000:]
    
    def get_all_scores(self) -> Dict[str, int]:
        """
        Get all device trust scores
        
        Returns:
            Dictionary mapping device_id to trust score
        """
        return {
            device_id: data['score']
            for device_id, data in self.device_scores.items()
        }
    
    def get_trust_level(self, device_id: str) -> str:
        """
        Get trust level category for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Trust level: 'trusted', 'monitored', 'suspicious', 'untrusted'
        """
        score = self.get_trust_score(device_id)
        if score is None:
            return 'unknown'
        
        if score >= 70:
            return 'trusted'
        elif score >= 50:
            return 'monitored'
        elif score >= 30:
            return 'suspicious'
        else:
            return 'untrusted'
    
    def register_change_callback(self, callback: Callable[[str, int, int, str], None]):
        """
        Register a callback function to be called when trust scores change
        
        Args:
            callback: Function that takes (device_id, old_score, new_score, reason)
        """
        self.change_callbacks.append(callback)
        logger.info(f"Registered trust score change callback: {callback.__name__}")
    
    def _notify_score_change(self, device_id: str, old_score: int, new_score: int, reason: str):
        """
        Notify all registered callbacks of a trust score change
        
        Args:
            device_id: Device identifier
            old_score: Previous trust score
            new_score: New trust score
            reason: Reason for change
        """
        for callback in self.change_callbacks:
            try:
                callback(device_id, old_score, new_score, reason)
            except Exception as e:
                logger.error(f"Error in trust score change callback {callback.__name__}: {e}")
    
    def _load_trust_scores_from_db(self):
        """Load all trust scores from database"""
        try:
            scores = self.identity_db.load_all_trust_scores()
            for device_id, score in scores.items():
                self.device_scores[device_id] = {
                    'score': score,
                    'history': [],
                    'factors': {
                        'behavioral': 0,
                        'attestation': 0,
                        'alerts': 0,
                        'time_based': 0
                    },
                    'last_updated': time.time()
                }
            logger.info(f"Loaded {len(scores)} trust scores from database")
        except Exception as e:
            logger.warning(f"Failed to load trust scores from database: {e}")
    
    def set_identity_db(self, identity_db):
        """
        Set identity database for persistence
        
        Args:
            identity_db: Identity database instance
        """
        self.identity_db = identity_db
        if identity_db:
            self._load_trust_scores_from_db()
            logger.info("Identity database connected for trust score persistence")

