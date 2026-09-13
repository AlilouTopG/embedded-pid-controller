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
    page_title="APEX SCADA | High-Speed Telemetry Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Cyberpunk/OLED Ultra-Smooth UI ---
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
        font-size: 1rem;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
    }
    div.stButton > button[key="btn_estop"]:hover {
        background: #DC2626 !important;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.8);
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(180deg, #0B101A 0%, #06090F 100%);
        border: 1px solid #1A263B;
        border-radius: 8px;
        padding: 12px 14px;
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

    /* Zero-Flicker Hardware Dial Gauges (CSS Native) */
    .gauge-wrapper {
        background: #080C14;
        border: 1px solid #162032;
        border-radius: 8px;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .gauge-header {
        display: flex;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .gauge-track {
        background: #101622;
        border-radius: 6px;
        height: 18px;
        width: 100%;
        overflow: hidden;
        position: relative;
        border: 1px solid #1E293B;
    }
    .gauge-fill-pv {
        height: 100%;
        background: linear-gradient(90deg, #00B0FF 0%, #00E5FF 100%);
        box-shadow: 0 0 12px #00E5FF;
        transition: width 0.12s linear;
    }
    .gauge-fill-mv {
        height: 100%;
        background: linear-gradient(90deg, #D50000 0%, #FF3D00 100%);
        box-shadow: 0 0 12px #FF3D00;
        transition: width 0.12s linear;
    }
    .gauge-marker {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 3px;
        background: #FFD700;
        box-shadow: 0 0 8px #FFD700;
        z-index: 2;
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

if st.sidebar.button("🔄 RESET BUFFER"):
    st.session_state.telemetry_history = {"time": [], "sp": [], "pv": [], "mv": []}
    st.session_state.pv_live = 0.0
    st.session_state.sim_time = 0.0
    st.session_state.disturbance_val = 0.0
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏭 PLANT PRESETS")
selected_preset = st.sidebar.selectbox("Select Model:", list(PRESETS.keys()))
p_cfg = PRESETS[selected_preset]

st.sidebar.markdown("---")
control_mode = st.sidebar.radio("Control Strategy:", ["Automatic PID", "Manual Override"])
st.session_state.manual_mode = (control_mode == "Manual Override")

if st.session_state.manual_mode:
    st.session_state.manual_mv = st.sidebar.slider("Manual Output (MV %):", 0.0, 100.0, float(st.session_state.manual_mv))

st.sidebar.markdown("---")
col_p1, col_p2 = st.sidebar.columns(2)
kp = col_p1.number_input("Kp", min_value=0.0, max_value=50.0, value=p_cfg["kp"], step=0.1)
ki = col_p2.number_input("Ki", min_value=0.0, max_value=20.0, value=p_cfg["ki"], step=0.05)
kd = col_p1.number_input("Kd", min_value=0.0, max_value=10.0, value=p_cfg["kd"], step=0.01)
sp = col_p2.number_input("Target SP", min_value=0.0, max_value=100.0, value=p_cfg["sp"], step=1.0)
tau = st.sidebar.slider("Plant Inertia (τ)", 0.5, 12.0, float(p_cfg["tau"]), step=0.1)

st.sidebar.markdown("---")
if st.sidebar.button("⚡ +20% LOAD SPIKE"):
    st.session_state.disturbance_val += 20.0
st.session_state.noise_enabled = st.sidebar.checkbox("Gaussian Noise", value=st.session_state.noise_enabled)

# Initialize Controller
dt = 0.05
controller = IndustrialPID(
    kp=kp,
    ki=ki,
    kd=kd,
    setpoint=sp,
    output_limits=(0.0, 100.0),
    sample_time=0.04,
)

# --- Top Header ---
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown("## ⚡ APEX SCADA | HIGH-SPEED TELEMETRY")
    st.caption("GPU-Accelerated Zero-Flicker Closed-Loop Control")

with h2:
    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
    if st.session_state.estop:
        st.markdown('<b style="color: #EF4444; font-family: monospace;">🛑 E-STOP ACTIVE</b>', unsafe_allow_html=True)
    elif st.session_state.running:
        st.markdown('<span class="pulse-live"></span> <b style="color: #00E676; font-family: monospace;">LIVE (6-7 Hz)</b>', unsafe_allow_html=True)
    else:
        st.markdown('<b style="color: #64748B; font-family: monospace;">● STANDBY</b>', unsafe_allow_html=True)

# سرعة تحديث الواجهة: 150ms لتوفير انسيابية عالية دون وميض
UI_INTERVAL = 0.15 if st.session_state.running and not st.session_state.estop else None


@st.fragment(run_every=UI_INTERVAL)
def live_scada_viewport():
    # تنفيذ عدة خطوات فيزيائية في الدورة الواحدة لدقة الحركة وسرعتها
    if st.session_state.running and not st.session_state.estop:
        for _ in range(3):
            current_pv = st.session_state.pv_live
            if st.session_state.manual_mode:
                mv = float(st.session_state.manual_mv)
            else:
                mv = controller.update(pv=current_pv, current_time=st.session_state.sim_time)

            dist = st.session_state.disturbance_val
            dpv = ((mv + dist) - current_pv) / tau * dt
            st.session_state.pv_live += dpv
            st.session_state.sim_time += dt
            st.session_state.disturbance_val *= 0.94

        measured_pv = st.session_state.pv_live
        if st.session_state.noise_enabled:
            measured_pv += np.random.normal(0, 0.7)

        hist = st.session_state.telemetry_history
        hist["time"].append(round(st.session_state.sim_time, 2))
        hist["sp"].append(sp)
        hist["pv"].append(round(measured_pv, 2))
        hist["mv"].append(round(mv, 2))

    hist = st.session_state.telemetry_history
    last_pv = hist["pv"][-1] if hist["pv"] else 0.0
    last_mv = hist["mv"][-1] if hist["mv"] else 0.0
    error = sp - last_pv

    # 1. KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="metric-card"><div class="metric-title">PROCESS VALUE (PV)</div><div class="metric-value" style="color: #00E5FF;">{last_pv:.2f}%</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="metric-card"><div class="metric-title">TARGET SETPOINT (SP)</div><div class="metric-value" style="color: #FFD700;">{sp:.2f}%</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="metric-card"><div class="metric-title">ACTUATOR OUTPUT (MV)</div><div class="metric-value" style="color: #FF3D00;">{last_mv:.2f}%</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="metric-card"><div class="metric-title">TRACKING ERROR</div><div class="metric-value" style="color: {"#00E676" if abs(error)<2 else "#FFAB00"};">{error:+.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    # 2. Native CSS Industrial Linear Gauges (Zero-Flicker Hardware Twin)
    clamped_pv = max(0.0, min(100.0, last_pv))
    clamped_mv = max(0.0, min(100.0, last_mv))
    clamped_sp = max(0.0, min(100.0, sp))

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.markdown(
            f"""
        <div class="gauge-wrapper">
            <div class="gauge-header">
                <span style="color: #00E5FF;">PROCESS VALUE (PV)</span>
                <span style="color: #FFFFFF;">{clamped_pv:.1f}%</span>
            </div>
            <div class="gauge-track">
                <div class="gauge-fill-pv" style="width: {clamped_pv}%;"></div>
                <div class="gauge-marker" style="left: calc({clamped_sp}% - 1.5px);" title="Setpoint Target"></div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with g_col2:
        st.markdown(
            f"""
        <div class="gauge-wrapper">
            <div class="gauge-header">
                <span style="color: #FF3D00;">ACTUATOR EFFORT (MV)</span>
                <span style="color: #FFFFFF;">{clamped_mv:.1f}%</span>
            </div>
            <div class="gauge-track">
                <div class="gauge-fill-mv" style="width: {clamped_mv}%;"></div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # 3. High-Speed WebGL Oscilloscope (Scattergl)
    if len(hist["time"]) > 1:
        display_pts = 60
        t_slice = hist["time"][-display_pts:]
        sp_slice = hist["sp"][-display_pts:]
        pv_slice = hist["pv"][-display_pts:]
        mv_slice = hist["mv"][-display_pts:]

        fig_osc = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            subplot_titles=("Real-Time Closed-Loop Response", "Actuator Output (MV %)"),
        )

        # استخدام Scattergl لتسريع الرسم عبر كرت الشاشة ومنع الوميض
        fig_osc.add_trace(
            go.Scattergl(
                x=t_slice,
                y=sp_slice,
                line=dict(color="#FFD700", width=2, dash="dash"),
                name="Setpoint",
            ),
            row=1,
            col=1,
        )
        fig_osc.add_trace(
            go.Scattergl(
                x=t_slice,
                y=pv_slice,
                line=dict(color="#00E5FF", width=2.5),
                name="Process Value",
            ),
            row=1,
            col=1,
        )
        fig_osc.add_trace(
            go.Scattergl(
                x=t_slice,
                y=mv_slice,
                line=dict(color="#FF3D00", width=2),
                name="Actuator (MV)",
            ),
            row=2,
            col=1,
        )

        fig_osc.update_layout(
            uirevision="steady_axis",
            paper_bgcolor="#04060A",
            plot_bgcolor="#080B12",
            font=dict(color="#94A3B8", family="JetBrains Mono"),
            height=430,
            margin=dict(l=30, r=30, t=32, b=15),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_osc.update_xaxes(gridcolor="#162032")
        fig_osc.update_yaxes(gridcolor="#162032")

        st.plotly_chart(
            fig_osc,
            use_container_width=True,
            key="smooth_webgl_chart",
            config={"displayModeBar": False, "staticPlot": False},
        )


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