# Python 3.13 Compatibility Guide

## ⚠️ Important Notice

Python 3.13.5 is very new (released October 2024) and some packages may not have full support yet. This guide helps you work with Python 3.13 or downgrade if needed.

## Compatibility Status

### ✅ Fully Compatible Packages
- Flask >= 3.0.0
- requests >= 2.31.0
- matplotlib >= 3.8.1
- pandas >= 2.1.2
- scikit-learn >= 1.3.2
- cryptography >= 41.0.0
- pyOpenSSL >= 23.0.0
- docker >= 6.0.0
- pytest >= 7.0.0

### ⚠️ Potentially Problematic Packages

#### TensorFlow
- **Issue**: TensorFlow 2.14+ may not have official Python 3.13 wheels yet
- **Impact**: ML-based DDoS detection features may not work
- **Workaround**: System will fall back to heuristic-based detection
- **Solution**: Use Python 3.11 or 3.12 if ML features are critical

#### Ryu SDN Controller
- **Status**: Should work, but may need latest version
- **Check**: `pip install --upgrade ryu eventlet`

#### NumPy
- **Status**: Should work with Python 3.13
- **Note**: May need to build from source if wheels unavailable

## Recommended Approach

### Option 1: Use Python 3.13 (Recommended for Testing)

The project will work with Python 3.13, but ML features may be limited:

```bash
# Check Python version
python3 --version

# If Python 3.13, proceed with deployment
# ML features will use fallback heuristics if TensorFlow fails
```

**What Works:**
- ✅ All core features (Flask controller, dashboard)
- ✅ SDN controller (Ryu)
- ✅ Zero Trust framework
- ✅ Honeypot management
- ✅ Heuristic-based anomaly detection
- ⚠️ ML-based detection (may not work)

### Option 2: Install Python 3.11 or 3.12 (Recommended for Production)

If you need full ML support, install Python 3.11 or 3.12:

```bash
# Install Python 3.11 (recommended)
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Create virtual environment with Python 3.11
cd ~/IOT-project
python3.11 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Update systemd services** to use Python 3.11:
```bash
# Edit service files
sudo nano /etc/systemd/system/flask-controller.service
# Change: ExecStart=/home/pi/IOT-project/venv/bin/python3
# To: ExecStart=/home/pi/IOT-project/venv/bin/python3.11

# Repeat for other services
sudo systemctl daemon-reload
```

## Deployment Script Updates

The deployment script (`scripts/deploy_raspberry_pi.sh`) has been updated to:
1. Detect Python 3.13
2. Warn about potential TensorFlow issues
3. Attempt TensorFlow installation (will gracefully fail if incompatible)
4. Continue with deployment (system works without ML)

## Testing Compatibility

### Test TensorFlow Installation

```bash
cd ~/IOT-project
source venv/bin/activate

# Try importing TensorFlow
python3 -c "import tensorflow as tf; print('TensorFlow version:', tf.__version__)"
```

**If it fails:**
- System will use heuristic detection (still functional)
- ML endpoints will return "ML engine not available"
- All other features work normally

### Test All Dependencies

```bash
# Run verification script
bash scripts/verify_deployment.sh

# Or manually test imports
python3 -c "import flask; print('Flask OK')"
python3 -c "import ryu; print('Ryu OK')"
python3 -c "import docker; print('Docker OK')"
python3 -c "import cryptography; print('Cryptography OK')"
```

## Known Issues and Solutions

### Issue: TensorFlow Installation Fails

**Error**: `ERROR: Could not find a version that satisfies the requirement tensorflow`

**Solution**:
```bash
# Option 1: Install TensorFlow CPU (may work)
pip install tensorflow-cpu

# Option 2: Skip TensorFlow (system works without it)
# Just continue deployment - ML features will be disabled

# Option 3: Use Python 3.11 (best for ML support)
python3.11 -m venv venv
source venv/bin/activate
pip install tensorflow
```

### Issue: NumPy Build Fails

**Error**: `Failed building wheel for numpy`

**Solution**:
```bash
# Install build dependencies
sudo apt install -y python3-dev gfortran libopenblas-dev liblapack-dev

# Try installing again
pip install --upgrade pip setuptools wheel
pip install numpy
```

### Issue: Ryu Installation Issues

**Error**: `ImportError` or version conflicts

**Solution**:
```bash
# Upgrade to latest version
pip install --upgrade ryu eventlet

# If still failing, check Python version compatibility
python3 --version
ryu-manager --version
```

## Compatibility Matrix

| Component | Python 3.11 | Python 3.12 | Python 3.13 |
|-----------|-------------|-------------|-------------|
| Flask Controller | ✅ | ✅ | ✅ |
| Ryu SDN Controller | ✅ | ✅ | ⚠️ |
| Zero Trust Framework | ✅ | ✅ | ✅ |
| TensorFlow/ML | ✅ | ✅ | ❌ |
| Docker Integration | ✅ | ✅ | ✅ |
| Honeypot Management | ✅ | ✅ | ✅ |
| Heuristic Detection | ✅ | ✅ | ✅ |

## Recommendations

### For Development/Testing
- **Use Python 3.13**: System works, ML features disabled
- **Pros**: Latest Python features, good for testing
- **Cons**: No ML-based detection

### For Production
- **Use Python 3.11**: Full feature support
- **Pros**: All features work, stable
- **Cons**: Slightly older Python version

### For Best Compatibility
- **Use Python 3.12**: Good balance
- **Pros**: Modern Python, good package support
- **Cons**: May need some package updates

## Quick Fix: Install Python 3.11 Alongside 3.13

```bash
# Install Python 3.11
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Create new virtual environment
cd ~/IOT-project
rm -rf venv  # Remove old venv if exists
python3.11 -m venv venv

# Install dependencies
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Update systemd services to use Python 3.11
sudo sed -i 's|venv/bin/python3|venv/bin/python3.11|g' /etc/systemd/system/*.service
sudo systemctl daemon-reload
```

## Verification

After deployment, verify everything works:

```bash
# Check Python version in venv
~/IOT-project/venv/bin/python3 --version

# Test TensorFlow (if installed)
~/IOT-project/venv/bin/python3 -c "import tensorflow; print('OK')" || echo "TensorFlow not available (OK for Python 3.13)"

# Run full verification
bash scripts/verify_deployment.sh
```

## Summary

**Python 3.13.5 Support:**
- ✅ **Core system works**: Flask, Ryu, Zero Trust, Honeypots
- ⚠️ **ML features limited**: TensorFlow may not install
- ✅ **Heuristic detection works**: System fully functional without ML
- 💡 **Recommendation**: Use Python 3.11 for production, Python 3.13 for testing

The project is designed to gracefully handle missing ML dependencies, so Python 3.13 will work for most use cases!


