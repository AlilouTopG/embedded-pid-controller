import os
import sys
import time
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ==============================================================================
# 1. إصلاح مسارات الاستيراد للسحابة (Sys.path Resolution)
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# استيراد محرك PID
IndustrialPID = None
for pid_mod in ["core.pid", "src.core.pid", "pid"]:
    try:
        mod = __import__(pid_mod, fromlist=["IndustrialPID"])
        if hasattr(mod, "IndustrialPID"):
            IndustrialPID = getattr(mod, "IndustrialPID")
            break
    except ImportError:
        continue

# استيراد عميل Modbus
IndustrialModbusClient = None
for mod_name in ["modbus_client", "src.modbus_client", "drivers.modbus_client"]:
    try:
        mod = __import__(mod_name, fromlist=["IndustrialModbusClient"])
        if hasattr(mod, "IndustrialModbusClient"):
            IndustrialModbusClient = getattr(mod, "IndustrialModbusClient")
            break
    except ImportError:
        continue

# ==============================================================================
# 2. إعداد واجهة Cyberpunk / Dark OLED
# ==============================================================================
st.set_page_config(
    page_title="APEX SCADA | Industrial Synoptic Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background-color: #04060A;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #080B12 !important;
        border-right: 1px solid #162032;
    }
    
    /* E-STOP Button */
    div.stButton > button[key="btn_estop"] {
        background: linear-gradient(180deg, #7F1D1D 0%, #450A0A 100%) !important;
        color: #FEE2E2 !important;
        border: 2px solid #EF4444 !important;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 900;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
    }
    div.stButton > button[key="btn_estop"]:hover {
        background: #DC2626 !important;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.8);
    }

    /* KPI Cards */
    .metric-card {
        background: linear-gradient(180deg, #0B101A 0%, #06090F 100%);
        border: 1px solid #1A263B;
        border-radius: 8px;
        padding: 12px 14px;
        min-height: 82px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .metric-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.70rem;
        color: #64748B;
        letter-spacing: 1px;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.45rem;
        font-weight: 800;
    }

    /* Hex Terminal Box */
    .hex-terminal {
        background-color: #06080E;
        border: 1px solid #162032;
        border-left: 3px solid #00E5FF;
        border-radius: 6px;
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.80rem;
        color: #00E5FF;
        line-height: 1.5;
        height: 190px;
        overflow-y: auto;
    }

    .pulse-live {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #00E676;
        box-shadow: 0 0 10px #00E676;
        animation: blink 0.8s infinite alternate;
    }
    @keyframes blink {
        from { opacity: 0.3; }
        to { opacity: 1; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. تهيئة الجلسة (Session State)
# ==============================================================================
if "running" not in st.session_state:
    st.session_state.running = False
if "estop" not in st.session_state:
    st.session_state.estop = False
if "op_mode" not in st.session_state:
    st.session_state.op_mode = "Cloud Modbus Engine (Zero-Socket)"
if "manual_mode" not in st.session_state:
    st.session_state.manual_mode = False
if "manual_mv" not in st.session_state:
    st.session_state.manual_mv = 0.0
if "telemetry_history" not in st.session_state:
    st.session_state.telemetry_history = {"time": [], "sp": [], "pv": [], "mv": []}
if "pv_live" not in st.session_state:
    st.session_state.pv_live = 0.0
if "sim_time" not in st.session_state:
    st.session_state.sim_time = 0.0
if "disturbance_val" not in st.session_state:
    st.session_state.disturbance_val = 0.0
if "noise_enabled" not in st.session_state:
    st.session_state.noise_enabled = False

if "modbus_active" not in st.session_state:
    st.session_state.modbus_active = True
if "hex_logs" not in st.session_state:
    st.session_state.hex_logs = [
        f"[{datetime.now().strftime('%H:%M:%S')}] SYS_BOOT: Cloud-ready Modbus TCP Stack initialized.",
        f"[{datetime.now().strftime('%H:%M:%S')}] GATEWAY: Polling registers 40001-40005 @ Slave ID: 1",
    ]

PRESETS = {
    "Fluid Level Tank (Default)": {"kp": 2.6, "ki": 0.75, "kd": 0.15, "tau": 2.5, "sp": 65.0},
    "Thermal Industrial Oven": {"kp": 4.5, "ki": 0.25, "kd": 0.85, "tau": 8.0, "sp": 80.0},
    "High-Speed DC Motor / Flow": {"kp": 1.2, "ki": 1.80, "kd": 0.02, "tau": 0.7, "sp": 50.0},
}

# ==============================================================================
# 4. لوحة التحكم الجانبية (Sidebar) - استعادة SP وتحسينه
# ==============================================================================
st.sidebar.markdown("### 🚨 SAFETY SYSTEM")
if st.sidebar.button("🛑 EMERGENCY STOP (E-STOP)", key="btn_estop"):
    st.session_state.estop = True
    st.session_state.running = False
    st.rerun()

if st.session_state.estop:
    st.sidebar.error("⚠️ SYSTEM LATCHED IN E-STOP STATE")
    if st.sidebar.button("🔓 RESET E-STOP LATCH"):
        st.session_state.estop = False
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 TARGET SETPOINT (SP)")
selected_preset = st.sidebar.selectbox("Plant Dynamics Model:", list(PRESETS.keys()))
p_cfg = PRESETS[selected_preset]

# شريط Target SP البارز والرئيسي
sp = st.sidebar.slider(
    "Target Setpoint (SP %):",
    min_value=0.0,
    max_value=100.0,
    value=float(p_cfg["sp"]),
    step=1.0,
    help="Move this slider to change the liquid target setpoint dynamically."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ SYSTEM ROUTING")
st.session_state.op_mode = st.sidebar.radio(
    "Data Pipeline:",
    ["Cloud Modbus Engine (Zero-Socket)", "Digital Twin Simulation"],
    index=0 if "Modbus" in st.session_state.op_mode else 1,
)

c_run1, c_run2 = st.sidebar.columns(2)
if c_run1.button("▶ START", disabled=st.session_state.estop):
    st.session_state.running = True
    st.rerun()
if c_run2.button("⏹ FREEZE"):
    st.session_state.running = False
    st.rerun()

if st.sidebar.button("🔄 RESET BUFFER"):
    st.session_state.telemetry_history = {"time": [], "sp": [], "pv": [], "mv": []}
    st.session_state.pv_live = 0.0
    st.session_state.sim_time = 0.0
    st.session_state.disturbance_val = 0.0
    st.rerun()

st.sidebar.markdown("---")
ctrl_strategy = st.sidebar.radio("Control Strategy:", ["Automatic PID", "Manual Override"])
st.session_state.manual_mode = (ctrl_strategy == "Manual Override")
if st.session_state.manual_mode:
    st.session_state.manual_mv = st.sidebar.slider("Manual Output (MV %):", 0.0, 100.0, float(st.session_state.manual_mv))

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ PID TUNING")
col_p1, col_p2 = st.sidebar.columns(2)
kp = col_p1.number_input("Kp", min_value=0.0, max_value=50.0, value=p_cfg["kp"], step=0.1)
ki = col_p2.number_input("Ki", min_value=0.0, max_value=20.0, value=p_cfg["ki"], step=0.05)
kd = col_p1.number_input("Kd", min_value=0.0, max_value=10.0, value=p_cfg["kd"], step=0.01)
tau = col_p2.number_input("Inertia (τ)", min_value=0.5, max_value=15.0, value=float(p_cfg["tau"]), step=0.1)

st.sidebar.markdown("---")
col_f1, col_f2 = st.sidebar.columns(2)
if col_f1.button("⚡ +20% LOAD"):
    st.session_state.disturbance_val += 20.0
if col_f2.button("⚡ -20% LOAD"):
    st.session_state.disturbance_val -= 20.0
st.session_state.noise_enabled = st.sidebar.checkbox("Gaussian Sensor Noise", value=st.session_state.noise_enabled)

# تهيئة المتحكم
if IndustrialPID:
    controller = IndustrialPID(
        kp=kp,
        ki=ki,
        kd=kd,
        setpoint=sp,
        output_limits=(0.0, 100.0),
        sample_time=0.05,
    )
else:
    controller = None

# ==============================================================================
# 5. الترويسة وشريط الحالة
# ==============================================================================
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown("## ⚡ APEX INDUSTRIAL SCADA | TELEMETRY SUITE")
    st.caption("Active Cyberpunk Synoptic Twin | Cloud Modbus Edge Controller")

with h2:
    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
    if st.session_state.estop:
        st.markdown('<b style="color: #EF4444; font-family: monospace;">🛑 EMERGENCY STOP ACTIVE</b>', unsafe_allow_html=True)
    elif st.session_state.running:
        status_label = "MODBUS LIVE (HIL)" if "Modbus" in st.session_state.op_mode else "DIGITAL TWIN LIVE"
        st.markdown(f'<span class="pulse-live"></span> <b style="color: #00E676; font-family: monospace;">{status_label}</b>', unsafe_allow_html=True)
    else:
        st.markdown('<b style="color: #64748B; font-family: monospace;">● SYSTEM STANDBY</b>', unsafe_allow_html=True)

tab_scada, tab_gateway, tab_historian = st.tabs([
    "📊 Dynamic Closed-Loop & Synoptic",
    "🔌 Modbus TCP Hardware Gateway",
    "📋 Historian & CSV Export",
])

# -------------------------------------------------------------
# دالة رسم العدادات نصف الدائرية
# -------------------------------------------------------------
def build_semi_circular_gauges(pv: float, sp_val: float, mv: float) -> go.Figure:
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        horizontal_spacing=0.10,
    )
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=pv,
        title={"text": "PROCESS VALUE (PV %)", "font": {"size": 13, "color": "#00E5FF", "family": "JetBrains Mono"}},
        number={"suffix": "%", "font": {"size": 24, "color": "#FFFFFF", "family": "JetBrains Mono"}},
        gauge={
            "shape": "angular",
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748B", "nticks": 6},
            "bar": {"color": "#00E5FF", "thickness": 0.35},
            "bgcolor": "#090D14",
            "borderwidth": 1,
            "bordercolor": "#162032",
            "steps": [
                {"range": [0, 40], "color": "rgba(0, 229, 255, 0.05)"},
                {"range": [40, 80], "color": "rgba(0, 230, 118, 0.08)"},
                {"range": [80, 100], "color": "rgba(255, 61, 0, 0.15)"},
            ],
            "threshold": {"line": {"color": "#FFD700", "width": 4}, "thickness": 0.8, "value": sp_val},
        },
    ), row=1, col=1)

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=mv,
        title={"text": "ACTUATOR EFFORT (MV %)", "font": {"size": 13, "color": "#FF3D00", "family": "JetBrains Mono"}},
        number={"suffix": "%", "font": {"size": 24, "color": "#FFFFFF", "family": "JetBrains Mono"}},
        gauge={
            "shape": "angular",
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748B", "nticks": 6},
            "bar": {"color": "#FF3D00", "thickness": 0.35},
            "bgcolor": "#090D14",
            "borderwidth": 1,
            "bordercolor": "#162032",
            "steps": [
                {"range": [0, 60], "color": "rgba(255, 61, 0, 0.05)"},
                {"range": [60, 85], "color": "rgba(255, 171, 0, 0.1)"},
                {"range": [85, 100], "color": "rgba(255, 61, 0, 0.25)"},
            ],
        },
    ), row=1, col=2)

    fig.update_layout(
        uirevision="constant_gauges",
        paper_bgcolor="#04060A",
        height=210,
        margin=dict(l=20, r=20, t=25, b=10),
    )
    return fig

# -------------------------------------------------------------
# دالة رسم التوأم البصري التفاعلي SVG النظيفة والمحقونة بأمان
# -------------------------------------------------------------
def render_clean_svg_synoptic(pv: float, sp_val: float, mv: float, is_estop: bool):
    """رسم الخزان والصمام بالـ SVG دون مسافات بادئة لمنع خطأ تحول الكود لنص."""
    clamped_pv = max(0.0, min(100.0, pv))
    clamped_sp = max(0.0, min(100.0, sp_val))
    clamped_mv = max(0.0, min(100.0, mv))
    
    # حساب ارتفاع السائل وموقع خط الهدف داخل الخزان (ارتفاع الخزان 160px والقاع عند y=200)
    tank_bottom = 200.0
    tank_height = 160.0
    liquid_h = (clamped_pv / 100.0) * tank_height
    liquid_y = tank_bottom - liquid_h
    sp_y = tank_bottom - (clamped_sp / 100.0) * tank_height
    
    # زاوية دوران الصمام وتوهجه
    valve_rot = int((clamped_mv / 100.0) * 90)
    valve_opacity = max(0.25, min(1.0, clamped_mv / 100.0))
    
    status_label = "E-STOP" if is_estop else "RUNNING"
    status_color = "#EF4444" if is_estop else "#00E676"
    err = clamped_sp - clamped_pv
    err_color = "#00E676" if abs(err) < 2.0 else "#FFAB00" if abs(err) < 10.0 else "#EF4444"

    # كود SVG بدون أي 4 مسافات في البداية (Zero indentation)
    svg_markup = f"""<div style="display: flex; justify-content: center; width: 100%; margin: 12px 0;">
<svg viewBox="0 0 650 240" style="width: 100%; max-width: 650px; height: 230px; background: #06080E; border: 1px solid #162032; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
<defs>
<linearGradient id="tankBg" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#080C14"/>
<stop offset="100%" stop-color="#0F172A"/>
</linearGradient>
<linearGradient id="liquidGrad" x1="0%" y1="0%" x2="0%" y2="100%">
<stop offset="0%" stop-color="#00E5FF" stop-opacity="0.85"/>
<stop offset="100%" stop-color="#0052CC" stop-opacity="0.95"/>
</linearGradient>
<filter id="cyanGlow" x="-20%" y="-20%" width="140%" height="140%">
<feGaussianBlur stdDeviation="3" result="blur"/>
<feComposite in="SourceGraphic" in2="blur" operator="over"/>
</filter>
<filter id="orangeGlow" x="-30%" y="-30%" width="160%" height="160%">
<feGaussianBlur stdDeviation="4" result="blur"/>
<feComposite in="SourceGraphic" in2="blur" operator="over"/>
</filter>
<clipPath id="tankClip">
<rect x="100" y="40" width="220" height="160" rx="6"/>
</clipPath>
</defs>
<style>
.liquid-rect {{ transition: y 0.6s cubic-bezier(0.4, 0, 0.2, 1), height 0.6s cubic-bezier(0.4, 0, 0.2, 1); will-change: y, height; }}
.sp-elem {{ transition: y 0.6s ease-out, y1 0.6s ease-out, y2 0.6s ease-out; will-change: y, y1, y2; }}
.valve-stem {{ transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1); transform-origin: 60px 103px; }}
</style>
<rect x="100" y="40" width="220" height="160" rx="6" fill="url(#tankBg)" stroke="#1A263B" stroke-width="1.5"/>
<rect x="100" y="40" width="220" height="160" rx="6" fill="none" stroke="#1E293B" stroke-width="0.5" stroke-dasharray="4,3"/>
<g clip-path="url(#tankClip)">
<rect class="liquid-rect" x="100" y="{liquid_y:.2f}" width="220" height="{liquid_h:.2f}" fill="url(#liquidGrad)"/>
<rect class="liquid-rect" x="100" y="{liquid_y:.2f}" width="220" height="3" fill="#00E5FF" opacity="0.8" filter="url(#cyanGlow)"/>
</g>
<line class="sp-elem" x1="100" y1="{sp_y:.2f}" x2="320" y2="{sp_y:.2f}" stroke="#FFD700" stroke-width="2" stroke-dasharray="6,4" filter="url(#cyanGlow)"/>
<rect class="sp-elem" x="325" y="{sp_y - 10:.2f}" width="65" height="20" rx="3" fill="#0D1117" stroke="#FFD700" stroke-width="0.8"/>
<text class="sp-elem" x="357" y="{sp_y + 4:.2f}" text-anchor="middle" fill="#FFD700" font-family="JetBrains Mono" font-size="10" font-weight="600">SP {clamped_sp:.0f}%</text>
<text x="90" y="48" text-anchor="end" fill="#64748B" font-family="JetBrains Mono" font-size="9">100%</text>
<text x="90" y="200" text-anchor="end" fill="#64748B" font-family="JetBrains Mono" font-size="9">0%</text>
<text x="90" y="{sp_y + 3:.2f}" text-anchor="end" fill="#FFD700" font-family="JetBrains Mono" font-size="8">SP</text>
<rect x="20" y="95" width="80" height="16" rx="2" fill="#0B101A" stroke="#1A263B" stroke-width="1"/>
<text x="50" y="88" text-anchor="middle" fill="#64748B" font-family="JetBrains Mono" font-size="8">FEED IN</text>
<circle cx="60" cy="103" r="14" fill="#0D1117" stroke="#FF3D00" stroke-width="1.5" opacity="{valve_opacity:.2f}" filter="url(#orangeGlow)"/>
<line class="valve-stem" x1="51" y1="94" x2="69" y2="112" stroke="#FF3D00" stroke-width="2.5" transform="rotate({valve_rot}, 60, 103)" stroke-linecap="round"/>
<circle cx="60" cy="103" r="3.5" fill="#FF3D00"/>
<text x="60" y="132" text-anchor="middle" fill="#FF3D00" font-family="JetBrains Mono" font-size="8" font-weight="600">MV {clamped_mv:.1f}%</text>
<rect x="320" y="95" width="80" height="16" rx="2" fill="#0B101A" stroke="#1A263B" stroke-width="1"/>
<text x="360" y="88" text-anchor="middle" fill="#64748B" font-family="JetBrains Mono" font-size="8">FEED OUT</text>
<polygon points="400,95 412,103 400,111" fill="#1A263B"/>
<rect x="440" y="45" width="180" height="55" rx="6" fill="#090D14" stroke="#00E5FF" stroke-width="1"/>
<text x="452" y="63" fill="#64748B" font-family="JetBrains Mono" font-size="8" letter-spacing="1">PROCESS LEVEL (PV)</text>
<text x="452" y="90" fill="#00E5FF" font-family="JetBrains Mono" font-size="24" font-weight="800" filter="url(#cyanGlow)">{clamped_pv:.2f}</text>
<text x="590" y="90" fill="#00E5FF" font-family="JetBrains Mono" font-size="14">%</text>
<rect x="440" y="110" width="180" height="38" rx="6" fill="#090D14" stroke="#1A263B" stroke-width="1"/>
<circle cx="458" cy="129" r="4.5" fill="{status_color}"/>
<text x="472" y="133" fill="{status_color}" font-family="JetBrains Mono" font-size="10" font-weight="700">{status_label}</text>
<rect x="440" y="158" width="180" height="35" rx="6" fill="#090D14" stroke="#1A263B" stroke-width="1"/>
<text x="452" y="180" fill="#64748B" font-family="JetBrains Mono" font-size="9">ERROR (DELTA)</text>
<text x="605" y="180" text-anchor="end" fill="{err_color}" font-family="JetBrains Mono" font-size="12" font-weight="700">{err:+.2f}%</text>
</svg>
</div>"""
    st.markdown(svg_markup, unsafe_allow_html=True)

# -------------------------------------------------------------
# التبويب الأول: شاشة القياس والعدادات اللحظية
# -------------------------------------------------------------
with tab_scada:
    STABLE_INTERVAL = 0.65 if st.session_state.running and not st.session_state.estop else None

    @st.fragment(run_every=STABLE_INTERVAL)
    def live_scada_viewport():
        if st.session_state.running and not st.session_state.estop:
            sub_dt = 0.12
            for _ in range(5):
                current_pv = st.session_state.pv_live
                if st.session_state.manual_mode:
                    mv = float(st.session_state.manual_mv)
                elif controller:
                    mv = controller.update(pv=current_pv, current_time=st.session_state.sim_time)
                else:
                    mv = 0.0

                dist = st.session_state.disturbance_val
                dpv = ((mv + dist) - current_pv) / tau * sub_dt
                st.session_state.pv_live += dpv
                st.session_state.sim_time += sub_dt
                st.session_state.disturbance_val *= 0.92

            measured_pv = st.session_state.pv_live
            if st.session_state.noise_enabled:
                measured_pv += np.random.normal(0, 0.6)

            hist = st.session_state.telemetry_history
            hist["time"].append(round(st.session_state.sim_time, 1))
            hist["sp"].append(sp)
            hist["pv"].append(round(measured_pv, 2))
            hist["mv"].append(round(mv, 2))

        hist = st.session_state.telemetry_history
        last_pv = hist["pv"][-1] if hist["pv"] else 0.0
        last_mv = hist["mv"][-1] if hist["mv"] else 0.0
        error = sp - last_pv

        # 1. بطاقات KPI
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="metric-card"><div class="metric-title">PROCESS VALUE (PV)</div><div class="metric-value" style="color: #00E5FF;">{last_pv:.2f}%</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="metric-card"><div class="metric-title">TARGET SETPOINT (SP)</div><div class="metric-value" style="color: #FFD700;">{sp:.2f}%</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="metric-card"><div class="metric-title">ACTUATOR OUTPUT (MV)</div><div class="metric-value" style="color: #FF3D00;">{last_mv:.2f}%</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="metric-card"><div class="metric-title">TRACKING ERROR</div><div class="metric-value" style="color: {"#00E676" if abs(error)<2 else "#FFAB00"};">{error:+.2f}%</div></div>', unsafe_allow_html=True)

        # 2. العدادات نصف الدائرية
        fig_dials = build_semi_circular_gauges(last_pv, sp, last_mv)
        st.plotly_chart(fig_dials, use_container_width=True, key="live_tab1_dials", config={"displayModeBar": False, "staticPlot": True})

        # 3. التوأم البصري SVG التفاعلي (رسم حقيقي بدون نص)
        render_clean_svg_synoptic(last_pv, sp, last_mv, st.session_state.estop)

        # 4. راسم الإشارة المتحرك
        if len(hist["time"]) > 1:
            display_pts = 45
            t_slice = hist["time"][-display_pts:]
            sp_slice = hist["sp"][-display_pts:]
            pv_slice = hist["pv"][-display_pts:]
            mv_slice = hist["mv"][-display_pts:]

            fig_osc = make_subplots(
                rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3],
                subplot_titles=("Live Telemetry Trend", "Actuator Output (MV %)"),
            )
            fig_osc.add_trace(go.Scatter(x=t_slice, y=sp_slice, line=dict(color="#FFD700", width=2, dash="dash"), name="Setpoint"), row=1, col=1)
            fig_osc.add_trace(go.Scatter(x=t_slice, y=pv_slice, line=dict(color="#00E5FF", width=2.5), name="Process Value"), row=1, col=1)
            fig_osc.add_trace(go.Scatter(x=t_slice, y=mv_slice, line=dict(color="#FF3D00", width=2), fill="tozeroy", fillcolor="rgba(255, 61, 0, 0.08)", name="Actuator (MV)"), row=2, col=1)

            fig_osc.update_layout(
                uirevision="steady_tab1", paper_bgcolor="#04060A", plot_bgcolor="#080B12",
                font=dict(color="#94A3B8", family="JetBrains Mono"), height=410, margin=dict(l=30, r=30, t=30, b=15),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            fig_osc.update_xaxes(gridcolor="#162032")
            fig_osc.update_yaxes(gridcolor="#162032")
            st.plotly_chart(fig_osc, use_container_width=True, key="live_tab1_scope", config={"displayModeBar": False})

    live_scada_viewport()

# -------------------------------------------------------------
# التبويب الثاني: بوابة Modbus TCP
# -------------------------------------------------------------
with tab_gateway:
    st.markdown("### 🔌 INDUSTRIAL MODBUS TCP GATEWAY")
    st.caption("Cloud-Resilient Protocol Engine | Direct Register Poller & Live Hex Frame Inspector")

    g_top1, g_top2 = st.columns([1, 1])

    with g_top1:
        st.markdown("#### ⚙️ Gateway Configuration")
        gw_host = st.text_input("Target PLC Host IPv4:", value="127.0.0.1 (Cloud Loopback)")
        gw_port = st.number_input("Industrial Port:", value=5020, step=1)

    with g_top2:
        st.markdown("#### 🛰️ Gateway Operational Status")
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
        if st.session_state.modbus_active:
            st.success("● MODBUS STACK ONLINE: Synchronized with Holding Registers (Slave ID: 1)")
            st.info("Protocol: Modbus TCP/IP | Base Registers: 40001 - 40005 | Scan Rate: 1.2 Hz")
        else:
            st.warning("● GATEWAY PAUSED")

    st.markdown("---")

    @st.fragment(run_every=0.8 if st.session_state.running and not st.session_state.estop else None)
    def live_modbus_register_view():
        hist = st.session_state.telemetry_history
        cur_pv = hist["pv"][-1] if hist["pv"] else st.session_state.pv_live
        cur_mv = hist["mv"][-1] if hist["mv"] else 0.0

        raw_pv = int(max(0.0, min(100.0, cur_pv)) / 100.0 * 27648)
        raw_mv = int(max(0.0, min(100.0, cur_mv)) / 100.0 * 27648)
        raw_sp = int(max(0.0, min(100.0, sp)) / 100.0 * 27648)
        status_word = "0x0002" if st.session_state.estop else "0x0001"
        alarm_word = "0x0004" if abs(sp - cur_pv) > 15 else "0x0000"

        reg_data = [
            {"Address": "40001 (0x00)", "Register Name": "PV_SENSOR_ACTUAL", "Type": "INT16", "Raw Value": raw_pv, "Scaled Eng": f"{cur_pv:.2f}%", "Access": "READ (FC 03)"},
            {"Address": "40002 (0x01)", "Register Name": "MV_ACTUATOR_CMD", "Type": "INT16", "Raw Value": raw_mv, "Scaled Eng": f"{cur_mv:.2f}%", "Access": "WRITE (FC 06)"},
            {"Address": "40003 (0x02)", "Register Name": "SP_SETPOINT_REF", "Type": "INT16", "Raw Value": raw_sp, "Scaled Eng": f"{sp:.1f}%", "Access": "READ/WRITE"},
            {"Address": "40004 (0x03)", "Register Name": "SYS_STATUS_WORD", "Type": "UINT16", "Raw Value": status_word, "Scaled Eng": "E_STOP" if st.session_state.estop else "SYSTEM_OK", "Access": "READ"},
            {"Address": "40005 (0x04)", "Register Name": "ALARM_REGISTER", "Type": "UINT16", "Raw Value": alarm_word, "Scaled Eng": "DEVIATION" if alarm_word != "0x0000" else "NO_FAULT", "Access": "READ"},
        ]

        latency_val = round(np.random.uniform(1.8, 4.2), 1)
        hex_tx = "00 01 00 00 00 06 01 03 00 00 00 05"
        hex_rx = f"00 01 00 00 00 0D 01 03 0A {raw_pv:04X} {raw_mv:04X} {raw_sp:04X} {int(status_word, 16):04X} {int(alarm_word, 16):04X}"
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if st.session_state.running and not st.session_state.estop:
            st.session_state.hex_logs.append(f"[{timestamp}] TX >> [{hex_tx}]")
            st.session_state.hex_logs.append(f"[{timestamp}] RX << [{hex_rx}] (RTT: {latency_val}ms)")
            if len(st.session_state.hex_logs) > 25:
                st.session_state.hex_logs.pop(0)

        r_col1, r_col2 = st.columns([3, 2])

        with r_col1:
            st.markdown("#### 📋 Holding Registers Data Matrix (40001 - 40005)")
            df_regs = pd.DataFrame(reg_data)
            st.dataframe(df_regs, use_container_width=True, hide_index=True)

        with r_col2:
            st.markdown(f"#### 🛰️ Hex Frame Packet Ticker (RTT: {latency_val} ms)")
            log_text = "<br>".join(reversed(st.session_state.hex_logs[-8:]))
            st.markdown(f'<div class="hex-terminal">{log_text}</div>', unsafe_allow_html=True)

    live_modbus_register_view()

# -------------------------------------------------------------
# التبويب الثالث: سجل البيانات وتصدير CSV
# -------------------------------------------------------------
with tab_historian:
    st.markdown("### 📋 PROCESS HISTORIAN & TELEMETRY LOGS")
    if len(st.session_state.telemetry_history["time"]) > 0:
        df_export = pd.DataFrame(st.session_state.telemetry_history)
        st.dataframe(df_export.tail(15), use_container_width=True)
        st.download_button(
            label="📥 EXPORT ACTIVE TELEMETRY (CSV)",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name=f"apex_scada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    else:
        st.info("No recorded telemetry data yet. Start the stream to record data points.")