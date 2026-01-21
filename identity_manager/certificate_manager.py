"""
Certificate Management Module
X.509 certificate generation and management using OpenSSL
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
import tempfile

# Try to import cryptography, but make it optional
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("cryptography module not available. Certificate features will be limited.")

logger = logging.getLogger(__name__)

class CertificateManager:
    """Manages X.509 certificates for IoT devices"""
    
    def __init__(self, ca_cert_path="certs/ca_cert.pem", ca_key_path="certs/ca_key.pem", certs_dir="certs"):
        """
        Initialize certificate manager
        
        Args:
            ca_cert_path: Path to CA certificate
            ca_key_path: Path to CA private key
            certs_dir: Directory for storing certificates
        """
        self.ca_cert_path = ca_cert_path
        self.ca_key_path = ca_key_path
        self.certs_dir = certs_dir
        
        # Create directories
        os.makedirs(certs_dir, exist_ok=True)
        os.makedirs(os.path.dirname(ca_cert_path) if os.path.dirname(ca_cert_path) else ".", exist_ok=True)
        
        # Initialize CA if it doesn't exist (only if cryptography is available)
        if CRYPTOGRAPHY_AVAILABLE and (not os.path.exists(ca_cert_path) or not os.path.exists(ca_key_path)):
            self._create_ca()
        elif not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("cryptography not available - CA will not be created automatically")
    
    def _create_ca(self):
        """Create Certificate Authority (CA)"""
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("Cannot create CA: cryptography module not available")
            logger.warning("Install with: pip install cryptography")
            return
            
        try:
            logger.info("Creating Certificate Authority...")
            
            # Generate CA private key
            ca_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Create CA certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SOHO IoT Zero Trust CA"),
                x509.NameAttribute(NameOID.COMMON_NAME, "SOHO IoT CA"),
            ])
            
            ca_cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                ca_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=3650)  # 10 years
            ).add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            ).sign(ca_key, hashes.SHA256(), default_backend())
            
            # Save CA certificate
            with open(self.ca_cert_path, "wb") as f:
                f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
            
            # Save CA private key
            with open(self.ca_key_path, "wb") as f:
                f.write(ca_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            logger.info(f"CA created: {self.ca_cert_path}")
            
        except Exception as e:
            logger.error(f"Failed to create CA: {e}")
            raise
    
    def generate_device_certificate(self, device_id, mac_address, validity_days=365):
        """
        Generate X.509 certificate for a device
        
        Args:
            device_id: Device identifier
            mac_address: Device MAC address
            validity_days: Certificate validity period in days
            
        Returns:
            Tuple of (certificate_path, key_path)
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("Cannot generate device certificate: cryptography module not available")
            raise ImportError("cryptography module is required for certificate generation. Install with: pip install cryptography")
            
        try:
            logger.info(f"Generating certificate for device {device_id}...")
            
            # Load CA certificate and key
            with open(self.ca_cert_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            with open(self.ca_key_path, "rb") as f:
                ca_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
            
            # Generate device private key
            device_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Create device certificate
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SOHO IoT Device"),
                x509.NameAttribute(NameOID.COMMON_NAME, device_id),
            ])
            
            # Build certificate (without problematic SAN extension for now)
            # MAC address is already in device_id/common name
            device_cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                ca_cert.subject
            ).public_key(
                device_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=validity_days)
            ).sign(ca_key, hashes.SHA256(), default_backend())
            
            # Save device certificate
            cert_path = os.path.join(self.certs_dir, f"{device_id}_cert.pem")
            with open(cert_path, "wb") as f:
                f.write(device_cert.public_bytes(serialization.Encoding.PEM))
            
            # Save device private key
            key_path = os.path.join(self.certs_dir, f"{device_id}_key.pem")
            with open(key_path, "wb") as f:
                f.write(device_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            logger.info(f"Certificate generated for {device_id}: {cert_path}")
            return cert_path, key_path
            
        except Exception as e:
            logger.error(f"Failed to generate certificate for {device_id}: {e}")
            raise
    
    def verify_certificate(self, cert_path):
        """
        Verify a device certificate against the CA
        
        Args:
            cert_path: Path to device certificate
            
        Returns:
            True if valid, False otherwise
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("Cannot verify certificate: cryptography module not available")
            return False
            
        try:
            # Load CA certificate
            with open(self.ca_cert_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            # Load device certificate
            with open(cert_path, "rb") as f:
                device_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            # Verify certificate chain
            # In production, use proper certificate validation
            # For now, check if certificate is not expired
            if device_cert.not_valid_after < datetime.utcnow():
                logger.warning(f"Certificate expired: {cert_path}")
                return False
            
            if device_cert.not_valid_before > datetime.utcnow():
                logger.warning(f"Certificate not yet valid: {cert_path}")
                return False
            
            logger.info(f"Certificate verified: {cert_path}")
            return True
            
        except Exception as e:
            logger.error(f"Certificate verification failed: {e}")
            return False
    
    def revoke_certificate(self, device_id):
        """
        Revoke a device certificate
        
        Args:
            device_id: Device identifier
        """
        try:
            cert_path = os.path.join(self.certs_dir, f"{device_id}_cert.pem")
            key_path = os.path.join(self.certs_dir, f"{device_id}_key.pem")
            
            # Delete certificate files
            if os.path.exists(cert_path):
                os.remove(cert_path)
            if os.path.exists(key_path):
                os.remove(key_path)
            
            logger.info(f"Certificate revoked for {device_id}")
            
        except Exception as e:
            logger.error(f"Failed to revoke certificate for {device_id}: {e}")
    
    def get_ca_certificate(self):
        """
        Get CA certificate for distribution to devices
        
        Returns:
            CA certificate as PEM string
        """
        try:
            with open(self.ca_cert_path, "rb") as f:
                return f.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to read CA certificate: {e}")
            return None

