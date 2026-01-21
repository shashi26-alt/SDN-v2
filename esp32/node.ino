#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Gateway Access Point Configuration
const char *ssid = "ESP32-AP";           // Must match gateway AP name
const char *password = "12345678";       // Must match gateway AP password

// Gateway IP (when connected to gateway AP)
const char *gateway_ip = "192.168.4.1";  // Gateway AP IP (usually 192.168.4.1)
const int gateway_port = 80;

// Device Identity
String device_id = "0011";               // Change for each node (must be unique)
String token = "";

// Timing
unsigned long lastTokenRequest = 0;
unsigned long lastDataSend = 0;
const unsigned long TOKEN_RETRY_INTERVAL = 30000;  // Retry token every 30 seconds if failed
const unsigned long DATA_SEND_INTERVAL = 5000;     // Send data every 5 seconds

void setup()
{
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n========================================");
    Serial.println("    ESP32 Node Starting...");
    Serial.println("========================================\n");

    Serial.println("[Node] Step 1: Connecting to Gateway AP...");
    Serial.print("[Node] SSID: ");
    Serial.println(ssid);

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30)
    {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.println("\n[Node] ✅ Connected to Gateway!");
        Serial.print("[Node] Node IP Address: ");
        Serial.println(WiFi.localIP());
        Serial.print("[Node] Node MAC Address: ");
        Serial.println(WiFi.macAddress());
        Serial.print("[Node] Gateway IP: ");
        Serial.print(gateway_ip);
        Serial.print(":");
        Serial.println(gateway_port);
        Serial.print("[Node] Device ID: ");
        Serial.println(device_id);
    }
    else
    {
        Serial.println("\n[Node] ❌ Failed to connect to Gateway");
        Serial.println("[Node] Please check:");
        Serial.println("  1. Gateway is powered on");
        Serial.println("  2. AP name and password are correct");
        Serial.println("  3. You are within WiFi range");
        while (1)
        {
            delay(1000); // Stop here if can't connect
        }
    }

    Serial.println("\n[Node] Step 2: Requesting authentication token...");
    requestToken();

    Serial.println("\n========================================");
    Serial.println("    Node Setup Complete");
    Serial.println("========================================\n");
}

void loop()
{
    unsigned long currentMillis = millis();

    // Check WiFi connection
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("\n[Node] ⚠️ WiFi disconnected, reconnecting...");
        WiFi.begin(ssid, password);
        delay(5000);
        return;
    }

    // Request token if we don't have one
    if (token == "")
    {
        if (currentMillis - lastTokenRequest >= TOKEN_RETRY_INTERVAL)
        {
            Serial.println("\n[Node] No token available, requesting...");
            requestToken();
            lastTokenRequest = currentMillis;
        }
        return; // Don't send data without token
    }

    // Send data periodically
    if (currentMillis - lastDataSend >= DATA_SEND_INTERVAL)
    {
        sendData();
        lastDataSend = currentMillis;
    }

    delay(100); // Small delay to prevent watchdog issues
}

void requestToken()
{
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("[Node] ❌ Cannot request token - WiFi not connected");
        return;
    }

    Serial.println("[Node] Sending token request to gateway...");

    HTTPClient http;
    String url = "http://" + String(gateway_ip) + ":" + String(gateway_port) + "/get_token";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);

    // Build request payload
    StaticJsonDocument<200> requestDoc;
    requestDoc["device_id"] = device_id;
    requestDoc["mac_address"] = WiFi.macAddress();

    String requestPayload;
    serializeJson(requestDoc, requestPayload);

    Serial.print("[Node] Payload: ");
    Serial.println(requestPayload);
    Serial.print("[Node] URL: ");
    Serial.println(url);

    int httpCode = http.POST(requestPayload);
    String response = http.getString();

    Serial.print("[Node] HTTP Response Code: ");
    Serial.println(httpCode);
    Serial.print("[Node] Response: ");
    Serial.println(response);

    if (httpCode == 200)
    {
        // Parse JSON response
        StaticJsonDocument<200> responseDoc;
        DeserializationError error = deserializeJson(responseDoc, response);

        if (!error && responseDoc.containsKey("token"))
        {
            token = responseDoc["token"].as<String>();
            Serial.println("[Node] ✅ Token received successfully!");
            Serial.print("[Node] Token: ");
            Serial.println(token);
        }
        else if (responseDoc.containsKey("error"))
        {
            String errorMsg = responseDoc["error"].as<String>();
            Serial.print("[Node] ❌ Token request failed: ");
            Serial.println(errorMsg);
            if (errorMsg.indexOf("not authorized") >= 0)
            {
                Serial.println("[Node] 💡 Device needs to be authorized on controller");
                Serial.println("[Node]    Run: curl -X POST http://CONTROLLER_IP:5000/api/authorize_device \\");
                Serial.println("[Node]         -H 'Content-Type: application/json' \\");
                Serial.print("[Node]         -d '{\"device_id\":\"");
                Serial.print(device_id);
                Serial.print("\",\"mac_address\":\"");
                Serial.print(WiFi.macAddress());
                Serial.println("\"}'");
            }
            token = "";
        }
        else
        {
            Serial.println("[Node] ❌ Failed to parse token from response");
            Serial.print("[Node] Parse error: ");
            Serial.println(error.c_str());
            token = "";
        }
    }
    else
    {
        Serial.print("[Node] ❌ Token request failed with HTTP code: ");
        Serial.println(httpCode);
        token = "";
    }

    http.end();
    lastTokenRequest = millis();
}

void sendData()
{
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("[Node] ❌ Cannot send data - WiFi not connected");
        return;
    }

    if (token == "")
    {
        Serial.println("[Node] ⚠️ Cannot send data - no token");
        return;
    }

    Serial.println("\n[Node] Step 3: Sending data to controller...");

    HTTPClient http;
    String url = "http://" + String(gateway_ip) + ":" + String(gateway_port) + "/data";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);

    // Generate sensor data (replace with real sensor readings)
    float temperature = random(200, 300) / 10.0; // 20.0 - 30.0°C
    int humidity = random(40, 70);                // 40-70%

    // Build JSON payload
    StaticJsonDocument<300> dataDoc;
    dataDoc["device_id"] = device_id;
    dataDoc["token"] = token;
    dataDoc["timestamp"] = String(millis() / 1000);
    dataDoc["data"] = String(temperature);
    dataDoc["temperature"] = temperature;
    dataDoc["humidity"] = humidity;

    String dataPayload;
    serializeJson(dataDoc, dataPayload);

    Serial.print("[Node] Payload: ");
    Serial.println(dataPayload);
    Serial.print("[Node] URL: ");
    Serial.println(url);

    int httpCode = http.POST(dataPayload);
    String response = http.getString();

    Serial.print("[Node] HTTP Response Code: ");
    Serial.println(httpCode);
    Serial.print("[Node] Response: ");
    Serial.println(response);

    if (httpCode == 200)
    {
        // Parse response to check for errors
        StaticJsonDocument<200> responseDoc;
        DeserializationError error = deserializeJson(responseDoc, response);

        if (!error && responseDoc.containsKey("status"))
        {
            String status = responseDoc["status"].as<String>();
            if (status == "accepted")
            {
                Serial.println("[Node] ✅ Data sent successfully!");
            }
            else if (status == "rejected")
            {
                String reason = responseDoc.containsKey("reason") ? responseDoc["reason"].as<String>() : "Unknown";
                Serial.print("[Node] ⚠️ Data rejected: ");
                Serial.println(reason);

                // If token is invalid, clear it
                if (reason.indexOf("token") >= 0 || reason.indexOf("authorized") >= 0)
                {
                    Serial.println("[Node] Clearing token, will request new one...");
                    token = "";
                }
            }
        }
        else
        {
            Serial.println("[Node] ✅ Data sent (response: " + response + ")");
        }
    }
    else
    {
        Serial.print("[Node] ❌ Data send failed with HTTP code: ");
        Serial.println(httpCode);

        // If unauthorized, clear token
        if (httpCode == 401 || httpCode == 403)
        {
            Serial.println("[Node] Clearing token due to authorization error...");
            token = "";
        }
    }

    http.end();
}
