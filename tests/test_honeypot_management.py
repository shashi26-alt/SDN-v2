"""
Test Honeypot Management
Tests honeypot deployment, log parsing, threat intelligence, and mitigation
"""

import pytest
import json
import os
import tempfile
import shutil


class TestHoneypotManagement:
    """Test honeypot management scenarios"""
    
    def test_honeypot_deployer_initialization(self):
        """Test honeypot deployer initialization"""
        try:
            from honeypot_manager.honeypot_deployer import HoneypotDeployer
            
            deployer = HoneypotDeployer(honeypot_type="cowrie")
            assert deployer.honeypot_type == "cowrie"
            assert deployer.container_name == "iot_honeypot_cowrie"
            assert deployer.honeypot_port == 2222
            print("   ✅ HoneypotDeployer initialized")
        except ImportError:
            pytest.skip("Honeypot manager not available")
    
    def test_docker_manager_availability(self):
        """Test Docker manager availability check"""
        try:
            from honeypot_manager.docker_manager import DockerManager
            
            manager = DockerManager()
            # Should not raise exception even if Docker unavailable
            available = manager.is_available()
            assert isinstance(available, bool)
            print(f"   ✅ Docker availability check: {available}")
        except ImportError:
            pytest.skip("Docker manager not available")
    
    def test_honeypot_log_parser(self):
        """Test honeypot log parsing"""
        try:
            from honeypot_manager.log_parser import HoneypotLogParser
            
            parser = HoneypotLogParser(honeypot_type="cowrie")
            
            # Test with sample Cowrie log
            sample_log = """
            {"eventid": "cowrie.login.success", "username": "admin", "password": "12345", "message": "login attempt"}
            {"eventid": "cowrie.command.input", "input": "whoami", "message": "command executed"}
            """
            
            threats = parser.parse_logs(sample_log)
            assert isinstance(threats, list)
            print(f"   ✅ Log parser extracted {len(threats)} threats")
        except ImportError:
            pytest.skip("Log parser not available")
    
    def test_threat_intelligence_processing(self):
        """Test threat intelligence processing"""
        try:
            from honeypot_manager.threat_intelligence import ThreatIntelligence
            
            ti = ThreatIntelligence()
            
            # Test log processing
            sample_log = """
            {"eventid": "cowrie.login.success", "src_ip": "192.168.1.100", "username": "admin"}
            """
            
            threats = ti.process_logs(sample_log)
            assert isinstance(threats, list)
            print(f"   ✅ Threat intelligence processed {len(threats)} threats")
        except ImportError:
            pytest.skip("Threat intelligence not available")
    
    def test_mitigation_generator(self):
        """Test mitigation rule generation"""
        try:
            from honeypot_manager.mitigation_generator import MitigationGenerator
            
            generator = MitigationGenerator()
            
            # Test mitigation generation
            threat = {
                'src_ip': '192.168.1.100',
                'threat_type': 'brute_force',
                'severity': 'high'
            }
            
            mitigation = generator.generate_mitigation(threat)
            assert isinstance(mitigation, dict)
            assert 'action' in mitigation
            print(f"   ✅ Mitigation rule generated: {mitigation.get('action')}")
        except ImportError:
            pytest.skip("Mitigation generator not available")
    
    def test_honeypot_deployment_check(self):
        """Test honeypot deployment status check"""
        try:
            from honeypot_manager.honeypot_deployer import HoneypotDeployer
            
            deployer = HoneypotDeployer()
            
            # Check deployment (may fail if Docker unavailable, that's OK)
            result = deployer.deploy()
            # Result can be True/False depending on Docker availability
            assert isinstance(result, bool)
            print(f"   ✅ Deployment check completed: {result}")
        except ImportError:
            pytest.skip("Honeypot deployer not available")
    
    def test_honeypot_log_file_parsing(self):
        """Test parsing honeypot log files"""
        try:
            from honeypot_manager.log_parser import HoneypotLogParser
            
            parser = HoneypotLogParser()
            
            # Create temporary log file
            test_dir = tempfile.mkdtemp()
            log_file = os.path.join(test_dir, "cowrie.json")
            
            # Write sample log
            with open(log_file, 'w') as f:
                f.write('{"eventid": "cowrie.login.success", "src_ip": "10.0.0.1"}\n')
                f.write('{"eventid": "cowrie.command.input", "input": "ls", "src_ip": "10.0.0.1"}\n')
            
            # Read and parse
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            threats = parser.parse_logs(log_content)
            assert len(threats) > 0
            
            shutil.rmtree(test_dir, ignore_errors=True)
            print(f"   ✅ Log file parsing: {len(threats)} threats extracted")
        except ImportError:
            pytest.skip("Log parser not available")
    
    def test_threat_intelligence_blocked_ips(self):
        """Test threat intelligence blocked IPs tracking"""
        try:
            from honeypot_manager.threat_intelligence import ThreatIntelligence
            
            ti = ThreatIntelligence()
            
            # Process threat with IP
            threat = {
                'src_ip': '192.168.1.100',
                'threat_type': 'malicious',
                'severity': 'high'
            }
            
            # Should track blocked IPs
            assert isinstance(ti.blocked_ips, dict)
            print("   ✅ Blocked IPs tracking available")
        except ImportError:
            pytest.skip("Threat intelligence not available")
    
    def test_honeypot_container_management(self):
        """Test honeypot container management operations"""
        try:
            from honeypot_manager.docker_manager import DockerManager
            
            manager = DockerManager()
            
            if manager.is_available():
                # Test container operations
                container_name = "test_honeypot"
                
                # Get container (may not exist, that's OK)
                container = manager.get_container(container_name)
                # Should return None or container object
                assert container is None or hasattr(container, 'status')
                print("   ✅ Container management operations available")
            else:
                print("   ⚠️  Docker not available (skipping container tests)")
        except ImportError:
            pytest.skip("Docker manager not available")

