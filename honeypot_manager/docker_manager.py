"""
Docker Manager Module
Manages Docker containers for honeypots
"""

import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# Try to import docker, but make it optional
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    # Create a dummy module object to avoid NameError
    class DummyDocker:
        @staticmethod
        def from_env():
            raise ImportError("Docker not available")
    docker = DummyDocker()

logger = logging.getLogger(__name__)
if not DOCKER_AVAILABLE:
    logger.warning("Docker module not available. Honeypot features will be limited.")

class DockerManager:
    """Manages Docker containers"""
    
    def __init__(self):
        """Initialize Docker manager"""
        if not DOCKER_AVAILABLE or docker is None:
            self.client = None
            logger.warning("Docker not available. Install with: pip install docker")
            return
            
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """
        Check if Docker is available
        
        Returns:
            True if Docker is available, False otherwise
        """
        if self.client is None:
            return False
        
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker not available: {e}")
            return False
    
    def create_container(self, image: str, name: str, ports: Dict = None,
                        volumes: Dict = None, environment: Dict = None):
        """
        Create a Docker container
        
        Args:
            image: Docker image name
            name: Container name
            ports: Port mappings {container_port: host_port}
            volumes: Volume mappings {host_path: container_path}
            environment: Environment variables
            
        Returns:
            Container object or None
        """
        if not self.is_available():
            logger.error("Docker not available")
            return None
        
        try:
            container = self.client.containers.run(
                image=image,
                name=name,
                ports=ports or {},
                volumes=volumes or {},
                environment=environment or {},
                detach=True,
                remove=False
            )
            
            logger.info(f"Container created: {name}")
            return container
            
        except Exception as e:
            logger.error(f"Failed to create container {name}: {e}")
            return None
    
    def get_container(self, name: str):
        """
        Get container by name
        
        Args:
            name: Container name
            
        Returns:
            Container object or None
        """
        if not self.is_available():
            return None
        
        try:
            container = self.client.containers.get(name)
            return container
        except Exception as e:
            if 'NotFound' in str(type(e).__name__) or 'NotFound' in str(e):
                return None
            logger.error(f"Failed to get container {name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get container {name}: {e}")
            return None
    
    def start_container(self, name: str) -> bool:
        """
        Start a container
        
        Args:
            name: Container name
            
        Returns:
            True if successful, False otherwise
        """
        container = self.get_container(name)
        if not container:
            return False
        
        try:
            container.start()
            logger.info(f"Container started: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start container {name}: {e}")
            return False
    
    def stop_container(self, name: str) -> bool:
        """
        Stop a container
        
        Args:
            name: Container name
            
        Returns:
            True if successful, False otherwise
        """
        container = self.get_container(name)
        if not container:
            return False
        
        try:
            container.stop()
            logger.info(f"Container stopped: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop container {name}: {e}")
            return False
    
    def remove_container(self, name: str) -> bool:
        """
        Remove a container
        
        Args:
            name: Container name
            
        Returns:
            True if successful, False otherwise
        """
        container = self.get_container(name)
        if not container:
            return True  # Already removed
        
        try:
            container.remove(force=True)
            logger.info(f"Container removed: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove container {name}: {e}")
            return False
    
    def get_container_logs(self, name: str, tail: int = 100) -> str:
        """
        Get container logs
        
        Args:
            name: Container name
            tail: Number of lines to retrieve
            
        Returns:
            Log output as string
        """
        container = self.get_container(name)
        if not container:
            return ""
        
        try:
            logs = container.logs(tail=tail)
            return logs.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to get logs for {name}: {e}")
            return ""
    
    def get_container_status(self, name: str) -> Optional[str]:
        """
        Get container status
        
        Args:
            name: Container name
            
        Returns:
            Status string or None
        """
        container = self.get_container(name)
        if not container:
            return None
        
        try:
            container.reload()
            return container.status
        except Exception as e:
            logger.error(f"Failed to get status for {name}: {e}")
            return None
    
    def list_containers(self, all_containers: bool = False) -> List[Dict]:
        """
        List all containers
        
        Args:
            all_containers: Include stopped containers
            
        Returns:
            List of container dictionaries
        """
        if not self.is_available():
            return []
        
        try:
            containers = self.client.containers.list(all=all_containers)
            return [
                {
                    'id': c.id[:12],
                    'name': c.name,
                    'status': c.status,
                    'image': c.image.tags[0] if c.image.tags else 'unknown'
                }
                for c in containers
            ]
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []


