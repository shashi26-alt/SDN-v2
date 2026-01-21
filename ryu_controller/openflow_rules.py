"""
OpenFlow Rule Generation Module
Generates OpenFlow rules for policy enforcement (allow, deny, redirect, quarantine)
"""

import logging

# Try to import Ryu, but make it optional
try:
    from ryu.ofproto import ofproto_v1_3
    from ryu.ofproto.ofproto_v1_3_parser import OFPMatch, OFPActionOutput, OFPInstructionActions
    RYU_AVAILABLE = True
except ImportError:
    RYU_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Ryu not available. OpenFlow features will be limited.")
    # Create dummy classes
    class ofproto_v1_3:
        OFP_VERSION = 0x04
    class OFPMatch:
        pass
    class OFPActionOutput:
        pass
    class OFPInstructionActions:
        pass

logger = logging.getLogger(__name__)

class OpenFlowRuleGenerator:
    """Generate OpenFlow rules for various policy actions"""
    
    def __init__(self, datapath):
        """
        Initialize rule generator
        
        Args:
            datapath: Ryu datapath object representing the switch
        """
        self.datapath = datapath
        self.ofproto = datapath.ofproto
        self.parser = datapath.ofproto_parser
        
    def create_allow_rule(self, match_fields, priority=100, cookie=0):
        """
        Create an OpenFlow rule to allow traffic
        
        Args:
            match_fields: Dictionary of match fields (e.g., {'eth_src': 'aa:bb:cc:dd:ee:ff'})
            priority: Rule priority (higher = more important)
            cookie: Cookie value for rule identification
            
        Returns:
            OFPFlowMod message
        """
        match = self._create_match(match_fields)
        actions = []  # No actions = forward normally
        instructions = [self.parser.OFPInstructionActions(
            self.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        flow_mod = self.parser.OFPFlowMod(
            datapath=self.datapath,
            match=match,
            cookie=cookie,
            command=self.ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=0,
            priority=priority,
            instructions=instructions
        )
        
        logger.info(f"Created ALLOW rule: {match_fields}")
        return flow_mod
    
    def create_deny_rule(self, match_fields, priority=200, cookie=0):
        """
        Create an OpenFlow rule to deny/block traffic
        
        Args:
            match_fields: Dictionary of match fields
            priority: Rule priority
            cookie: Cookie value for rule identification
            
        Returns:
            OFPFlowMod message
        """
        match = self._create_match(match_fields)
        actions = []  # No actions = drop packet
        instructions = [self.parser.OFPInstructionActions(
            self.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        flow_mod = self.parser.OFPFlowMod(
            datapath=self.datapath,
            match=match,
            cookie=cookie,
            command=self.ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=0,
            priority=priority,
            instructions=instructions
        )
        
        logger.info(f"Created DENY rule: {match_fields}")
        return flow_mod
    
    def create_redirect_rule(self, match_fields, output_port, priority=150, cookie=0):
        """
        Create an OpenFlow rule to redirect traffic to a specific port (e.g., honeypot)
        
        Args:
            match_fields: Dictionary of match fields
            output_port: Port number to redirect traffic to
            priority: Rule priority
            cookie: Cookie value for rule identification
            
        Returns:
            OFPFlowMod message
        """
        match = self._create_match(match_fields)
        actions = [self.parser.OFPActionOutput(output_port)]
        instructions = [self.parser.OFPInstructionActions(
            self.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        flow_mod = self.parser.OFPFlowMod(
            datapath=self.datapath,
            match=match,
            cookie=cookie,
            command=self.ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=0,
            priority=priority,
            instructions=instructions
        )
        
        logger.info(f"Created REDIRECT rule: {match_fields} -> port {output_port}")
        return flow_mod
    
    def create_quarantine_rule(self, match_fields, quarantine_port, priority=180, cookie=0):
        """
        Create an OpenFlow rule to quarantine a device (redirect to isolated network)
        
        Args:
            match_fields: Dictionary of match fields (typically device MAC/IP)
            quarantine_port: Port number for quarantine network
            priority: Rule priority
            cookie: Cookie value for rule identification
            
        Returns:
            OFPFlowMod message
        """
        match = self._create_match(match_fields)
        actions = [self.parser.OFPActionOutput(quarantine_port)]
        instructions = [self.parser.OFPInstructionActions(
            self.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        flow_mod = self.parser.OFPFlowMod(
            datapath=self.datapath,
            match=match,
            cookie=cookie,
            command=self.ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=0,
            priority=priority,
            instructions=instructions
        )
        
        logger.info(f"Created QUARANTINE rule: {match_fields} -> quarantine port {quarantine_port}")
        return flow_mod
    
    def delete_rule(self, match_fields, cookie=0):
        """
        Delete an OpenFlow rule
        
        Args:
            match_fields: Dictionary of match fields to match the rule
            cookie: Cookie value for rule identification
            
        Returns:
            OFPFlowMod message
        """
        match = self._create_match(match_fields)
        
        flow_mod = self.parser.OFPFlowMod(
            datapath=self.datapath,
            match=match,
            cookie=cookie,
            command=self.ofproto.OFPFC_DELETE,
            out_port=self.ofproto.OFPP_ANY,
            out_group=self.ofproto.OFPG_ANY
        )
        
        logger.info(f"Deleted rule: {match_fields}")
        return flow_mod
    
    def _create_match(self, match_fields):
        """
        Create an OFPMatch object from match fields dictionary
        
        Args:
            match_fields: Dictionary of match fields
            
        Returns:
            OFPMatch object
        """
        match_dict = {}
        
        # Map common field names to OpenFlow match fields
        field_mapping = {
            'eth_src': 'eth_src',
            'eth_dst': 'eth_dst',
            'ipv4_src': 'ipv4_src',
            'ipv4_dst': 'ipv4_dst',
            'in_port': 'in_port',
            'ip_proto': 'ip_proto',
            'tcp_src': 'tcp_src',
            'tcp_dst': 'tcp_dst',
            'udp_src': 'udp_src',
            'udp_dst': 'udp_dst'
        }
        
        for key, value in match_fields.items():
            if key in field_mapping:
                match_dict[field_mapping[key]] = value
        
        return self.parser.OFPMatch(**match_dict)
    
    def install_rule(self, flow_mod):
        """
        Install a flow rule on the switch
        
        Args:
            flow_mod: OFPFlowMod message to install
        """
        self.datapath.send_msg(flow_mod)
        logger.info(f"Installed rule on switch {self.datapath.id}")

