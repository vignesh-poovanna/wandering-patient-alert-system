"""
Wandering Patient Alert System — Serial Bridge
------------------------------------------------
Reads ESP32 JSON data over USB Serial and serves it
to the browser dashboard via a local HTTP server.

Install dependencies:
    pip install pyserial

Run:
    python server.py

Then open: http://localhost:8080
"""

import serial
import serial.tools.list_ports
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────
BAUD_RATE = 115200
HTTP_PORT = 8080
# ──────────────────────────────────────────────────────────────

# Shared state
state = {
    "status": "CONNECTING",
    "absent_ms": 0,
    "alert": False,
    "last_updated": "",
    "log": []          # list of {time, message, type}
}
state_lock = threading.Lock()


def find_esp32_port():
    """Auto-detect ESP32 COM port on Windows."""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = p.description.upper()
        if any(k in desc for k in ["CP210", "CH340", "UART", "USB SERIAL", "SILICON"]):
            return p.device
    # Fallback: return first available port
    if ports:
        return ports[0].device
    return None


def add_log(message, log_type="info"):
    now = datetime.now().strftime("%H:%M:%S")
    entry = {"time": now, "message": message, "type": log_type}
    with state_lock:
        state["log"].insert(0, entry)
        if len(state["log"]) > 50:
            state["log"].pop()


def serial_reader():
    add_log("Connecting to COM3...", "info")
    try:
        ser = serial.Serial("COM3", 115200, timeout=2)
        time.sleep(2)
        add_log("Connected to COM3", "info")

        while True:
            try:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                data = json.loads(line)
                with state_lock:
                    state["last_updated"] = datetime.now().strftime("%H:%M:%S")
                    if "event" in data:
                        ev = data["event"]
                        if ev == "SYSTEM_START":
                            add_log("System started", "info")
                        elif ev == "PATIENT_LEFT":
                            add_log("Patient left the bed", "warning")
                        elif ev == "PATIENT_RETURNED":
                            add_log("Patient returned to bed", "success")
                        elif ev == "ALERT_TRIGGERED":
                            add_log("⚠ ALERT: Patient absent too long!", "alert")
                    if "status" in data:
                        state["status"] = data["status"]
                        state["absent_ms"] = data.get("absent_ms", 0)
                        state["alert"] = data.get("alert", False)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                add_log(f"Read error: {e}", "error")
                time.sleep(1)

    except serial.SerialException as e:
        add_log(f"Cannot open COM3: {e}", "error")
        with state_lock:
            state["status"] = "DISCONNECTED"


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

    def do_GET(self):
        if self.path == "/":
            self.serve_dashboard()
        elif self.path == "/api/state":
            self.serve_state()
        else:
            self.send_error(404)

    def serve_state(self):
        with state_lock:
            data = json.dumps(state)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data.encode())

    def serve_dashboard(self):
        html = open("dashboard.html", "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html)


if __name__ == "__main__":
    print("=" * 50)
    print("  Wandering Patient Alert System")
    print("  Dashboard → http://localhost:8080")
    print("=" * 50)

    # Start serial reader in background
    t = threading.Thread(target=serial_reader, daemon=True)
    t.start()

    # Start HTTP server
    server = HTTPServer(("localhost", HTTP_PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
