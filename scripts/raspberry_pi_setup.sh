#!/bin/bash

# Raspberry Pi Setup Script for Zero Trust SDN Framework
# This script sets up the SDN controller and all required services on Raspberry Pi

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Raspberry Pi SDN Controller Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}Warning: This script is designed for Raspberry Pi${NC}"
    read -p "Continue anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Get project directory
PROJECT_DIR="${1:-/home/pi/IOT-project}"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Error: Project directory not found: $PROJECT_DIR${NC}"
    echo "Usage: sudo $0 [project_directory]"
    exit 1
fi

echo -e "${GREEN}Project directory: $PROJECT_DIR${NC}"
cd "$PROJECT_DIR"

# Step 1: Update system
echo ""
echo -e "${BLUE}Step 1: Updating system packages...${NC}"
apt update
apt upgrade -y

# Step 2: Install required packages
echo ""
echo -e "${BLUE}Step 2: Installing required packages...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    openssl \
    sqlite3 \
    docker.io \
    systemd \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev

# Step 3: Start and enable Docker
echo ""
echo -e "${BLUE}Step 3: Configuring Docker...${NC}"
systemctl enable docker
systemctl start docker

# Add pi user to docker group (if exists)
if id "pi" &>/dev/null; then
    usermod -aG docker pi
    echo -e "${GREEN}Added pi user to docker group${NC}"
fi

# Step 4: Install Ryu SDN Controller
echo ""
echo -e "${BLUE}Step 4: Installing Ryu SDN Controller...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip
    pip install ryu eventlet
    echo -e "${GREEN}Ryu installed in virtual environment${NC}"
else
    pip3 install --user ryu eventlet
    echo -e "${GREEN}Ryu installed for current user${NC}"
fi

# Step 5: Create necessary directories
echo ""
echo -e "${BLUE}Step 5: Creating directories...${NC}"
mkdir -p "$PROJECT_DIR/certs"
mkdir -p "$PROJECT_DIR/honeypot_data"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data/logs"
mkdir -p "$PROJECT_DIR/data/models"
chmod 755 "$PROJECT_DIR/certs" "$PROJECT_DIR/honeypot_data" "$PROJECT_DIR/logs"

# Step 6: Install systemd service files
echo ""
echo -e "${BLUE}Step 6: Installing systemd services...${NC}"

# Ryu SDN Controller service
cat > /etc/systemd/system/ryu-sdn-controller.service <<EOF
[Unit]
Description=Ryu SDN Controller for Zero Trust Framework
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/ryu-manager --ofp-tcp-listen-port 6653 $PROJECT_DIR/ryu_controller/sdn_policy_engine.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/ryu.log
StandardError=append:$PROJECT_DIR/logs/ryu.log

[Install]
WantedBy=multi-user.target
EOF

# Zero Trust Framework service
cat > /etc/systemd/system/zero-trust-sdn.service <<EOF
[Unit]
Description=Zero Trust SDN Framework
After=network.target docker.service ryu-sdn-controller.service
Wants=network-online.target docker.service ryu-sdn-controller.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/zero_trust_integration.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/zero_trust.log
StandardError=append:$PROJECT_DIR/logs/zero_trust.log

[Install]
WantedBy=multi-user.target
EOF

# Flask Controller service (optional, if not integrated into zero_trust_integration)
if [ -f "$PROJECT_DIR/controller.py" ]; then
    cat > /etc/systemd/system/flask-controller.service <<EOF
[Unit]
Description=Flask Controller for Zero Trust SDN Framework
After=network.target zero-trust-sdn.service
Wants=network-online.target zero-trust-sdn.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/controller.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/controller.log
StandardError=append:$PROJECT_DIR/logs/controller.log

[Install]
WantedBy=multi-user.target
EOF
fi

# Reload systemd
systemctl daemon-reload

# Step 7: Configure firewall
echo ""
echo -e "${BLUE}Step 7: Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 5000/tcp comment "Flask Controller"
    ufw allow 6653/tcp comment "OpenFlow Controller"
    ufw allow 22/tcp comment "SSH"
    echo -e "${GREEN}Firewall rules configured${NC}"
else
    echo -e "${YELLOW}UFW not installed, skipping firewall configuration${NC}"
fi

# Step 8: Set permissions
echo ""
echo -e "${BLUE}Step 8: Setting permissions...${NC}"
if id "pi" &>/dev/null; then
    chown -R pi:pi "$PROJECT_DIR"
    echo -e "${GREEN}Permissions set for pi user${NC}"
fi

# Step 9: Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services installed:"
echo "  - ryu-sdn-controller.service"
echo "  - zero-trust-sdn.service"
if [ -f "/etc/systemd/system/flask-controller.service" ]; then
    echo "  - flask-controller.service"
fi
echo ""
echo "To start services:"
echo "  sudo systemctl start ryu-sdn-controller"
echo "  sudo systemctl start zero-trust-sdn"
if [ -f "/etc/systemd/system/flask-controller.service" ]; then
    echo "  sudo systemctl start flask-controller"
fi
echo ""
echo "To enable services on boot:"
echo "  sudo systemctl enable ryu-sdn-controller"
echo "  sudo systemctl enable zero-trust-sdn"
if [ -f "/etc/systemd/system/flask-controller.service" ]; then
    echo "  sudo systemctl enable flask-controller"
fi
echo ""
echo "To check status:"
echo "  sudo systemctl status ryu-sdn-controller"
echo "  sudo systemctl status zero-trust-sdn"
echo ""
echo "Logs are located in: $PROJECT_DIR/logs/"
echo ""

