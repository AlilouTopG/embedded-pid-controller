import os
import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="NEXUS | Industrial PID Operations Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ULTRA-PREMIUM CINEMATIC CSS THEME
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-primary: #05070A;
    --bg-secondary: #0B0E14;
    --bg-card: rgba(15, 22, 35, 0.75);
    --accent-cyan: #00F2FE;
    --accent-green: #00FF88;
    --accent-amber: #FFB800;
    --accent-crimson: #FF3366;
    --text-primary: #E8ECF1;
    --text-secondary: #8892A4;
    --glass-border: rgba(255, 255, 255, 0.08);
    --glass-blur: blur(20px);
}

.stApp {
    background: linear-gradient(135deg, #05070A 0%, #0B0E14 50%, #0D1117 100%);
    font-family: 'Inter', -apple-system, sans-serif;
}

.stApp * {
    color: var(--text-primary) !important;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B0E14 0%, #0F1923 100%) !important;
    border-right: 1px solid var(--glass-border) !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary) !important;
}

/* Glass Card Component */
.glass-card {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
    border-color: rgba(0, 242, 254, 0.3);
    box-shadow: 
        0 8px 32px rgba(0, 242, 254, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
}

/* KPI Metric Cards */
.kpi-card {
    background: linear-gradient(145deg, rgba(15, 22, 35, 0.85), rgba(10, 15, 25, 0.95));
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 14px;
    padding: 20px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.kpi-card:hover::before {
    opacity: 1;
}

.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0, 242, 254, 0.15);
}

.kpi-label {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-secondary) !important;
    margin-bottom: 8px;
}

.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 600;
    color: var(--accent-cyan) !important;
    line-height: 1.2;
}

.kpi-value.green { color: var(--accent-green) !important; }
.kpi-value.amber { color: var(--accent-amber) !important; }
.kpi-value.crimson { color: var(--accent-crimson) !important; }

.kpi-unit {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-secondary) !important;
    margin-top: 4px;
}

/* Status Pulse Indicator */
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
}

.status-pulse {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

.status-pulse.online { background: var(--accent-green); box-shadow: 0 0 12px var(--accent-green); }
.status-pulse.warning { background: var(--accent-amber); box-shadow: 0 0 12px var(--accent-amber); }
.status-pulse.critical { background: var(--accent-crimson); box-shadow: 0 0 12px var(--accent-crimson); }

/* Header Bar */
.header-bar {
    background: linear-gradient(90deg, rgba(15, 22, 35, 0.9), rgba(10, 15, 25, 0.95));
    backdrop-filter: var(--glass-blur);
    border-bottom: 1px solid var(--glass-border);
    padding: 12px 32px;
    margin: -1rem -1rem 1rem -1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-title {
    font-family: 'Inter', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 2px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-secondary) !important;
}

/* Custom Slider Styling */
.stSlider > div > div > div > div {
    background: var(--accent-cyan) !important;
}

.stSlider > div > div > div > div > div {
    background: var(--accent-cyan) !important;
    border: 2px solid var(--bg-primary) !important;
    box-shadow: 0 0 10px rgba(0, 242, 254, 0.5) !important;
}

/* Custom Selectbox */
.stSelectbox > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
}

/* Custom Buttons */
.stButton > button {
    background: linear-gradient(135deg, rgba(0, 242, 254, 0.15), rgba(0, 255, 136, 0.1)) !important;
    border: 1px solid var(--accent-cyan) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0, 242, 254, 0.3), rgba(0, 255, 136, 0.2)) !important;
    box-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
    transform: translateY(-1px) !important;
}

/* Expander Styling */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}

/* Divider */
.tactical-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
    margin: 16px 0;
}

/* Section Header */
.section-header {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent-cyan) !important;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-header::before {
    content: '';
    width: 3px;
    height: 14px;
    background: var(--accent-cyan);
    border-radius: 2px;
}

/* Hide Streamlit Defaults */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.15); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0, 242, 254, 0.2), rgba(0, 255, 136, 0.1)) !important;
    border-bottom: none !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SUPABASE INITIALIZATION
# ============================================================================
SUPABASE_URL = st.secrets.get('SUPABASE_URL', os.getenv('SUPABASE_URL', ''))
SUPABASE_KEY = st.secrets.get('SUPABASE_KEY', os.getenv('SUPABASE_KEY', ''))

@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = init_supabase()

# ============================================================================
# SESSION STATE
# ============================================================================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'sim_history' not in st.session_state:
    st.session_state.sim_history = []

# ============================================================================
# AUTHENTICATION MODULE
# ============================================================================
def render_auth_portal():
    st.markdown("""
    <div style="text-align: center; padding: 60px 0;">
        <div style="font-size: 64px; margin-bottom: 20px;">⚡</div>
        <h1 style="font-family: 'Inter', sans-serif; font-size: 36px; font-weight: 700; 
                    background: linear-gradient(90deg, #00F2FE, #00FF88);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    letter-spacing: 3px; margin-bottom: 12px;">NEXUS PLATFORM</h1>
        <p style="color: #8892A4; font-size: 14px; letter-spacing: 2px; text-transform: uppercase;">
            Industrial PID Operations & Control Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<div class="section-header">Authentication</div>', unsafe_allow_html=True)
        
        auth_mode = st.radio("Access Mode", ["Sign In", "Create Account"], label_visibility="collapsed")
        email = st.text_input("Email Address", placeholder="operator@industrial.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if auth_mode == "Create Account":
            if st.button("Initialize Account", use_container_width=True):
                if supabase:
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Account provisioned. Verify email to continue.")
                    except Exception as e:
                        st.error(f"Provisioning failed: {str(e)[:50]}")
                else:
                    st.error("Supabase credentials not configured.")
        else:
            if st.button("Authenticate", use_container_width=True):
                if supabase:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.rerun()
                    except Exception:
                        st.error("Authentication failed. Verify credentials.")
                else:
                    st.error("Supabase credentials not configured.")
    
    st.stop()

if st.session_state.user is None:
    render_auth_portal()

# ============================================================================
# SYSTEM CONFIGURATIONS
# ============================================================================
PROCESSES = {
    "🔥 Thermal Reactor": {
        "unit": "°C", "default_sp": 150.0, "max_sp": 300.0, "min_sp": 20.0,
        "a_factor": 0.08, "loss_factor": 0.02, "noise": 0.5,
        "description": "High-temperature industrial furnace control"
    },
    "💧 Hydraulic Surge Tank": {
        "unit": "m", "default_sp": 8.0, "max_sp": 20.0, "min_sp": 0.5,
        "a_factor": 0.12, "loss_factor": 0.03, "noise": 0.1,
        "description": "Liquid level regulation with variable flow"
    },
    "⚡ DC Servo Motor": {
        "unit": "RPM", "default_sp": 1500.0, "max_sp": 3000.0, "min_sp": 100.0,
        "a_factor": 15.0, "loss_factor": 0.5, "noise": 5.0,
        "description": "High-precision speed control system"
    },
    "🔴 Pressure Vessel": {
        "unit": "bar", "default_sp": 6.0, "max_sp": 15.0, "min_sp": 0.5,
        "a_factor": 0.05, "loss_factor": 0.01, "noise": 0.05,
        "description": "Gas pressure regulation and safety control"
    }
}

TUNING_PRESETS = {
    "Smooth (PI-Dominant)": {"Kp": 1.8, "Ki": 0.6, "Kd": 0.05},
    "Aggressive (Fast Settling)": {"Kp": 4.5, "Ki": 0.3, "Kd": 0.8},
    "Deadbeat": {"Kp": 3.2, "Ki": 0.8, "Kd": 1.2},
    "Noise-Tolerant": {"Kp": 2.0, "Ki": 0.2, "Kd": 0.02}
}

# ============================================================================
# PID CONTROLLER ENGINE
# ============================================================================
class PIDEngine:
    def __init__(self, Kp, Ki, Kd, dt=0.05, lim_min=0.0, lim_max=100.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt
        self.lim_min = lim_min
        self.lim_max = lim_max
        self.prev_error = 0.0
        self.integral = 0.0
        self.output = 0.0
        
    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0
        self.output = 0.0
        
    def update(self, setpoint, measurement):
        error = setpoint - measurement
        
        proportional = self.Kp * error
        
        self.integral += 0.5 * self.Ki * self.dt * (error + self.prev_error)
        self.integral = max(self.lim_min, min(self.lim_max, self.integral))
        
        derivative = self.Kd * (error - self.prev_error) / self.dt if self.dt > 0 else 0.0
        
        self.output = proportional + self.integral + derivative
        self.output = max(self.lim_min, min(self.lim_max, self.output))
        
        self.prev_error = error
        return self.output

# ============================================================================
# PERFORMANCE ANALYTICS
# ============================================================================
def calculate_kpis(time_arr, error_arr, setpoint, pv_arr, output_arr):
    dt = time_arr[1] - time_arr[0] if len(time_arr) > 1 else 0.05
    
    iae = np.sum(np.abs(error_arr)) * dt
    ise = np.sum(np.array(error_arr)**2) * dt
    
    max_pv = max(pv_arr)
    overshoot = max(0, ((max_pv - setpoint) / setpoint * 100)) if setpoint > 0 else 0
    
    steady_state_error = abs(error_arr[-1]) if len(error_arr) > 0 else 0
    
    settling_time = time_arr[-1]
    for i in range(len(pv_arr) - 1, -1, -1):
        if abs(pv_arr[i] - setpoint) > 0.02 * setpoint if setpoint > 0 else 0.1:
            settling_time = time_arr[min(i + 1, len(time_arr) - 1)]
            break
    
    rise_time = 0
    for i, pv in enumerate(pv_arr):
        if pv >= 0.9 * setpoint if setpoint > 0 else pv >= 0.9:
            rise_time = time_arr[i]
            break
    
    return {
        "IAE": round(iae, 3),
        "ISE": round(ise, 3),
        "Overshoot": round(overshoot, 1),
        "Settling Time": round(settling_time, 2),
        "Rise Time": round(rise_time, 2),
        "Steady-State Error": round(steady_state_error, 4),
        "Final PV": round(pv_arr[-1], 2) if pv_arr else 0,
        "Final Output": round(output_arr[-1], 2) if output_arr else 0
    }

# ============================================================================
# PLOTLY CHART CONFIGURATION
# ============================================================================
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, sans-serif", "color": "#8892A4", "size": 11},
        "xaxis": {
            "gridcolor": "rgba(255,255,255,0.05)",
            "zerolinecolor": "rgba(255,255,255,0.08)",
            "linecolor": "rgba(255,255,255,0.1)"
        },
        "yaxis": {
            "gridcolor": "rgba(255,255,255,0.05)",
            "zerolinecolor": "rgba(255,255,255,0.08)",
            "linecolor": "rgba(255,255,255,0.1)"
        },
        "hoverlabel": {
            "bgcolor": "#0B0E14",
            "bordercolor": "#00F2FE",
            "font": {"family": "JetBrains Mono", "size": 12, "color": "#E8ECF1"}
        }
    }
}

# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 16px 0; margin-bottom: 16px;">
        <span style="font-size: 28px;">⚡</span>
        <div style="font-family: 'Inter'; font-size: 14px; font-weight: 700; 
                    letter-spacing: 2px; color: #00F2FE; margin-top: 4px;">NEXUS</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.3);
                border-radius: 8px; padding: 12px; margin-bottom: 16px;">
        <span class="status-pulse online"></span>
        <span style="font-family: 'JetBrains Mono'; font-size: 11px; color: #00FF88;">
            {st.session_state.user.email}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Sign Out", use_container_width=True):
        if supabase:
            supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
    
    st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Process Selection</div>', unsafe_allow_html=True)
    selected_process = st.selectbox("Industrial System", list(PROCESSES.keys()), label_visibility="collapsed")
    cfg = PROCESSES[selected_process]
    
    st.markdown(f"""
    <div style="background: rgba(15, 22, 35, 0.6); border-radius: 8px; padding: 12px; margin: 8px 0 16px 0;">
        <p style="font-size: 11px; color: #8892A4; margin: 0;">{cfg['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Control Mode</div>', unsafe_allow_html=True)
    control_mode = st.radio("Mode", ["Automatic PID", "Manual Override"], label_visibility="collapsed")
    
    manual_duty = 50.0
    if control_mode == "Manual Override":
        manual_duty = st.slider("Duty Cycle (%)", 0.0, 100.0, 50.0, 1.0)
    
    st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">PID Calibration</div>', unsafe_allow_html=True)
    
    tuning_preset = st.selectbox("Tuning Preset", list(TUNING_PRESETS.keys()))
    preset = TUNING_PRESETS[tuning_preset]
    
    Kp = st.slider("Proportional (Kp)", 0.0, 10.0, preset["Kp"], 0.1, key="kp_slider")
    Ki = st.slider("Integral (Ki)", 0.0, 2.0, preset["Ki"], 0.05, key="ki_slider")
    Kd = st.slider("Derivative (Kd)", 0.0, 2.0, preset["Kd"], 0.01, key="kd_slider")
    
    target_setpoint = st.slider(
        f"Setpoint ({cfg['unit']})",
        cfg['min_sp'], cfg['max_sp'], cfg['default_sp'], 0.5
    )

# ============================================================================
# HEADER BAR
# ============================================================================
st.markdown(f"""
<div class="header-bar">
    <div class="header-title">NEXUS OPERATIONS PLATFORM</div>
    <div class="header-status">
        <span class="status-pulse online"></span>
        SYSTEM NOMINAL &nbsp;|&nbsp; 
        <span style="color: #00F2FE;">{selected_process}</span> &nbsp;|&nbsp;
        SIM TIME: 20.0s
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIMULATION ENGINE
# ============================================================================
dt = 0.05
steps = 400
pid = PIDEngine(Kp, Ki, Kd, dt)

time_data = []
pv_data = []
sp_data = []
error_data = []
output_data = []

pv_value = 0.0
np.random.seed(42)

for step in range(steps):
    t = step * dt
    
    if control_mode == "Automatic PID":
        u = pid.update(target_setpoint, pv_value)
    else:
        u = manual_duty
    
    noise = np.random.normal(0, cfg['noise'])
    pv_value = max(0.0, pv_value + (u * cfg['a_factor'] - pv_value * cfg['loss_factor']) * dt)
    pv_measured = pv_value + noise
    
    error = target_setpoint - pv_value
    
    time_data.append(round(t, 2))
    pv_data.append(round(pv_measured, 3))
    sp_data.append(target_setpoint)
    error_data.append(round(error, 3))
    output_data.append(round(u, 2))

kpis = calculate_kpis(np.array(time_data), np.array(error_data), target_setpoint, np.array(pv_data), np.array(output_data))

# ============================================================================
# TELEMETRY KPI CARDS
# ============================================================================
st.markdown('<div class="section-header">Real-Time Telemetry</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    final_pv = kpis["Final PV"]
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Process Variable</div>
        <div class="kpi-value">{final_pv}</div>
        <div class="kpi-unit">{cfg['unit']}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Setpoint Target</div>
        <div class="kpi-value">{target_setpoint}</div>
        <div class="kpi-unit">{cfg['unit']}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    sse = kpis["Steady-State Error"]
    sse_class = "green" if sse < 0.5 else "amber" if sse < 2.0 else "crimson"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Steady-State Error</div>
        <div class="kpi-value {sse_class}">{sse}</div>
        <div class="kpi-unit">{cfg['unit']}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    overshoot = kpis["Overshoot"]
    os_class = "green" if overshoot < 5 else "amber" if overshoot < 15 else "crimson"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Max Overshoot</div>
        <div class="kpi-value {os_class}">{overshoot}%</div>
        <div class="kpi-unit">of setpoint</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Control Output</div>
        <div class="kpi-value">{kpis['Final Output']}</div>
        <div class="kpi-unit">% PWM</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# ADVANCED ANALYTICS CARDS
# ============================================================================
st.markdown('<div class="section-header">Performance Analytics</div>', unsafe_allow_html=True)

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">IAE (Integral Absolute)</div>
        <div class="kpi-value" style="font-size: 22px;">{kpis['IAE']}</div>
        <div class="kpi-unit">error·seconds</div>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">ISE (Integral Squared)</div>
        <div class="kpi-value" style="font-size: 22px;">{kpis['ISE']}</div>
        <div class="kpi-unit">error²·seconds</div>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Rise Time</div>
        <div class="kpi-value" style="font-size: 22px;">{kpis['Rise Time']}</div>
        <div class="kpi-unit">seconds</div>
    </div>
    """, unsafe_allow_html=True)

with col_d:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Settling Time</div>
        <div class="kpi-value" style="font-size: 22px;">{kpis['Settling Time']}</div>
        <div class="kpi-unit">seconds</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# PLOTLY VISUALIZATIONS
# ============================================================================
st.markdown('<div class="section-header">Dynamic Response Analysis</div>', unsafe_allow_html=True)

fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=("Process Variable vs Setpoint", "Control Effort Signal"),
    vertical_spacing=0.12,
    row_heights=[0.65, 0.35]
)

fig.add_trace(
    go.Scatter(
        x=time_data, y=sp_data,
        name="Setpoint",
        line=dict(color="#FF3366", width=2, dash="dash"),
        hovertemplate="t=%{x}s<br>SP=%{y}<extra></extra>"
    ),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(
        x=time_data, y=pv_data,
        name="Process Variable",
        line=dict(color="#00F2FE", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(0, 242, 254, 0.08)",
        hovertemplate="t=%{x}s<br>PV=%{y:.3f}<extra></extra>"
    ),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(
        x=time_data, y=output_data,
        name="Control Output",
        line=dict(color="#00FF88", width=2),
        fill="tozeroy",
        fillcolor="rgba(0, 255, 136, 0.08)",
        hovertemplate="t=%{x}s<br>u=%{y:.1f}%<extra></extra>"
    ),
    row=2, col=1
)

fig.update_layout(
    **PLOTLY_TEMPLATE["layout"],
    height=520,
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11, color="#8892A4")
    ),
    margin=dict(l=50, r=30, t=40, b=30)
)

fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
fig.update_yaxes(title_text=f"Value ({cfg['unit']})", row=1, col=1)
fig.update_yaxes(title_text="Output (%)", row=2, col=1)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ============================================================================
# TABS: DATA EXPORT & EVENT LOG
# ============================================================================
st.markdown('<div class="section-header">Data Operations</div>', unsafe_allow_html=True)

tab_export, tab_log, tab_archive = st.tabs(["📊 Telemetry Export", "📋 Event Log", "☁️ Cloud Archive"])

with tab_export:
    df_export = pd.DataFrame({
        "Time_s": time_data,
        "Setpoint": sp_data,
        "Process_Variable": pv_data,
        "Error": error_data,
        "Control_Output_Pct": output_data
    })
    
    csv_data = df_export.to_csv(index=False)
    
    col_dl1, col_dl2, col_dl3 = st.columns([2, 2, 1])
    with col_dl1:
        st.download_button(
            "📥 Download Full Telemetry (CSV)",
            data=csv_data,
            file_name=f"nexus_telemetry_{selected_process.split()[0].lower()}_{int(time.time())}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_dl2:
        st.metric("Data Points", f"{len(df_export)}")
    with col_dl3:
        st.metric("File Size", f"{len(csv_data.encode()) / 1024:.1f} KB")

with tab_log:
    events = [
        {"time": "00:00.00", "event": "System initialized", "level": "INFO"},
        {"time": "00:00.05", "event": f"Process: {selected_process}", "level": "INFO"},
        {"time": "00:00.05", "event": f"Controller: {control_mode}", "level": "CONFIG"},
        {"time": "00:00.05", "event": f"Tuning: Kp={Kp}, Ki={Ki}, Kd={Kd}", "level": "CONFIG"},
        {"time": "00:00.10", "event": f"Setpoint: {target_setpoint} {cfg['unit']}", "level": "SETPOINT"},
        {"time": f"{time_data[-1]:05.2f}", "event": f"Simulation complete: SSE={kpis['Steady-State Error']}", "level": "SUCCESS" if kpis['Steady-State Error'] < 1 else "WARNING"},
    ]
    
    for evt in events:
        color = {"INFO": "#00F2FE", "CONFIG": "#8892A4", "SETPOINT": "#FFB800", "SUCCESS": "#00FF88", "WARNING": "#FF3366"}[evt["level"]]
        st.markdown(f"""
        <div style="font-family: 'JetBrains Mono'; font-size: 12px; padding: 6px 0; 
                    border-bottom: 1px solid rgba(255,255,255,0.05);">
            <span style="color: #8892A4;">[{evt['time']}]</span>
            <span style="color: {color}; margin: 0 8px;">{evt['level']}</span>
            <span style="color: #E8ECF1;">{evt['event']}</span>
        </div>
        """, unsafe_allow_html=True)

with tab_archive:
    if st.button("💾 Save Simulation to Cloud Database", use_container_width=True):
        if supabase and st.session_state.user:
            try:
                record = {
                    "user_id": st.session_state.user.id,
                    "process_type": selected_process,
                    "setpoint": target_setpoint,
                    "kp": Kp, "ki": Ki, "kd": Kd,
                    "iae": kpis["IAE"],
                    "ise": kpis["ISE"],
                    "overshoot": kpis["Overshoot"],
                    "settling_time": kpis["Settling Time"],
                    "steady_state_error": kpis["Steady-State Error"]
                }
                supabase.table("pid_simulations").insert(record).execute()
                st.success("✅ Simulation record saved to Supabase PostgreSQL.")
            except Exception as e:
                st.error(f"❌ Archive failed: {str(e)[:80]}")
        else:
            st.warning("⚠️ Supabase not configured or user not authenticated.")
    
    st.markdown("""
    <div style="background: rgba(15, 22, 35, 0.6); border-radius: 8px; padding: 16px; margin-top: 12px;">
        <p style="font-size: 12px; color: #8892A4; margin: 0;">
            Cloud archive stores: Process Type, PID Gains, Performance KPIs, User ID, and Timestamp.
            Historical data enables trend analysis and tuning optimization across sessions.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align: center; padding: 20px 0; font-family: 'JetBrains Mono'; font-size: 11px; color: #8892A4;">
    NEXUS v3.0 | Industrial PID Operations Platform | 
    Developed by <span style="color: #00F2FE;">Ali Nasreddine Benseffa</span> | 
    © 2026 Automation Engineering
</div>
""", unsafe_allow_html=True)
