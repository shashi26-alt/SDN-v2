"""
Traffic Orchestrator Module
Central intelligent orchestration engine for dynamic and multifaceted traffic orchestration
Enforces policies based on device identity, trust scores, and threat intelligence
"""

import logging
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class PolicyAction(Enum):
    """Policy action types"""
    ALLOW = "allow"
    DENY = "deny"
    REDIRECT = "redirect"
    QUARANTINE = "quarantine"

class TrafficOrchestrator:
    """
    Central orchestration engine that dynamically enforces security policies
    based on multiple real-time variables including device identity, trust scores,
    and current threat intelligence.
    """
    
    def __init__(self, sdn_policy_engine=None, identity_module=None, 
                 trust_module=None, analyst_module=None):
        """
        Initialize traffic orchestrator
        
        Args:
            sdn_policy_engine: SDN policy engine instance
            identity_module: Identity management module
            trust_module: Trust evaluation module
            analyst_module: Analyst module for threat detection
        """
        self.sdn_policy_engine = sdn_policy_engine
        self.identity_module = identity_module
        self.trust_module = trust_module
        self.analyst_module = analyst_module
        
        # Policy decision history
        self.policy_decisions = {}  # {device_id: [decision_history]}
        
        logger.info("Traffic Orchestrator initialized")
    
    def orchestrate_policy(self, device_id: str, 
                          threat_intelligence: Optional[Dict] = None) -> PolicyAction:
        """
        Make intelligent policy decision based on multiple variables
        
        This is the central decision-making function that considers:
        - Device identity and authentication status
        - Current trust score
        - Active threat intelligence
        - Recent security alerts
        
        Args:
            device_id: Device identifier
            threat_intelligence: Optional threat intelligence dictionary
            
        Returns:
            PolicyAction enum value
        """
        # Gather all relevant information
        device_info = self._get_device_info(device_id)
        trust_score = self._get_trust_score(device_id)
        recent_alerts = self._get_recent_alerts(device_id)
        threat_level = self._assess_threat_level(device_id, threat_intelligence)
        
        # Decision logic: prioritize most restrictive action
        decision = self._make_decision(
            device_id=device_id,
            device_info=device_info,
            trust_score=trust_score,
            recent_alerts=recent_alerts,
            threat_level=threat_level
        )
        
        # Apply decision
        self._apply_decision(device_id, decision)
        
        # Record decision
        self._record_decision(device_id, decision, {
            'trust_score': trust_score,
            'threat_level': threat_level,
            'recent_alerts': len(recent_alerts) if recent_alerts else 0
        })
        
        logger.info(f"Orchestrated policy for {device_id}: {decision.value} "
                   f"(trust: {trust_score}, threats: {threat_level})")
        
        return decision
    
    def _get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get device information from identity module"""
        if self.identity_module:
            return self.identity_module.get_device_info(device_id)
        return None
    
    def _get_trust_score(self, device_id: str) -> Optional[int]:
        """Get current trust score"""
        if self.trust_module:
            return self.trust_module.get_trust_score(device_id)
        return None
    
    def _get_recent_alerts(self, device_id: str) -> List[Dict]:
        """Get recent security alerts for device"""
        if self.analyst_module and hasattr(self.analyst_module, 'get_recent_alerts'):
            # Get alerts from analyst module
            all_alerts = self.analyst_module.get_recent_alerts(limit=100)
            return [a for a in all_alerts if a.get('device_id') == device_id]
        return []
    
    def _assess_threat_level(self, device_id: str, 
                            threat_intelligence: Optional[Dict]) -> str:
        """
        Assess overall threat level for device
        
        Returns:
            'none', 'low', 'medium', 'high', 'critical'
        """
        threat_level = 'none'
        
        # Check threat intelligence
        if threat_intelligence:
            severity = threat_intelligence.get('severity', 'low')
            if severity == 'high':
                threat_level = 'high'
            elif severity == 'medium':
                threat_level = 'medium'
            elif severity == 'low':
                threat_level = 'low'
        
        # Check recent alerts
        recent_alerts = self._get_recent_alerts(device_id)
        if recent_alerts:
            high_severity_count = sum(1 for a in recent_alerts 
                                     if a.get('severity') == 'high')
            medium_severity_count = sum(1 for a in recent_alerts 
                                       if a.get('severity') == 'medium')
            
            if high_severity_count > 0:
                threat_level = 'critical' if threat_level != 'critical' else 'high'
            elif medium_severity_count >= 2:
                threat_level = 'high' if threat_level not in ['high', 'critical'] else threat_level
            elif medium_severity_count > 0:
                threat_level = 'medium' if threat_level == 'none' else threat_level
        
        return threat_level
    
    def _make_decision(self, device_id: str, device_info: Optional[Dict],
                      trust_score: Optional[int], recent_alerts: List[Dict],
                      threat_level: str) -> PolicyAction:
        """
        Make policy decision based on all factors
        
        Decision priority (most restrictive first):
        1. Critical threat level -> QUARANTINE
        2. High threat level -> REDIRECT or QUARANTINE
        3. Trust score < 30 -> QUARANTINE
        4. Trust score < 50 -> DENY
        5. Medium threat level -> REDIRECT
        6. Trust score < 70 -> REDIRECT
        7. Low threat level -> ALLOW (with monitoring)
        8. Trust score >= 70 -> ALLOW
        """
        # Critical threat: immediate quarantine
        if threat_level == 'critical':
            return PolicyAction.QUARANTINE
        
        # High threat: redirect or quarantine based on trust
        if threat_level == 'high':
            if trust_score is not None and trust_score < 30:
                return PolicyAction.QUARANTINE
            return PolicyAction.REDIRECT
        
        # Trust-based decisions
        if trust_score is not None:
            if trust_score < 30:
                return PolicyAction.QUARANTINE
            elif trust_score < 50:
                return PolicyAction.DENY
            elif trust_score < 70:
                # Medium trust: redirect for monitoring
                if threat_level in ['medium', 'high']:
                    return PolicyAction.REDIRECT
                return PolicyAction.REDIRECT
        
        # Threat-based decisions (when trust is high)
        if threat_level == 'medium':
            return PolicyAction.REDIRECT
        elif threat_level == 'low':
            # Low threat but monitor
            return PolicyAction.ALLOW
        
        # Default: allow
        return PolicyAction.ALLOW
    
    def _apply_decision(self, device_id: str, decision: PolicyAction):
        """Apply policy decision to SDN controller"""
        if not self.sdn_policy_engine:
            logger.warning("SDN policy engine not available, cannot apply decision")
            return
        
        try:
            self.sdn_policy_engine.apply_policy(device_id, decision.value)
        except Exception as e:
            logger.error(f"Failed to apply policy decision for {device_id}: {e}")
    
    def _record_decision(self, device_id: str, decision: PolicyAction, context: Dict):
        """Record policy decision for audit trail"""
        from datetime import datetime
        
        if device_id not in self.policy_decisions:
            self.policy_decisions[device_id] = []
        
        decision_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': decision.value,
            'context': context
        }
        
        self.policy_decisions[device_id].append(decision_record)
        
        # Keep only last 100 decisions per device
        if len(self.policy_decisions[device_id]) > 100:
            self.policy_decisions[device_id] = self.policy_decisions[device_id][-100:]
    
    def get_decision_history(self, device_id: str, limit: int = 50) -> List[Dict]:
        """
        Get policy decision history for a device
        
        Args:
            device_id: Device identifier
            limit: Maximum number of decisions to return
            
        Returns:
            List of decision dictionaries
        """
        if device_id not in self.policy_decisions:
            return []
        
        return self.policy_decisions[device_id][-limit:]
    
    def set_sdn_policy_engine(self, sdn_policy_engine):
        """Set SDN policy engine reference"""
        self.sdn_policy_engine = sdn_policy_engine
        logger.info("SDN policy engine connected to orchestrator")
    
    def set_identity_module(self, identity_module):
        """Set identity module reference"""
        self.identity_module = identity_module
        logger.info("Identity module connected to orchestrator")
    
    def set_trust_module(self, trust_module):
        """Set trust module reference"""
        self.trust_module = trust_module
        logger.info("Trust module connected to orchestrator")
    
    def set_analyst_module(self, analyst_module):
        """Set analyst module reference"""
        self.analyst_module = analyst_module
        logger.info("Analyst module connected to orchestrator")

