import time
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from core.pid import IndustrialPID

# --- Page Configuration ---
st.set_page_config(
    page_title="APEX SCADA | Cyberpunk Telemetry Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Cyberpunk/OLED Dark UI ---
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background-color: #05070A;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #090D14 !important;
        border-right: 1px solid #162032;
    }
    .metric-card {
        background: linear-gradient(180deg, #0D131F 0%, #080C14 100%);
        border: 1px solid #19253B;
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
    div.stButton > button {
        background: #0F172A;
        color: #00E5FF;
        border: 1px solid #00E5FF;
        font-family: 'JetBrains Mono', monospace;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background: #00E5FF;
        color: #000;
        box-shadow: 0 0 15px #00E5FF;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- State Initialization ---
if "running" not in st.session_state:
    st.session_state.running = False
if "telemetry_history" not in st.session_state:
    st.session_state.telemetry_history = {"time": [], "sp": [], "pv": [], "mv": []}
if "pv_live" not in st.session_state:
    st.session_state.pv_live = 0.0
if "sim_time" not in st.session_state:
    st.session_state.sim_time = 0.0
if "disturbance_val" not in st.session_state:
    st.session_state.disturbance_val = 0.0

# --- Sidebar: Control Station ---
st.sidebar.markdown("### 🎛️ SCADA CONTROL STATION")

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("▶ START STREAM"):
    st.session_state.running = True
    st.rerun()

if col_btn2.button("⏹ FREEZE STREAM"):
    st.session_state.running = False
    st.rerun()

if st.sidebar.button("🔄 RESET SYSTEM"):
    st.session_state.telemetry_history = {"time": [], "sp": [], "pv": [], "mv": []}
    st.session_state.pv_live = 0.0
    st.session_state.sim_time = 0.0
    st.session_state.disturbance_val = 0.0
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚡ Real-Time PID Tuning")
col_p1, col_p2 = st.sidebar.columns(2)
kp = col_p1.number_input("Kp", min_value=0.0, max_value=50.0, value=2.6, step=0.1)
ki = col_p2.number_input("Ki", min_value=0.0, max_value=20.0, value=0.75, step=0.05)
kd = col_p1.number_input("Kd", min_value=0.0, max_value=10.0, value=0.15, step=0.01)
sp = col_p2.number_input("Target SP", min_value=0.0, max_value=100.0, value=65.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 💥 Stress Load Testing")
if st.sidebar.button("⚠️ INJECT +20% LOAD SHOCK"):
    st.session_state.disturbance_val = 20.0

# Fixed execution parameters
dt = 0.35  # متطابق تماماً مع زمن التحديث الانسيابي
tau = 2.5
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
    st.markdown("## ⚡ APEX SCADA | COCKPIT TELEMETRY & RADIAL GAUGES")
    st.caption("Industrial Closed-Loop Edge Controller with Native Zero-Flicker Architecture")

with h2:
    st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
    if st.session_state.running:
        st.markdown(
            '<span class="pulse-live"></span> <b style="color: #00E676; font-family: monospace;">STREAMING LIVE (~3 Hz)</b>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<b style="color: #FF3D00; font-family: monospace;">● STREAM PAUSED (STANDBY)</b>',
            unsafe_allow_html=True,
        )


def build_radial_gauges(pv: float, sp_val: float, mv: float) -> go.Figure:
    fig_gauge = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        horizontal_spacing=0.12,
    )

    # 1. Process Value Gauge
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
                "threshold": {
                    "line": {"color": "#FFD700", "width": 4},
                    "thickness": 0.8,
                    "value": sp_val,
                },
            },
        ),
        row=1,
        col=1,
    )

    # 2. Manipulated Variable Gauge
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
        paper_bgcolor="#05070A",
        height=220,
        margin=dict(l=25, r=25, t=30, b=10),
    )
    return fig_gauge


# معدل التحديث اللحظي عبر تقنية Fragment الرسمية
REFRESH_INTERVAL = 0.35 if st.session_state.running else None


@st.fragment(run_every=REFRESH_INTERVAL)
def live_scada_viewport():
    """هذه الدالة تُحدّث نفسها تلقائياً في الخلفية بدون وميض وبدون إعادة تحميل الصفحة."""
    # 1. تحديث معادلات التحكم والفيزياء إذا كان البث مفعلاً
    if st.session_state.running:
        current_pv = st.session_state.pv_live
        mv = controller.update(pv=current_pv, current_time=st.session_state.sim_time)

        dist = st.session_state.disturbance_val
        dpv = ((mv + dist) - current_pv) / tau * dt
        st.session_state.pv_live += dpv
        st.session_state.sim_time += dt
        st.session_state.disturbance_val *= 0.85

        hist = st.session_state.telemetry_history
        hist["time"].append(round(st.session_state.sim_time, 1))
        hist["sp"].append(sp)
        hist["pv"].append(round(st.session_state.pv_live, 2))
        hist["mv"].append(round(mv, 2))

    hist = st.session_state.telemetry_history
    last_pv = hist["pv"][-1] if hist["pv"] else 0.0
    last_mv = hist["mv"][-1] if hist["mv"] else 0.0
    error = sp - last_pv

    # 2. بطاقات KPI
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(
        f'<div class="metric-card"><div class="metric-title">PROCESS VALUE (PV)</div><div class="metric-value" style="color: #00E5FF;">{last_pv:.2f}%</div></div>',
        unsafe_allow_html=True,
    )
    k2.markdown(
        f'<div class="metric-card"><div class="metric-title">TARGET SETPOINT (SP)</div><div class="metric-value" style="color: #FFD700;">{sp:.2f}%</div></div>',
        unsafe_allow_html=True,
    )
    k3.markdown(
        f'<div class="metric-card"><div class="metric-title">ACTUATOR OUTPUT (MV)</div><div class="metric-value" style="color: #FF3D00;">{last_mv:.2f}%</div></div>',
        unsafe_allow_html=True,
    )
    k4.markdown(
        f'<div class="metric-card"><div class="metric-title">TRACKING ERROR</div><div class="metric-value" style="color: {"#00E676" if abs(error)<2 else "#FFAB00"};">{error:+.2f}%</div></div>',
        unsafe_allow_html=True,
    )

    # 3. العدادات الدائرية مع مفتاح فريد لمنع خطأ DuplicateElementId
    fig_gauges = build_radial_gauges(last_pv, sp, last_mv)
    st.plotly_chart(
        fig_gauges,
        use_container_width=True,
        key="fixed_radial_gauges",
        config={"displayModeBar": False},
    )

    # 4. راسم الإشارة المتحرك (Oscilloscope)
    if len(hist["time"]) > 1:
        display_pts = 50
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
            subplot_titles=(
                "Real-Time Oscilloscope Response",
                "Actuator Effort (MV %)",
            ),
        )

        fig_osc.add_trace(
            go.Scatter(
                x=t_slice,
                y=sp_slice,
                line=dict(color="#FFD700", width=2, dash="dash"),
                name="Setpoint",
            ),
            row=1,
            col=1,
        )
        fig_osc.add_trace(
            go.Scatter(
                x=t_slice,
                y=pv_slice,
                line=dict(color="#00E5FF", width=3),
                name="Process Value",
            ),
            row=1,
            col=1,
        )
        fig_osc.add_trace(
            go.Scatter(
                x=t_slice,
                y=mv_slice,
                line=dict(color="#FF3D00", width=2),
                fill="tozeroy",
                fillcolor="rgba(255, 61, 0, 0.08)",
                name="Actuator (MV)",
            ),
            row=2,
            col=1,
        )

        fig_osc.update_layout(
            uirevision="constant_view",
            paper_bgcolor="#05070A",
            plot_bgcolor="#090D14",
            font=dict(color="#94A3B8", family="JetBrains Mono"),
            height=440,
            margin=dict(l=30, r=30, t=35, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_osc.update_xaxes(gridcolor="#141D2D")
        fig_osc.update_yaxes(gridcolor="#141D2D")

        st.plotly_chart(
            fig_osc,
            use_container_width=True,
            key="fixed_oscilloscope_chart",
            config={"displayModeBar": False},
        )


# استدعاء الحاوية المستقلة
live_scada_viewport()

# قسم تصدير البيانات (خارج الـ Fragment حتى لا يعيد رسم نفسه)
if len(st.session_state.telemetry_history["time"]) > 0:
    st.markdown("---")
    df_export = pd.DataFrame(st.session_state.telemetry_history)
    st.download_button(
        label="📥 EXPORT ACQUISITION LOG (CSV)",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name=f"scada_live_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )