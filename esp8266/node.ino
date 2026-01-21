#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// Connect to gateway AP
const char *ssid = "ESP8266-Gateway";  // Gateway AP name (change if using ESP32 gateway)
const char *password = "12345678";      // Gateway AP password

// Gateway IP (when connecting to gateway AP)
const char *controller_ip = "192.168.4.1"; // Gateway AP IP

// Device identity
String device_id = "ESP8266_Node1";     // Change to unique ID for each node
String token = "";

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n=== ESP8266 Node Setup ===");
    Serial.print("Connecting to Gateway: ");
    Serial.println(ssid);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✅ Connected to Gateway!");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
        Serial.print("MAC address: ");
        Serial.println(WiFi.macAddress());
    } else {
        Serial.println("\n❌ Failed to connect to Gateway");
        Serial.println("Please check:");
        Serial.println("  1. Gateway is powered on");
        Serial.println("  2. AP name and password are correct");
        Serial.println("  3. You are within WiFi range");
        while (1) delay(1000); // Stop here if can't connect
    }
    
    // Request token from controller (via gateway)
    requestToken();
    
    Serial.println("\n=== Setup Complete ===");
    Serial.println("Device ID: " + device_id);
    Serial.println("========================\n");
}

void loop() {
    if (WiFi.status() == WL_CONNECTED && token != "") {
        sendData();
    } else if (WiFi.status() != WL_CONNECTED) {
        // Try to reconnect
        Serial.println("[Node] WiFi disconnected, reconnecting...");
        WiFi.begin(ssid, password);
        delay(5000);
    } else if (token == "") {
        // Try to get token again
        Serial.println("[Node] No token, requesting...");
        requestToken();
    }
    
    delay(5000); // Send data every 5 seconds
}

void requestToken() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[Node] Cannot request token - not connected");
        return;
    }
    
    Serial.println("\n[Node] Requesting token from controller...");
    
    HTTPClient http;
    WiFiClient client;
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
            token = responseDoc["token"].as<String>();
            Serial.println("[Node] ✅ Token received: " + token);
        } else {
            Serial.println("[Node] ❌ Failed to parse token from response");
            Serial.println("[Node] Error: " + String(error.c_str()));
            token = ""; // Clear invalid token
        }
    } else {
        Serial.println("[Node] ❌ Token request failed");
        Serial.print("[Node] HTTP Code: ");
        Serial.println(httpCode);
        token = ""; // Clear token on failure
    }
    
    http.end();
}

void sendData() {
    Serial.println("\n[Node] Sending data...");
    
    HTTPClient http;
    WiFiClient client;
    http.begin(client, "http://" + String(controller_ip) + ":5000/data");
    http.addHeader("Content-Type", "application/json");
    
    // Build data payload
    StaticJsonDocument<300> dataDoc;
    dataDoc["device_id"] = device_id;
    dataDoc["token"] = token;
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
    
    // Check if token expired
    if (httpCode == 200) {
        if (response.indexOf("Invalid token") >= 0 || 
            response.indexOf("rejected") >= 0 || 
            response.indexOf("authorized") >= 0 && response.indexOf("false") >= 0) {
            Serial.println("[Node] Token may be invalid, requesting new token...");
            token = "";
            requestToken();
        } else {
            Serial.println("[Node] ✅ Data sent successfully");
        }
    } else {
        Serial.print("[Node] ❌ Data send failed: ");
        Serial.println(httpCode);
    }
    
    http.end();
}

