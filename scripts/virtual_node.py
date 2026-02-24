"""
Virtual ESP32 Node Simulator
============================
Simulates a legitimate ESP32 IoT sensor node for testing without physical hardware.

Behavior:
  - Connects to the SDN controller directly (no gateway needed)
  - Requests authentication token
  - Authenticates session
  - Sends normal sensor data (temperature, humidity) every 5 seconds
  - Maintains trust score at 70 (Trusted)

Usage:
  python virtual_node.py [--server SERVER_IP] [--port PORT] [--device-id DEVICE_ID]

Example:
  python virtual_node.py --server 127.0.0.1 --port 5000 --device-id ESP32_Node_01
"""

import argparse
import json
import random
import sys
import time
import requests

# Fix Windows terminal encoding (cp1252 can't handle emoji)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ─── Configuration ────────────────────────────────────────────────────────────
DEFAULT_SERVER = "127.0.0.1"
DEFAULT_PORT = 5000
DEFAULT_DEVICE_ID = "ESP32_Node_01"
DATA_SEND_INTERVAL = 5       # seconds
TOKEN_RETRY_INTERVAL = 10    # seconds


def generate_fake_mac():
    """Generate a realistic ESP32-style MAC address."""
    oui = random.choice(["24:6F:28", "30:AE:A4", "A4:CF:12", "CC:50:E3"])
    nic = ":".join(f"{random.randint(0, 255):02X}" for _ in range(3))
    return f"{oui}:{nic}"


class VirtualNode:
    def __init__(self, server, port, device_id):
        self.base_url = f"http://{server}:{port}"
        self.device_id = device_id
        self.mac_address = generate_fake_mac()
        self.token = None
        self.session_authorized = False
        self.packets_sent = 0
        self.start_time = time.time()

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] [NODE {self.device_id}] {msg}")

    # ── Step 1: Request Token ─────────────────────────────────────────────
    def request_token(self):
        self.log("Requesting authentication token...")
        try:
            resp = requests.post(
                f"{self.base_url}/get_token",
                json={"device_id": self.device_id, "mac_address": self.mac_address},
                timeout=5,
            )
            data = resp.json()
            if resp.status_code == 200 and "token" in data:
                self.token = data["token"]
                self.session_authorized = False
                self.log(f"✅ Token received: {self.token[:16]}...")
                return True
            else:
                error = data.get("error", "Unknown error")
                self.log(f"❌ Token request failed: {error}")
                if "pending" in str(error).lower():
                    self.log("⏳ Device is pending approval — approve on dashboard")
                return False
        except requests.exceptions.ConnectionError:
            self.log(f"❌ Cannot connect to controller at {self.base_url}")
            return False
        except Exception as e:
            self.log(f"❌ Token request error: {e}")
            return False

    # ── Step 2: Authenticate Session ──────────────────────────────────────
    def authenticate_session(self):
        if not self.token:
            return False

        self.log("Authenticating session...")
        try:
            resp = requests.post(
                f"{self.base_url}/auth",
                json={"device_id": self.device_id, "token": self.token},
                timeout=5,
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("authorized"):
                self.session_authorized = True
                self.log("✅ Session authenticated successfully!")
                return True
            else:
                self.log("❌ Session auth failed — requesting new token")
                self.token = None
                return False
        except Exception as e:
            self.log(f"❌ Auth error: {e}")
            return False

    # ── Step 3: Send Normal Sensor Data ───────────────────────────────────
    def send_data(self):
        if not self.token or not self.session_authorized:
            return False

        temperature = round(random.uniform(20.0, 30.0), 1)
        humidity = random.randint(40, 70)

        payload = {
            "device_id": self.device_id,
            "token": self.token,
            "timestamp": str(int(time.time())),
            "data": str(temperature),
            "temperature": temperature,
            "humidity": humidity,
            # Normal network characteristics
            "size": 64,
            "protocol": 6,       # TCP
            "src_port": 49152,   # Normal ephemeral port
            "dst_port": 80,      # Normal HTTP
            "rate": 0.2,         # Low rate
            "duration": 5.0,     # Normal duration
            "bps": 100,          # Low bandwidth
            "pps": 1,            # 1 packet per second
            "tcp_flags": 24,     # PSH+ACK (normal data transfer)
            "window_size": 65535,
            "ttl": 64,
            "fragment_offset": 0,
            "ip_length": 84,
            "tcp_length": 32,
            "udp_length": 0,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/data",
                json=payload,
                timeout=5,
            )
            data = resp.json()
            self.packets_sent += 1
            status = data.get("status", "unknown")

            if status == "accepted":
                self.log(
                    f"🟢 Data sent #{self.packets_sent} — "
                    f"temp={temperature}°C humidity={humidity}% → accepted"
                )
            elif status == "rejected":
                reason = data.get("reason", "Unknown")
                self.log(f"⚠️  Data rejected: {reason}")
                if "token" in reason.lower() or "authorized" in reason.lower():
                    self.token = None
                    self.session_authorized = False
            return True
        except Exception as e:
            self.log(f"❌ Data send error: {e}")
            return False

    # ── Main Loop ─────────────────────────────────────────────────────────
    def run(self):
        self.log("=" * 50)
        self.log("  Virtual ESP32 Node Starting")
        self.log(f"  Device ID : {self.device_id}")
        self.log(f"  MAC       : {self.mac_address}")
        self.log(f"  Controller: {self.base_url}")
        self.log("=" * 50)

        last_token_attempt = 0
        last_data_send = 0

        while True:
            try:
                now = time.time()

                # Step 1: Get token if we don't have one
                if not self.token:
                    if now - last_token_attempt >= TOKEN_RETRY_INTERVAL:
                        self.request_token()
                        last_token_attempt = now
                    time.sleep(1)
                    continue

                # Step 2: Authenticate if not yet authenticated
                if not self.session_authorized:
                    self.authenticate_session()
                    time.sleep(2)
                    continue

                # Step 3: Send data at regular intervals
                if now - last_data_send >= DATA_SEND_INTERVAL:
                    self.send_data()
                    last_data_send = now

                time.sleep(0.5)

            except KeyboardInterrupt:
                self.log("")
                self.log("🛑 Shutting down virtual node...")
                self.log(f"   Total packets sent: {self.packets_sent}")
                self.log(f"   Uptime: {int(time.time() - self.start_time)}s")
                sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Virtual ESP32 Node Simulator")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Controller IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Controller port")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="Device ID")
    args = parser.parse_args()

    node = VirtualNode(args.server, args.port, args.device_id)
    node.run()


if __name__ == "__main__":
    main()
