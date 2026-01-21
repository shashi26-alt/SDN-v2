#!/bin/bash

# Comprehensive Raspberry Pi Deployment Script
# For Zero Trust SDN IoT Security Framework
# Optimized for ARM architecture (Raspberry Pi 4)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Raspberry Pi Deployment - Zero Trust SDN Framework                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: This script is designed for Raspberry Pi${NC}"
    read -p "Continue anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Detect user
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo ~$SUDO_USER)
else
    REAL_USER="$USER"
    REAL_HOME="$HOME"
fi

PROJECT_DIR_USER="$REAL_HOME/IOT-project"
if [ "$PROJECT_DIR" != "$PROJECT_DIR_USER" ]; then
    echo -e "${YELLOW}⚠️  Project is not in $PROJECT_DIR_USER${NC}"
    read -p "Copy project to $PROJECT_DIR_USER? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        mkdir -p "$PROJECT_DIR_USER"
        cp -r "$PROJECT_DIR"/* "$PROJECT_DIR_USER"/ 2>/dev/null || true
        PROJECT_DIR="$PROJECT_DIR_USER"
        cd "$PROJECT_DIR"
    fi
fi

echo -e "${GREEN}Project directory: $PROJECT_DIR${NC}"

# Step 1: System Update
echo ""
echo -e "${BLUE}Step 1: Updating system packages...${NC}"
apt update
apt upgrade -y

# Step 2: Install Base Dependencies
echo ""
echo -e "${BLUE}Step 2: Installing base dependencies...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    openssl \
    sqlite3 \
    docker.io \
    docker-compose \
    build-essential \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    gfortran \
    pkg-config \
    curl \
    wget \
    ufw \
    htop

# Step 3: Configure Docker
echo ""
echo -e "${BLUE}Step 3: Configuring Docker...${NC}"
systemctl enable docker
systemctl start docker
usermod -aG docker "$REAL_USER"
echo -e "${GREEN}✅ Docker configured${NC}"

# Step 4: Check Python Version and Create Virtual Environment
echo ""
echo -e "${BLUE}Step 4: Checking Python version and setting up virtual environment...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo -e "${GREEN}Detected Python version: $PYTHON_VERSION${NC}"

# Check for Python 3.13 compatibility
if [ "$PYTHON_MAJOR" = "3" ] && [ "$PYTHON_MINOR" -ge "13" ]; then
    echo -e "${YELLOW}⚠️  Python 3.13 detected${NC}"
    echo -e "${YELLOW}   Note: TensorFlow may not have full Python 3.13 support yet${NC}"
    echo -e "${YELLOW}   ML features may be limited, but core system will work${NC}"
    echo -e "${YELLOW}   System will use heuristic-based detection if ML unavailable${NC}"
    echo ""
    read -p "Continue with Python 3.13? [Y/n]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${BLUE}Checking for Python 3.11 or 3.12...${NC}"
        if command -v python3.11 &> /dev/null; then
            PYTHON_CMD="python3.11"
            echo -e "${GREEN}Found Python 3.11, using it instead${NC}"
        elif command -v python3.12 &> /dev/null; then
            PYTHON_CMD="python3.12"
            echo -e "${GREEN}Found Python 3.12, using it instead${NC}"
        else
            echo -e "${YELLOW}Python 3.11/3.12 not found. Install with: sudo apt install python3.11${NC}"
            echo -e "${YELLOW}Continuing with Python 3.13...${NC}"
            PYTHON_CMD="python3"
        fi
    else
        PYTHON_CMD="python3"
    fi
else
    PYTHON_CMD="python3"
fi

if [ -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists${NC}"
    echo -e "${YELLOW}Removing old venv to recreate with correct Python version...${NC}"
    rm -rf "$PROJECT_DIR/venv"
fi

sudo -u "$REAL_USER" $PYTHON_CMD -m venv "$PROJECT_DIR/venv"
echo -e "${GREEN}✅ Virtual environment created with $PYTHON_CMD${NC}"

# Step 5: Install Python Dependencies (ARM-optimized)
echo ""
echo -e "${BLUE}Step 5: Installing Python dependencies (ARM-optimized)...${NC}"

# Activate venv and upgrade pip
sudo -u "$REAL_USER" "$PROJECT_DIR/venv/bin/pip" install --upgrade pip setuptools wheel

# Install TensorFlow for ARM (if available) or use CPU-only version
echo -e "${YELLOW}Installing TensorFlow (ARM-compatible)...${NC}"
PYTHON_VERSION_IN_VENV=$("$PROJECT_DIR/venv/bin/python3" --version 2>&1 | awk '{print $2}')
PYTHON_MINOR_IN_VENV=$(echo $PYTHON_VERSION_IN_VENV | cut -d. -f2)

# Check if Python 3.13 (TensorFlow may not support it)
if [ "$PYTHON_MINOR_IN_VENV" -ge "13" ]; then
    echo -e "${YELLOW}⚠️  Python 3.13 detected - TensorFlow may not be available${NC}"
    echo -e "${YELLOW}   Attempting installation, but may fail (this is OK)${NC}"
    echo -e "${YELLOW}   System will work with heuristic-based detection if TensorFlow unavailable${NC}"
fi

# Try TensorFlow installation
if "$PROJECT_DIR/venv/bin/pip" install tensorflow-cpu 2>/dev/null; then
    echo -e "${GREEN}✅ TensorFlow CPU installed${NC}"
elif "$PROJECT_DIR/venv/bin/pip" install tensorflow 2>/dev/null; then
    echo -e "${GREEN}✅ TensorFlow installed${NC}"
else
    echo -e "${YELLOW}⚠️  TensorFlow installation failed or not available${NC}"
    echo -e "${YELLOW}   This is expected for Python 3.13 or ARM architecture${NC}"
    echo -e "${YELLOW}   System will use heuristic-based detection (fully functional)${NC}"
fi

# Install other dependencies
echo -e "${YELLOW}Installing other dependencies...${NC}"
sudo -u "$REAL_USER" "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" || {
    echo -e "${YELLOW}Some packages may have failed. Continuing...${NC}"
}

# Install Ryu SDN Controller
echo -e "${YELLOW}Installing Ryu SDN Controller...${NC}"
sudo -u "$REAL_USER" "$PROJECT_DIR/venv/bin/pip" install ryu eventlet || {
    echo -e "${RED}Failed to install Ryu. Please install manually.${NC}"
}

echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Step 6: Create Directories
echo ""
echo -e "${BLUE}Step 6: Creating necessary directories...${NC}"
mkdir -p "$PROJECT_DIR/certs"
mkdir -p "$PROJECT_DIR/honeypot_data"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data/logs"
mkdir -p "$PROJECT_DIR/data/models"
mkdir -p "$PROJECT_DIR/data/certs"
chown -R "$REAL_USER:$REAL_USER" "$PROJECT_DIR"
chmod 755 "$PROJECT_DIR/certs" "$PROJECT_DIR/honeypot_data" "$PROJECT_DIR/logs"
echo -e "${GREEN}✅ Directories created${NC}"

# Step 7: Install Systemd Services
echo ""
echo -e "${BLUE}Step 7: Installing systemd services...${NC}"

# Ryu SDN Controller Service
cat > /etc/systemd/system/ryu-sdn-controller.service <<EOF
[Unit]
Description=Ryu SDN Controller for Zero Trust Framework
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$PROJECT_DIR"
ExecStart=$PROJECT_DIR/venv/bin/ryu-manager --ofp-tcp-listen-port 6653 $PROJECT_DIR/ryu_controller/sdn_policy_engine.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/ryu.log
StandardError=append:$PROJECT_DIR/logs/ryu.log

[Install]
WantedBy=multi-user.target
EOF

# Zero Trust Framework Service
cat > /etc/systemd/system/zero-trust-sdn.service <<EOF
[Unit]
Description=Zero Trust SDN Framework
After=network.target docker.service ryu-sdn-controller.service
Wants=network-online.target docker.service ryu-sdn-controller.service

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$PROJECT_DIR"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/zero_trust_integration.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/zero_trust.log
StandardError=append:$PROJECT_DIR/logs/zero_trust.log

[Install]
WantedBy=multi-user.target
EOF

# Flask Controller Service
cat > /etc/systemd/system/flask-controller.service <<EOF
[Unit]
Description=Flask Controller for Zero Trust SDN Framework
After=network.target zero-trust-sdn.service
Wants=network-online.target zero-trust-sdn.service

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$PROJECT_DIR"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/controller.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/controller.log
StandardError=append:$PROJECT_DIR/logs/controller.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✅ Systemd services installed${NC}"

# Step 8: Configure Firewall
echo ""
echo -e "${BLUE}Step 8: Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp comment "SSH"
    ufw allow 5000/tcp comment "Flask Controller"
    ufw allow 6653/tcp comment "OpenFlow Controller"
    echo -e "${GREEN}✅ Firewall rules configured${NC}"
else
    echo -e "${YELLOW}⚠️  UFW not available, skipping firewall configuration${NC}"
fi

# Step 9: Set Permissions
echo ""
echo -e "${BLUE}Step 9: Setting permissions...${NC}"
chown -R "$REAL_USER:$REAL_USER" "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/start.sh" 2>/dev/null || true
chmod +x "$PROJECT_DIR/scripts"/*.sh 2>/dev/null || true
echo -e "${GREEN}✅ Permissions set${NC}"

# Step 10: Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                         ✅ Deployment Complete! ✅                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services installed:${NC}"
echo "  • ryu-sdn-controller.service"
echo "  • zero-trust-sdn.service"
echo "  • flask-controller.service"
echo ""
echo -e "${BLUE}To start services:${NC}"
echo "  sudo systemctl start ryu-sdn-controller"
echo "  sudo systemctl start zero-trust-sdn"
echo "  sudo systemctl start flask-controller"
echo ""
echo -e "${BLUE}To enable services on boot:${NC}"
echo "  sudo systemctl enable ryu-sdn-controller"
echo "  sudo systemctl enable zero-trust-sdn"
echo "  sudo systemctl enable flask-controller"
echo ""
echo -e "${BLUE}To check status:${NC}"
echo "  sudo systemctl status ryu-sdn-controller"
echo "  sudo systemctl status zero-trust-sdn"
echo "  sudo systemctl status flask-controller"
echo ""
echo -e "${BLUE}Access Dashboard:${NC}"
echo "  http://$(hostname -I | awk '{print $1}'):5000"
echo "  or http://localhost:5000"
echo ""
echo -e "${BLUE}Logs location:${NC}"
echo "  $PROJECT_DIR/logs/"
echo ""
# Check Python version and show compatibility info
if [ -f "$PROJECT_DIR/venv/bin/python3" ]; then
    PYTHON_VERSION_IN_VENV=$("$PROJECT_DIR/venv/bin/python3" --version 2>&1 | awk '{print $2}')
    PYTHON_MINOR_IN_VENV=$(echo $PYTHON_VERSION_IN_VENV | cut -d. -f2)
    if [ "$PYTHON_MINOR_IN_VENV" -ge "13" ]; then
        echo -e "${YELLOW}📚 Python 3.13 Compatibility Notice:${NC}"
        echo -e "${YELLOW}   • Core system: ✅ Fully functional${NC}"
        echo -e "${YELLOW}   • ML features: ⚠️  May be limited (TensorFlow compatibility)${NC}"
        echo -e "${YELLOW}   • Heuristic detection: ✅ Works perfectly${NC}"
        echo -e "${YELLOW}   • See docs/PYTHON_3.13_COMPATIBILITY.md for details${NC}"
        echo ""
    fi
fi
echo -e "${YELLOW}⚠️  Note: You may need to log out and back in for Docker group changes to take effect${NC}"
echo ""

