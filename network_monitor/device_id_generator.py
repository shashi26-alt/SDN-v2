"""
Device ID Generator
Generates unique device IDs from MAC addresses with random keys for security
"""

import random
import string
import logging
from typing import Optional
from .config import (
    DEVICE_ID_PREFIX,
    DEVICE_ID_RANDOM_LENGTH,
    DEVICE_ID_SEPARATOR
)

logger = logging.getLogger(__name__)


class DeviceIDGenerator:
    """Generates unique device IDs from MAC addresses"""
    
    def __init__(self):
        """Initialize device ID generator"""
        self.generated_ids = set()  # Track generated IDs for uniqueness
    
    def _normalize_mac(self, mac_address: str) -> str:
        """
        Normalize MAC address to consistent format
        
        Args:
            mac_address: MAC address in any format
            
        Returns:
            Normalized MAC address (uppercase, colons)
        """
        # Remove common separators and convert to uppercase
        mac = mac_address.replace('-', '').replace(':', '').replace('.', '').upper()
        
        # Add colons every 2 characters
        normalized = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
        return normalized
    
    def _extract_mac_prefix(self, mac_address: str, length: int = 6) -> str:
        """
        Extract prefix from MAC address
        
        Args:
            mac_address: MAC address
            length: Number of characters to extract (default: 6 for first 3 octets)
            
        Returns:
            MAC prefix string
        """
        normalized = self._normalize_mac(mac_address)
        # Remove colons and take first N characters
        mac_clean = normalized.replace(':', '')
        prefix = mac_clean[:length]
        
        # Format as pairs (e.g., "AABBCC")
        return '_'.join([prefix[i:i+2] for i in range(0, len(prefix), 2)])
    
    def _generate_random_key(self, length: int = None) -> str:
        """
        Generate random alphanumeric key
        
        Args:
            length: Length of random key (default from config)
            
        Returns:
            Random key string
        """
        if length is None:
            length = DEVICE_ID_RANDOM_LENGTH
        
        # Use alphanumeric characters (uppercase and digits)
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_device_id(self, mac_address: str, ensure_unique: bool = True) -> str:
        """
        Generate device ID from MAC address + random key
        
        Format: DEV_<MAC_PREFIX>_<RANDOM_KEY>
        Example: DEV_AA_BB_CC_A3F2K9
        
        Args:
            mac_address: Device MAC address
            ensure_unique: Ensure generated ID is unique (default: True)
            
        Returns:
            Generated device ID
        """
        # Extract MAC prefix (first 3 octets)
        mac_prefix = self._extract_mac_prefix(mac_address, length=6)
        
        # Generate random key
        max_attempts = 100
        for attempt in range(max_attempts):
            random_key = self._generate_random_key()
            
            # Construct device ID
            device_id = f"{DEVICE_ID_PREFIX}{DEVICE_ID_SEPARATOR}{mac_prefix}{DEVICE_ID_SEPARATOR}{random_key}"
            
            # Check uniqueness if required
            if not ensure_unique or device_id not in self.generated_ids:
                self.generated_ids.add(device_id)
                logger.debug(f"Generated device ID: {device_id} for MAC {mac_address}")
                return device_id
        
        # Fallback: use timestamp if uniqueness can't be achieved
        import time
        timestamp_suffix = str(int(time.time()))[-6:]
        device_id = f"{DEVICE_ID_PREFIX}{DEVICE_ID_SEPARATOR}{mac_prefix}{DEVICE_ID_SEPARATOR}{timestamp_suffix}"
        logger.warning(f"Using timestamp fallback for device ID: {device_id}")
        self.generated_ids.add(device_id)
        return device_id
    
    def is_valid_device_id(self, device_id: str) -> bool:
        """
        Validate device ID format
        
        Args:
            device_id: Device ID to validate
            
        Returns:
            True if valid format
        """
        if not device_id:
            return False
        
        parts = device_id.split(DEVICE_ID_SEPARATOR)
        if len(parts) < 3:
            return False
        
        if parts[0] != DEVICE_ID_PREFIX:
            return False
        
        # Check MAC prefix format (should be 3 pairs)
        if len(parts[1].split('_')) < 2:
            return False
        
        return True
    
    def extract_mac_from_device_id(self, device_id: str) -> Optional[str]:
        """
        Extract MAC address prefix from device ID (reverse operation)
        
        Note: This only extracts the prefix, not the full MAC
        
        Args:
            device_id: Device ID
            
        Returns:
            MAC prefix or None if invalid
        """
        if not self.is_valid_device_id(device_id):
            return None
        
        parts = device_id.split(DEVICE_ID_SEPARATOR)
        if len(parts) < 2:
            return None
        
        mac_prefix = parts[1]
        # Convert back to MAC format (add colons)
        mac_clean = mac_prefix.replace('_', '')
        if len(mac_clean) >= 6:
            return ':'.join([mac_clean[i:i+2] for i in range(0, 6, 2)])
        
        return None

