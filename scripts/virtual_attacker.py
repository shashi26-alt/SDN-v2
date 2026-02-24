"""
Virtual ESP32 Attacker Node Simulator
======================================
Simulates a compromised ESP32 IoT device performing a DDoS attack.

Behavior:
  Phase 1 (0-30s)  : Normal operation — sends legit sensor data every 5s
  Phase 2 (30s+)   : Attack mode — sends DDoS-signature traffic every 2s

Expected ML/Trust Score Result:
  - ML engine detects high-confidence attack (confidence > 0.8)
  - Trust score drops below 30 → device marked "untrusted"
  - Device redirected to honeypot on dashboard
  - Dashboard shows suspicious device alert

Usage:
  python virtual_attacker.py [--server SERVER_IP] [--port PORT] [--device-id DEVICE_ID]

Example:
  python virtual_attacker.py --server 127.0.0.1 --port 5000 --device-id ATTACKER_01
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
DEFAULT_DEVICE_ID = "ATTACKER_01"

NORMAL_PHASE_DURATION = 30   # seconds of normal behavior before attack
NORMAL_SEND_INTERVAL = 5     # seconds between normal data sends
ATTACK_SEND_INTERVAL = 2     # seconds between attack packets
TOKEN_RETRY_INTERVAL = 15    # seconds between token retries


def generate_fake_mac():
    """Generate a realistic ESP32-style MAC address."""
    oui = random.choice(["24:6F:28", "30:AE:A4", "A4:CF:12", "CC:50:E3"])
    nic = ":".join(f"{random.randint(0, 255):02X}" for _ in range(3))
    return f"{oui}:{nic}"


class VirtualAttacker:
    def __init__(self, server, port, device_id):
        self.base_url = f"http://{server}:{port}"
        self.device_id = device_id
        self.mac_address = generate_fake_mac()
        self.token = None
        self.session_authorized = False

        # Counters
        self.packets_sent = 0
        self.attack_packets_sent = 0
        self.accepted_count = 0
        self.rejected_count = 0
        self.rate_limited_count = 0

        # Phase tracking
        self.start_time = None
        self.attack_mode = False
        self.attack_start_time = None

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] [ATTACKER {self.device_id}] {msg}")

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
                    self.log("⏳ Device pending approval — approve on dashboard")
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
                self.log("✅ Session authenticated!")
                return True
            else:
                self.log("❌ Auth failed, clearing token")
                self.token = None
                return False
        except Exception as e:
            self.log(f"❌ Auth error: {e}")
            return False

    # ── Phase 1: Normal Sensor Data ───────────────────────────────────────
    def send_normal_data(self):
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
            "tcp_flags": 24,     # PSH+ACK
            "window_size": 65535,
            "ttl": 64,
            "fragment_offset": 0,
            "ip_length": 84,
            "tcp_length": 32,
            "udp_length": 0,
        }

        try:
            resp = requests.post(f"{self.base_url}/data", json=payload, timeout=5)
            data = resp.json()
            self.packets_sent += 1
            self._handle_response(data)
            self.log(
                f"🟢 Normal #{self.packets_sent} — temp={temperature}°C "
                f"humidity={humidity}% → {data.get('status', '?')}"
            )
            return True
        except Exception as e:
            self.log(f"❌ Data send error: {e}")
            return False

    # ── Phase 2: DDoS Attack Traffic ──────────────────────────────────────
    def send_attack_data(self):
        if not self.token or not self.session_authorized:
            return False

        attack_type = random.randint(0, 3)
        attack_names = ["SYN_FLOOD", "UDP_FLOOD", "HTTP_FLOOD", "ICMP_FLOOD"]

        payload = {
            "device_id": self.device_id,
            "token": self.token,
            "timestamp": str(int(time.time())),
            "data": "0",
        }

        if attack_type == 0:  # SYN Flood
            payload.update({
                "size": 40 + random.randint(0, 20),
                "protocol": 6,                         # TCP
                "src_port": random.randint(1024, 65535),
                "dst_port": random.randint(1, 1024),   # Scanning low ports
                "rate": random.randint(500, 2000) / 10.0,
                "duration": random.randint(1, 5) / 10.0,
                "bps": random.randint(50000, 500000),
                "pps": random.randint(500, 5000),      # Very high PPS
                "tcp_flags": 2,                        # SYN only
                "window_size": 1024,                   # Suspiciously small
                "ttl": random.randint(30, 64),
                "fragment_offset": 0,
                "ip_length": random.randint(40, 60),
                "tcp_length": 20,
                "udp_length": 0,
            })
        elif attack_type == 1:  # UDP Flood
            payload.update({
                "size": random.randint(1000, 1500),
                "protocol": 17,                        # UDP
                "src_port": random.randint(1024, 65535),
                "dst_port": random.randint(1, 65535),
                "rate": random.randint(800, 3000) / 10.0,
                "duration": random.randint(1, 3) / 10.0,
                "bps": random.randint(100000, 1000000),
                "pps": random.randint(1000, 10000),
                "tcp_flags": 0,
                "window_size": 0,
                "ttl": random.randint(20, 128),
                "fragment_offset": random.randint(0, 100),
                "ip_length": random.randint(1000, 1500),
                "tcp_length": 0,
                "udp_length": random.randint(1000, 1472),
            })
        elif attack_type == 2:  # HTTP Flood
            payload.update({
                "size": random.randint(200, 800),
                "protocol": 6,                         # TCP
                "src_port": random.randint(49152, 65535),
                "dst_port": 80,
                "rate": random.randint(300, 1500) / 10.0,
                "duration": random.randint(1, 10) / 10.0,
                "bps": random.randint(30000, 200000),
                "pps": random.randint(200, 2000),
                "tcp_flags": 24,                       # PSH+ACK (high rate)
                "window_size": random.randint(512, 4096),
                "ttl": 64,
                "fragment_offset": 0,
                "ip_length": random.randint(200, 800),
                "tcp_length": random.randint(100, 500),
                "udp_length": 0,
            })
        elif attack_type == 3:  # ICMP Flood
            payload.update({
                "size": random.randint(56, 65535),
                "protocol": 1,                         # ICMP
                "src_port": 0,
                "dst_port": 0,
                "rate": random.randint(600, 2500) / 10.0,
                "duration": random.randint(1, 3) / 10.0,
                "bps": random.randint(80000, 800000),
                "pps": random.randint(800, 8000),
                "tcp_flags": 0,
                "window_size": 0,
                "ttl": random.randint(1, 255),
                "fragment_offset": random.randint(0, 500),
                "ip_length": random.randint(56, 65535),
                "tcp_length": 0,
                "udp_length": 0,
            })

        try:
            resp = requests.post(f"{self.base_url}/data", json=payload, timeout=3)
            data = resp.json()
            self.packets_sent += 1
            self.attack_packets_sent += 1
            self._handle_response(data)

            self.log(
                f"🔴 ATK#{self.attack_packets_sent} type={attack_names[attack_type]} "
                f"pps={payload.get('pps', 0)} → {data.get('status', '?')}"
            )
            return True
        except Exception as e:
            self.log(f"❌ Attack send error: {e}")
            return False

    def _handle_response(self, data):
        status = data.get("status", "")
        if status == "accepted":
            self.accepted_count += 1
        elif status == "rejected":
            self.rejected_count += 1
            reason = data.get("reason", "")
            if "Rate limit" in reason:
                self.rate_limited_count += 1
            if "token" in reason.lower() or "authorized" in reason.lower():
                self.log("🛑 Token/Auth rejected — may have been blacklisted!")
                self.token = None
                self.session_authorized = False

    def print_attack_stats(self):
        elapsed = int(time.time() - self.attack_start_time)
        self.log("─── ATTACK STATS ───")
        self.log(f"  Duration       : {elapsed}s")
        self.log(f"  Total packets  : {self.packets_sent}")
        self.log(f"  Attack packets : {self.attack_packets_sent}")
        self.log(f"  Accepted       : {self.accepted_count}")
        self.log(f"  Rejected       : {self.rejected_count}")
        self.log(f"  Rate limited   : {self.rate_limited_count}")
        self.log("────────────────────")

    # ── Main Loop ─────────────────────────────────────────────────────────
    def run(self):
        self.log("╔══════════════════════════════════════╗")
        self.log("║  ⚠️  VIRTUAL ATTACKER NODE STARTING  ║")
        self.log("║  DDoS Simulation for Trust Test      ║")
        self.log("╚══════════════════════════════════════╝")
        self.log(f"  Device ID : {self.device_id}")
        self.log(f"  MAC       : {self.mac_address}")
        self.log(f"  Controller: {self.base_url}")
        self.log(f"  Normal phase: {NORMAL_PHASE_DURATION}s, then attack mode")
        self.log("")

        last_token_attempt = 0
        last_data_send = 0

        while True:
            try:
                now = time.time()

                # Step 1: Get token
                if not self.token:
                    if now - last_token_attempt >= TOKEN_RETRY_INTERVAL:
                        if self.request_token():
                            self.authenticate_session()
                        last_token_attempt = now
                    time.sleep(1)
                    continue

                # Step 2: Authenticate
                if not self.session_authorized:
                    self.authenticate_session()
                    time.sleep(2)
                    continue

                # Initialize start time once authenticated
                if self.start_time is None:
                    self.start_time = time.time()
                    self.log(f"⏱️  Normal phase begins ({NORMAL_PHASE_DURATION}s)")

                elapsed = now - self.start_time

                # ── Phase switching ───────────────────────────────────
                if not self.attack_mode and elapsed >= NORMAL_PHASE_DURATION:
                    self.attack_mode = True
                    self.attack_start_time = time.time()
                    self.log("")
                    self.log("╔══════════════════════════════════════╗")
                    self.log("║   🔴 ATTACK MODE ACTIVATED!          ║")
                    self.log("║   Flooding /data endpoint...         ║")
                    self.log("╚══════════════════════════════════════╝")
                    self.log("")
                    self.log("Attack parameters:")
                    self.log("  • Interval: 2s")
                    self.log("  • Types: SYN/UDP/HTTP/ICMP flood (randomized)")
                    self.log("  • High pps/bps/rate values")
                    self.log("  • Suspicious port patterns & TCP flags")
                    self.log("")

                # ── Send data ─────────────────────────────────────────
                send_interval = ATTACK_SEND_INTERVAL if self.attack_mode else NORMAL_SEND_INTERVAL

                if now - last_data_send >= send_interval:
                    if self.attack_mode:
                        self.send_attack_data()

                        # Print stats every 25 attack packets
                        if self.attack_packets_sent % 25 == 0:
                            self.print_attack_stats()
                    else:
                        remaining = int(NORMAL_PHASE_DURATION - elapsed)
                        self.log(f"  (attack in {remaining}s)")
                        self.send_normal_data()

                    last_data_send = now

                time.sleep(0.1)

            except KeyboardInterrupt:
                self.log("")
                self.log("🛑 Shutting down virtual attacker...")
                self.log(f"   Total packets: {self.packets_sent}")
                self.log(f"   Attack packets: {self.attack_packets_sent}")
                self.log(f"   Accepted: {self.accepted_count}")
                self.log(f"   Rejected: {self.rejected_count}")
                sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Virtual ESP32 Attacker Simulator")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Controller IP")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Controller port")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="Device ID")
    args = parser.parse_args()

    attacker = VirtualAttacker(args.server, args.port, args.device_id)
    attacker.run()


if __name__ == "__main__":
    main()
