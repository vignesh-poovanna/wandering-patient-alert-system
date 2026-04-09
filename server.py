"""Patient Alert Dashboard - Sync Only (No Threads)"""

import streamlit as st
import serial
import serial.tools.list_ports
import json
from datetime import datetime
import time
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Patient Monitor", layout="wide")

# State
if "log" not in st.session_state:
    st.session_state.log = []
    st.session_state.status = "CONNECTING"
    st.session_state.absent_ms = 0
    st.session_state.alert = False

if "ser" not in st.session_state:
    st.session_state.ser = None

# Find port
def get_port():
    all_ports = [p.device for p in serial.tools.list_ports.comports()]
    print(f"[DEBUG] All ports: {all_ports}")
    for p in serial.tools.list_ports.comports():
        desc = p.description or ""
        print(f"[DEBUG] Port {p.device}: {desc}")
        if "CP210" in desc or "CH340" in desc:
            print(f"[DEBUG] Selected: {p.device}")
            return p.device
    if all_ports:
        print(f"[DEBUG] Fallback to first: {all_ports[0]}")
        return all_ports[0]
    print("[DEBUG] No ports found!")
    return None

# Connect
if not st.session_state.ser:
    port = get_port()
    if port:
        try:
            print(f"[DEBUG] Opening {port}...")
            st.session_state.ser = serial.Serial(port, 115200, timeout=0.2)
            time.sleep(1)
            st.session_state.ser.reset_input_buffer()
            print(f"[DEBUG] Connected successfully")
            st.session_state.log.insert(0, {"t": datetime.now().strftime("%H:%M:%S"), "m": f"✓ Connected {port}", "type": "success"})
        except Exception as e:
            print(f"[DEBUG] Connection failed: {e}")
            st.session_state.ser = None
    else:
        print("[DEBUG] No port found to connect")

# Read
if st.session_state.ser:
    try:
        if st.session_state.ser.in_waiting:
            line = st.session_state.ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                d = json.loads(line)
                t = datetime.now().strftime("%H:%M:%S")
                
                if "event" in d:
                    msgs = {
                        "SYSTEM_START": "✓ Started",
                        "PATIENT_LEFT": "👤 Patient left",
                        "PATIENT_RETURNED": "✓ Patient returned",
                        "ALERT_TRIGGERED": "🚨 ALERT!",
                    }
                    msg = msgs.get(d["event"], d["event"])
                    typ = "alert" if "ALERT" in d["event"] else "warning" if "LEFT" in d["event"] else "success" if "RETURNED" in d["event"] else "info"
                    st.session_state.log.insert(0, {"t": t, "m": msg, "type": typ})
                
                if "status" in d:
                    st.session_state.status = d["status"]
                    st.session_state.absent_ms = d.get("absent_ms", 0)
                    st.session_state.alert = d.get("alert", False)
                
                if len(st.session_state.log) > 30:
                    st.session_state.log = st.session_state.log[:30]
    except:
        pass

# UI
st.title("🏥 Patient Alert System")
st.divider()

c1, c2, c3 = st.columns(3)
m, s = divmod(st.session_state.absent_ms // 1000, 60)

with c1:
    if st.session_state.alert:
        st.error("🚨 ALERT")
    elif "ABSENT" in st.session_state.status:
        st.warning("⏱️ ABSENT")
    else:
        st.success("✓ IN BED")

with c2:
    st.metric("Time", f"{m}:{s:02d}")

with c3:
    st.metric("Status", st.session_state.status)

st.divider()
st.subheader("📋 Events")

if st.session_state.log:
    for e in st.session_state.log[:10]:
        txt = f"[{e['t']}] {e['m']}"
        if e["type"] == "alert":
            st.error(txt)
        elif e["type"] == "warning":
            st.warning(txt)
        elif e["type"] == "success":
            st.success(txt)
        else:
            st.info(txt)
else:
    st.info("Waiting...")

time.sleep(0.3)
st.rerun()
