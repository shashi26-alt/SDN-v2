"""
WiFi Detector
Monitors WiFi association events to detect new devices connecting to the network
"""

import os
import re
import time
import logging
from typing import Set, Optional, Callable
from .config import (
    WIFI_INTERFACE,
    HOSTAPD_LOG_PATHS,
    MONITORING_INTERVAL,
    LOG_TAIL_LINES
)

logger = logging.getLogger(__name__)


class WiFiDetector:
    """Monitors WiFi association events from hostapd logs"""
    
    # Regex patterns for hostapd log entries
    PATTERN_AUTHENTICATED = re.compile(
        r'(\w+):\s+STA\s+([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})\s+IEEE\s+802\.11:\s+authenticated'
    )
    PATTERN_ASSOCIATED = re.compile(
        r'(\w+):\s+STA\s+([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})\s+IEEE\s+802\.11:\s+associated'
    )
    PATTERN_DISASSOCIATED = re.compile(
        r'(\w+):\s+STA\s+([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})\s+IEEE\s+802\.11:\s+disassociated'
    )
    
    def __init__(self, interface: str = None, log_path: str = None, 
                 on_new_device: Callable[[str], None] = None):
        """
        Initialize WiFi detector
        
        Args:
            interface: WiFi interface name (default from config)
            log_path: Path to hostapd log file (auto-detect if None)
            on_new_device: Callback function when new device detected (mac_address)
        """
        self.interface = interface or WIFI_INTERFACE
        self.log_path = log_path or self._find_hostapd_log()
        self.on_new_device = on_new_device
        
        self.known_devices: Set[str] = set()
        self.last_position = 0
        
        if not self.log_path:
            logger.warning("hostapd log file not found. Auto-detection will be limited.")
        else:
            logger.info(f"Monitoring WiFi interface {self.interface}, log: {self.log_path}")
    
    def _find_hostapd_log(self) -> Optional[str]:
        """
        Find hostapd log file
        
        Returns:
            Path to log file or None if not found
        """
        for log_path in HOSTAPD_LOG_PATHS:
            if os.path.exists(log_path):
                logger.info(f"Found hostapd log: {log_path}")
                return log_path
        
        # Try to find log in common systemd journal locations
        # For systemd-based systems, hostapd might log to journal
        logger.warning("hostapd log file not found in standard locations")
        logger.info("Consider configuring hostapd to log to a file")
        return None
    
    def _normalize_mac(self, mac: str) -> str:
        """
        Normalize MAC address to consistent format
        
        Args:
            mac: MAC address in any format
            
        Returns:
            Normalized MAC address (uppercase, colons)
        """
        # Remove separators and convert to uppercase
        mac_clean = re.sub(r'[:-]', '', mac).upper()
        
        # Add colons every 2 characters
        return ':'.join([mac_clean[i:i+2] for i in range(0, len(mac_clean), 2)])
    
    def _extract_mac_from_line(self, line: str) -> Optional[str]:
        """
        Extract MAC address from log line
        
        Args:
            line: Log line to parse
            
        Returns:
            MAC address or None
        """
        # Try authenticated pattern
        match = self.PATTERN_AUTHENTICATED.search(line)
        if match:
            mac = match.group(2) + match.group(3)
            return self._normalize_mac(mac)
        
        # Try associated pattern
        match = self.PATTERN_ASSOCIATED.search(line)
        if match:
            mac = match.group(2) + match.group(3)
            return self._normalize_mac(mac)
        
        return None
    
    def _read_log_tail(self) -> list:
        """
        Read tail of log file (new lines since last check)
        
        Returns:
            List of new log lines
        """
        if not self.log_path or not os.path.exists(self.log_path):
            return []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to last known position
                if self.last_position > 0:
                    f.seek(self.last_position)
                else:
                    # First run: read only tail
                    f.seek(0, os.SEEK_END)
                    file_size = f.tell()
                    # Read last N lines
                    if file_size > 0:
                        f.seek(max(0, file_size - 10000))  # Read last 10KB
                        # Skip first line (might be partial)
                        f.readline()
                
                lines = f.readlines()
                self.last_position = f.tell()
                return lines
                
        except PermissionError:
            logger.error(f"Permission denied reading log file: {self.log_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return []
    
    def _check_arp_table(self) -> Set[str]:
        """
        Check ARP table for connected devices (fallback method)
        
        Returns:
            Set of MAC addresses
        """
        devices = set()
        
        try:
            import subprocess
            # Get ARP entries for WiFi interface
            result = subprocess.run(
                ['arp', '-n', '-i', self.interface],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse ARP output
                for line in result.stdout.split('\n'):
                    if self.interface in line:
                        # Extract MAC address (format: XX:XX:XX:XX:XX:XX)
                        mac_match = re.search(
                            r'([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})',
                            line,
                            re.IGNORECASE
                        )
                        if mac_match:
                            mac = mac_match.group(0)
                            devices.add(self._normalize_mac(mac))
        except FileNotFoundError:
            logger.debug("arp command not found")
        except Exception as e:
            logger.debug(f"Error checking ARP table: {e}")
        
        return devices
    
    def scan_once(self) -> Set[str]:
        """
        Perform a single scan for new devices
        
        Returns:
            Set of newly detected MAC addresses
        """
        new_devices = set()
        
        # Method 1: Read hostapd log
        if self.log_path:
            lines = self._read_log_tail()
            for line in lines:
                mac = self._extract_mac_from_line(line)
                if mac and mac not in self.known_devices:
                    new_devices.add(mac)
                    self.known_devices.add(mac)
                    logger.info(f"New device detected via log: {mac}")
        
        # Method 2: Check ARP table (fallback)
        arp_devices = self._check_arp_table()
        for mac in arp_devices:
            if mac not in self.known_devices:
                new_devices.add(mac)
                self.known_devices.add(mac)
                logger.info(f"New device detected via ARP: {mac}")
        
        return new_devices
    
    def start_monitoring(self, callback: Callable[[str], None] = None, 
                        interval: float = None):
        """
        Start continuous monitoring (blocking)
        
        Args:
            callback: Callback function for new devices (mac_address)
            interval: Monitoring interval in seconds (default from config)
        """
        if callback:
            self.on_new_device = callback
        
        interval = interval or MONITORING_INTERVAL
        
        logger.info(f"Starting WiFi monitoring (interval: {interval}s)")
        
        try:
            while True:
                new_devices = self.scan_once()
                
                for mac in new_devices:
                    if self.on_new_device:
                        try:
                            self.on_new_device(mac)
                        except Exception as e:
                            logger.error(f"Error in new device callback: {e}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("WiFi monitoring stopped")
        except Exception as e:
            logger.error(f"Error in WiFi monitoring: {e}")
            raise
    
    def get_known_devices(self) -> Set[str]:
        """
        Get set of known device MAC addresses
        
        Returns:
            Set of MAC addresses
        """
        return self.known_devices.copy()
    
    def add_known_device(self, mac_address: str):
        """
        Manually add a device to known devices (e.g., from database)
        
        Args:
            mac_address: MAC address to add
        """
        normalized = self._normalize_mac(mac_address)
        self.known_devices.add(normalized)
        logger.debug(f"Added known device: {normalized}")

