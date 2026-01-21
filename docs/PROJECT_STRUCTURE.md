# Project Structure

This document describes the organization of the IoT Security Framework project.

## Directory Structure

```
IOT-project/
├── README.md                 # Main project documentation
├── LICENSE                   # License file
├── requirements.txt          # Python dependencies
├── start.sh                  # Main startup script
│
├── controller.py            # Main Flask web controller
├── zero_trust_integration.py # Zero Trust framework integration
├── ml_security_engine.py    # ML-based security engine
├── mininet_topology.py      # Virtual network topology
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md
│   ├── AUTO_ONBOARDING_DOCUMENTATION.md
│   ├── AUTO_ONBOARDING_CHANGELOG.md
│   ├── FEATURES_GUIDE.md
│   ├── PROJECT_DOCUMENTATION.md
│   ├── REAL_WORLD_DEPLOYMENT.md
│   ├── START_GUIDE.md
│   ├── deployment_guide.md
│   └── *.pdf                 # Reference documents
│
├── scripts/                  # Utility scripts
│   ├── cleanup.sh           # Cleanup script
│   ├── restart_controller.py
│   └── run_iot_framework.py
│
├── tests/                    # Test files
│   ├── test_ml_model.py
│   ├── test_sdn_devices.py
│   └── simple_ddos_detector.py
│
├── integration_test/         # Integration tests
│   ├── test_honeypot_flow.py
│   └── test_zero_trust.py
│
├── data/                     # Data directories (symlinked to root)
│   ├── certs/               # SSL certificates
│   ├── logs/                # Log files
│   ├── models/              # ML models
│   └── honeypot_data/       # Honeypot data
│
├── heuristic_analyst/       # Heuristic-based security analysis
│   ├── anomaly_detector.py
│   ├── baseline_manager.py
│   └── flow_analyzer.py
│
├── identity_manager/         # Device identity management
│   ├── device_onboarding.py
│   ├── certificate_manager.py
│   ├── identity_database.py
│   ├── behavioral_profiler.py
│   └── policy_generator.py
│
├── network_monitor/          # WiFi device monitoring
│   ├── wifi_detector.py
│   ├── device_id_generator.py
│   ├── pending_devices.py
│   └── auto_onboarding_service.py
│
├── trust_evaluator/          # Trust scoring system
│   ├── trust_scorer.py
│   ├── device_attestation.py
│   └── policy_adapter.py
│
├── honeypot_manager/         # Honeypot management
│   ├── honeypot_deployer.py
│   ├── docker_manager.py
│   ├── log_parser.py
│   ├── threat_intelligence.py
│   └── mitigation_generator.py
│
├── ryu_controller/           # SDN controller
│   ├── sdn_policy_engine.py
│   ├── openflow_rules.py
│   └── traffic_redirector.py
│
├── templates/                # Web templates
│   ├── dashboard.html
│   └── attack_detection.html
│
├── static/                   # Static web assets
│   └── vis-network.min.js
│
├── esp32/                    # ESP32 firmware
│   ├── gateway.ino
│   └── node.ino
│
├── *.db                      # SQLite databases
└── venv/                     # Virtual environment (gitignored)
```

## Key Directories

### Root Level
- **Main entry points**: `controller.py`, `start.sh`
- **Core modules**: Python packages in root (heuristic_analyst, identity_manager, etc.)
- **Configuration**: `requirements.txt`, `.gitignore`

### docs/
All project documentation including:
- Architecture and design documents
- User guides and deployment instructions
- API documentation
- Reference PDFs

### scripts/
Utility scripts for:
- System cleanup
- Controller management
- Framework execution

### tests/
Test files and simulators:
- Unit tests
- Integration tests
- Attack simulators
- Device simulators

### data/
Data directories (symlinked for compatibility):
- **certs/**: SSL/TLS certificates
- **logs/**: Application logs
- **models/**: Machine learning models
- **honeypot_data/**: Honeypot logs and data

### Module Packages
Each module is a Python package with:
- `__init__.py` for package initialization
- Module-specific Python files
- Self-contained functionality

## File Naming Conventions

- **Python modules**: `snake_case.py`
- **Documentation**: `UPPER_CASE.md` or `Title_Case.md`
- **Scripts**: `snake_case.sh` or `snake_case.py`
- **Databases**: `snake_case.db`

## Symlinks

The following directories are symlinked from `data/` to root for backward compatibility:
- `certs/` → `data/certs/`
- `logs/` → `data/logs/`
- `models/` → `data/models/`
- `honeypot_data/` → `data/honeypot_data/`

This ensures existing code continues to work while maintaining organized structure.

## Adding New Files

When adding new files:

1. **Documentation**: Place in `docs/`
2. **Scripts**: Place in `scripts/`
3. **Tests**: Place in `tests/` or `integration_test/`
4. **Data files**: Place in appropriate `data/` subdirectory
5. **Modules**: Create new package directory in root if needed

## Maintenance

- Run `scripts/cleanup.sh` periodically to remove cache files
- Keep `docs/` organized by topic
- Update this file when structure changes significantly

