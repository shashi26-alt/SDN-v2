#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char *ap_ssid = "ESP8266-Gateway";  // Access Point name for other nodes
const char *ap_password = "12345678";     // AP password (min 8 chars)

// STA mode - Connect to your WiFi to reach controller
const char *sta_ssid = "cyber wing 2";        // Your WiFi network SSID
const char *sta_password = "cyber@123"; // Your WiFi password

// Controller IP (where controller.py runs)
const char *controller_ip = "172.16.0.135"; // Change to your controller IP

// This device's identity (as a node)
String device_id = "ESP8266_GatewayNode"; // Change to unique ID
String device_token = "";

// Gateway server for forwarding node data
WiFiServer gatewayServer(80);

// Timing
unsigned long lastNodeDataSent = 0;
const unsigned long NODE_DATA_INTERVAL = 5000; // Send own data every 5 seconds
unsigned long lastWiFiCheck = 0;
const unsigned long WIFI_CHECK_INTERVAL = 10000; // Check WiFi every 10 seconds
unsigned long lastTokenRefresh = 0;
const unsigned long TOKEN_REFRESH_INTERVAL = 240000; // Refresh token every 4 minutes (before 5min expiry)
unsigned long lastConnectionAttempt = 0;
const unsigned long RECONNECT_DELAY = 5000; // Wait 5 seconds between reconnection attempts

bool staConnected = false;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n=== ESP8266 Gateway + Node Setup ===");
    
    // Configure WiFi for stability
    WiFi.persistent(true); // Save WiFi config to flash
    WiFi.setAutoReconnect(true); // Enable auto-reconnect
    WiFi.setAutoConnect(true); // Auto-connect on startup
    
    // Set WiFi to AP+STA mode
    WiFi.mode(WIFI_AP_STA);
    
    // Start Access Point for other nodes (always active)
    Serial.print("Starting Access Point: ");
    Serial.println(ap_ssid);
    WiFi.softAP(ap_ssid, ap_password);
    IPAddress apIP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(apIP);
    Serial.print("AP MAC: ");
    Serial.println(WiFi.softAPmacAddress());
    
    // Connect to STA WiFi (to reach controller)
    connectToWiFi();
    
    // Start gateway server for receiving node data
    gatewayServer.begin();
    Serial.println("Gateway server started on port 80");
    
    // Request token for this device (as a node) if connected
    if (WiFi.status() == WL_CONNECTED) {
        requestToken();
    }
    
    Serial.println("\n=== Setup Complete ===");
    Serial.println("Device ID: " + device_id);
    Serial.println("Gateway AP: " + String(ap_ssid));
    Serial.println("Controller: " + String(controller_ip));
    Serial.println("========================\n");
}

void loop() {
    // Feed watchdog
    yield();
    
    // Monitor and maintain WiFi connection
    maintainWiFiConnection();
    
    // Handle incoming connections from nodes (Gateway function)
    handleNodeConnections();
    
    // Send own data as a node (Node function)
    sendOwnData();
    
    delay(100); // Small delay to prevent watchdog issues
}

void connectToWiFi() {
    if (WiFi.status() == WL_CONNECTED) {
        staConnected = true;
        return;
    }
    
    Serial.print("\nConnecting to WiFi: ");
    Serial.println(sta_ssid);
    WiFi.begin(sta_ssid, sta_password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
        yield(); // Feed watchdog during connection
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        staConnected = true;
        Serial.println("\n✅ Connected to WiFi!");
        Serial.print("STA IP address: ");
        Serial.println(WiFi.localIP());
        Serial.print("STA MAC: ");
        Serial.println(WiFi.macAddress());
        
        // Request token after successful connection
        if (device_token == "") {
            requestToken();
        }
    } else {
        staConnected = false;
        Serial.println("\n❌ Failed to connect to WiFi");
        Serial.println("Gateway AP is still active for local nodes");
    }
}

void maintainWiFiConnection() {
    unsigned long currentMillis = millis();
    
    // Check WiFi status periodically
    if (currentMillis - lastWiFiCheck >= WIFI_CHECK_INTERVAL) {
        lastWiFiCheck = currentMillis;
        
        wl_status_t status = WiFi.status();
        
        if (status == WL_CONNECTED) {
            if (!staConnected) {
                // Just reconnected
                staConnected = true;
                Serial.println("\n[WiFi] ✅ Reconnected to WiFi!");
                Serial.print("[WiFi] IP: ");
                Serial.println(WiFi.localIP());
                
                // Request new token after reconnection
                device_token = "";
                requestToken();
            }
            // Refresh token before expiration (every 4 minutes)
            if (device_token != "" && currentMillis - lastTokenRefresh >= TOKEN_REFRESH_INTERVAL) {
                Serial.println("[Node] Refreshing token before expiration...");
                requestToken();
                lastTokenRefresh = currentMillis;
            }
        } else {
            if (staConnected) {
                // Just disconnected
                staConnected = false;
                Serial.println("\n[WiFi] ⚠️ WiFi disconnected!");
                device_token = ""; // Clear token on disconnect
            }
            
            // Attempt reconnection (with delay to avoid spamming)
            if (currentMillis - lastConnectionAttempt >= RECONNECT_DELAY) {
                lastConnectionAttempt = currentMillis;
                Serial.println("[WiFi] Attempting to reconnect...");
                WiFi.disconnect();
                delay(100);
                connectToWiFi();
            }
        }
    }
}

void handleNodeConnections() {
    WiFiClient client = gatewayServer.available();
    if (client) {
        Serial.println("\n[Gateway] New node connection");
        
        String request = "";
        unsigned long timeout = millis() + 5000; // 5 second timeout
        
        // Read request with timeout
        while (client.connected() && millis() < timeout) {
            if (client.available()) {
                String line = client.readStringUntil('\r');
                request += line;
                if (line.length() == 1 && line[0] == '\n') {
                    break;
                }
            }
            yield(); // Feed watchdog during reading
        }
        
        if (request.length() > 0) {
            int len = request.length() > 100 ? 100 : request.length();
            Serial.println("[Gateway] Received: " + request.substring(0, len));
            
            // Forward to controller if connected to WiFi
            if (WiFi.status() == WL_CONNECTED) {
                forwardToController(request);
            } else {
                Serial.println("[Gateway] Cannot forward - WiFi not connected");
            }
        } else {
            Serial.println("[Gateway] Empty or timeout request");
        }
        
        // Send response to node
        client.println("HTTP/1.1 200 OK");
        client.println("Content-Type: text/plain");
        client.println("Connection: close");
        client.println();
        client.println("Gateway received");
        
        // Flush and close connection
        client.flush();
        delay(10); // Small delay to ensure data is sent
        client.stop();
        Serial.println("[Gateway] Response sent and connection closed");
        yield(); // Feed watchdog after client handling
    }
}

void forwardToController(String data) {
    // Extract JSON from HTTP request (simple parsing)
    int jsonStart = data.indexOf('{');
    int jsonEnd = data.lastIndexOf('}') + 1;
    
    if (jsonStart >= 0 && jsonEnd > jsonStart) {
        String jsonData = data.substring(jsonStart, jsonEnd);
        Serial.println("[Gateway] Forwarding to controller: " + jsonData);
        
        HTTPClient http;
        WiFiClient client;
        
        // Set timeout
        http.setTimeout(5000); // 5 second timeout
        http.begin(client, "http://" + String(controller_ip) + ":5000/data");
        http.addHeader("Content-Type", "application/json");
        
        int httpCode = http.POST(jsonData);
        String response = http.getString();
        
        Serial.print("[Gateway] Controller response: ");
        Serial.print(httpCode);
        Serial.print(" - ");
        Serial.println(response);
        
        http.end();
        yield(); // Feed watchdog after HTTP operation
    } else {
        Serial.println("[Gateway] No valid JSON found in request");
    }
}

void requestToken() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[Node] Cannot request token - WiFi not connected");
        return;
    }
    
    Serial.println("\n[Node] Requesting token from controller...");
    
    HTTPClient http;
    WiFiClient client;
    
    // Set timeout
    http.setTimeout(5000); // 5 second timeout
    http.begin(client, "http://" + String(controller_ip) + ":5000/get_token");
    http.addHeader("Content-Type", "application/json");
    
    // Build request payload
    StaticJsonDocument<200> requestDoc;
    requestDoc["device_id"] = device_id;
    requestDoc["mac_address"] = WiFi.macAddress();
    
    String requestPayload;
    serializeJson(requestDoc, requestPayload);
    
    Serial.println("[Node] Sending: " + requestPayload);
    
    int httpCode = http.POST(requestPayload);
    String response = http.getString();
    
    Serial.print("[Node] Response code: ");
    Serial.println(httpCode);
    Serial.print("[Node] Response: ");
    Serial.println(response);
    
    if (httpCode == 200) {
        // Parse JSON response
        StaticJsonDocument<200> responseDoc;
        DeserializationError error = deserializeJson(responseDoc, response);
        
        if (!error && responseDoc.containsKey("token")) {
            device_token = responseDoc["token"].as<String>();
            Serial.println("[Node] ✅ Token received successfully");
            lastTokenRefresh = millis(); // Update token refresh timer
        } else {
            Serial.println("[Node] ❌ Failed to parse token from response");
            Serial.println("[Node] Error: " + String(error.c_str()));
            device_token = ""; // Clear invalid token
        }
    } else {
        Serial.print("[Node] ❌ Token request failed: HTTP ");
        Serial.println(httpCode);
        device_token = ""; // Clear token on failure
    }
    
    http.end();
    yield(); // Feed watchdog
}

void sendOwnData() {
    // Check if we should send data
    if (WiFi.status() != WL_CONNECTED) {
        return; // Can't send if not connected
    }
    
    if (device_token == "") {
        // Try to get token again if we don't have one
        if (millis() - lastNodeDataSent > 30000) { // Try every 30 seconds
            requestToken();
            lastNodeDataSent = millis();
        }
        return;
    }
    
    // Send data every NODE_DATA_INTERVAL
    if (millis() - lastNodeDataSent >= NODE_DATA_INTERVAL) {
        Serial.println("\n[Node] Sending own data...");
        
        HTTPClient http;
        WiFiClient client;
        
        // Set timeout
        http.setTimeout(5000); // 5 second timeout
        http.begin(client, "http://" + String(controller_ip) + ":5000/data");
        http.addHeader("Content-Type", "application/json");
        
        // Build data payload
        StaticJsonDocument<300> dataDoc;
        dataDoc["device_id"] = device_id;
        dataDoc["token"] = device_token;
        dataDoc["timestamp"] = String(millis() / 1000);
        
        // Simulated sensor data (replace with real sensors)
        float temperature = random(200, 300) / 10.0; // 20.0 - 30.0
        int humidity = random(40, 70);
        
        dataDoc["data"] = String(temperature);
        dataDoc["temperature"] = temperature;
        dataDoc["humidity"] = humidity;
        
        String dataPayload;
        serializeJson(dataDoc, dataPayload);
        
        Serial.println("[Node] Payload: " + dataPayload);
        
        int httpCode = http.POST(dataPayload);
        String response = http.getString();
        
        Serial.print("[Node] Response: ");
        Serial.print(httpCode);
        Serial.print(" - ");
        Serial.println(response);
        
        if (httpCode == 200) {
            Serial.println("[Node] ✅ Data sent successfully");
            // Check if response indicates token expired
            if (response.indexOf("Invalid token") >= 0 || 
                response.indexOf("rejected") >= 0 ||
                response.indexOf("authorized") >= 0 && response.indexOf("false") >= 0) {
                Serial.println("[Node] ⚠️ Token may be invalid, requesting new token...");
                device_token = "";
                requestToken();
            }
        } else {
            Serial.print("[Node] ⚠️ Data send failed: HTTP ");
            Serial.println(httpCode);
            // On failure, check if it's a token issue
            if (httpCode == 401 || httpCode == 403 || response.indexOf("token") >= 0) {
                device_token = "";
                requestToken();
            }
        }
        
        http.end();
        lastNodeDataSent = millis();
        yield(); // Feed watchdog after HTTP operation
    }
}

