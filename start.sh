#!/bin/bash

# Zero Trust SDN Framework - Complete System Startup Script
# Automatically starts all components of the Zero Trust SDN Framework
# Includes: ML-based DDoS detection, Honeypot Management, Suspicious Device Redirection, Dashboard Alerts

# Don't exit on error for process checks
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root/sudo
if [ "$EUID" -eq 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Warning: Running as root/sudo is not recommended${NC}"
    echo -e "${YELLOW}   This may cause permission issues with log files and directories${NC}"
    echo -e "${YELLOW}   Consider running without sudo: ./start.sh${NC}"
    read -p "Continue anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    echo ""
fi

# Process IDs
CONTROLLER_PID=""
RYU_PID=""
ZERO_TRUST_PID=""
MININET_PID=""
HONEYPOT_CONTAINER=""

# Status flags to prevent repeated warnings
CONTROLLER_STOPPED_REPORTED="false"
RYU_STOPPED_REPORTED="false"
ZERO_TRUST_STOPPED_REPORTED="false"
MININET_STOPPED_REPORTED="false"

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down Zero Trust SDN Framework...${NC}"
    
    # Kill all processes
    if [ ! -z "$CONTROLLER_PID" ]; then
        echo "   Stopping Flask controller (PID: $CONTROLLER_PID)..."
        kill $CONTROLLER_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$RYU_PID" ]; then
        echo "   Stopping Ryu SDN controller (PID: $RYU_PID)..."
        kill $RYU_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$ZERO_TRUST_PID" ]; then
        echo "   Stopping Zero Trust framework (PID: $ZERO_TRUST_PID)..."
        kill $ZERO_TRUST_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$MININET_PID" ] && kill -0 $MININET_PID 2>/dev/null; then
        echo "   Stopping Mininet topology (PID: $MININET_PID)..."
        kill $MININET_PID 2>/dev/null || true
        # Mininet may need special cleanup
        sudo mn -c 2>/dev/null || true
    fi
    
    # Stop honeypot container if it was started by this script
    if [ ! -z "$HONEYPOT_CONTAINER" ] && command -v docker &> /dev/null; then
        echo "   Stopping honeypot container..."
        docker stop "$HONEYPOT_CONTAINER" 2>/dev/null || true
    fi
    
    # Wait for processes to terminate
    sleep 2
    
    # Force kill if still running (only if we have permission)
    if [ "$EUID" -eq 0 ] || [ -z "$EUID" ]; then
        pkill -f "controller.py" 2>/dev/null || true
        pkill -f "ryu-manager" 2>/dev/null || true
        pkill -f "zero_trust_integration.py" 2>/dev/null || true
        pkill -f "mininet_topology.py" 2>/dev/null || true
        pkill -f "mininet" 2>/dev/null || true
        # Mininet cleanup may require sudo
        sudo mn -c 2>/dev/null || true
    else
        pkill -u $USER -f "controller.py" 2>/dev/null || true
        pkill -u $USER -f "ryu-manager" 2>/dev/null || true
        pkill -u $USER -f "zero_trust_integration.py" 2>/dev/null || true
        pkill -u $USER -f "mininet_topology.py" 2>/dev/null || true
        pkill -u $USER -f "mininet" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ All components stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Banner
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          🔐 Zero Trust SDN Framework - Complete System Startup 🔐          ║${NC}"
echo -e "${BLUE}║                                                                              ║${NC}"
echo -e "${BLUE}║  • Flask Controller (Web Dashboard & API)                                  ║${NC}"
echo -e "${BLUE}║  • Ryu SDN Controller (OpenFlow Policy Enforcement)                        ║${NC}"
echo -e "${BLUE}║  • Zero Trust Integration Framework                                        ║${NC}"
echo -e "${BLUE}║  • ML-Based DDoS Detection (TensorFlow/Keras)                             ║${NC}"
echo -e "${BLUE}║  • Honeypot Management (Suspicious Device Redirection)                     ║${NC}"
echo -e "${BLUE}║  • Dashboard Alerts & Threat Intelligence                                  ║${NC}"
echo -e "${BLUE}║  • Virtual IoT Devices (Optional)                                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✅ Python version: $PYTHON_VERSION${NC}"

# Check if we're in the right directory
if [ ! -f "controller.py" ]; then
    echo -e "${RED}❌ Error: controller.py not found. Please run this script from the project directory${NC}"
    exit 1
fi

# Check for virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    VENV_PYTHON="./venv/bin/python3"
    if [ -f "$VENV_PYTHON" ]; then
        PYTHON_CMD="$VENV_PYTHON"
    else
        PYTHON_CMD="python3"
    fi
else
    echo -e "${YELLOW}⚠️  Virtual environment not found, using system Python${NC}"
    PYTHON_CMD="python3"
    
    # Offer to install from requirements.txt
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}💡 Tip: You can install all dependencies from requirements.txt${NC}"
        read -p "Install all dependencies from requirements.txt now? [Y/n]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${BLUE}📦 Installing dependencies from requirements.txt...${NC}"
            local pip_cmd=""
            if command -v pip3 &> /dev/null; then
                pip_cmd="pip3"
            elif command -v pip &> /dev/null; then
                pip_cmd="pip"
            fi
            
            if [ ! -z "$pip_cmd" ]; then
                if $pip_cmd install -q -r requirements.txt 2>/dev/null; then
                    echo -e "${GREEN}✅ All dependencies installed successfully${NC}"
                elif [ "$EUID" -ne 0 ] && sudo $pip_cmd install -q -r requirements.txt 2>/dev/null; then
                    echo -e "${GREEN}✅ All dependencies installed successfully${NC}"
                else
                    echo -e "${YELLOW}⚠️  Some packages may have failed to install${NC}"
                    echo -e "${YELLOW}   You can install manually later: $pip_cmd install -r requirements.txt${NC}"
                fi
            else
                echo -e "${RED}❌ pip not found. Cannot install dependencies.${NC}"
            fi
        fi
    fi
fi

# Function to install package (defined before use)
install_package() {
    local package_name=$1
    local import_name=$2  # Optional: different import name
    local pip_cmd=""
    
    # Use import_name if provided, otherwise derive from package_name
    if [ -z "$import_name" ]; then
        # Common mappings
        case "$package_name" in
            "pyOpenSSL") import_name="OpenSSL" ;;
            "python-dotenv") import_name="dotenv" ;;
            *) import_name="${package_name//-/_}" ;;
        esac
    fi
    
    # Determine pip command
    if [ -d "venv" ] && [ -f "./venv/bin/pip" ]; then
        pip_cmd="./venv/bin/pip"
    elif [ -d "venv" ] && [ -f "./venv/bin/pip3" ]; then
        pip_cmd="./venv/bin/pip3"
    elif command -v pip3 &> /dev/null; then
        pip_cmd="pip3"
    elif command -v pip &> /dev/null; then
        pip_cmd="pip"
    else
        echo -e "${RED}  ❌ pip not found. Cannot install packages.${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}     Installing $package_name...${NC}"
    
    # Try installation (suppress output but show errors)
    if $pip_cmd install --upgrade $package_name > /dev/null 2>&1; then
        # Check if it can be imported
        if $PYTHON_CMD -c "import $import_name" 2>/dev/null; then
            echo -e "${GREEN}     ✅ $package_name installed successfully${NC}"
            return 0
        fi
    fi
    
    # Try with sudo if not in venv and not root
    if [ ! -d "venv" ] && [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}     Trying with sudo...${NC}"
        if sudo $pip_cmd install --upgrade $package_name > /dev/null 2>&1; then
            if $PYTHON_CMD -c "import $import_name" 2>/dev/null; then
                echo -e "${GREEN}     ✅ $package_name installed successfully${NC}"
                return 0
            fi
        fi
    fi
    
    echo -e "${RED}     ❌ Failed to install $package_name${NC}"
    return 1
}

# Special handler for ryu (needs eventlet too)
install_ryu() {
    if install_package "ryu" "ryu" && install_package "eventlet" "eventlet"; then
        return 0
    else
        return 1
    fi
}

# Check dependencies
echo ""
echo -e "${BLUE}📦 Checking dependencies...${NC}"

# Check Flask (required)
if $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo -e "${GREEN}  ✅ Flask${NC}"
else
    echo -e "${YELLOW}  ⚠️  Flask not found (required)${NC}"
    if install_package "flask" "flask"; then
        echo -e "${GREEN}  ✅ Flask${NC}"
    else
        echo -e "${RED}  ❌ Failed to install Flask. Please install manually: pip install flask${NC}"
        exit 1
    fi
fi

# Check TensorFlow/Keras (optional, for ML model)
if $PYTHON_CMD -c "import tensorflow" 2>/dev/null || $PYTHON_CMD -c "import keras" 2>/dev/null; then
    TENSORFLOW_AVAILABLE=true
    echo -e "${GREEN}  ✅ TensorFlow/Keras (ML model support)${NC}"
else
    TENSORFLOW_AVAILABLE=false
    echo -e "${YELLOW}  ⚠️  TensorFlow/Keras not found (optional, for ML-based DDoS detection)${NC}"
    echo -e "${YELLOW}     ML detection will use fallback heuristics${NC}"
    read -p "     Install TensorFlow? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if install_package "tensorflow" "tensorflow"; then
            TENSORFLOW_AVAILABLE=true
            echo -e "${GREEN}  ✅ TensorFlow/Keras${NC}"
        else
            echo -e "${YELLOW}  ⚠️  TensorFlow installation failed (will use fallback detection)${NC}"
        fi
    fi
fi

# Check cryptography (optional, for Zero Trust)
if $PYTHON_CMD -c "import cryptography" 2>/dev/null; then
    CRYPTOGRAPHY_AVAILABLE=true
    echo -e "${GREEN}  ✅ cryptography${NC}"
else
    CRYPTOGRAPHY_AVAILABLE=false
    echo -e "${YELLOW}  ⚠️  cryptography not found (optional, for certificates)${NC}"
    read -p "     Install cryptography? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        if install_package "cryptography" "cryptography"; then
            CRYPTOGRAPHY_AVAILABLE=true
            echo -e "${GREEN}  ✅ cryptography${NC}"
        else
            echo -e "${YELLOW}  ⚠️  cryptography installation failed (will skip Zero Trust features)${NC}"
        fi
    fi
fi

# Check Ryu/os-ken (required - other components depend on it)
# os-ken is the Python 3.13+ compatible fork of Ryu
if $PYTHON_CMD -c "import os_ken" 2>/dev/null; then
    RYU_AVAILABLE=true
    USING_OSKEN=true
    echo -e "${GREEN}  ✅ os-ken SDN Controller (Python 3.13+ compatible)${NC}"
elif command -v ryu-manager &> /dev/null || $PYTHON_CMD -c "import ryu" 2>/dev/null; then
    RYU_AVAILABLE=true
    USING_OSKEN=false
    echo -e "${GREEN}  ✅ Ryu SDN Controller${NC}"
else
    RYU_AVAILABLE=false
    USING_OSKEN=false
    echo -e "${YELLOW}  ⚠️  Ryu/os-ken SDN Controller not found (required)${NC}"
    echo -e "${YELLOW}     Installing os-ken (required for Zero Trust Framework)...${NC}"
    if install_package "os-ken" "os_ken" && install_package "eventlet" "eventlet"; then
        RYU_AVAILABLE=true
        USING_OSKEN=true
        echo -e "${GREEN}  ✅ os-ken SDN Controller installed${NC}"
    else
        echo -e "${RED}  ❌ Failed to install os-ken SDN Controller${NC}"
        echo -e "${RED}     Please install manually: pip install os-ken eventlet${NC}"
        echo -e "${RED}     Or: pip3 install -r requirements.txt${NC}"
        exit 1
    fi
fi

# Check Docker (optional, for honeypot)
DOCKER_AVAILABLE=false
DOCKER_RUNNING=false
if command -v docker &> /dev/null; then
    # Check if Docker daemon is running
    if docker info > /dev/null 2>&1; then
        DOCKER_RUNNING=true
        if $PYTHON_CMD -c "import docker" 2>/dev/null; then
            DOCKER_AVAILABLE=true
            echo -e "${GREEN}  ✅ Docker (honeypot support enabled)${NC}"
        else
            echo -e "${YELLOW}  ⚠️  Docker command found, but Python module missing${NC}"
            read -p "     Install docker Python module? [Y/n]: " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                if install_package "docker" "docker"; then
                    DOCKER_AVAILABLE=true
                    echo -e "${GREEN}  ✅ Docker${NC}"
                else
                    echo -e "${YELLOW}  ⚠️  Docker Python module installation failed${NC}"
                fi
            fi
        fi
    else
        echo -e "${YELLOW}  ⚠️  Docker installed but daemon not running${NC}"
        echo -e "${YELLOW}     Start Docker with: sudo systemctl start docker${NC}"
        echo -e "${YELLOW}     Honeypot features will be unavailable${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  Docker not found (optional, for honeypot)${NC}"
    echo -e "${YELLOW}     Install with: sudo apt-get install docker.io${NC}"
    echo -e "${YELLOW}     Or visit: https://docs.docker.com/get-docker/${NC}"
    echo -e "${YELLOW}     Honeypot features will be unavailable${NC}"
fi

# Create necessary directories
echo ""
echo -e "${BLUE}📁 Setting up directories...${NC}"
mkdir -p certs honeypot_data logs data/models

# Fix permissions if running as root
if [ "$EUID" -eq 0 ] && [ ! -z "$SUDO_USER" ]; then
    chown -R $SUDO_USER:$SUDO_USER certs honeypot_data logs data 2>/dev/null || true
fi

# Check database file permissions
if [ -f "identity.db" ]; then
    if [ ! -w "identity.db" ]; then
        echo -e "${YELLOW}⚠️  Database file identity.db is not writable${NC}"
        echo -e "${YELLOW}   File is owned by: $(stat -c '%U:%G' identity.db 2>/dev/null || echo 'unknown')${NC}"
        echo -e "${YELLOW}   The system will automatically use an alternative database location${NC}"
        echo -e "${YELLOW}   To fix permissions, run:${NC}"
        echo -e "${YELLOW}     sudo chown $USER:$USER identity.db${NC}"
        echo -e "${YELLOW}     chmod 664 identity.db${NC}"
    fi
fi

echo -e "${GREEN}✅ Directories ready${NC}"

# Check for ML model
if [ -d "data/models/ddos_model_retrained" ] || [ -f "data/models/ddos_model_retrained.keras" ]; then
    echo -e "${GREEN}✅ ML model found${NC}"
else
    echo -e "${YELLOW}⚠️  ML model not found at data/models/ddos_model_retrained${NC}"
    echo -e "${YELLOW}   System will use fallback heuristic detection${NC}"
fi

# Start Flask Controller
echo ""
echo -e "${BLUE}🚀 Starting Flask Controller...${NC}"

# Check if port 5000 is already in use
if command -v lsof &> /dev/null; then
    EXISTING_PID=$(lsof -ti:5000 2>/dev/null)
    if [ ! -z "$EXISTING_PID" ]; then
        echo -e "${YELLOW}⚠️  Port 5000 is already in use (PID: $EXISTING_PID)${NC}"
        echo -e "${YELLOW}   Stopping existing process...${NC}"
        kill $EXISTING_PID 2>/dev/null || true
        sleep 2
    fi
elif command -v netstat &> /dev/null; then
    EXISTING_PID=$(netstat -tuln 2>/dev/null | grep ":5000 " | awk '{print $NF}' | cut -d'/' -f1 | head -1)
    if [ ! -z "$EXISTING_PID" ]; then
        echo -e "${YELLOW}⚠️  Port 5000 is already in use${NC}"
        echo -e "${YELLOW}   Attempting to stop existing process...${NC}"
        pkill -f "controller.py" 2>/dev/null || true
        sleep 2
    fi
fi

# Also kill any existing controller.py processes
pkill -f "controller.py" 2>/dev/null || true
sleep 1

nohup $PYTHON_CMD controller.py > logs/controller.log 2>&1 &
CONTROLLER_PID=$!
echo -e "${GREEN}✅ Flask Controller started (PID: $CONTROLLER_PID)${NC}"

# Wait for controller to be ready
echo -e "${YELLOW}⏳ Waiting for controller to initialize...${NC}"
CONTROLLER_READY=false

# Function to check if controller is ready
check_controller_ready() {
    # First check if port 5000 is listening (more reliable)
    if command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":5000 "; then
            PORT_LISTENING=true
        else
            PORT_LISTENING=false
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln 2>/dev/null | grep -q ":5000 "; then
            PORT_LISTENING=true
        else
            PORT_LISTENING=false
        fi
    else
        PORT_LISTENING=true  # Assume listening if we can't check
    fi
    
    if [ "$PORT_LISTENING" = false ]; then
        return 1
    fi
    
    # Try curl first (with timeout)
    if command -v curl &> /dev/null; then
        HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 3 http://localhost:5000 2>/dev/null)
        if [ "$HTTP_CODE" = "200" ]; then
            return 0
        fi
    fi
    
    # Try wget (with timeout)
    if command -v wget &> /dev/null; then
        if wget -q -O /dev/null -T 2 http://localhost:5000 2>&1 | grep -q "200 OK"; then
            return 0
        fi
    fi
    
    # Try python (with timeout)
    if $PYTHON_CMD -c "import urllib.request, socket; socket.setdefaulttimeout(2); urllib.request.urlopen('http://localhost:5000').read()" 2>/dev/null; then
        return 0
    fi
    
    return 1
}

# Wait for controller (up to 40 seconds)
for i in {1..40}; do
    # Check if process is still running
    if ! kill -0 $CONTROLLER_PID 2>/dev/null; then
        echo ""
        echo -e "${RED}❌ Controller process died!${NC}"
        echo -e "${YELLOW}   Check logs/controller.log for errors:${NC}"
        tail -30 logs/controller.log 2>/dev/null || echo "   (log file not found)"
        cleanup
        exit 1
    fi
    
    # Check if controller is responding
    if check_controller_ready; then
        echo ""
        echo -e "${GREEN}✅ Controller is ready!${NC}"
        CONTROLLER_READY=true
        break
    fi
    
    sleep 1
    if [ $((i % 5)) -eq 0 ]; then
        echo -n " [${i}s]"
    else
        echo -n "."
    fi
done

if [ "$CONTROLLER_READY" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Controller not responding after 40 seconds${NC}"
    echo -e "${YELLOW}   Process is running (PID: $CONTROLLER_PID)${NC}"
    echo -e "${YELLOW}   Check logs/controller.log:${NC}"
    tail -20 logs/controller.log 2>/dev/null || echo "   (log file not found)"
    echo -e "${YELLOW}   Continuing anyway - controller may be starting slowly...${NC}"
fi

# Start Ryu SDN Controller (required - must start before other components)
if [ "$RYU_AVAILABLE" = true ]; then
    echo ""
    echo -e "${BLUE}🌐 Starting Ryu SDN Controller (required)...${NC}"
    
    # Check if Ryu module file exists
    if [ ! -f "ryu_controller/sdn_policy_engine.py" ]; then
        echo -e "${RED}❌ Ryu controller file not found: ryu_controller/sdn_policy_engine.py${NC}"
        echo -e "${RED}   Cannot start system without Ryu controller${NC}"
        exit 1
    fi
    
    # Set PYTHONPATH to include project root for imports
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    if [ "$USING_OSKEN" = true ]; then
        if command -v osken-manager &> /dev/null; then
            osken-manager --ofp-tcp-listen-port 6653 --verbose ryu_controller.sdn_policy_engine > logs/ryu.log 2>&1 &
            RYU_PID=$!
        else
            $PYTHON_CMD -m os_ken.cmd.manager --ofp-tcp-listen-port 6653 --verbose ryu_controller.sdn_policy_engine > logs/ryu.log 2>&1 &
            RYU_PID=$!
        fi
    elif command -v ryu-manager &> /dev/null; then
        ryu-manager --ofp-tcp-listen-port 6653 --verbose ryu_controller.sdn_policy_engine > logs/ryu.log 2>&1 &
        RYU_PID=$!
    else
        $PYTHON_CMD -m ryu.cmd.manager --ofp-tcp-listen-port 6653 --verbose ryu_controller.sdn_policy_engine > logs/ryu.log 2>&1 &
        RYU_PID=$!
    fi
    
    # Wait for Ryu to start and verify it's running
    echo -e "${YELLOW}⏳ Waiting for Ryu SDN Controller to initialize...${NC}"
    RYU_READY=false
    for i in {1..20}; do
        if kill -0 $RYU_PID 2>/dev/null; then
            # Check if Ryu is listening on port 6653 (OpenFlow)
            if command -v netstat &> /dev/null; then
                if netstat -tuln 2>/dev/null | grep -q ":6653 "; then
                    RYU_READY=true
                    break
                fi
            elif command -v ss &> /dev/null; then
                if ss -tuln 2>/dev/null | grep -q ":6653 "; then
                    RYU_READY=true
                    break
                fi
            else
                # If we can't check port, just verify process is running
                sleep 2
                if kill -0 $RYU_PID 2>/dev/null; then
                    RYU_READY=true
                    break
                fi
            fi
        else
            echo -e "${RED}❌ Ryu SDN Controller process died${NC}"
            echo -e "${YELLOW}   Check logs/ryu.log for errors:${NC}"
            tail -20 logs/ryu.log 2>/dev/null || echo "   (log file not found)"
            exit 1
        fi
        
        sleep 1
        if [ $((i % 3)) -eq 0 ]; then
            echo -n "."
        fi
    done
    
    if [ "$RYU_READY" = true ]; then
        echo ""
        echo -e "${GREEN}✅ Ryu SDN Controller started and ready (PID: $RYU_PID)${NC}"
    else
        echo ""
        echo -e "${RED}❌ Ryu SDN Controller failed to start properly${NC}"
        echo -e "${YELLOW}   Check logs/ryu.log for errors:${NC}"
        tail -20 logs/ryu.log 2>/dev/null || echo "   (log file not found)"
        echo -e "${RED}   Cannot continue without Ryu controller${NC}"
        exit 1
    fi
else
    echo ""
    echo -e "${RED}❌ Ryu SDN Controller is required but not available${NC}"
    echo -e "${RED}   Cannot start system without Ryu${NC}"
    exit 1
fi

# Start Zero Trust Integration Framework (requires Ryu to be running)
echo ""
echo -e "${BLUE}🔐 Starting Zero Trust Integration Framework...${NC}"
if [ -f "zero_trust_integration.py" ]; then
    if [ "$RYU_AVAILABLE" != true ] || [ -z "$RYU_PID" ]; then
        echo -e "${RED}❌ Cannot start Zero Trust Framework: Ryu SDN Controller is not running${NC}"
        echo -e "${YELLOW}   Zero Trust Framework requires Ryu to be running${NC}"
    elif [ "$CRYPTOGRAPHY_AVAILABLE" = true ]; then
        # Wait a moment to ensure Ryu is fully ready
        sleep 2
        $PYTHON_CMD zero_trust_integration.py > logs/zero_trust.log 2>&1 &
        ZERO_TRUST_PID=$!
        sleep 3
        # Check if it's still running
        if kill -0 $ZERO_TRUST_PID 2>/dev/null; then
            echo -e "${GREEN}✅ Zero Trust Framework started (PID: $ZERO_TRUST_PID)${NC}"
            echo -e "${BLUE}   Features enabled:${NC}"
            echo -e "${BLUE}     • Suspicious device detection (ML + Anomaly + Trust Score)${NC}"
            echo -e "${BLUE}     • Automatic traffic redirection to honeypot${NC}"
            echo -e "${BLUE}     • Honeypot log monitoring & threat intelligence${NC}"
            echo -e "${BLUE}     • Dashboard alerts for suspicious devices${NC}"
        else
            echo -e "${RED}❌ Zero Trust Framework failed to start${NC}"
            echo -e "${YELLOW}   Check logs/zero_trust.log for errors:${NC}"
            tail -10 logs/zero_trust.log 2>/dev/null || echo "   (log file not found)"
            ZERO_TRUST_PID=""
        fi
    else
        echo -e "${YELLOW}⚠️  Skipping Zero Trust Framework (cryptography not installed)${NC}"
        echo -e "${YELLOW}   Install with: pip install cryptography${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Zero Trust integration file not found, skipping${NC}"
fi

# Check honeypot status (managed by Zero Trust Framework)
if [ "$DOCKER_AVAILABLE" = true ] && [ "$DOCKER_RUNNING" = true ]; then
    echo ""
    echo -e "${BLUE}🍯 Checking Honeypot Status...${NC}"
    sleep 2  # Give Zero Trust Framework time to deploy honeypot
    
    if docker ps --format "{{.Names}}" 2>/dev/null | grep -q "iot_honeypot"; then
        HONEYPOT_CONTAINER=$(docker ps --format "{{.Names}}" 2>/dev/null | grep "iot_honeypot" | head -1)
        echo -e "${GREEN}✅ Honeypot container running: $HONEYPOT_CONTAINER${NC}"
    else
        echo -e "${YELLOW}⚠️  Honeypot container not yet deployed${NC}"
        echo -e "${YELLOW}   Zero Trust Framework will deploy it automatically when needed${NC}"
    fi
fi

# Start Mininet Topology (optional, for testing)
if [ -f "mininet_topology.py" ]; then
    echo ""
    read -p "Start virtual IoT devices (Mininet)? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🌐 Starting Virtual IoT Devices...${NC}"
        $PYTHON_CMD mininet_topology.py > logs/mininet.log 2>&1 &
        MININET_PID=$!
        echo -e "${GREEN}✅ Virtual devices started (PID: $MININET_PID)${NC}"
    fi
fi

# Display status
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ System Started Successfully! ✅                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 System Status:${NC}"
echo -e "   ${GREEN}✅${NC} Flask Controller:     http://localhost:5000 (PID: $CONTROLLER_PID)"
if [ ! -z "$RYU_PID" ]; then
    echo -e "   ${GREEN}✅${NC} Ryu SDN Controller:   Running (PID: $RYU_PID)"
else
    echo -e "   ${RED}❌${NC}  Ryu SDN Controller:   Not running (REQUIRED)"
fi
if [ ! -z "$ZERO_TRUST_PID" ]; then
    echo -e "   ${GREEN}✅${NC} Zero Trust Framework:  Running (PID: $ZERO_TRUST_PID)"
else
    echo -e "   ${YELLOW}⚠️${NC}  Zero Trust Framework:  Not running"
fi
if [ "$DOCKER_AVAILABLE" = true ] && [ "$DOCKER_RUNNING" = true ]; then
    if [ ! -z "$HONEYPOT_CONTAINER" ]; then
        echo -e "   ${GREEN}✅${NC} Honeypot:              Running ($HONEYPOT_CONTAINER)"
    else
        echo -e "   ${YELLOW}⚠️${NC}  Honeypot:              Available (will deploy on demand)"
    fi
else
    echo -e "   ${YELLOW}⚠️${NC}  Honeypot:              Not available (Docker required)"
fi
if [ ! -z "$MININET_PID" ]; then
    echo -e "   ${GREEN}✅${NC} Virtual Devices:      Running (PID: $MININET_PID)"
fi

echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo -e "   • Web Dashboard:    ${GREEN}http://localhost:5000${NC}"
echo -e "   • API Endpoints:     ${GREEN}http://localhost:5000/api/*${NC}"
echo -e "   • Security Alerts:   ${GREEN}http://localhost:5000/api/alerts/suspicious_devices${NC}"
echo -e "   • Honeypot Status:   ${GREEN}http://localhost:5000/api/honeypot/redirected_devices${NC}"
if [ ! -z "$RYU_PID" ]; then
    echo -e "   • SDN Controller:   ${GREEN}Port 6653 (OpenFlow)${NC}"
fi

echo ""
echo -e "${BLUE}🔒 Security Features:${NC}"
echo -e "   • ML-Based DDoS Detection:     ${GREEN}Enabled${NC}"
echo -e "   • Suspicious Device Detection:  ${GREEN}Enabled${NC}"
echo -e "   • Honeypot Redirection:         ${GREEN}Enabled${NC}"
echo -e "   • Dashboard Alerts:             ${GREEN}Enabled${NC}"
echo -e "   • Threat Intelligence:         ${GREEN}Enabled${NC}"

echo ""
echo -e "${BLUE}📝 Log Files:${NC}"
echo -e "   • Controller:        ${YELLOW}logs/controller.log${NC}"
if [ ! -z "$RYU_PID" ]; then
    echo -e "   • Ryu:               ${YELLOW}logs/ryu.log${NC}"
fi
if [ ! -z "$ZERO_TRUST_PID" ]; then
    echo -e "   • Zero Trust:        ${YELLOW}logs/zero_trust.log${NC}"
fi
if [ ! -z "$MININET_PID" ]; then
    echo -e "   • Virtual Devices:   ${YELLOW}logs/mininet.log${NC}"
fi
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "   • Honeypot Logs:     ${YELLOW}honeypot_data/cowrie/logs/${NC}"
fi

echo ""
echo -e "${YELLOW}⌨️  Press Ctrl+C to stop all components${NC}"
echo ""

# Monitor processes and keep script running
echo -e "${GREEN}🔄 System is running... Monitoring components...${NC}"
echo ""

# Keep script running and monitor
while true; do
    sleep 10
    
    # Check if controller is still running
    if [ ! -z "$CONTROLLER_PID" ] && ! kill -0 $CONTROLLER_PID 2>/dev/null; then
        if [ "$CONTROLLER_STOPPED_REPORTED" != "true" ]; then
            echo ""
            echo -e "${RED}❌ Flask Controller stopped unexpectedly!${NC}"
            echo -e "${YELLOW}   Checking logs/controller.log for errors:${NC}"
            tail -20 logs/controller.log 2>/dev/null || echo "   (log file not found)"
            
            # Check if port is still in use (might be a different process)
            if command -v lsof &> /dev/null; then
                OTHER_PID=$(lsof -ti:5000 2>/dev/null)
                if [ ! -z "$OTHER_PID" ] && [ "$OTHER_PID" != "$CONTROLLER_PID" ]; then
                    echo -e "${YELLOW}   Port 5000 is in use by another process (PID: $OTHER_PID)${NC}"
                    echo -e "${YELLOW}   Stopping conflicting process...${NC}"
                    kill $OTHER_PID 2>/dev/null || true
                    sleep 1
                fi
            fi
            
            # Try to restart the controller
            echo -e "${YELLOW}   Attempting to restart Flask Controller...${NC}"
            nohup $PYTHON_CMD controller.py > logs/controller.log 2>&1 &
            CONTROLLER_PID=$!
            sleep 3
            if kill -0 $CONTROLLER_PID 2>/dev/null; then
                echo -e "${GREEN}✅ Flask Controller restarted (PID: $CONTROLLER_PID)${NC}"
                CONTROLLER_STOPPED_REPORTED="false"
            else
                echo -e "${RED}❌ Failed to restart Flask Controller${NC}"
                CONTROLLER_STOPPED_REPORTED="true"
                cleanup
                exit 1
            fi
        fi
    fi
    
    # Check Ryu - CRITICAL: other components depend on it
    if [ ! -z "$RYU_PID" ] && ! kill -0 $RYU_PID 2>/dev/null; then
        if [ "$RYU_STOPPED_REPORTED" != "true" ]; then
            echo ""
            echo -e "${RED}❌ CRITICAL: Ryu SDN Controller stopped unexpectedly!${NC}"
            echo -e "${RED}   Other components depend on Ryu and may not function correctly${NC}"
            echo -e "${YELLOW}   Check logs/ryu.log for errors:${NC}"
            tail -20 logs/ryu.log 2>/dev/null || echo "   (log file not found)"
            RYU_STOPPED_REPORTED="true"
            echo -e "${YELLOW}   Attempting to restart Ryu...${NC}"
            # Try to restart Ryu
            export PYTHONPATH="${PYTHONPATH}:$(pwd)"
            if [ "$USING_OSKEN" = true ]; then
                if command -v osken-manager &> /dev/null; then
                    osken-manager --ofp-tcp-listen-port 6653 --verbose ryu_controller.sdn_policy_engine >> logs/ryu.log 2>&1 &
                else
                    $PYTHON_CMD -m os_ken.cmd.manager --ofp-tcp-listen-port 6653 --verbose ryu_controller.sdn_policy_engine >> logs/ryu.log 2>&1 &
                fi
                RYU_PID=$!
            elif command -v ryu-manager &> /dev/null; then
                ryu-manager --ofp-tcp-listen-port 6653 --verbose ryu_controller.sdn_policy_engine >> logs/ryu.log 2>&1 &
                RYU_PID=$!
            else
                $PYTHON_CMD -m ryu.cmd.manager --ofp-tcp-listen-port 6653 --verbose ryu_controller.sdn_policy_engine >> logs/ryu.log 2>&1 &
                RYU_PID=$!
            fi
            sleep 3
            if kill -0 $RYU_PID 2>/dev/null; then
                echo -e "${GREEN}✅ Ryu SDN Controller restarted (PID: $RYU_PID)${NC}"
                RYU_STOPPED_REPORTED="false"
            else
                echo -e "${RED}❌ Failed to restart Ryu SDN Controller${NC}"
            fi
        fi
    fi
    
    # Check Zero Trust if it was started (only report once)
    if [ ! -z "$ZERO_TRUST_PID" ] && ! kill -0 $ZERO_TRUST_PID 2>/dev/null; then
        if [ "$ZERO_TRUST_STOPPED_REPORTED" != "true" ]; then
            echo ""
            echo -e "${YELLOW}⚠️  Zero Trust Framework stopped unexpectedly${NC}"
            echo -e "${YELLOW}   Check logs/zero_trust.log for errors:${NC}"
            tail -10 logs/zero_trust.log 2>/dev/null || echo "   (log file not found)"
            ZERO_TRUST_STOPPED_REPORTED="true"
        fi
        ZERO_TRUST_PID=""
    fi
    
    # Check Mininet if it was started (only report once)
    if [ ! -z "$MININET_PID" ] && ! kill -0 $MININET_PID 2>/dev/null; then
        if [ "$MININET_STOPPED_REPORTED" != "true" ]; then
            echo ""
            echo -e "${YELLOW}⚠️  Virtual Devices (Mininet) stopped unexpectedly${NC}"
            echo -e "${YELLOW}   Check logs/mininet.log for errors:${NC}"
            tail -10 logs/mininet.log 2>/dev/null || echo "   (log file not found)"
            MININET_STOPPED_REPORTED="true"
        fi
        MININET_PID=""
    fi
    
    # Check honeypot container status (if Docker is available)
    if [ "$DOCKER_AVAILABLE" = true ] && [ "$DOCKER_RUNNING" = true ]; then
        if [ ! -z "$HONEYPOT_CONTAINER" ]; then
            if ! docker ps --format "{{.Names}}" 2>/dev/null | grep -q "$HONEYPOT_CONTAINER"; then
                # Container stopped, update status
                HONEYPOT_CONTAINER=""
            fi
        else
            # Check if honeypot was deployed
            NEW_CONTAINER=$(docker ps --format "{{.Names}}" 2>/dev/null | grep "iot_honeypot" | head -1)
            if [ ! -z "$NEW_CONTAINER" ]; then
                HONEYPOT_CONTAINER="$NEW_CONTAINER"
            fi
        fi
    fi
done
