#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WebServer.h>

// Gateway Access Point Configuration
const char *ap_ssid = "ESP32-AP";     // AP name for nodes to connect
const char *ap_password = "12345678"; // AP password (min 8 chars)

// WiFi Station Configuration (connects to your network)
const char *sta_ssid = "iPhone (2)";   // Your WiFi network name
const char *sta_password = "55566678"; // Your WiFi password

// Controller Configuration
const char *controller_ip =
    "172.20.10.3"; // Raspberry Pi IP where controller.py runs
const int controller_port = 5000;

// Gateway HTTP Server — WebServer handles concurrent clients properly
WebServer server(80);

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n========================================");
  Serial.println("    ESP32 Gateway Starting...");
  Serial.println("========================================\n");

  // Set WiFi to AP + STA mode
  WiFi.mode(WIFI_AP_STA);

  // Start Access Point for nodes
  Serial.println("[Gateway] Starting Access Point...");
  WiFi.softAP(ap_ssid, ap_password, 1, 0, 4); // channel 1, not hidden, max 4 connections
  delay(100); // Let soft-AP stabilize
  IPAddress apIP = WiFi.softAPIP();
  Serial.print("[Gateway] AP SSID: ");
  Serial.println(ap_ssid);
  Serial.print("[Gateway] AP IP Address: ");
  Serial.println(apIP);
  Serial.print("[Gateway] AP MAC Address: ");
  Serial.println(WiFi.softAPmacAddress());

  // Connect to WiFi Station (to reach controller)
  Serial.println("\n[Gateway] Connecting to WiFi (STA mode)...");
  Serial.print("[Gateway] Network: ");
  Serial.println(sta_ssid);
  WiFi.begin(sta_ssid, sta_password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[Gateway] ✅ Connected to WiFi!");
    Serial.print("[Gateway] STA IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("[Gateway] STA MAC Address: ");
    Serial.println(WiFi.macAddress());
    Serial.print("[Gateway] Controller IP: ");
    Serial.print(controller_ip);
    Serial.print(":");
    Serial.println(controller_port);
  } else {
    Serial.println("\n[Gateway] ❌ Failed to connect to WiFi");
    Serial.println("[Gateway] AP is still active for local nodes");
  }

  // Register route handlers
  server.on("/get_token", HTTP_POST, handleGetToken);
  server.on("/auth", HTTP_POST, handleAuth);
  server.on("/data", HTTP_POST, handleData);
  server.on("/onboard", HTTP_POST, handleOnboard);
  server.on("/finalize_onboarding", HTTP_POST, handleFinalizeOnboarding);
  server.onNotFound(handleNotFound);

  // Start HTTP server
  server.begin();
  Serial.println("\n[Gateway] HTTP Server started on port 80");
  Serial.println("[Gateway] Routes: /get_token, /auth, /data, /onboard, /finalize_onboarding");
  Serial.println("[Gateway] Ready to receive node connections");
  Serial.println("========================================\n");
}

void loop() {
  // Handle incoming HTTP requests (non-blocking, event-driven)
  server.handleClient();

  // Monitor WiFi connection status
  static unsigned long lastWiFiCheck = 0;
  if (millis() - lastWiFiCheck > 10000) // Check every 10 seconds
  {
    lastWiFiCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println(
          "\n[Gateway] ⚠️ WiFi disconnected! Attempting to reconnect...");
      WiFi.begin(sta_ssid, sta_password);
      int attempts = 0;
      while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
      }
      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[Gateway] ✅ WiFi reconnected!");
        Serial.print("[Gateway] STA IP: ");
        Serial.println(WiFi.localIP());
      } else {
        Serial.println("\n[Gateway] ❌ WiFi reconnection failed");
      }
    }
  }

  delay(2); // Minimal delay — WebServer handles timing
}

// ===== Forward a request to the controller and return the response =====
String forwardToController(String endpoint, String jsonPayload, int &outStatusCode) {
  if (WiFi.status() != WL_CONNECTED) {
    outStatusCode = 503;
    return "{\"error\":\"Gateway not connected to controller\"}";
  }

  String controllerUrl = "http://" + String(controller_ip) + ":" +
                         String(controller_port) + endpoint;
  Serial.print("[Gateway] Forwarding to: ");
  Serial.println(controllerUrl);

  HTTPClient http;
  http.begin(controllerUrl);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(8000);

  int httpCode = http.POST(jsonPayload);
  String response = http.getString();
  http.end();

  outStatusCode = httpCode > 0 ? httpCode : 502;

  Serial.print("[Gateway] Controller response code: ");
  Serial.println(httpCode);
  Serial.print("[Gateway] Controller response: ");
  Serial.println(response);

  return response;
}

// ===== Route Handlers =====

void handleGetToken() {
  Serial.println("\n--- [Gateway] New Request: /get_token ---");
  Serial.print("[Gateway] Client IP: ");
  Serial.println(server.client().remoteIP());
  Serial.println("[Gateway] 📝 Node requesting TOKEN");

  String body = server.arg("plain");
  Serial.print("[Gateway] Payload: ");
  Serial.println(body);

  if (body.length() == 0) {
    server.send(400, "application/json", "{\"error\":\"Empty request body\"}");
    return;
  }

  int statusCode;
  String response = forwardToController("/get_token", body, statusCode);
  server.send(statusCode, "application/json", response);
  Serial.println("[Gateway] Response sent to node");
}

void handleAuth() {
  Serial.println("\n--- [Gateway] New Request: /auth ---");
  Serial.print("[Gateway] Client IP: ");
  Serial.println(server.client().remoteIP());
  Serial.println("[Gateway] 🔐 Node authenticating SESSION");

  String body = server.arg("plain");
  Serial.print("[Gateway] Payload: ");
  Serial.println(body);

  if (body.length() == 0) {
    server.send(400, "application/json", "{\"error\":\"Empty request body\"}");
    return;
  }

  int statusCode;
  String response = forwardToController("/auth", body, statusCode);
  server.send(statusCode, "application/json", response);
  Serial.println("[Gateway] Response sent to node");
}

void handleData() {
  Serial.println("\n--- [Gateway] New Request: /data ---");
  Serial.print("[Gateway] Client IP: ");
  Serial.println(server.client().remoteIP());
  Serial.println("[Gateway] 📊 Node sending DATA");

  String body = server.arg("plain");

  if (body.length() == 0) {
    server.send(400, "application/json", "{\"error\":\"Empty request body\"}");
    return;
  }

  // Log payload but truncate if too long (attack data can be large)
  Serial.print("[Gateway] Payload (");
  Serial.print(body.length());
  Serial.print(" bytes): ");
  Serial.println(body.substring(0, min(200, (int)body.length())));

  int statusCode;
  String response = forwardToController("/data", body, statusCode);
  server.send(statusCode, "application/json", response);
}

void handleOnboard() {
  Serial.println("\n--- [Gateway] New Request: /onboard ---");
  Serial.print("[Gateway] Client IP: ");
  Serial.println(server.client().remoteIP());
  Serial.println("[Gateway] 🚀 Node requesting ONBOARDING");

  String body = server.arg("plain");
  Serial.print("[Gateway] Payload: ");
  Serial.println(body);

  if (body.length() == 0) {
    server.send(400, "application/json", "{\"error\":\"Empty request body\"}");
    return;
  }

  int statusCode;
  String response = forwardToController("/onboard", body, statusCode);
  server.send(statusCode, "application/json", response);
  Serial.println("[Gateway] Response sent to node");
}

void handleFinalizeOnboarding() {
  Serial.println("\n--- [Gateway] New Request: /finalize_onboarding ---");
  Serial.print("[Gateway] Client IP: ");
  Serial.println(server.client().remoteIP());
  Serial.println("[Gateway] ✅ Node finalizing ONBOARDING");

  String body = server.arg("plain");
  Serial.print("[Gateway] Payload: ");
  Serial.println(body);

  if (body.length() == 0) {
    server.send(400, "application/json", "{\"error\":\"Empty request body\"}");
    return;
  }

  int statusCode;
  String response = forwardToController("/finalize_onboarding", body, statusCode);
  server.send(statusCode, "application/json", response);
  Serial.println("[Gateway] Response sent to node");
}

void handleNotFound() {
  Serial.println("\n--- [Gateway] Unknown Request ---");
  Serial.print("[Gateway] URI: ");
  Serial.println(server.uri());
  Serial.print("[Gateway] Method: ");
  Serial.println(server.method() == HTTP_POST ? "POST" : "OTHER");
  server.send(404, "application/json", "{\"error\":\"Unknown endpoint\"}");
}
