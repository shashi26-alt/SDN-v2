"""
Identity Database Module
SQLite database for device identity management
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class IdentityDatabase:
    """Manages device identity database using SQLite"""
    
    def __init__(self, db_path="identity.db"):
        """
        Initialize identity database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    mac_address TEXT UNIQUE NOT NULL,
                    certificate_path TEXT,
                    key_path TEXT,
                    onboarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    device_type TEXT,
                    device_info TEXT,
                    physical_identity TEXT,
                    first_seen TIMESTAMP,
                    device_fingerprint TEXT,
                    ip_address TEXT
                )
            ''')
            
            # Behavioral baselines table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS behavioral_baselines (
                    device_id TEXT PRIMARY KEY,
                    baseline_data TEXT,
                    established_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            ''')
            
            # Policies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_policies (
                    device_id TEXT PRIMARY KEY,
                    policy_data TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            ''')
            
            # Trust score history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trust_score_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    trust_score INTEGER NOT NULL,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            ''')
            
            # Create index on device_id for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trust_score_history_device 
                ON trust_score_history(device_id, timestamp)
            ''')
            
            # Migrate existing databases to add new columns if they don't exist
            self._migrate_database(conn)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Identity database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _migrate_database(self, conn):
        """Migrate existing database schema to add new columns"""
        cursor = conn.cursor()
        
        try:
            # Check if physical_identity column exists
            cursor.execute("PRAGMA table_info(devices)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add physical_identity column if it doesn't exist
            if 'physical_identity' not in columns:
                cursor.execute('ALTER TABLE devices ADD COLUMN physical_identity TEXT')
                logger.info("Added physical_identity column to devices table")
            
            # Add first_seen column if it doesn't exist
            if 'first_seen' not in columns:
                cursor.execute('ALTER TABLE devices ADD COLUMN first_seen TIMESTAMP')
                logger.info("Added first_seen column to devices table")
            
            # Add device_fingerprint column if it doesn't exist
            if 'device_fingerprint' not in columns:
                cursor.execute('ALTER TABLE devices ADD COLUMN device_fingerprint TEXT')
                logger.info("Added device_fingerprint column to devices table")
            
            # Add trust_score column if it doesn't exist
            if 'trust_score' not in columns:
                cursor.execute('ALTER TABLE devices ADD COLUMN trust_score INTEGER DEFAULT 70')
                logger.info("Added trust_score column to devices table")
            
            # Add ip_address column if it doesn't exist
            if 'ip_address' not in columns:
                cursor.execute('ALTER TABLE devices ADD COLUMN ip_address TEXT')
                logger.info("Added ip_address column to devices table")
            
        except Exception as e:
            logger.warning(f"Database migration warning: {e}")
            # Don't raise - migration is optional
    
    def add_device(self, device_id: str, mac_address: str, certificate_path: str = None,
                   key_path: str = None, device_type: str = None, device_info: str = None,
                   physical_identity: str = None, device_fingerprint: str = None) -> bool:
        """
        Add a new device to the database
        
        Args:
            device_id: Device identifier
            mac_address: Device MAC address
            certificate_path: Path to device certificate
            key_path: Path to device private key
            device_type: Type of device
            device_info: Additional device information (JSON string)
            physical_identity: Physical identity metadata (JSON string)
            device_fingerprint: Device fingerprint hash
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if device exists to preserve first_seen timestamp
            existing = self.get_device(device_id)
            first_seen = datetime.utcnow()
            if existing:
                # Try to preserve existing first_seen if available
                existing_first_seen = existing.get('first_seen')
                if existing_first_seen:
                    # Handle both string and datetime objects
                    if isinstance(existing_first_seen, str):
                        try:
                            from datetime import datetime as dt
                            # Try to parse ISO format
                            first_seen = dt.fromisoformat(existing_first_seen.replace('Z', '+00:00'))
                        except:
                            # If parsing fails, use current time
                            first_seen = datetime.utcnow()
                    else:
                        first_seen = existing_first_seen
            
            # Get existing trust_score if device exists
            existing = self.get_device(device_id)
            trust_score = 70  # Default initial trust score
            if existing and existing.get('trust_score') is not None:
                trust_score = existing['trust_score']
            
            cursor.execute('''
                INSERT OR REPLACE INTO devices 
                (device_id, mac_address, certificate_path, key_path, device_type, device_info, 
                 last_seen, physical_identity, device_fingerprint, first_seen, trust_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (device_id, mac_address, certificate_path, key_path, device_type, device_info, 
                  datetime.utcnow(), physical_identity, device_fingerprint, first_seen, trust_score))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Device added: {device_id} ({mac_address}) with physical identity linked")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add device {device_id}: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[Dict]:
        """
        Get device information
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device information dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get device {device_id}: {e}")
            return None
    
    def get_device_by_mac(self, mac_address: str) -> Optional[Dict]:
        """
        Get device by MAC address
        
        Args:
            mac_address: MAC address
            
        Returns:
            Device information dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM devices WHERE mac_address = ?', (mac_address,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get device by MAC {mac_address}: {e}")
            return None
    
    def update_device_status(self, device_id: str, status: str) -> bool:
        """
        Update device status
        
        Args:
            device_id: Device identifier
            status: New status ('active', 'inactive', 'revoked', 'quarantined')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE devices SET status = ? WHERE device_id = ?', (status, device_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Device {device_id} status updated to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            return False
    
    def update_device_ip(self, device_id: str, ip_address: str) -> bool:
        """
        Update device IP address
        
        Args:
            device_id: Device identifier
            ip_address: IP address
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE devices SET ip_address = ? WHERE device_id = ?', (ip_address, device_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Device {device_id} IP updated to {ip_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update device IP: {e}")
            return False
    
    def get_device_ip(self, device_id: str) -> Optional[str]:
        """
        Get device IP address
        
        Args:
            device_id: Device identifier
            
        Returns:
            IP address or None
        """
        device = self.get_device(device_id)
        if device:
            return device.get('ip_address')
        return None
    
    def get_device_from_ip(self, ip_address: str) -> Optional[Dict]:
        """
        Get device by IP address
        
        Args:
            ip_address: IP address
            
        Returns:
            Device information dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM devices WHERE ip_address = ?', (ip_address,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get device by IP {ip_address}: {e}")
            return None
    
    def update_last_seen(self, device_id: str) -> bool:
        """
        Update device last seen timestamp
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE devices SET last_seen = ? WHERE device_id = ?', 
                          (datetime.utcnow(), device_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update last seen: {e}")
            return False
    
    def get_all_devices(self) -> List[Dict]:
        """
        Get all devices
        
        Returns:
            List of device dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM devices')
            rows = cursor.fetchall()
            
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get all devices: {e}")
            return []
    
    def save_behavioral_baseline(self, device_id: str, baseline_data: str) -> bool:
        """
        Save behavioral baseline for a device
        
        Args:
            device_id: Device identifier
            baseline_data: Baseline data (JSON string)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO behavioral_baselines 
                (device_id, baseline_data, updated_at)
                VALUES (?, ?, ?)
            ''', (device_id, baseline_data, datetime.utcnow()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Behavioral baseline saved for {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save baseline: {e}")
            return False
    
    def get_behavioral_baseline(self, device_id: str) -> Optional[str]:
        """
        Get behavioral baseline for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Baseline data (JSON string) or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT baseline_data FROM behavioral_baselines WHERE device_id = ?', (device_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return row[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get baseline: {e}")
            return None
    
    def save_device_policy(self, device_id: str, policy_data: str) -> bool:
        """
        Save device policy
        
        Args:
            device_id: Device identifier
            policy_data: Policy data (JSON string)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO device_policies 
                (device_id, policy_data, updated_at)
                VALUES (?, ?, ?)
            ''', (device_id, policy_data, datetime.utcnow()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Policy saved for {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save policy: {e}")
            return False
    
    def get_device_policy(self, device_id: str) -> Optional[str]:
        """
        Get device policy
        
        Args:
            device_id: Device identifier
            
        Returns:
            Policy data (JSON string) or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT policy_data FROM device_policies WHERE device_id = ?', (device_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return row[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get policy: {e}")
            return None
    
    def save_trust_score(self, device_id: str, trust_score: int, reason: str = None) -> bool:
        """
        Save trust score for a device
        
        Args:
            device_id: Device identifier
            trust_score: Trust score (0-100)
            reason: Reason for the score (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update trust score in devices table
            cursor.execute('UPDATE devices SET trust_score = ? WHERE device_id = ?', 
                          (trust_score, device_id))
            
            # Add to history
            cursor.execute('''
                INSERT INTO trust_score_history (device_id, trust_score, reason, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (device_id, trust_score, reason, datetime.utcnow()))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Trust score saved for {device_id}: {trust_score}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save trust score for {device_id}: {e}")
            return False
    
    def get_trust_score(self, device_id: str) -> Optional[int]:
        """
        Get current trust score for a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            Trust score (0-100) or None if device not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT trust_score FROM devices WHERE device_id = ?', (device_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row and row[0] is not None:
                return int(row[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get trust score for {device_id}: {e}")
            return None
    
    def get_trust_score_history(self, device_id: str, limit: int = 100) -> List[Dict]:
        """
        Get trust score history for a device
        
        Args:
            device_id: Device identifier
            limit: Maximum number of history entries
            
        Returns:
            List of trust score history dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT trust_score, reason, timestamp 
                FROM trust_score_history 
                WHERE device_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (device_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get trust score history for {device_id}: {e}")
            return []
    
    def load_all_trust_scores(self) -> Dict[str, int]:
        """
        Load all trust scores from database
        
        Returns:
            Dictionary mapping device_id to trust_score
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT device_id, trust_score FROM devices WHERE trust_score IS NOT NULL')
            rows = cursor.fetchall()
            
            conn.close()
            
            return {device_id: int(trust_score) for device_id, trust_score in rows}
            
        except Exception as e:
            logger.error(f"Failed to load trust scores: {e}")
            return {}

