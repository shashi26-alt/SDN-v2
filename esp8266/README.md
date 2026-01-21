# ESP8266 Gateway + Node Firmware

This firmware makes an ESP8266 board act as both a **Gateway** and a **Node** simultaneously. This allows you to test the entire system with a single ESP8266 device.

## Features

- **Gateway Mode**: Creates WiFi Access Point for other ESP8266/ESP32 nodes to connect
- **Node Mode**: Sends its own sensor data to the controller
- **Data Forwarding**: Forwards data from connected nodes to the controller
- **Dual WiFi Mode**: AP+STA mode allows both roles simultaneously

## Hardware Requirements

- ESP8266 Development Board (NodeMCU, Wemos D1 Mini, etc.)
- USB cable for programming and power
- Optional: Sensors (temperature, humidity, etc.)

## Software Requirements

### Arduino IDE Setup

1. **Install ESP8266 Board Support**:
   - File → Preferences → Additional Board Manager URLs
   - Add: `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - Tools → Board → Boards Manager → Search "ESP8266" → Install

2. **Install Required Libraries**:
   - **ArduinoJson** (version 6.x recommended)
     - Sketch → Include Library → Manage Libraries → Search "ArduinoJson" → Install
   - **ESP8266WiFi** (built-in)
   - **ESP8266HTTPClient** (built-in)

3. **Select Board**:
   - Tools → Board → NodeMCU 1.0 (ESP-12E Module) or your ESP8266 board
   - Tools → Port → Select your COM port

## Configuration

Edit `gateway_node.ino` and update these settings:

```cpp
// Access Point settings (for other nodes)
const char *ap_ssid = "ESP8266-Gateway";
const char *ap_password = "12345678";

// WiFi settings (to connect to your network and reach controller)
const char *sta_ssid = "YourWiFi";           // Your WiFi SSID
const char *sta_password = "YourWiFiPassword"; // Your WiFi password

// Controller settings
const char *controller_ip = "192.168.1.100";  // Your controller IP address

// Device identity
String device_id = "ESP8266_GatewayNode";     // Change to unique ID
```

### Network Configuration

**Important**: Make sure your controller and the ESP8266 are on the same network (connected to the same WiFi router).

1. **Controller**: Running on a computer/server (e.g., `192.168.1.100`)
2. **ESP8266 STA**: Connects to your WiFi network (gets IP from router, e.g., `192.168.1.150`)
3. **ESP8266 AP**: Creates its own network `ESP8266-Gateway` (IP: `192.168.4.1`)

## Upload Instructions

1. Connect ESP8266 to computer via USB
2. Select correct board and port in Arduino IDE
3. Update configuration settings in the code
4. Click **Upload** button
5. Open Serial Monitor (115200 baud) to see status

## How It Works

### Gateway Functionality

1. Creates WiFi Access Point `ESP8266-Gateway`
2. Listens on port 80 for HTTP requests from nodes
3. Forwards received JSON data to the controller at `/data` endpoint
4. Responds to nodes confirming receipt

### Node Functionality

1. Connects to your WiFi network (STA mode)
2. Requests authentication token from controller at `/get_token`
3. Sends sensor data every 5 seconds to controller at `/data` endpoint
4. Handles token expiration and re-authentication

### Simultaneous Operation

The ESP8266 runs both functions concurrently:
- Continuously checks for incoming node connections (gateway)
- Periodically sends its own data (node)
- Both use the same WiFi connection to reach the controller

## Testing

### 1. Verify Gateway AP

- Look for WiFi network `ESP8266-Gateway` on your phone/computer
- Should be visible and connectable (password: `12345678`)

### 2. Check Serial Monitor

You should see:
```
=== ESP8266 Gateway + Node Setup ===
Starting Access Point: ESP8266-Gateway
AP IP address: 192.168.4.1
Connected to WiFi!
STA IP address: 192.168.1.150
Gateway server started on port 80
[Node] Requesting token from controller...
[Node] ✅ Token received: ...
=== Setup Complete ===
```

### 3. Verify Controller Connection

- Check controller logs - you should see token requests
- Dashboard should show device `ESP8266_GatewayNode`
- Data should appear every 5 seconds

### 4. Test with Additional Nodes

You can connect other ESP8266/ESP32 nodes to the gateway:
- Configure them to connect to `ESP8266-Gateway` AP
- Set controller IP to `192.168.4.1` (gateway's AP IP)
- They will connect and forward data through the gateway

## Troubleshooting

### Gateway AP Not Visible

- **Problem**: Can't see `ESP8266-Gateway` network
- **Solution**: 
  - Check Serial Monitor for AP startup message
  - ESP8266 may have limited AP range
  - Try moving closer to the device

### Cannot Connect to WiFi

- **Problem**: STA mode fails to connect
- **Solution**:
  - Verify WiFi SSID and password are correct
  - Check WiFi router is 2.4GHz (ESP8266 doesn't support 5GHz)
  - Ensure WiFi signal is strong enough
  - Check router doesn't block new devices

### Token Request Fails (403)

- **Problem**: Controller returns 403 Forbidden
- **Solution**:
  - Verify controller IP address is correct
  - Check controller is running and accessible
  - Ensure ESP8266 and controller are on same network
  - Check controller logs for authorization issues
  - The device should auto-authorize with valid MAC address

### Controller Not Receiving Data

- **Problem**: Data not appearing in controller dashboard
- **Solution**:
  - Verify controller IP address
  - Check network connectivity (ping controller from computer)
  - Verify controller is listening on port 5000
  - Check firewall settings
  - Look at Serial Monitor for error messages

### Memory Issues

- **Problem**: ESP8266 crashes or reboots
- **Solution**:
  - ESP8266 has limited RAM (~80KB)
  - Reduce JSON document sizes if using large payloads
  - Minimize string operations
  - Consider using String instead of String() for concatenation in some cases

## Adding Real Sensors

Replace the simulated sensor data in `sendOwnData()`:

```cpp
// Replace this:
float temperature = random(200, 300) / 10.0;
int humidity = random(40, 70);

// With real sensor code, for example DHT22:
#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

void setup() {
    // ... existing setup ...
    dht.begin();
}

void sendOwnData() {
    // ... existing code ...
    
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    
    // ... rest of code ...
}
```

## Network Topology

```
[Controller] (192.168.1.100)
      |
      | WiFi Network
      |
[ESP8266 Gateway+Node] (STA: 192.168.1.150, AP: 192.168.4.1)
      |
      | AP Network: ESP8266-Gateway
      |
   [Other Nodes] (ESP8266/ESP32)
```

## Notes

- ESP8266 has limited processing power - may have slight delays when handling multiple nodes
- AP and STA modes can run simultaneously but share WiFi resources
- Maximum connections to AP: Typically 4-8 devices depending on ESP8266 module
- For production, consider using separate gateway and node devices for better performance

