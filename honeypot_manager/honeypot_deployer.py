"""
Honeypot Deployer Module
Deploys and manages honeypot containers (Cowrie)
"""

import logging
import os
from typing import Optional, Dict

from honeypot_manager.docker_manager import DockerManager, DOCKER_AVAILABLE

logger = logging.getLogger(__name__)

class HoneypotDeployer:
    """Deploys and manages honeypot containers"""
    
    def __init__(self, honeypot_type: str = "cowrie"):
        """
        Initialize honeypot deployer
        
        Args:
            honeypot_type: Type of honeypot ('cowrie', 'dionaea', etc.)
        """
        self.honeypot_type = honeypot_type
        self.docker_manager = DockerManager()
        self.container_name = f"iot_honeypot_{honeypot_type}"
        self.honeypot_port = 2222  # SSH port for Cowrie
        self.honeypot_http_port = 8080  # HTTP port for Cowrie
        
    def deploy(self) -> bool:
        """
        Deploy honeypot container
        
        Returns:
            True if successful, False otherwise
        """
        if not self.docker_manager.is_available():
            logger.error("Docker not available")
            return False
        
        # Check if container already exists
        existing = self.docker_manager.get_container(self.container_name)
        if existing:
            logger.info(f"Honeypot container {self.container_name} already exists")
            # Start if stopped
            if existing.status != 'running':
                return self.docker_manager.start_container(self.container_name)
            return True
        
        # Deploy based on honeypot type
        if self.honeypot_type == "cowrie":
            return self._deploy_cowrie()
        else:
            logger.error(f"Unknown honeypot type: {self.honeypot_type}")
            return False
    
    def _deploy_cowrie(self) -> bool:
        """
        Deploy Cowrie honeypot
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directories for Cowrie data
            cowrie_data_dir = os.path.join(os.getcwd(), "honeypot_data", "cowrie")
            os.makedirs(cowrie_data_dir, exist_ok=True)
            
            # Port mappings
            ports = {
                '2222/tcp': 2222,  # SSH
                '8080/tcp': 8080   # HTTP
            }
            
            # Volume mappings
            volumes = {
                cowrie_data_dir: {
                    'bind': '/data',
                    'mode': 'rw'
                }
            }
            
            # Environment variables
            environment = {
                'COWRIE_SSH_PORT': '2222',
                'COWRIE_HTTP_PORT': '8080'
            }
            
            # Create container
            container = self.docker_manager.create_container(
                image="cowrie/cowrie:latest",
                name=self.container_name,
                ports=ports,
                volumes=volumes,
                environment=environment
            )
            
            if container:
                logger.info("Cowrie honeypot deployed successfully")
                return True
            else:
                logger.error("Failed to deploy Cowrie honeypot")
                return False
                
        except Exception as e:
            logger.error(f"Failed to deploy Cowrie: {e}")
            return False
    
    def start(self) -> bool:
        """
        Start honeypot container
        
        Returns:
            True if successful, False otherwise
        """
        return self.docker_manager.start_container(self.container_name)
    
    def stop(self) -> bool:
        """
        Stop honeypot container
        
        Returns:
            True if successful, False otherwise
        """
        return self.docker_manager.stop_container(self.container_name)
    
    def remove(self) -> bool:
        """
        Remove honeypot container
        
        Returns:
            True if successful, False otherwise
        """
        return self.docker_manager.remove_container(self.container_name)
    
    def get_status(self) -> Optional[str]:
        """
        Get honeypot status
        
        Returns:
            Status string or None
        """
        return self.docker_manager.get_container_status(self.container_name)
    
    def is_running(self) -> bool:
        """
        Check if honeypot is running
        
        Returns:
            True if running, False otherwise
        """
        status = self.get_status()
        return status == 'running'
    
    def get_logs(self, tail: int = 100) -> str:
        """
        Get honeypot logs
        
        Args:
            tail: Number of lines to retrieve
            
        Returns:
            Log output as string
        """
        return self.docker_manager.get_container_logs(self.container_name, tail)
    
    def get_honeypot_info(self) -> Dict:
        """
        Get honeypot information
        
        Returns:
            Dictionary with honeypot information
        """
        return {
            'type': self.honeypot_type,
            'container_name': self.container_name,
            'status': self.get_status(),
            'running': self.is_running(),
            'ssh_port': self.honeypot_port,
            'http_port': self.honeypot_http_port
        }

