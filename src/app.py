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
    page_title="APEX SCADA | Industrial Control & Edge Telemetry",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Cyberpunk/OLED Dark UI & Interactive Button Styles ---
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@400;600;700&display=swap');

    .stApp {
        background-color: #05070A;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #090D14 !important;
        border-right: 1px solid #162032;
    }
    
    /* Headings */
    h1, h2, h3, h4 {
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: -0.5px;
    }

    /* KPI Metric Cards */
    .metric-card {
        background: linear-gradient(180deg, #0D131F 0%, #080C14 100%);
        border: 1px solid #19253B;
        border-radius: 8px;
        padding: 16px;
        position: relative;
        transition: all 0.25s ease-in-out;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }
    .metric-card:hover {
        border-color: #00E5FF;
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.25);
    }
    .metric-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    .metric-sub {
        font-size: 0.8rem;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Interactive Buttons Hover / Active States */
    div.stButton > button {
        background: linear-gradient(180deg, #0F172A 0%, #090D16 100%);
        color: #00E5FF;
        border: 1px solid #1E293B;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        padding: 0.6rem 1.2rem;
        width: 100%;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    }
    div.stButton > button:hover {
        border-color: #00E5FF;
        color: #FFFFFF;
        background: #00E5FF;
        box-shadow: 0 0 22px rgba(0, 229, 255, 0.5);
        transform: translateY(-2px);
    }
    div.stButton > button:active {
        transform: translateY(0px);
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
    }

    /* Interactive CSV Download Button */
    div.stDownloadButton > button {
        background: linear-gradient(180deg, #062B20 0%, #031510 100%);
        color: #00E676;
        border: 1px solid #00E676;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.65rem 1.4rem;
        transition: all 0.25s ease-in-out;
        box-shadow: 0 2px 8px rgba(0, 230, 118, 0.2);
    }
    div.stDownloadButton > button:hover {
        background: #00E676;
        color: #04100B;
        box-shadow: 0 0 24px rgba(0, 230, 118, 0.55);
        transform: translateY(-2px);
    }

    /* SCADA Tabs Custom Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #080C14;
        padding: 6px;
        border-radius: 8px;
        border: 1px solid #141D2D;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background-color: transparent;
        border-radius: 6px;
        color: #94A3B8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #00E5FF;
        background-color: #0F1726;
        border-color: rgba(0, 229, 255, 0.3);
    }
    .stTabs [aria-selected="true"] {
        background-color: #101B2E !important;
        color: #00E5FF !important;
        border: 1px solid #00E5FF !important;
        box-shadow: 0 0 14px rgba(0, 229, 255, 0.25);
    }

    /* Badges */
    .status-badge-sim {
        background-color: rgba(0, 229, 255, 0.1);
        color: #00E5FF;
        border: 1px solid #00E5FF;
        padding: 4px 12px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .status-badge-hw {
        background-color: rgba(255, 171, 0, 0.1);
        color: #FFAB00;
        border: 1px solid #FFAB00;
        padding: 4px 12px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- Sidebar: SCADA Control Panel ---
st.sidebar.markdown("### 🎛️ SCADA CONTROL STATION")

op_mode = st.sidebar.radio(
    "System Operation Mode:",
    ["Digital Twin Simulation", "Hardware Modbus Gateway"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚡ PID Loop Parameters")
col_p1, col_p2 = st.sidebar.columns(2)
kp = col_p1.number_input("Proportional (Kp)", min_value=0.0, max_value=50.0, value=2.8, step=0.1)
ki = col_p2.number_input("Integral (Ki)", min_value=0.0, max_value=20.0, value=0.65, step=0.05)
kd = col_p1.number_input("Derivative (Kd)", min_value=0.0, max_value=10.0, value=0.18, step=0.01)
sp = col_p2.number_input("Setpoint (SP)", min_value=0.0, max_value=100.0, value=65.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚙️ Plant Dynamic Variables")
tau = st.sidebar.slider("Time Constant (τ in sec)", 0.5, 10.0, 2.2, step=0.1)
dead_time = st.sidebar.slider("Transport Delay (Dead Time L)", 0.0, 3.0, 0.2, step=0.1)
disturbance = st.sidebar.slider("Step Disturbance Load (%)", -25.0, 25.0, 0.0, step=1.0)
duration = st.sidebar.select_slider("Monitoring Horizon (s):", options=[10, 20, 30, 45, 60], value=20)

if st.sidebar.button("🔄 RE-SYNC / INITIALIZE SYSTEM"):
    st.rerun()

# --- Simulation & Control Loop Logic ---
dt = 0.05
steps = int(duration / dt)
delay_steps = int(dead_time / dt)

controller = IndustrialPID(
    kp=kp,
    ki=ki,
    kd=kd,
    setpoint=sp,
    output_limits=(0.0, 100.0),
    sample_time=dt,
)

time_arr = np.linspace(0, duration, steps)
pv_arr = np.zeros(steps)
sp_arr = np.full(steps, sp)
mv_arr = np.zeros(steps)
p_term_arr = np.zeros(steps)
i_term_arr = np.zeros(steps)
d_term_arr = np.zeros(steps)

pv_current = 0.0
delay_buffer = [0.0] * (delay_steps + 1)
iae = 0.0

for idx, t in enumerate(time_arr):
    # Compute manipulated variable
    mv = controller.update(pv=pv_current, current_time=t)
    mv_arr[idx] = mv

    # Calculate PID sub-components
    err = sp - pv_current
    p_term_arr[idx] = kp * err
    i_term_arr[idx] = controller._integral
    d_term_arr[idx] = mv - p_term_arr[idx] - i_term_arr[idx]

    # Disturbance load injected at midpoint
    dist_val = disturbance if t > (duration / 2.0) else 0.0

    # Plant model dynamics (FOPDT)
    delayed_input = delay_buffer.pop(0)
    dpv = (delayed_input - pv_current + dist_val) / tau * dt
    pv_current += dpv
    delay_buffer.append(mv)
    pv_arr[idx] = pv_current

    iae += abs(err) * dt

# Performance Index Metrics
final_pv = pv_arr[-1]
final_err = abs(sp - final_pv)
max_pv = np.max(pv_arr)
overshoot_pct = max(0.0, (max_pv - sp) / sp * 100.0) if sp > 0 else 0.0

# --- Top Header & Live Status Bar ---
head_col, status_col = st.columns([3, 1])
with head_col:
    st.markdown("## ⚡ APEX INDUSTRIAL SCADA | TELEMETRY SUITE")
    st.caption("Embedded Digital Twin & Hardware-in-the-Loop Gateway | Real-Time Execution")

with status_col:
    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
    if "Simulation" in op_mode:
        st.markdown('<span class="status-badge-sim">● DIGITAL TWIN ENGINE ACTIVE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-hw">● MODBUS TCP GATEWAY STANDBY</span>', unsafe_allow_html=True)

# --- KPI Metric Dashboard (HTML Cards) ---
k1, k2, k3, k4, k5 = st.columns(5)

k1.markdown(f"""
<div class="metric-card">
    <div class="metric-title">Process Value (PV)</div>
    <div class="metric-value" style="color: #00E5FF;">{final_pv:.2f}%</div>
    <div class="metric-sub" style="color: #64748B;">Δ {final_pv - sp:+.2f}%</div>
</div>
""", unsafe_allow_html=True)

k2.markdown(f"""
<div class="metric-card">
    <div class="metric-title">Target Setpoint (SP)</div>
    <div class="metric-value" style="color: #FFD700;">{sp:.2f}%</div>
    <div class="metric-sub" style="color: #64748B;">Stationary</div>
</div>
""", unsafe_allow_html=True)

k3.markdown(f"""
<div class="metric-card">
    <div class="metric-title">Control Output (MV)</div>
    <div class="metric-value" style="color: #FF3D00;">{mv_arr[-1]:.2f}%</div>
    <div class="metric-sub" style="color: #64748B;">Actuator Command</div>
</div>
""", unsafe_allow_html=True)

k4.markdown(f"""
<div class="metric-card">
    <div class="metric-title">Peak Overshoot</div>
    <div class="metric-value" style="color: {'#FF3D00' if overshoot_pct > 15 else '#00E676'};">{overshoot_pct:.1f}%</div>
    <div class="metric-sub" style="color: #64748B;">Max: {max_pv:.1f}%</div>
</div>
""", unsafe_allow_html=True)

k5.markdown(f"""
<div class="metric-card">
    <div class="metric-title">Integral Abs Error</div>
    <div class="metric-value" style="color: #E2E8F0;">{iae:.1f}</div>
    <div class="metric-sub" style="color: #64748B;">IAE Index</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 18px'></div>", unsafe_allow_html=True)

# --- Navigation Tabs ---
tab_live, tab_spectrum, tab_data, tab_plc = st.tabs([
    "📊 Live Dynamic Telemetry",
    "🔬 P-I-D Component Analysis",
    "📋 Historian Buffer & CSV Export",
    "🔌 Modbus TCP Hardware Gateway",
])

# 1. Tab: Live Telemetry
with tab_live:
    fig_main = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.72, 0.28],
        subplot_titles=("Closed-Loop Dynamic Step Response", "Actuator Command Output (MV %)")
    )

    # ±2% Error Tolerance Band
    fig_main.add_trace(go.Scatter(
        x=np.concatenate([time_arr, time_arr[::-1]]),
        y=np.concatenate([sp_arr * 1.02, (sp_arr * 0.98)[::-1]]),
        fill='toself',
        fillcolor='rgba(0, 229, 255, 0.04)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="±2% Settling Corridor"
    ), row=1, col=1)

    # Setpoint (SP)
    fig_main.add_trace(go.Scatter(
        x=time_arr, y=sp_arr,
        line=dict(color='#FFD700', width=2, dash='dash'),
        name="Setpoint (SP)"
    ), row=1, col=1)

    # Process Value (PV)
    fig_main.add_trace(go.Scatter(
        x=time_arr, y=pv_arr,
        line=dict(color='#00E5FF', width=3),
        name="Process Value (PV)"
    ), row=1, col=1)

    # Manipulated Variable (MV)
    fig_main.add_trace(go.Scatter(
        x=time_arr, y=mv_arr,
        line=dict(color='#FF3D00', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 61, 0, 0.08)',
        name="Control Effort (MV)"
    ), row=2, col=1)

    fig_main.update_layout(
        paper_bgcolor='#05070A',
        plot_bgcolor='#090D14',
        font=dict(color='#94A3B8', family='JetBrains Mono'),
        height=540,
        margin=dict(l=30, r=30, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_main.update_xaxes(gridcolor='#141D2D', zerolinecolor='#141D2D')
    fig_main.update_yaxes(gridcolor='#141D2D', zerolinecolor='#141D2D')
    st.plotly_chart(fig_main, use_container_width=True)

# 2. Tab: PID Decomposition
with tab_spectrum:
    fig_pid = go.Figure()
    fig_pid.add_trace(go.Scatter(x=time_arr, y=p_term_arr, name="Proportional Term (Kp·e)", line=dict(color='#00E5FF', width=2)))
    fig_pid.add_trace(go.Scatter(x=time_arr, y=i_term_arr, name="Integral Term (Ki·∫e dt)", line=dict(color='#A855F7', width=2)))
    fig_pid.add_trace(go.Scatter(x=time_arr, y=d_term_arr, name="Derivative Term (-Kd·dPV/dt)", line=dict(color='#00E676', width=2)))

    fig_pid.update_layout(
        paper_bgcolor='#05070A',
        plot_bgcolor='#090D14',
        font=dict(color='#94A3B8', family='JetBrains Mono'),
        title="Dynamic Component Contribution Spectrum",
        xaxis=dict(title="Time (seconds)", gridcolor='#141D2D'),
        yaxis=dict(title="Output Signal Component", gridcolor='#141D2D'),
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_pid, use_container_width=True)

# 3. Tab: Historian & CSV Export
with tab_data:
    df_telemetry = pd.DataFrame({
        "Timestamp_s": np.round(time_arr, 2),
        "Setpoint_SP": np.round(sp_arr, 2),
        "Process_Value_PV": np.round(pv_arr, 2),
        "Control_Output_MV": np.round(mv_arr, 2),
        "Error": np.round(sp_arr - pv_arr, 2)
    })
    
    st.markdown("#### 📋 Real-Time Historian Telemetry Stream")
    st.dataframe(df_telemetry.tail(12), use_container_width=True)

    csv_payload = df_telemetry.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 DOWNLOAD HISTORIAN TELEMETRY (CSV)",
        data=csv_payload,
        file_name=f"apex_scada_telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# 4. Tab: Modbus Gateway
with tab_plc:
    st.markdown("#### 📡 Edge Industrial Modbus TCP Configuration")
    m1, m2 = st.columns(2)
    m1.text_input("Target PLC Host IPv4 Address:", value="192.168.1.105")
    m2.number_input("Industrial Port (Standard 502):", value=502)
    m1.number_input("Sensor Input Register (Raw PV):", value=30001)
    m2.number_input("Actuator Holding Register (Raw MV):", value=40001)
    
    if st.button("⚡ EXECUTE GATEWAY HANDSHAKE & HEALTH CHECK"):
        st.info("Checking Edge socket layer on port 502... Ensure `modbus_driver.py` is operational.")