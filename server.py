"""
Wandering Patient Alert System — Professional Clinical Dashboard
ESP32 + IR Sensor · Real-time Monitoring · Multi-Page Analytics
"""

import streamlit as st
import serial
import serial.tools.list_ports
import json
from datetime import datetime, timedelta
import time
import warnings
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from collections import deque
import random
import math

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="MediWatch Pro — Patient Alert System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: linear-gradient(135deg, #050d1a 0%, #0a1628 40%, #071222 100%);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071222 0%, #0d1f3c 100%);
    border-right: 1px solid #1a3a5c;
}
[data-testid="stSidebar"] * { color: #cdd9e8 !important; }
[data-testid="stSidebarNav"] { padding-top: 0; }

/* Hide default header */
#MainMenu, footer, header { visibility: hidden; }

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d1f3c 0%, #122540 100%);
    border: 1px solid #1a3a5c;
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 4px 24px rgba(0,200,255,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(0,200,255,0.14);
    border-color: #00c8ff44;
}
[data-testid="stMetricLabel"] > div { color: #7fb3d3 !important; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }
[data-testid="stMetricValue"] > div { color: #e8f4ff !important; font-size: 2rem; font-weight: 700; }
[data-testid="stMetricDelta"] > div { font-size: 0.8rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #071222;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #1a3a5c;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #7fb3d3;
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 8px 18px;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #00c8ff22, #0066ff22) !important;
    color: #00c8ff !important;
    border: 1px solid #00c8ff44;
}

/* Dividers */
hr { border-color: #1a3a5c; }

/* Text colors */
h1, h2, h3, h4, h5 { color: #e8f4ff !important; }
p, li, label, span { color: #a8c4d9; }

/* Cards */
.kpi-card {
    background: linear-gradient(135deg, #0d1f3c, #0a1a30);
    border: 1px solid #1a3a5c;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.alert-banner {
    background: linear-gradient(135deg, #3d0000, #5a0a0a);
    border: 2px solid #ff3333;
    border-radius: 14px;
    padding: 20px 28px;
    animation: pulse-red 1.5s infinite;
    margin-bottom: 20px;
}
.safe-banner {
    background: linear-gradient(135deg, #003d1a, #005a28);
    border: 2px solid #00cc66;
    border-radius: 14px;
    padding: 20px 28px;
    margin-bottom: 20px;
}
.warn-banner {
    background: linear-gradient(135deg, #3d2800, #5a3c00);
    border: 2px solid #ffaa00;
    border-radius: 14px;
    padding: 20px 28px;
    margin-bottom: 20px;
}
@keyframes pulse-red {
    0%,100% { box-shadow: 0 0 20px #ff333344; }
    50%      { box-shadow: 0 0 40px #ff3333aa; }
}
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-alert  { background: #ff333322; color: #ff6666; border:1px solid #ff333355; }
.badge-warn   { background: #ffaa0022; color: #ffcc44; border:1px solid #ffaa0055; }
.badge-ok     { background: #00cc6622; color: #33ff99; border:1px solid #00cc6655; }
.badge-info   { background: #0066ff22; color: #66aaff; border:1px solid #0066ff55; }
.badge-sys    { background: #9933ff22; color: #bb77ff; border:1px solid #9933ff55; }

.stat-row { display:flex; gap:10px; align-items:center; margin:8px 0; }
.stat-label { color:#7fb3d3; font-size:0.8rem; min-width:130px; }
.stat-val   { color:#e8f4ff; font-weight:600; font-size:0.95rem; }

.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
}
.section-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg,#00c8ff22,#0066ff22);
    border: 1px solid #00c8ff44;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
}

/* Progress bar override */
.stProgress > div > div { background: linear-gradient(90deg,#00c8ff,#0066ff); border-radius:4px; }

/* Log table */
.log-row {
    display: grid;
    grid-template-columns: 90px 1fr 100px;
    gap: 12px;
    padding: 10px 14px;
    border-bottom: 1px solid #1a3a5c22;
    align-items: center;
    transition: background 0.15s;
}
.log-row:hover { background: #0d1f3c88; border-radius: 8px; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #071222; }
::-webkit-scrollbar-thumb { background: #1a3a5c; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00c8ff44; }

/* Sidebar radio labels */
.css-1kyxreq, .css-q8sbsg { color:#cdd9e8 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
DEFAULTS = {
    "log": [],
    "status": "CONNECTING",
    "absent_ms": 0,
    "alert": False,
    "timeline": deque(maxlen=200),
    "timestamps": deque(maxlen=200),
    "event_count": 0,
    "alert_count": 0,
    "return_count": 0,
    "left_count": 0,
    "total_absent_ms": 0,
    "session_start": datetime.now(),
    "last_update": datetime.now(),
    "ser": None,
    "connected_port": None,
    "hourly_events": [0]*24,
    "daily_absent_seconds": deque(maxlen=60),
    "daily_ts": deque(maxlen=60),
    "peak_absent_ms": 0,
    "uptime_start": datetime.now(),
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  SERIAL PORT LOGIC
# ─────────────────────────────────────────────
def get_port():
    for p in serial.tools.list_ports.comports():
        desc = p.description or ""
        if "CP210" in desc or "CH340" in desc:
            return p.device
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return ports[0] if ports else None

if not st.session_state.ser:
    port = get_port()
    if port:
        try:
            st.session_state.ser = serial.Serial(port, 115200, timeout=0.2)
            time.sleep(0.5)
            st.session_state.ser.reset_input_buffer()
            st.session_state.connected_port = port
            st.session_state.log.insert(0, {
                "t": datetime.now().strftime("%H:%M:%S"),
                "m": f"Connected to {port}",
                "type": "sys"
            })
        except Exception:
            st.session_state.ser = None

# ─────────────────────────────────────────────
#  READ SERIAL DATA
# ─────────────────────────────────────────────
if st.session_state.ser:
    try:
        if st.session_state.ser.in_waiting:
            line = st.session_state.ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                d = json.loads(line)
                t = datetime.now().strftime("%H:%M:%S")
                hr = datetime.now().hour

                if "event" in d:
                    evt = d["event"]
                    labels = {
                        "SYSTEM_START":      ("⚙️ System Started", "sys"),
                        "PATIENT_LEFT":      ("🚶 Patient Left Bed", "warn"),
                        "PATIENT_RETURNED":  ("✅ Patient Returned", "ok"),
                        "ALERT_TRIGGERED":   ("🚨 ALERT TRIGGERED", "alert"),
                    }
                    msg, typ = labels.get(evt, (evt, "info"))
                    st.session_state.log.insert(0, {"t": t, "m": msg, "type": typ})
                    st.session_state.event_count += 1
                    st.session_state.hourly_events[hr] += 1
                    if evt == "ALERT_TRIGGERED":
                        st.session_state.alert_count += 1
                    elif evt == "PATIENT_RETURNED":
                        st.session_state.return_count += 1
                    elif evt == "PATIENT_LEFT":
                        st.session_state.left_count += 1

                if "status" in d:
                    st.session_state.status = d["status"]
                    st.session_state.absent_ms = d.get("absent_ms", 0)
                    st.session_state.alert = d.get("alert", False)
                    st.session_state.timeline.append(st.session_state.absent_ms)
                    st.session_state.timestamps.append(t)
                    st.session_state.last_update = datetime.now()
                    if st.session_state.absent_ms > 0:
                        st.session_state.total_absent_ms += st.session_state.absent_ms
                    if st.session_state.absent_ms > st.session_state.peak_absent_ms:
                        st.session_state.peak_absent_ms = st.session_state.absent_ms

                if len(st.session_state.log) > 100:
                    st.session_state.log = st.session_state.log[:100]
    except Exception:
        pass

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def ms_to_str(ms):
    s = ms // 1000
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s:02d}s"
    return f"{m}m {s:02d}s"

def elapsed(dt):
    delta = datetime.now() - dt
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(13,31,60,0.6)",
    font=dict(family="Inter", color="#a8c4d9"),
    margin=dict(l=10, r=10, t=36, b=10),
)

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:2.5rem">🏥</div>
        <div style="font-size:1.15rem; font-weight:800; color:#e8f4ff; letter-spacing:0.02em">MediWatch Pro</div>
        <div style="font-size:0.7rem; color:#7fb3d3; letter-spacing:0.12em; text-transform:uppercase; margin-top:4px">Patient Alert System</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # Connection status
    if st.session_state.ser:
        st.markdown(f"""
        <div style="background:#00cc6611;border:1px solid #00cc6633;border-radius:10px;padding:12px 16px;margin-bottom:12px">
            <span style="color:#33ff99;font-size:0.75rem;font-weight:700;text-transform:uppercase">● CONNECTED</span><br>
            <span style="color:#7fb3d3;font-size:0.8rem">Port: <b style="color:#e8f4ff">{st.session_state.connected_port}</b></span><br>
            <span style="color:#7fb3d3;font-size:0.8rem">Baud: <b style="color:#e8f4ff">115200</b></span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#ff333311;border:1px solid #ff333333;border-radius:10px;padding:12px 16px;margin-bottom:12px">
            <span style="color:#ff6666;font-size:0.75rem;font-weight:700;text-transform:uppercase">● DISCONNECTED</span><br>
            <span style="color:#7fb3d3;font-size:0.75rem">No ESP32 detected</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='color:#7fb3d3;font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin: 10px 0 6px'>Navigation</div>", unsafe_allow_html=True)
    page = st.radio("", [
        "🏠  Dashboard",
        "📈  Analytics",
        "🗂️  Event Log",
        "⚙️  System Info",
        "ℹ️  About",
    ], label_visibility="collapsed")

    st.divider()

    # Quick stats in sidebar
    st.markdown("<div style='color:#7fb3d3;font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px'>Quick Stats</div>", unsafe_allow_html=True)
    stats = [
        ("Uptime",         elapsed(st.session_state.uptime_start)),
        ("Total Events",   str(st.session_state.event_count)),
        ("Alerts Fired",   str(st.session_state.alert_count)),
        ("Times Left Bed", str(st.session_state.left_count)),
        ("Peak Absence",   ms_to_str(st.session_state.peak_absent_ms)),
    ]
    for label, val in stats:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a3a5c33">
            <span style="color:#7fb3d3;font-size:0.78rem">{label}</span>
            <span style="color:#e8f4ff;font-size:0.78rem;font-weight:600">{val}</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"<div style='color:#1a3a5c;font-size:0.68rem;text-align:center'>v2.0.0 · ESP32 + IR Sensor<br>Last update: {st.session_state.last_update.strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PAGE: DASHBOARD
# ─────────────────────────────────────────────
if "Dashboard" in page:
    # ── Header ──
    status = st.session_state.status
    is_alert = st.session_state.alert
    is_absent = "ABSENT" in status

    if is_alert:
        st.markdown("""
        <div class="alert-banner">
            <div style="display:flex;align-items:center;gap:14px">
                <span style="font-size:2rem">🚨</span>
                <div>
                    <div style="color:#ff4444;font-size:1.2rem;font-weight:800;letter-spacing:0.02em">PATIENT ALERT — IMMEDIATE ATTENTION REQUIRED</div>
                    <div style="color:#ff9999;font-size:0.85rem;margin-top:3px">Patient has been absent beyond threshold. Nurse notification sent.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif is_absent:
        st.markdown(f"""
        <div class="warn-banner">
            <div style="display:flex;align-items:center;gap:14px">
                <span style="font-size:2rem">⚠️</span>
                <div>
                    <div style="color:#ffcc44;font-size:1.1rem;font-weight:700">Patient Away from Bed</div>
                    <div style="color:#ffdd88;font-size:0.85rem;margin-top:3px">Monitoring absence duration: {ms_to_str(st.session_state.absent_ms)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="safe-banner">
            <div style="display:flex;align-items:center;gap:14px">
                <span style="font-size:2rem">✅</span>
                <div>
                    <div style="color:#33ff99;font-size:1.1rem;font-weight:700">Patient In Bed — All Normal</div>
                    <div style="color:#88ffcc;font-size:0.85rem;margin-top:3px">IR sensor active · ESP32 monitoring online</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── KPI Row ──
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    status_icon = "🔴" if is_alert else "🟠" if is_absent else "🟢"
    m_abs, s_abs = divmod(st.session_state.absent_ms // 1000, 60)
    peak_m, peak_s = divmod(st.session_state.peak_absent_ms // 1000, 60)

    with c1: st.metric("Patient Status", status_icon, help="Current patient presence status")
    with c2: st.metric("Time Away", f"{m_abs}m {s_abs:02d}s", help="Current continuous absence duration")
    with c3: st.metric("State", "⚠️ ALERT" if is_alert else status, help="System state")
    with c4: st.metric("Total Events", st.session_state.event_count, help="All events since boot")
    with c5: st.metric("🚨 Alerts", st.session_state.alert_count, help="Number of alerts triggered")
    with c6: st.metric("Peak Absence", f"{peak_m}m {peak_s:02d}s", help="Longest recorded absence")

    st.divider()

    # ── Absence Timeline ──
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">📈</div>
            <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Absence Duration Timeline</h3>
        </div>
        """, unsafe_allow_html=True)

        tl = list(st.session_state.timeline)
        ts = list(st.session_state.timestamps)

        if len(tl) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts, y=[v/1000 for v in tl],
                mode='lines',
                name='Absence (s)',
                line=dict(color='#00c8ff', width=2.5, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(0,200,255,0.08)',
                hovertemplate='<b>%{x}</b><br>Away: %{y:.1f}s<extra></extra>'
            ))
            threshold_line = [1.0] * len(tl)  # 1s threshold from firmware
            fig.add_trace(go.Scatter(
                x=ts, y=threshold_line,
                mode='lines',
                name='Alert Threshold (1s)',
                line=dict(color='#ff4444', width=1.5, dash='dot'),
            ))
            fig.update_layout(
                **DARK_LAYOUT,
                height=260,
                xaxis=dict(title="Time", gridcolor="#1a3a5c33"),
                yaxis=dict(title="Seconds Away", gridcolor="#1a3a5c33"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                hovermode='x unified',
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div style="height:220px;display:flex;align-items:center;justify-content:center;
                        background:#0d1f3c;border-radius:12px;border:1px solid #1a3a5c">
                <div style="text-align:center">
                    <div style="font-size:2rem;margin-bottom:8px">📡</div>
                    <div style="color:#7fb3d3;font-size:0.85rem">Awaiting sensor data…</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">🎯</div>
            <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Session Overview</h3>
        </div>
        """, unsafe_allow_html=True)
        total_events = st.session_state.event_count or 1
        alert_pct = round((st.session_state.alert_count / total_events) * 100)

        st.markdown(f"""
        <div class="kpi-card" style="margin-bottom:10px">
            <div style="color:#7fb3d3;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Alert Rate</div>
            <div style="color:#e8f4ff;font-size:1.6rem;font-weight:800">{alert_pct}%</div>
            <div style="color:#7fb3d3;font-size:0.72rem;margin-top:2px">{st.session_state.alert_count} alerts / {total_events} events</div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(min(alert_pct / 100, 1.0))

        st.markdown(f"""
        <div class="kpi-card" style="margin-top:10px">
            <table style="width:100%;border-collapse:collapse">
                <tr><td style="color:#7fb3d3;font-size:0.78rem;padding:5px 0">Session Started</td>
                    <td style="color:#e8f4ff;font-size:0.78rem;font-weight:600;text-align:right">{st.session_state.session_start.strftime('%H:%M:%S')}</td></tr>
                <tr><td style="color:#7fb3d3;font-size:0.78rem;padding:5px 0">Uptime</td>
                    <td style="color:#e8f4ff;font-size:0.78rem;font-weight:600;text-align:right">{elapsed(st.session_state.uptime_start)}</td></tr>
                <tr><td style="color:#7fb3d3;font-size:0.78rem;padding:5px 0">Left Bed</td>
                    <td style="color:#ffcc44;font-size:0.78rem;font-weight:600;text-align:right">{st.session_state.left_count}×</td></tr>
                <tr><td style="color:#7fb3d3;font-size:0.78rem;padding:5px 0">Returned</td>
                    <td style="color:#33ff99;font-size:0.78rem;font-weight:600;text-align:right">{st.session_state.return_count}×</td></tr>
                <tr><td style="color:#7fb3d3;font-size:0.78rem;padding:5px 0">Peak Absence</td>
                    <td style="color:#ff9966;font-size:0.78rem;font-weight:600;text-align:right">{ms_to_str(st.session_state.peak_absent_ms)}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Event Breakdown + Gauge ──
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("""<div class="section-header"><div class="section-icon">🥧</div>
        <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Event Breakdown</h3></div>""", unsafe_allow_html=True)
        labels = ["Alerts", "Left Bed", "Returned"]
        values = [
            max(st.session_state.alert_count, 0),
            max(st.session_state.left_count, 0),
            max(st.session_state.return_count, 0),
        ]
        if sum(values) > 0:
            fig_pie = go.Figure(go.Pie(
                labels=labels, values=values,
                hole=0.6,
                marker=dict(colors=["#ff4444", "#ffaa00", "#00cc66"]),
                textfont=dict(size=11),
            ))
            fig_pie.update_layout(**DARK_LAYOUT, height=240,
                                  showlegend=True,
                                  legend=dict(orientation="h", y=-0.15))
            fig_pie.update_traces(hovertemplate='%{label}: <b>%{value}</b><extra></extra>')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No events recorded yet.")

    with col_b:
        st.markdown("""<div class="section-header"><div class="section-icon">🔵</div>
        <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Absence Gauge</h3></div>""", unsafe_allow_html=True)
        cur_s = st.session_state.absent_ms / 1000
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=cur_s,
            delta={"reference": 1.0, "increasing": {"color": "#ff4444"}, "decreasing": {"color": "#00cc66"}},
            gauge={
                "axis": {"range": [0, 30], "tickcolor": "#7fb3d3"},
                "bar": {"color": "#00c8ff"},
                "steps": [
                    {"range": [0, 1],  "color": "#00cc6622"},
                    {"range": [1, 10], "color": "#ffaa0022"},
                    {"range": [10, 30],"color": "#ff444422"},
                ],
                "threshold": {"line": {"color": "#ff4444", "width": 3}, "thickness": 0.75, "value": 1},
            },
            number={"suffix": "s", "font": {"size": 28, "color": "#e8f4ff"}},
        ))
        fig_gauge.update_layout(**DARK_LAYOUT, height=240)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_c:
        st.markdown("""<div class="section-header"><div class="section-icon">⏱️</div>
        <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Hourly Activity</h3></div>""", unsafe_allow_html=True)
        hours = [f"{h:02d}:00" for h in range(24)]
        counts = st.session_state.hourly_events
        bar_colors = ["#00c8ff" if c == 0 else "#ffaa00" if c < 3 else "#ff4444" for c in counts]
        fig_bar = go.Figure(go.Bar(
            x=hours, y=counts,
            marker_color=bar_colors,
            hovertemplate='%{x}<br>Events: <b>%{y}</b><extra></extra>',
        ))
        fig_bar.update_layout(**DARK_LAYOUT, height=240,
                              xaxis=dict(tickangle=-90, tickfont=dict(size=9)),
                              yaxis=dict(gridcolor="#1a3a5c33"))
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Recent Events strip ──
    st.divider()
    st.markdown("""<div class="section-header"><div class="section-icon">📋</div>
    <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Recent Events</h3></div>""", unsafe_allow_html=True)

    badge_map = {
        "alert": ("badge-alert", "ALERT"),
        "warn":  ("badge-warn",  "WARNING"),
        "ok":    ("badge-ok",    "OK"),
        "info":  ("badge-info",  "INFO"),
        "sys":   ("badge-sys",   "SYSTEM"),
    }
    recent = st.session_state.log[:5]
    if recent:
        for e in recent:
            cls, label = badge_map.get(e["type"], ("badge-info", e["type"].upper()))
            st.markdown(f"""
            <div class="log-row">
                <span style="color:#7fb3d3;font-family:'JetBrains Mono',monospace;font-size:0.8rem">{e['t']}</span>
                <span style="color:#e8f4ff;font-size:0.88rem">{e['m']}</span>
                <span class="badge {cls}">{label}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#7fb3d3;padding:12px 0'>Waiting for first event…</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PAGE: ANALYTICS
# ─────────────────────────────────────────────
elif "Analytics" in page:
    st.markdown("## 📈 Analytics & Insights")
    st.markdown("<div style='color:#7fb3d3;margin-bottom:24px'>Deep-dive into patient monitoring trends, comparisons, and pattern analysis.</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Trend Analysis", "🔥 Heatmap & Distribution", "📐 Statistics"])

    with tab1:
        st.markdown("### Absence Duration Over Time")
        tl = list(st.session_state.timeline)
        ts = list(st.session_state.timestamps)

        if len(tl) > 2:
            # Dual-axis chart
            fig_dual = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                                     subplot_titles=("Absence Duration (seconds)", "Cumulative Events"))
            fig_dual.add_trace(go.Scatter(
                x=ts, y=[v/1000 for v in tl],
                fill='tozeroy', fillcolor='rgba(0,200,255,0.1)',
                line=dict(color='#00c8ff', width=2),
                name='Absence (s)'
            ), row=1, col=1)
            cumulative = list(range(1, len(tl)+1))
            fig_dual.add_trace(go.Scatter(
                x=ts, y=cumulative,
                line=dict(color='#9933ff', width=2),
                name='Cumulative',
            ), row=2, col=1)
            fig_dual.update_layout(**DARK_LAYOUT, height=420,
                                   showlegend=True,
                                   paper_bgcolor="rgba(0,0,0,0)")
            fig_dual.update_yaxes(gridcolor="#1a3a5c33")
            st.plotly_chart(fig_dual, use_container_width=True)
        else:
            st.info("Not enough data collected yet. Keep the system running.")

        st.markdown("### Rolling Average")
        if len(tl) > 5:
            window = 5
            rolling = []
            for i in range(len(tl)):
                chunk = tl[max(0, i-window):i+1]
                rolling.append(sum(chunk)/len(chunk)/1000)
            fig_roll = go.Figure()
            fig_roll.add_trace(go.Scatter(x=ts, y=[v/1000 for v in tl],
                                          line=dict(color='#00c8ff33', width=1),
                                          name='Raw', mode='lines'))
            fig_roll.add_trace(go.Scatter(x=ts, y=rolling,
                                          line=dict(color='#00c8ff', width=2.5),
                                          name='5-pt Avg', mode='lines'))
            fig_roll.update_layout(**DARK_LAYOUT, height=220,
                                   yaxis=dict(title="Seconds", gridcolor="#1a3a5c33"))
            st.plotly_chart(fig_roll, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Hourly Event Heatmap")
            hours = list(range(24))
            h_labels = [f"{h:02d}:00" for h in hours]
            counts = st.session_state.hourly_events
            fig_heat = go.Figure(go.Bar(
                x=h_labels, y=counts,
                marker=dict(
                    color=counts,
                    colorscale=[[0, '#071222'],[0.3,'#1a3a5c'],[0.7,'#0066ff'],[1,'#00c8ff']],
                    showscale=True,
                    colorbar=dict(thickness=10, tickfont=dict(color='#7fb3d3'))
                ),
                hovertemplate='%{x}<br>Events: <b>%{y}</b><extra></extra>',
            ))
            fig_heat.update_layout(**DARK_LAYOUT, height=280,
                                   xaxis=dict(tickangle=-90, tickfont=dict(size=9)),
                                   yaxis=dict(gridcolor="#1a3a5c33"))
            st.plotly_chart(fig_heat, use_container_width=True)

        with col2:
            st.markdown("### Absence Duration Distribution")
            tl = list(st.session_state.timeline)
            if len(tl) > 5:
                fig_hist = go.Figure(go.Histogram(
                    x=[v/1000 for v in tl],
                    nbinsx=20,
                    marker=dict(color='#0066ff', line=dict(color='#00c8ff', width=0.5)),
                    hovertemplate='Range: %{x}s<br>Count: %{y}<extra></extra>',
                ))
                fig_hist.update_layout(**DARK_LAYOUT, height=280,
                                       xaxis=dict(title="Seconds", gridcolor="#1a3a5c33"),
                                       yaxis=dict(title="Frequency", gridcolor="#1a3a5c33"))
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Need more data for distribution.")

        # Scatter
        st.markdown("### Event Index vs Absence Duration")
        tl = list(st.session_state.timeline)
        if len(tl) > 3:
            fig_sc = go.Figure(go.Scatter(
                x=list(range(len(tl))),
                y=[v/1000 for v in tl],
                mode='markers',
                marker=dict(
                    color=[v/1000 for v in tl],
                    colorscale='Teal',
                    size=8, opacity=0.7,
                    line=dict(color='#00c8ff44', width=1),
                ),
                hovertemplate='Point #%{x}<br>Away: %{y:.2f}s<extra></extra>',
            ))
            fig_sc.update_layout(**DARK_LAYOUT, height=220,
                                  xaxis=dict(title="Reading #", gridcolor="#1a3a5c33"),
                                  yaxis=dict(title="Seconds", gridcolor="#1a3a5c33"))
            st.plotly_chart(fig_sc, use_container_width=True)

    with tab3:
        st.markdown("### Statistical Summary")
        tl = list(st.session_state.timeline)
        if len(tl) > 1:
            vals_s = [v/1000 for v in tl if v > 0]
            if vals_s:
                n = len(vals_s)
                mean_v = sum(vals_s)/n
                sorted_v = sorted(vals_s)
                median_v = sorted_v[n//2]
                max_v = max(vals_s)
                min_v = min(vals_s) if vals_s else 0
                variance = sum((x-mean_v)**2 for x in vals_s)/n
                std_v = math.sqrt(variance)

                stat_cols = st.columns(4)
                stat_data = [
                    ("Mean", f"{mean_v:.2f}s"),
                    ("Median", f"{median_v:.2f}s"),
                    ("Std Dev", f"{std_v:.2f}s"),
                    ("Max", f"{max_v:.2f}s"),
                ]
                for col, (lbl, val) in zip(stat_cols, stat_data):
                    with col:
                        st.metric(lbl, val)

                st.markdown(f"""
                <div class="kpi-card" style="margin-top:16px">
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px">
                        <div>
                            <div style="color:#7fb3d3;font-size:0.75rem;text-transform:uppercase;font-weight:700">Total Readings</div>
                            <div style="color:#e8f4ff;font-size:1.1rem;font-weight:700;margin-top:4px">{len(tl)}</div>
                        </div>
                        <div>
                            <div style="color:#7fb3d3;font-size:0.75rem;text-transform:uppercase;font-weight:700">Non-zero Readings</div>
                            <div style="color:#ffcc44;font-size:1.1rem;font-weight:700;margin-top:4px">{len(vals_s)}</div>
                        </div>
                        <div>
                            <div style="color:#7fb3d3;font-size:0.75rem;text-transform:uppercase;font-weight:700">Alert Threshold</div>
                            <div style="color:#ff6666;font-size:1.1rem;font-weight:700;margin-top:4px">1.0s</div>
                        </div>
                        <div>
                            <div style="color:#7fb3d3;font-size:0.75rem;text-transform:uppercase;font-weight:700">Readings > Threshold</div>
                            <div style="color:#ff9966;font-size:1.1rem;font-weight:700;margin-top:4px">{sum(1 for v in vals_s if v>=1)}</div>
                        </div>
                        <div>
                            <div style="color:#7fb3d3;font-size:0.75rem;text-transform:uppercase;font-weight:700">Minimum Absence</div>
                            <div style="color:#33ff99;font-size:1.1rem;font-weight:700;margin-top:4px">{min_v:.2f}s</div>
                        </div>
                        <div>
                            <div style="color:#7fb3d3;font-size:0.75rem;text-transform:uppercase;font-weight:700">Data Range</div>
                            <div style="color:#66aaff;font-size:1.1rem;font-weight:700;margin-top:4px">{max_v-min_v:.2f}s</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No absence data recorded yet.")
        else:
            st.info("Collecting data — please wait.")

# ─────────────────────────────────────────────
#  PAGE: EVENT LOG
# ─────────────────────────────────────────────
elif "Event Log" in page:
    st.markdown("## 🗂️ Full Event Log")
    st.markdown("<div style='color:#7fb3d3;margin-bottom:20px'>Complete chronological record of all patient monitoring events this session.</div>", unsafe_allow_html=True)

    # Filter row
    filter_col, count_col = st.columns([3, 1])
    with filter_col:
        filter_type = st.multiselect(
            "Filter by type",
            ["alert", "warn", "ok", "info", "sys"],
            default=["alert", "warn", "ok", "info", "sys"],
            key="log_filter"
        )
    with count_col:
        st.metric("Total Events", len(st.session_state.log))

    # Header row
    st.markdown("""
    <div style="display:grid;grid-template-columns:90px 1fr 100px;gap:12px;
                padding:10px 14px;border-bottom:2px solid #1a3a5c;margin-bottom:4px">
        <span style="color:#7fb3d3;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em">Time</span>
        <span style="color:#7fb3d3;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em">Message</span>
        <span style="color:#7fb3d3;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em">Type</span>
    </div>
    """, unsafe_allow_html=True)

    badge_map = {
        "alert": ("badge-alert", "ALERT"),
        "warn":  ("badge-warn",  "WARNING"),
        "ok":    ("badge-ok",    "OK"),
        "info":  ("badge-info",  "INFO"),
        "sys":   ("badge-sys",   "SYSTEM"),
    }

    logs = [e for e in st.session_state.log if e["type"] in filter_type]
    if logs:
        for e in logs:
            cls, label = badge_map.get(e["type"], ("badge-info", e["type"].upper()))
            st.markdown(f"""
            <div class="log-row">
                <span style="color:#7fb3d3;font-family:'JetBrains Mono',monospace;font-size:0.8rem">{e['t']}</span>
                <span style="color:#e8f4ff;font-size:0.88rem">{e['m']}</span>
                <span class="badge {cls}">{label}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#7fb3d3">
            <div style="font-size:2.5rem;margin-bottom:12px">📭</div>
            <div>No events match the current filter.</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    # Summary mini-charts below log
    st.markdown("### Event Type Breakdown")
    type_counts = {t: sum(1 for e in st.session_state.log if e["type"]==t) for t in ["alert","warn","ok","info","sys"]}
    labels = list(type_counts.keys())
    values = list(type_counts.values())
    colors = ["#ff4444", "#ffaa00", "#00cc66", "#0066ff", "#9933ff"]
    fig_types = go.Figure(go.Bar(
        x=[l.upper() for l in labels], y=values,
        marker_color=colors,
        text=values, textposition='outside',
        textfont=dict(color='#e8f4ff'),
        hovertemplate='%{x}: <b>%{y}</b><extra></extra>',
    ))
    fig_types.update_layout(**DARK_LAYOUT, height=230,
                            yaxis=dict(gridcolor="#1a3a5c33"),
                            xaxis=dict(gridcolor="transparent"))
    st.plotly_chart(fig_types, use_container_width=True)

# ─────────────────────────────────────────────
#  PAGE: SYSTEM INFO
# ─────────────────────────────────────────────
elif "System Info" in page:
    st.markdown("## ⚙️ System Information")
    st.markdown("<div style='color:#7fb3d3;margin-bottom:24px'>Hardware details, firmware configuration, and connectivity status.</div>", unsafe_allow_html=True)

    col_hw, col_fw = st.columns(2)

    with col_hw:
        st.markdown("""
        <div class="section-header"><div class="section-icon">🔧</div>
        <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Hardware</h3></div>
        """, unsafe_allow_html=True)
        hw_rows = [
            ("Microcontroller", "ESP32 Dev Module"),
            ("Architecture", "Xtensa LX6 Dual-Core"),
            ("Clock Speed", "240 MHz"),
            ("RAM", "320 KB SRAM"),
            ("Flash", "4 MB"),
            ("Sensor", "MH-Series IR Obstacle"),
            ("Sensor Pin", "GPIO 13"),
            ("Sensor Logic", "LOW = In Bed"),
            ("Baud Rate", "115200"),
            ("Framework", "Arduino / PlatformIO"),
        ]
        for lbl, val in hw_rows:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:9px 14px;border-bottom:1px solid #1a3a5c33">
                <span style="color:#7fb3d3;font-size:0.82rem">{lbl}</span>
                <span style="color:#e8f4ff;font-size:0.82rem;font-weight:600;
                             font-family:'JetBrains Mono',monospace">{val}</span>
            </div>
            """, unsafe_allow_html=True)

    with col_fw:
        st.markdown("""
        <div class="section-header"><div class="section-icon">💻</div>
        <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Firmware & Config</h3></div>
        """, unsafe_allow_html=True)
        fw_rows = [
            ("Firmware Version", "v1.0.0"),
            ("Platform", "Espressif32 6.13.0"),
            ("Alert Threshold", "1 000 ms (1 second)"),
            ("Report Interval", "500 ms"),
            ("Protocol", "USB Serial · JSON"),
            ("Event: Left Bed", "JSON {event: PATIENT_LEFT}"),
            ("Event: Returned", "JSON {event: PATIENT_RETURNED}"),
            ("Event: Alert", "JSON {event: ALERT_TRIGGERED}"),
            ("Dashboard Version", "v2.0.0"),
            ("Dashboard Stack", "Streamlit · Plotly"),
        ]
        for lbl, val in fw_rows:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:9px 14px;border-bottom:1px solid #1a3a5c33">
                <span style="color:#7fb3d3;font-size:0.82rem">{lbl}</span>
                <span style="color:#e8f4ff;font-size:0.82rem;font-weight:600;
                             font-family:'JetBrains Mono',monospace">{val}</span>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Connection diagnostics
    st.markdown("""<div class="section-header"><div class="section-icon">🔌</div>
    <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Serial Port Diagnostics</h3></div>""", unsafe_allow_html=True)

    ports = list(serial.tools.list_ports.comports())
    if ports:
        port_cols = st.columns(min(len(ports), 4))
        for i, p in enumerate(ports[:4]):
            with port_cols[i]:
                is_active = (p.device == st.session_state.connected_port)
                border = "#00cc66" if is_active else "#1a3a5c"
                st.markdown(f"""
                <div style="background:#0d1f3c;border:1px solid {border};border-radius:12px;padding:16px">
                    <div style="color:{'#33ff99' if is_active else '#7fb3d3'};font-size:0.7rem;font-weight:700;text-transform:uppercase">
                        {'● ACTIVE' if is_active else '○ AVAILABLE'}
                    </div>
                    <div style="color:#e8f4ff;font-size:1rem;font-weight:700;margin:6px 0">{p.device}</div>
                    <div style="color:#7fb3d3;font-size:0.75rem">{p.description or 'Unknown Device'}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No serial ports detected. Ensure the ESP32 is connected via USB.")

    st.divider()

    # Wiring diagram
    st.markdown("""<div class="section-header"><div class="section-icon">🔗</div>
    <h3 style="margin:0;font-size:1rem;font-weight:700;color:#e8f4ff">Wiring Reference</h3></div>""", unsafe_allow_html=True)

    wiring = [
        ("IR Sensor VCC", "→", "ESP32 3.3V", "#ff6666"),
        ("IR Sensor GND", "→", "ESP32 GND",  "#888888"),
        ("IR Sensor OUT", "→", "ESP32 GPIO 13", "#00c8ff"),
    ]
    for src, arrow, dst, color in wiring:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:10px 16px;
                    background:#0d1f3c;border-radius:10px;margin-bottom:8px;
                    border:1px solid #1a3a5c">
            <span style="color:{color};font-family:'JetBrains Mono',monospace;font-size:0.88rem;min-width:160px">{src}</span>
            <span style="color:#1a3a5c;font-size:1.2rem">{arrow}</span>
            <span style="color:#e8f4ff;font-family:'JetBrains Mono',monospace;font-size:0.88rem">{dst}</span>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PAGE: ABOUT
# ─────────────────────────────────────────────
elif "About" in page:
    st.markdown("## ℹ️ About MediWatch Pro")
    st.markdown("<div style='color:#7fb3d3;margin-bottom:24px'>Project documentation and system architecture overview.</div>", unsafe_allow_html=True)

    col_desc, col_arch = st.columns([3, 2])
    with col_desc:
        st.markdown("""
        <div class="kpi-card">
            <h3 style="color:#e8f4ff;margin-top:0">Wandering Patient Alert System</h3>
            <p style="color:#a8c4d9;line-height:1.7">
                The MediWatch Pro system is a real-time patient-safety solution designed to alert medical staff 
                when a patient unexpectedly leaves their bed. Using an ESP32 microcontroller and an infrared 
                obstacle-avoidance sensor, the system continuously monitors bed occupancy and transmits 
                structured JSON telemetry over USB serial at 500ms intervals.
            </p>
            <p style="color:#a8c4d9;line-height:1.7">
                When the patient is absent for longer than the configured threshold (default: 1 second for demo; 
                adjustable in firmware), an alert event is fired and the dashboard prominently notifies staff via 
                visual indicators and logged events.
            </p>
            <div style="margin-top:16px">
                <span class="badge badge-info" style="margin-right:8px">ESP32</span>
                <span class="badge badge-info" style="margin-right:8px">IR Sensor</span>
                <span class="badge badge-info" style="margin-right:8px">Streamlit</span>
                <span class="badge badge-info" style="margin-right:8px">Plotly</span>
                <span class="badge badge-sys">PlatformIO</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_arch:
        st.markdown("""
        <div class="kpi-card">
            <h4 style="color:#e8f4ff;margin-top:0">Data Flow</h4>
            <div style="display:flex;flex-direction:column;gap:6px">
        """, unsafe_allow_html=True)
        flow = [
            ("🔴", "IR Sensor",         "Detects bed occupancy (LOW = present)"),
            ("🔵", "ESP32 Firmware",    "Reads pin, computes absence time"),
            ("📡", "USB Serial",        "JSON telemetry at 500ms intervals"),
            ("🐍", "Python Server",     "Parses events, updates session state"),
            ("📊", "Streamlit Dashboard","Live charts, alerts, and analytics"),
        ]
        for icon, title, desc in flow:
            st.markdown(f"""
            <div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1a3a5c33">
                <span style="font-size:1.1rem">{icon}</span>
                <div>
                    <div style="color:#e8f4ff;font-size:0.85rem;font-weight:600">{title}</div>
                    <div style="color:#7fb3d3;font-size:0.75rem;margin-top:2px">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style="text-align:center;padding:30px 20px;color:#1a3a5c">
        <div style="font-size:2.5rem;margin-bottom:8px">🏥</div>
        <div style="color:#7fb3d3;font-size:0.85rem">MediWatch Pro v2.0.0 · Built with ESP32 + Python + Streamlit</div>
        <div style="color:#1a3a5c;font-size:0.72rem;margin-top:6px">Real-time IoT Patient Safety Monitoring System</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  AUTO-REFRESH
# ─────────────────────────────────────────────
time.sleep(0.3)
st.rerun()
