"""
Policy Adapter Module
Adapts access control policies based on trust scores
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PolicyAdapter:
    """Adapts policies based on trust scores"""
    
    def __init__(self, trust_scorer=None, sdn_policy_engine=None):
        """
        Initialize policy adapter
        
        Args:
            trust_scorer: Trust scorer instance (optional)
            sdn_policy_engine: SDN policy engine instance (optional)
        """
        self.trust_scorer = trust_scorer
        self.sdn_policy_engine = sdn_policy_engine
        self.policy_history = {}  # {device_id: [(timestamp, old_policy, new_policy)]}
        
        # Register as callback for trust score changes
        if self.trust_scorer:
            self.trust_scorer.register_change_callback(self.on_trust_score_change)
    
    def adapt_policy_for_device(self, device_id: str) -> Optional[str]:
        """
        Adapt policy for a device based on its trust score
        
        Args:
            device_id: Device identifier
            
        Returns:
            New policy action or None
        """
        if not self.trust_scorer:
            logger.warning("Trust scorer not available")
            return None
        
        trust_score = self.trust_scorer.get_trust_score(device_id)
        if trust_score is None:
            logger.warning(f"No trust score for {device_id}")
            return None
        
        # Determine policy action based on trust score
        if trust_score < 30:
            new_action = 'quarantine'
        elif trust_score < 50:
            new_action = 'deny'
        elif trust_score < 70:
            new_action = 'redirect'
        else:
            new_action = 'allow'
        
        # Apply policy if SDN engine available
        if self.sdn_policy_engine:
            try:
                # Get device info for match fields
                if hasattr(self.sdn_policy_engine, 'identity_module') and self.sdn_policy_engine.identity_module:
                    device_info = self.sdn_policy_engine.identity_module.get_device_info(device_id)
                    if device_info and 'mac_address' in device_info:
                        match_fields = {'eth_src': device_info['mac_address']}
                        self.sdn_policy_engine.apply_policy(
                            device_id=device_id,
                            action=new_action,
                            match_fields=match_fields
                        )
                        
                        logger.info(f"Policy adapted for {device_id}: {new_action} (trust score: {trust_score})")
                        
                        # Record policy change
                        self._record_policy_change(device_id, new_action, trust_score)
                        
                        return new_action
            except Exception as e:
                logger.error(f"Failed to adapt policy for {device_id}: {e}")
        
        return new_action
    
    def _record_policy_change(self, device_id: str, new_action: str, trust_score: int):
        """
        Record policy change in history
        
        Args:
            device_id: Device identifier
            new_action: New policy action
            trust_score: Trust score that triggered the change
        """
        if device_id not in self.policy_history:
            self.policy_history[device_id] = []
        
        from datetime import datetime
        self.policy_history[device_id].append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': new_action,
            'trust_score': trust_score
        })
        
        # Keep only last 100 entries
        if len(self.policy_history[device_id]) > 100:
            self.policy_history[device_id] = self.policy_history[device_id][-100:]
    
    def get_policy_history(self, device_id: str, limit: int = 50) -> list:
        """
        Get policy change history for a device
        
        Args:
            device_id: Device identifier
            limit: Maximum number of history entries
            
        Returns:
            List of policy change dictionaries
        """
        if device_id not in self.policy_history:
            return []
        
        return self.policy_history[device_id][-limit:]
    
    def set_trust_scorer(self, trust_scorer):
        """
        Set trust scorer reference
        
        Args:
            trust_scorer: Trust scorer instance
        """
        self.trust_scorer = trust_scorer
        logger.info("Trust scorer connected")
    
    def set_sdn_policy_engine(self, sdn_policy_engine):
        """
        Set SDN policy engine reference
        
        Args:
            sdn_policy_engine: SDN policy engine instance
        """
        self.sdn_policy_engine = sdn_policy_engine
        logger.info("SDN policy engine connected")
    
    def on_trust_score_change(self, device_id: str, old_score: int, new_score: int, reason: str):
        """
        Callback method called when trust score changes
        
        Args:
            device_id: Device identifier
            old_score: Previous trust score
            new_score: New trust score
            reason: Reason for change
        """
        # Only adapt policy if score crossed a threshold
        thresholds = [30, 50, 70]
        old_threshold = None
        new_threshold = None
        
        for threshold in thresholds:
            if old_score >= threshold:
                old_threshold = threshold
            if new_score >= threshold:
                new_threshold = threshold
        
        # If threshold changed, adapt policy immediately
        if old_threshold != new_threshold:
            logger.info(f"Trust score threshold crossed for {device_id}: {old_score} -> {new_score}, adapting policy")
            self.adapt_policy_for_device(device_id)
        elif abs(old_score - new_score) >= 10:  # Significant change (>= 10 points)
            logger.info(f"Significant trust score change for {device_id}: {old_score} -> {new_score}, adapting policy")
            self.adapt_policy_for_device(device_id)

