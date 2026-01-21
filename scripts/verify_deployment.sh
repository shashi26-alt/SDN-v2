#!/bin/bash

# Deployment Verification Script
# Checks if all components are properly installed and running

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="${1:-$HOME/IOT-project}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Deployment Verification - Zero Trust SDN Framework            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to check
check() {
    local name="$1"
    local command="$2"
    local required="${3:-false}"
    
    echo -n "Checking $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ REQUIRED${NC}"
            ERRORS=$((ERRORS + 1))
            return 1
        else
            echo -e "${YELLOW}⚠️  Optional${NC}"
            WARNINGS=$((WARNINGS + 1))
            return 1
        fi
    fi
}

# Check project directory
echo -e "${BLUE}📁 Project Structure${NC}"
check "Project directory exists" "[ -d '$PROJECT_DIR' ]" true
check "controller.py exists" "[ -f '$PROJECT_DIR/controller.py' ]" true
check "zero_trust_integration.py exists" "[ -f '$PROJECT_DIR/zero_trust_integration.py' ]" true
check "requirements.txt exists" "[ -f '$PROJECT_DIR/requirements.txt' ]" true

# Check directories
check "certs directory" "[ -d '$PROJECT_DIR/certs' ]" false
check "logs directory" "[ -d '$PROJECT_DIR/logs' ]" false
check "honeypot_data directory" "[ -d '$PROJECT_DIR/honeypot_data' ]" false

# Check Python environment
echo ""
echo -e "${BLUE}🐍 Python Environment${NC}"
check "Python 3 installed" "python3 --version" true
check "Virtual environment exists" "[ -d '$PROJECT_DIR/venv' ]" true
check "pip in venv" "[ -f '$PROJECT_DIR/venv/bin/pip' ]" true

# Check Python packages
if [ -d "$PROJECT_DIR/venv" ]; then
    echo ""
    echo -e "${BLUE}📦 Python Packages${NC}"
    check "Flask installed" "$PROJECT_DIR/venv/bin/python3 -c 'import flask'" true
    check "Ryu installed" "$PROJECT_DIR/venv/bin/python3 -c 'import ryu'" true
    check "TensorFlow installed" "$PROJECT_DIR/venv/bin/python3 -c 'import tensorflow'" false
    check "Docker Python module" "$PROJECT_DIR/venv/bin/python3 -c 'import docker'" false
    check "Cryptography installed" "$PROJECT_DIR/venv/bin/python3 -c 'import cryptography'" false
fi

# Check system services
echo ""
echo -e "${BLUE}⚙️  System Services${NC}"
check "Docker installed" "command -v docker" false
check "Docker running" "systemctl is-active --quiet docker" false
check "Ryu service file" "[ -f /etc/systemd/system/ryu-sdn-controller.service ]" false
check "Zero Trust service file" "[ -f /etc/systemd/system/zero-trust-sdn.service ]" false
check "Flask service file" "[ -f /etc/systemd/system/flask-controller.service ]" false

# Check running services
echo ""
echo -e "${BLUE}🔄 Running Services${NC}"
if systemctl is-active --quiet ryu-sdn-controller 2>/dev/null; then
    echo -e "Ryu SDN Controller... ${GREEN}✅ Running${NC}"
else
    echo -e "Ryu SDN Controller... ${YELLOW}⚠️  Not running${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

if systemctl is-active --quiet zero-trust-sdn 2>/dev/null; then
    echo -e "Zero Trust Framework... ${GREEN}✅ Running${NC}"
else
    echo -e "Zero Trust Framework... ${YELLOW}⚠️  Not running${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

if systemctl is-active --quiet flask-controller 2>/dev/null; then
    echo -e "Flask Controller... ${GREEN}✅ Running${NC}"
else
    echo -e "Flask Controller... ${YELLOW}⚠️  Not running${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check ports
echo ""
echo -e "${BLUE}🌐 Network Ports${NC}"
if command -v netstat &> /dev/null; then
    if netstat -tuln 2>/dev/null | grep -q ":5000 "; then
        echo -e "Port 5000 (Flask)... ${GREEN}✅ Listening${NC}"
    else
        echo -e "Port 5000 (Flask)... ${YELLOW}⚠️  Not listening${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    if netstat -tuln 2>/dev/null | grep -q ":6653 "; then
        echo -e "Port 6653 (OpenFlow)... ${GREEN}✅ Listening${NC}"
    else
        echo -e "Port 6653 (OpenFlow)... ${YELLOW}⚠️  Not listening${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  netstat not available, skipping port checks${NC}"
fi

# Check dashboard accessibility
echo ""
echo -e "${BLUE}🌐 Dashboard Access${NC}"
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://localhost:5000 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "Dashboard (http://localhost:5000)... ${GREEN}✅ Accessible${NC}"
    else
        echo -e "Dashboard (http://localhost:5000)... ${YELLOW}⚠️  Not accessible (HTTP $HTTP_CODE)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  curl not available, skipping dashboard check${NC}"
fi

# Check Docker containers
echo ""
echo -e "${BLUE}🐳 Docker Containers${NC}"
if command -v docker &> /dev/null && systemctl is-active --quiet docker 2>/dev/null; then
    HONEYPOT=$(docker ps --format "{{.Names}}" 2>/dev/null | grep -i honeypot || echo "")
    if [ -n "$HONEYPOT" ]; then
        echo -e "Honeypot container... ${GREEN}✅ Running ($HONEYPOT)${NC}"
    else
        echo -e "Honeypot container... ${YELLOW}⚠️  Not running (will deploy on demand)${NC}"
    fi
else
    echo -e "Docker... ${YELLOW}⚠️  Not available${NC}"
fi

# Check logs
echo ""
echo -e "${BLUE}📝 Log Files${NC}"
if [ -f "$PROJECT_DIR/logs/controller.log" ]; then
    echo -e "Controller log... ${GREEN}✅ Exists${NC}"
    if [ -s "$PROJECT_DIR/logs/controller.log" ]; then
        ERRORS_IN_LOG=$(grep -i error "$PROJECT_DIR/logs/controller.log" 2>/dev/null | wc -l || echo "0")
        if [ "$ERRORS_IN_LOG" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠️  $ERRORS_IN_LOG error(s) found in log${NC}"
        fi
    fi
else
    echo -e "Controller log... ${YELLOW}⚠️  Not found${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}║                    ✅ All Checks Passed! ✅                              ║${NC}"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}║              ⚠️  Deployment Complete with Warnings ⚠️                    ║${NC}"
else
    echo -e "${RED}║                    ❌ Deployment Issues Found ❌                          ║${NC}"
fi
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Please fix errors before proceeding${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some optional components are missing, but core system should work${NC}"
    exit 0
else
    echo -e "${GREEN}✅ Deployment verified successfully!${NC}"
    exit 0
fi

