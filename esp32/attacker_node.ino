/*
 * ESP32 DDoS Attacker Node
 * ========================
 * Simulates a compromised IoT device performing a DDoS attack.
 *
 * Behavior:
 *   Phase 1 (0-30s)  : Normal operation — sends legit sensor data every 5s
 *   Phase 2 (30s+)   : Attack mode — floods /data endpoint with high-rate,
 *                       suspicious traffic patterns to trigger ML detection
 *
 * Expected result:
 *   - ML engine detects high-confidence attack (confidence > 0.8)
 *   - Trust score drops below 30 → device marked "untrusted"
 *   - SDN redirects traffic to honeypot
 *   - Dashboard shows suspicious device alert
 */

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>

// Gateway Access Point Configuration
const char *ssid = "ESP32-AP";     // Must match gateway AP name
const char *password = "12345678"; // Must match gateway AP password

// Gateway IP
const char *gateway_ip = "192.168.4.1";
const int gateway_port = 80;

// Device Identity — use a unique ID for this attacker node
String device_id = "ATTACKER_01";
String token = "";
bool session_authorized = false;

// ===== ATTACK CONFIGURATION =====
const unsigned long NORMAL_PHASE_DURATION =
    30000; // 30 seconds of normal behavior
const unsigned long NORMAL_SEND_INTERVAL = 5000; // Normal: send every 5 seconds
const unsigned long ATTACK_SEND_INTERVAL =
    2000; // Attack: send every 2s (avoids flooding gateway)
const int ATTACK_BURST_COUNT =
    1; // Send 1 packet per cycle (ML detects via content features)

// State tracking
unsigned long startTime = 0;
unsigned long lastDataSend = 0;
unsigned long lastTokenRequest = 0;
unsigned long attackStartTime = 0;
int totalPacketsSent = 0;
int attackPacketsSent = 0;
bool attackMode = false;

// Attack stats
int acceptedCount = 0;
int rejectedCount = 0;
int rateLimitedCount = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n╔══════════════════════════════════════╗");
  Serial.println("║   ⚠️  ESP32 ATTACKER NODE STARTING  ║");
  Serial.println("║   DDoS Simulation for Trust Test     ║");
  Serial.println("╚══════════════════════════════════════╝\n");

  // Connect to gateway AP
  Serial.println("[ATTACKER] Connecting to Gateway AP...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[ATTACKER] ✅ Connected to Gateway!");
    Serial.print("[ATTACKER] IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("[ATTACKER] MAC: ");
    Serial.println(WiFi.macAddress());
    Serial.print("[ATTACKER] Device ID: ");
    Serial.println(device_id);
  } else {
    Serial.println("\n[ATTACKER] ❌ Failed to connect to Gateway");
    while (1) {
      delay(1000);
    }
  }

  // Stagger startup to avoid colliding with other nodes at gateway
  int startupDelay = random(5000, 8000);
  Serial.print("\n[ATTACKER] Waiting ");
  Serial.print(startupDelay);
  Serial.println("ms before authenticating (stagger)...");
  delay(startupDelay);

  // Request token
  Serial.println("[ATTACKER] Phase 0: Authenticating...");
  requestToken();

  startTime = millis();
  Serial.println("\n[ATTACKER] ⏱️  Normal phase begins (30 seconds)");
  Serial.println("[ATTACKER] Will switch to ATTACK mode after normal phase\n");
}

void loop() {
  unsigned long currentMillis = millis();
  unsigned long elapsed = currentMillis - startTime;

  // Check WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[ATTACKER] ⚠️ WiFi lost, reconnecting...");
    WiFi.begin(ssid, password);
    delay(5000);
    return;
  }

  // Request token if needed
  if (token == "") {
    if (currentMillis - lastTokenRequest >= 15000) {
      requestToken();
      lastTokenRequest = currentMillis;
    }
    return;
  }

  // Authenticate session if needed
  if (!session_authorized) {
    if (currentMillis - lastTokenRequest >= 10000) {
      authenticateSession();
      lastTokenRequest = currentMillis;
    }
    return;
  }

  // ===== PHASE SWITCHING =====
  if (!attackMode && elapsed >= NORMAL_PHASE_DURATION) {
    attackMode = true;
    attackStartTime = currentMillis;
    Serial.println("\n╔══════════════════════════════════════╗");
    Serial.println("║   🔴 ATTACK MODE ACTIVATED!          ║");
    Serial.println("║   Flooding /data endpoint...         ║");
    Serial.println("╚══════════════════════════════════════╝\n");
    Serial.println("[ATTACKER] Attack parameters:");
    Serial.println("  • Interval: 2000ms (30 pkt/min)");
    Serial.println("  • Burst: 1 packet per cycle");
    Serial.println("  • High rate/pps/bps values in content");
    Serial.println("  • Suspicious port patterns");
    Serial.println("  • SYN flood TCP flags\n");
  }

  // ===== SEND DATA =====
  unsigned long sendInterval =
      attackMode ? ATTACK_SEND_INTERVAL : NORMAL_SEND_INTERVAL;

  if (currentMillis - lastDataSend >= sendInterval) {
    if (attackMode) {
      // Send burst of attack packets
      for (int i = 0; i < ATTACK_BURST_COUNT; i++) {
        sendAttackData();
        delay(50); // Small delay between burst packets
      }

      // Print attack stats periodically
      unsigned long attackElapsed = (currentMillis - attackStartTime) / 1000;
      if (attackPacketsSent % 25 == 0) {
        Serial.println("\n--- ATTACK STATS ---");
        Serial.print("  Attack Duration: ");
        Serial.print(attackElapsed);
        Serial.println("s");
        Serial.print("  Attack Packets: ");
        Serial.println(attackPacketsSent);
        Serial.print("  Accepted: ");
        Serial.println(acceptedCount);
        Serial.print("  Rejected: ");
        Serial.println(rejectedCount);
        Serial.print("  Rate Limited: ");
        Serial.println(rateLimitedCount);
        Serial.println("--------------------\n");
      }
    } else {
      sendNormalData();
    }
    lastDataSend = currentMillis;
  }

  delay(10);
}

// ===== TOKEN REQUEST =====
void requestToken() {
  Serial.println("[ATTACKER] Requesting token...");

  HTTPClient http;
  String url = "http://" + String(gateway_ip) + ":" + String(gateway_port) +
               "/get_token";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  StaticJsonDocument<200> doc;
  doc["device_id"] = device_id;
  doc["mac_address"] = WiFi.macAddress();

  String payload;
  serializeJson(doc, payload);

  int httpCode = http.POST(payload);
  String response = http.getString();

  Serial.print("[ATTACKER] Token response (");
  Serial.print(httpCode);
  Serial.print("): ");
  Serial.println(response);

  if (httpCode == 200) {
    StaticJsonDocument<200> resDoc;
    deserializeJson(resDoc, response);
    if (resDoc.containsKey("token")) {
      token = resDoc["token"].as<String>();
      session_authorized = false;
      Serial.println("[ATTACKER] ✅ Token received!");
      authenticateSession();
    }
  } else if (httpCode == 403) {
    Serial.println(
        "[ATTACKER] ⏳ Device pending approval — approve on dashboard");
  }

  http.end();
  lastTokenRequest = millis();
}

// ===== SESSION AUTH =====
void authenticateSession() {
  if (token == "")
    return;

  Serial.println("[ATTACKER] Authenticating session...");

  HTTPClient http;
  String url =
      "http://" + String(gateway_ip) + ":" + String(gateway_port) + "/auth";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  StaticJsonDocument<200> doc;
  doc["device_id"] = device_id;
  doc["token"] = token;

  String payload;
  serializeJson(doc, payload);

  int httpCode = http.POST(payload);
  String response = http.getString();

  if (httpCode == 200) {
    StaticJsonDocument<200> resDoc;
    deserializeJson(resDoc, response);
    if (resDoc["authorized"].as<bool>()) {
      session_authorized = true;
      Serial.println("[ATTACKER] ✅ Session authenticated!");
    } else {
      token = "";
      Serial.println("[ATTACKER] ❌ Auth failed, clearing token");
    }
  }

  http.end();
}

// ===== NORMAL DATA (Phase 1) =====
void sendNormalData() {
  HTTPClient http;
  String url =
      "http://" + String(gateway_ip) + ":" + String(gateway_port) + "/data";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  // Normal sensor data — small, legitimate-looking
  StaticJsonDocument<512> doc;
  doc["device_id"] = device_id;
  doc["token"] = token;
  doc["timestamp"] = String(millis() / 1000);
  doc["data"] = String(random(200, 300) / 10.0);
  doc["temperature"] = random(200, 300) / 10.0;
  doc["humidity"] = random(40, 70);

  // Normal network characteristics
  doc["size"] = 64;        // Small packet
  doc["protocol"] = 6;     // TCP
  doc["src_port"] = 49152; // Normal ephemeral port
  doc["dst_port"] = 80;    // Normal HTTP
  doc["rate"] = 0.2;       // Low rate
  doc["duration"] = 5.0;   // Normal duration
  doc["bps"] = 100;        // Low bandwidth
  doc["pps"] = 1;          // 1 packet per second
  doc["tcp_flags"] = 24;   // PSH+ACK (normal data transfer)
  doc["window_size"] = 65535;
  doc["ttl"] = 64;
  doc["fragment_offset"] = 0;
  doc["ip_length"] = 84;
  doc["tcp_length"] = 32;
  doc["udp_length"] = 0;

  String payload;
  serializeJson(doc, payload);

  int httpCode = http.POST(payload);
  String response = http.getString();
  totalPacketsSent++;

  Serial.print("[ATTACKER] 🟢 Normal data sent (");
  Serial.print(totalPacketsSent);
  Serial.print(" total) → ");
  Serial.println(response);

  handleResponse(response);
  http.end();
}

// ===== ATTACK DATA (Phase 2 — DDoS Flood) =====
void sendAttackData() {
  HTTPClient http;
  String url =
      "http://" + String(gateway_ip) + ":" + String(gateway_port) + "/data";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(3000); // Shorter timeout for flood

  // Generate DDoS-signature traffic patterns
  int attackType = random(0, 4);

  StaticJsonDocument<512> doc;
  doc["device_id"] = device_id;
  doc["token"] = token;
  doc["timestamp"] = String(millis() / 1000);
  doc["data"] = "0";

  switch (attackType) {
  case 0: // SYN Flood
    doc["size"] = 40 + random(0, 20);
    doc["protocol"] = 6; // TCP
    doc["src_port"] = random(1024, 65535);
    doc["dst_port"] = random(1, 1024); // Scanning low ports
    doc["rate"] = random(500, 2000) / 10.0;
    doc["duration"] = random(1, 5) / 10.0;
    doc["bps"] = random(50000, 500000);
    doc["pps"] = random(500, 5000); // Very high packets/sec
    doc["tcp_flags"] = 2;           // SYN only — classic SYN flood
    doc["window_size"] = 1024;      // Suspiciously small window
    doc["ttl"] = random(30, 64);    // Varied TTL (spoofed)
    doc["fragment_offset"] = 0;
    doc["ip_length"] = random(40, 60);
    doc["tcp_length"] = 20;
    doc["udp_length"] = 0;
    break;

  case 1:                             // UDP Flood
    doc["size"] = random(1000, 1500); // Large UDP packets
    doc["protocol"] = 17;             // UDP
    doc["src_port"] = random(1024, 65535);
    doc["dst_port"] = random(1, 65535);
    doc["rate"] = random(800, 3000) / 10.0;
    doc["duration"] = random(1, 3) / 10.0;
    doc["bps"] = random(100000, 1000000);
    doc["pps"] = random(1000, 10000); // Massive packet rate
    doc["tcp_flags"] = 0;             // No TCP flags (UDP)
    doc["window_size"] = 0;
    doc["ttl"] = random(20, 128);            // Random TTL (spoofed)
    doc["fragment_offset"] = random(0, 100); // Fragmentation
    doc["ip_length"] = random(1000, 1500);
    doc["tcp_length"] = 0;
    doc["udp_length"] = random(1000, 1472);
    break;

  case 2: // HTTP Flood
    doc["size"] = random(200, 800);
    doc["protocol"] = 6; // TCP
    doc["src_port"] = random(49152, 65535);
    doc["dst_port"] = 80; // HTTP
    doc["rate"] = random(300, 1500) / 10.0;
    doc["duration"] = random(1, 10) / 10.0;
    doc["bps"] = random(30000, 200000);
    doc["pps"] = random(200, 2000);
    doc["tcp_flags"] = 24; // PSH+ACK (looks like HTTP but very high rate)
    doc["window_size"] = random(512, 4096);
    doc["ttl"] = 64;
    doc["fragment_offset"] = 0;
    doc["ip_length"] = random(200, 800);
    doc["tcp_length"] = random(100, 500);
    doc["udp_length"] = 0;
    break;

  case 3:                            // ICMP/Ping Flood
    doc["size"] = random(56, 65535); // Ping of death - oversized
    doc["protocol"] = 1;             // ICMP
    doc["src_port"] = 0;
    doc["dst_port"] = 0;
    doc["rate"] = random(600, 2500) / 10.0;
    doc["duration"] = random(1, 3) / 10.0;
    doc["bps"] = random(80000, 800000);
    doc["pps"] = random(800, 8000);
    doc["tcp_flags"] = 0;
    doc["window_size"] = 0;
    doc["ttl"] = random(1, 255);             // Widely varied TTL
    doc["fragment_offset"] = random(0, 500); // Heavy fragmentation
    doc["ip_length"] = random(56, 65535);
    doc["tcp_length"] = 0;
    doc["udp_length"] = 0;
    break;
  }

  String payload;
  serializeJson(doc, payload);

  int httpCode = http.POST(payload);
  String response = http.getString();
  totalPacketsSent++;
  attackPacketsSent++;

  // Compact logging for attack mode
  Serial.print("[ATTACKER] 🔴 ATK#");
  Serial.print(attackPacketsSent);
  Serial.print(" type=");
  const char *types[] = {"SYN", "UDP", "HTTP", "ICMP"};
  Serial.print(types[attackType]);
  Serial.print(" pps=");
  Serial.print(doc["pps"].as<int>());
  Serial.print(" → ");
  Serial.println(response);

  handleResponse(response);
  http.end();
}

// ===== Handle response and track stats =====
void handleResponse(String response) {
  StaticJsonDocument<200> resDoc;
  DeserializationError error = deserializeJson(resDoc, response);

  if (!error && resDoc.containsKey("status")) {
    String status = resDoc["status"].as<String>();
    if (status == "accepted") {
      acceptedCount++;
    } else if (status == "rejected") {
      rejectedCount++;
      String reason =
          resDoc.containsKey("reason") ? resDoc["reason"].as<String>() : "";
      if (reason.indexOf("Rate limit") >= 0) {
        rateLimitedCount++;
        Serial.println(
            "[ATTACKER] ⚡ Rate limited! Controller is detecting flood.");
      }
      if (reason.indexOf("token") >= 0 || reason.indexOf("authorized") >= 0) {
        Serial.println(
            "[ATTACKER] 🛑 Token/Auth rejected — may have been blacklisted!");
        token = "";
        session_authorized = false;
      }
    }
  }
}
