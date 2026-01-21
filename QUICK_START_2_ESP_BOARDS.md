# 🚀 Quick Start: 2 ESP Boards Deployment

## ⚡ 5-Minute Quick Reference

### Step 1: Controller Setup (5 min)

```bash
# 1. Install dependencies
cd IOT-project-main
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Find your IP address
# Windows: ipconfig
# Linux/Mac: ifconfig
# Write down your IP: _______________

# 3. Start controller
python controller.py
# Keep terminal open!
```

✅ **Test**: Open http://localhost:5000 in browser

---

### Step 2: Gateway ESP32 (10 min)

1. **Open**: `esp32/gateway.ino` in Arduino IDE
2. **Change**:
   ```cpp
   const char *sta_ssid = "YOUR_WIFI_NAME";
   const char *sta_password = "YOUR_WIFI_PASSWORD";
   const char *controller_ip = "YOUR_COMPUTER_IP";  // From Step 1
   ```
3. **Upload** to ESP32 #1
4. **Check Serial Monitor**: Should see "Gateway AP Started"

✅ **Test**: Look for "ESP32-AP" WiFi network

---

### Step 3: Node ESP32 (5 min)

1. **Open**: `esp32/node.ino` in Arduino IDE
2. **Change**:
   ```cpp
   String device_id = "ESP32_Node1";  // Unique for each node
   ```
3. **Upload** to ESP32 #2
4. **Check Serial Monitor**: Should see "Connected to Gateway"

✅ **Test**: Should see "Response: 200" every 5 seconds

---

### Step 4: Approve Device (2 min)

1. **Open Dashboard**: http://localhost:5000
2. **Click**: "Device Approval" tab
3. **Click**: "Approve" button for your device
4. **Wait**: 5 minutes for auto-finalization

✅ **Test**: Device appears in topology, data flowing

---

## 🔧 Configuration Checklist

### Gateway Settings
- [ ] AP SSID: `ESP32-AP`
- [ ] AP Password: `12345678`
- [ ] WiFi SSID: `_________________`
- [ ] WiFi Password: `_________________`
- [ ] Controller IP: `_________________`

### Node Settings
- [ ] Device ID: `ESP32_Node1` (unique!)
- [ ] Gateway AP: `ESP32-AP`
- [ ] Gateway Password: `12345678`

### Controller
- [ ] Running on port 5000
- [ ] Dashboard accessible
- [ ] IP address: `_________________`

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Gateway no AP | Check Serial Monitor, reset ESP32 |
| Node not connecting | Verify AP name/password match |
| No token | Check controller is running |
| No data | Check device approved in dashboard |
| Dashboard not loading | Check controller terminal for errors |

---

## 📞 Need Help?

1. Check Serial Monitor (ESP32)
2. Check Controller terminal
3. Check Dashboard logs
4. See full guide: `docs/ESP32_2_BOARDS_DEPLOYMENT.md`

---

**Status**: ⬜ Not Started | ⬜ In Progress | ⬜ Complete

