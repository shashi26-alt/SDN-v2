"""
Network Monitor Configuration
Configuration settings for WiFi monitoring and auto-onboarding
"""

import os

# WiFi interface configuration
WIFI_INTERFACE = os.getenv('WIFI_INTERFACE', 'wlan0')  # Default WiFi AP interface

# hostapd log paths (common locations)
HOSTAPD_LOG_PATHS = [
    '/var/log/hostapd.log',
    '/var/log/hostapd/hostapd.log',
    '/tmp/hostapd.log',
    os.path.join(os.path.dirname(__file__), '..', 'logs', 'hostapd.log')
]

# Monitoring configuration
MONITORING_INTERVAL = 2  # seconds between log checks
LOG_TAIL_LINES = 50  # Number of lines to read from log tail

# Device ID generation
DEVICE_ID_PREFIX = 'DEV'
DEVICE_ID_RANDOM_LENGTH = 6
DEVICE_ID_SEPARATOR = '_'

# Pending devices storage
PENDING_DEVICES_DB = os.path.join(
    os.path.dirname(__file__), '..', 'pending_devices.db'
)

# Auto-onboarding settings
AUTO_ONBOARDING_ENABLED = True
NOTIFICATION_ENABLED = True

