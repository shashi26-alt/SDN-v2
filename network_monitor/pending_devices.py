"""
Pending Devices Manager
Manages pending device approval requests
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List
from .config import PENDING_DEVICES_DB

logger = logging.getLogger(__name__)


class PendingDeviceManager:
    """Manages pending device approval requests"""
    
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_ONBOARDED = 'onboarded'
    
    def __init__(self, db_path: str = None):
        """
        Initialize pending device manager
        
        Args:
            db_path: Path to SQLite database (default from config)
        """
        self.db_path = db_path or PENDING_DEVICES_DB
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Pending devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac_address TEXT UNIQUE NOT NULL,
                    device_id TEXT NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    approved_at TIMESTAMP,
                    rejected_at TIMESTAMP,
                    onboarded_at TIMESTAMP,
                    device_type TEXT,
                    device_info TEXT,
                    admin_notes TEXT
                )
            ''')
            
            # Device history table (for tracking all actions)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac_address TEXT NOT NULL,
                    device_id TEXT,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    admin_notes TEXT,
                    FOREIGN KEY (mac_address) REFERENCES pending_devices(mac_address)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Pending devices database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize pending devices database: {e}")
            raise
    
    def add_pending_device(self, mac_address: str, device_id: str, 
                          device_type: str = None, device_info: str = None) -> bool:
        """
        Add a new pending device request
        
        Args:
            mac_address: Device MAC address
            device_id: Auto-generated device ID
            device_type: Optional device type
            device_info: Optional device information
            
        Returns:
            True if added successfully, False if already exists
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if device already exists
            cursor.execute(
                'SELECT status FROM pending_devices WHERE mac_address = ?',
                (mac_address,)
            )
            existing = cursor.fetchone()
            
            if existing:
                status = existing[0]
                if status == self.STATUS_PENDING:
                    logger.warning(f"Device {mac_address} already pending approval")
                    conn.close()
                    return False
                elif status == self.STATUS_APPROVED:
                    logger.info(f"Device {mac_address} already approved")
                    conn.close()
                    return False
            
            # Insert new pending device
            cursor.execute('''
                INSERT INTO pending_devices 
                (mac_address, device_id, device_type, device_info, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (mac_address, device_id, device_type, device_info, self.STATUS_PENDING))
            
            # Add to history
            cursor.execute('''
                INSERT INTO device_history (mac_address, device_id, action)
                VALUES (?, ?, ?)
            ''', (mac_address, device_id, 'detected'))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added pending device: {device_id} ({mac_address})")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"Device {mac_address} already exists in database")
            return False
        except Exception as e:
            logger.error(f"Failed to add pending device: {e}")
            return False
    
    def get_pending_devices(self) -> List[Dict]:
        """
        Get all pending devices
        
        Returns:
            List of pending device dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM pending_devices 
                WHERE status = ?
                ORDER BY detected_at DESC
            ''', (self.STATUS_PENDING,))
            
            rows = cursor.fetchall()
            devices = [dict(row) for row in rows]
            conn.close()
            
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get pending devices: {e}")
            return []
    
    def get_device_by_mac(self, mac_address: str) -> Optional[Dict]:
        """
        Get device by MAC address
        
        Args:
            mac_address: Device MAC address
            
        Returns:
            Device dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM pending_devices WHERE mac_address = ?',
                (mac_address,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get device by MAC: {e}")
            return None
    
    def approve_device(self, mac_address: str, admin_notes: str = None) -> bool:
        """
        Approve a pending device
        
        Args:
            mac_address: Device MAC address
            admin_notes: Optional admin notes
            
        Returns:
            True if approved successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update status
            cursor.execute('''
                UPDATE pending_devices 
                SET status = ?, approved_at = CURRENT_TIMESTAMP, admin_notes = ?
                WHERE mac_address = ? AND status = ?
            ''', (self.STATUS_APPROVED, admin_notes, mac_address, self.STATUS_PENDING))
            
            if cursor.rowcount == 0:
                conn.close()
                logger.warning(f"Device {mac_address} not found or not pending")
                return False
            
            # Get device_id for history
            cursor.execute(
                'SELECT device_id FROM pending_devices WHERE mac_address = ?',
                (mac_address,)
            )
            row = cursor.fetchone()
            device_id = row[0] if row else None
            
            # Add to history
            cursor.execute('''
                INSERT INTO device_history (mac_address, device_id, action, admin_notes)
                VALUES (?, ?, ?, ?)
            ''', (mac_address, device_id, 'approved', admin_notes))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Device {mac_address} approved")
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve device: {e}")
            return False
    
    def reject_device(self, mac_address: str, admin_notes: str = None) -> bool:
        """
        Reject a pending device
        
        Args:
            mac_address: Device MAC address
            admin_notes: Optional admin notes
            
        Returns:
            True if rejected successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update status
            cursor.execute('''
                UPDATE pending_devices 
                SET status = ?, rejected_at = CURRENT_TIMESTAMP, admin_notes = ?
                WHERE mac_address = ? AND status = ?
            ''', (self.STATUS_REJECTED, admin_notes, mac_address, self.STATUS_PENDING))
            
            if cursor.rowcount == 0:
                conn.close()
                logger.warning(f"Device {mac_address} not found or not pending")
                return False
            
            # Get device_id for history
            cursor.execute(
                'SELECT device_id FROM pending_devices WHERE mac_address = ?',
                (mac_address,)
            )
            row = cursor.fetchone()
            device_id = row[0] if row else None
            
            # Add to history
            cursor.execute('''
                INSERT INTO device_history (mac_address, device_id, action, admin_notes)
                VALUES (?, ?, ?, ?)
            ''', (mac_address, device_id, 'rejected', admin_notes))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Device {mac_address} rejected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reject device: {e}")
            return False
    
    def mark_onboarded(self, mac_address: str) -> bool:
        """
        Mark device as onboarded (after successful onboarding)
        
        Args:
            mac_address: Device MAC address
            
        Returns:
            True if updated successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE pending_devices 
                SET status = ?, onboarded_at = CURRENT_TIMESTAMP
                WHERE mac_address = ?
            ''', (self.STATUS_ONBOARDED, mac_address))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Device {mac_address} marked as onboarded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark device as onboarded: {e}")
            return False
    
    def get_device_history(self, mac_address: str = None, limit: int = 100) -> List[Dict]:
        """
        Get device approval history
        
        Args:
            mac_address: Optional MAC address filter
            limit: Maximum number of records to return
            
        Returns:
            List of history records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if mac_address:
                cursor.execute('''
                    SELECT * FROM device_history 
                    WHERE mac_address = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (mac_address, limit))
            else:
                cursor.execute('''
                    SELECT * FROM device_history 
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            history = [dict(row) for row in rows]
            conn.close()
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get device history: {e}")
            return []
    
    def get_all_devices(self, status: str = None) -> List[Dict]:
        """
        Get all devices (optionally filtered by status)
        
        Args:
            status: Optional status filter
            
        Returns:
            List of device dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM pending_devices 
                    WHERE status = ?
                    ORDER BY detected_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT * FROM pending_devices 
                    ORDER BY detected_at DESC
                ''')
            
            rows = cursor.fetchall()
            devices = [dict(row) for row in rows]
            conn.close()
            
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get all devices: {e}")
            return []

