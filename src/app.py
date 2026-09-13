import time
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from core.pid import IndustrialPID

# --- Page Configuration ---
st.set_page_config(
    page_title="APEX SCADA | Industrial HMI Station",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Cyberpunk/OLED SCADA Styling ---
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
    
    /* E-STOP Button Style */
    div.stButton > button[key="btn_estop"] {
        background: linear-gradient(180deg, #7F1D1D 0%, #450A0A 100%) !important;
        color: #FEE2E2 !important;
        border: 2px solid #EF4444 !important;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 900;
        font-size: 1rem;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
        transition: 0.2s ease;
    }
    div.stButton > button[key="btn_estop"]:hover {
        background: #DC2626 !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.8);
        transform: scale(1.02);
    }

    /* KPI Metric Cards */
    .metric-card {
        background: linear-gradient(180deg, #0B101A 0%, #06090F 100%);
        border: 1px solid #1A263B;
        border-radius: 8px;
        padding: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .metric-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #64748B;
        letter-spacing: 1px;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 800;
    }
    .pulse-live {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #00E676;
        box-shadow: 0 0 10px #00E676;
        animation: blink 1s infinite alternate;
    }
    @keyframes blink {
        from { opacity: 0.3; }
        to { opacity: 1; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- State Initialization ---
if "running" not in st.session_state:
    st.session_state.running = False
if "estop" not in st.session_state:
    st.session_state.estop = False
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

# --- Plant Presets Dictionary ---
PRESETS = {
    "Fluid Level Tank (Default)": {"kp": 2.6, "ki": 0.75, "kd": 0.15, "tau": 2.5, "sp": 65.0},
    "Thermal Industrial Oven": {"kp": 4.5, "ki": 0.25, "kd": 0.85, "tau": 8.0, "sp": 80.0},
    "High-Speed DC Motor / Flow": {"kp": 1.2, "ki": 1.80, "kd": 0.02, "tau": 0.7, "sp": 50.0},
}

# --- Sidebar Controls ---
st.sidebar.markdown("### 🚨 SAFETY & EMERGENCY")
if st.sidebar.button("🛑 EMERGENCY STOP (E-STOP)", key="btn_estop"):
    st.session_state.estop = True
    st.session_state.running = False
    st.session_state.manual_mv = 0.0
    st.rerun()

if st.session_state.estop:
    st.sidebar.error("⚠️ SYSTEM LATCHED IN E-STOP STATE")
    if st.sidebar.button("🔓 RESET E-STOP LATCH"):
        st.session_state.estop = False
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ RUNTIME CONTROLS")
c_run1, c_run2 = st.sidebar.columns(2)
if c_run1.button("▶ START", disabled=st.session_state.estop):
    st.session_state.running = True
    st.rerun()
if c_run2.button("⏹ FREEZE"):
    st.session_state.running = False
    st.rerun()

if st.sidebar.button("🔄 CLEAR BUFFER & RE-INIT"):
    st.session_state.telemetry_history = {"time": [], "sp": [], "pv": [], "mv": []}
    st.session_state.pv_live = 0.0
    st.session_state.sim_time = 0.0
    st.session_state.disturbance_val = 0.0
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏭 PROCESS PLANT PRESETS")
selected_preset = st.sidebar.selectbox("Select Plant Dynamic Model:", list(PRESETS.keys()))
p_cfg = PRESETS[selected_preset]

# Auto/Manual Mode Switcher
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ OPERATION MODE")
control_mode = st.sidebar.radio("Control Loop Strategy:", ["Automatic PID", "Manual Actuator Override"])
st.session_state.manual_mode = (control_mode == "Manual Actuator Override")

if st.session_state.manual_mode:
    st.session_state.manual_mv = st.sidebar.slider("Manual Output (MV %):", 0.0, 100.0, float(st.session_state.manual_mv))

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ TUNING & TARGETS")
col_p1, col_p2 = st.sidebar.columns(2)
kp = col_p1.number_input("Kp", min_value=0.0, max_value=50.0, value=p_cfg["kp"], step=0.1)
ki = col_p2.number_input("Ki", min_value=0.0, max_value=20.0, value=p_cfg["ki"], step=0.05)
kd = col_p1.number_input("Kd", min_value=0.0, max_value=10.0, value=p_cfg["kd"], step=0.01)
sp = col_p2.number_input("Target SP", min_value=0.0, max_value=100.0, value=p_cfg["sp"], step=1.0)
tau = st.sidebar.slider("Plant Inertia (τ in sec)", 0.5, 12.0, float(p_cfg["tau"]), step=0.1)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💥 STRESS & FAULT INJECTION")
col_f1, col_f2 = st.sidebar.columns(2)
if col_f1.button("⚡ +20% LOAD"):
    st.session_state.disturbance_val += 20.0
if col_f2.button("⚡ -20% LOAD"):
    st.session_state.disturbance_val -= 20.0

st.session_state.noise_enabled = st.sidebar.checkbox("Inject Gaussian Sensor Noise", value=st.session_state.noise_enabled)

# Initialize Controller
dt = 0.35
controller = IndustrialPID(
    kp=kp,
    ki=ki,
    kd=kd,
    setpoint=sp,
    output_limits=(0.0, 100.0),
    sample_time=0.05,
)

# --- Top Header ---
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown("## ⚡ APEX INDUSTRIAL SCADA | TELEMETRY SUITE")
    st.caption("Active Cyberpunk Edge Control Station | Hardware-Ready Execution")

with h2:
    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
    if st.session_state.estop:
        st.markdown('<b style="color: #EF4444; font-family: monospace;">🛑 EMERGENCY STOP ACTIVE</b>', unsafe_allow_html=True)
    elif st.session_state.running:
        st.markdown('<span class="pulse-live"></span> <b style="color: #00E676; font-family: monospace;">TELEMETRY ACTIVE (~3 Hz)</b>', unsafe_allow_html=True)
    else:
        st.markdown('<b style="color: #64748B; font-family: monospace;">● SYSTEM STANDBY</b>', unsafe_allow_html=True)


def build_radial_gauges(pv: float, sp_val: float, mv: float) -> go.Figure:
    fig_gauge = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        horizontal_spacing=0.12,
    )

    fig_gauge.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=pv,
            title={"text": "PROCESS VALUE (PV %)", "font": {"size": 13, "color": "#00E5FF", "family": "JetBrains Mono"}},
            number={"suffix": "%", "font": {"size": 26, "color": "#FFFFFF", "family": "JetBrains Mono"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748B", "nticks": 6},
                "bar": {"color": "#00E5FF", "thickness": 0.32},
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
        ),
        row=1,
        col=1,
    )

    fig_gauge.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=mv,
            title={"text": "ACTUATOR EFFORT (MV %)", "font": {"size": 13, "color": "#FF3D00", "family": "JetBrains Mono"}},
            number={"suffix": "%", "font": {"size": 26, "color": "#FFFFFF", "family": "JetBrains Mono"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748B", "nticks": 6},
                "bar": {"color": "#FF3D00", "thickness": 0.32},
                "bgcolor": "#090D14",
                "borderwidth": 1,
                "bordercolor": "#162032",
                "steps": [
                    {"range": [0, 60], "color": "rgba(255, 61, 0, 0.05)"},
                    {"range": [60, 85], "color": "rgba(255, 171, 0, 0.1)"},
                    {"range": [85, 100], "color": "rgba(255, 61, 0, 0.25)"},
                ],
            },
        ),
        row=1,
        col=2,
    )

    fig_gauge.update_layout(
        uirevision="static_gauge",
        paper_bgcolor="#04060A",
        height=220,
        margin=dict(l=25, r=25, t=30, b=10),
    )
    return fig_gauge


REFRESH_INTERVAL = 0.35 if st.session_state.running and not st.session_state.estop else None


@st.fragment(run_every=REFRESH_INTERVAL)
def live_scada_viewport():
    if st.session_state.running and not st.session_state.estop:
        current_pv = st.session_state.pv_live
        
        # Calculate MV based on Auto vs Manual
        if st.session_state.manual_mode:
            mv = float(st.session_state.manual_mv)
        else:
            mv = controller.update(pv=current_pv, current_time=st.session_state.sim_time)

        # Plant dynamics calculation
        dist = st.session_state.disturbance_val
        dpv = ((mv + dist) - current_pv) / tau * dt
        st.session_state.pv_live += dpv
        st.session_state.sim_time += dt
        st.session_state.disturbance_val *= 0.88

        # Noise injection if enabled
        measured_pv = st.session_state.pv_live
        if st.session_state.noise_enabled:
            measured_pv += np.random.normal(0, 0.8)

        hist = st.session_state.telemetry_history
        hist["time"].append(round(st.session_state.sim_time, 1))
        hist["sp"].append(sp)
        hist["pv"].append(round(measured_pv, 2))
        hist["mv"].append(round(mv, 2))

    hist = st.session_state.telemetry_history
    last_pv = hist["pv"][-1] if hist["pv"] else 0.0
    last_mv = hist["mv"][-1] if hist["mv"] else 0.0
    error = sp - last_pv

    # KPI Metrics
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="metric-card"><div class="metric-title">PROCESS VALUE (PV)</div><div class="metric-value" style="color: #00E5FF;">{last_pv:.2f}%</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="metric-card"><div class="metric-title">TARGET SETPOINT (SP)</div><div class="metric-value" style="color: #FFD700;">{sp:.2f}%</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="metric-card"><div class="metric-title">ACTUATOR OUTPUT (MV)</div><div class="metric-value" style="color: #FF3D00;">{last_mv:.2f}%</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="metric-card"><div class="metric-title">TRACKING ERROR</div><div class="metric-value" style="color: {"#00E676" if abs(error)<2 else "#FFAB00"};">{error:+.2f}%</div></div>', unsafe_allow_html=True)

    # Radial Gauges
    fig_gauges = build_radial_gauges(last_pv, sp, last_mv)
    st.plotly_chart(fig_gauges, use_container_width=True, key="fixed_radial_gauges", config={"displayModeBar": False})

    # Oscilloscope Plot
    if len(hist["time"]) > 1:
        display_pts = 50
        t_slice = hist["time"][-display_pts:]
        sp_slice = hist["sp"][-display_pts:]
        pv_slice = hist["pv"][-display_pts:]
        mv_slice = hist["mv"][-display_pts:]

        fig_osc = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            subplot_titles=("Real-Time Closed-Loop Response", "Actuator Command Output (MV %)"),
        )

        fig_osc.add_trace(go.Scatter(x=t_slice, y=sp_slice, line=dict(color="#FFD700", width=2, dash="dash"), name="Setpoint"), row=1, col=1)
        fig_osc.add_trace(go.Scatter(x=t_slice, y=pv_slice, line=dict(color="#00E5FF", width=3), name="Process Value"), row=1, col=1)
        fig_osc.add_trace(go.Scatter(x=t_slice, y=mv_slice, line=dict(color="#FF3D00", width=2), fill="tozeroy", fillcolor="rgba(255, 61, 0, 0.08)", name="Actuator (MV)"), row=2, col=1)

        fig_osc.update_layout(
            uirevision="constant_view",
            paper_bgcolor="#04060A",
            plot_bgcolor="#080B12",
            font=dict(color="#94A3B8", family="JetBrains Mono"),
            height=440,
            margin=dict(l=30, r=30, t=35, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_osc.update_xaxes(gridcolor="#162032")
        fig_osc.update_yaxes(gridcolor="#162032")

        st.plotly_chart(fig_osc, use_container_width=True, key="fixed_oscilloscope_chart", config={"displayModeBar": False})


live_scada_viewport()

# Historian CSV Export
if len(st.session_state.telemetry_history["time"]) > 0:
    st.markdown("---")
    df_export = pd.DataFrame(st.session_state.telemetry_history)
    st.download_button(
        label="📥 EXPORT ACTIVE TELEMETRY (CSV)",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name=f"apex_scada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )