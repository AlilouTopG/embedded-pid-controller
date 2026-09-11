import os
import random
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client, Client

# Page Configuration
st.set_page_config(
    page_title="SCADA Twin | Industrial PID Control Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# HIGH-END INDUSTRIAL SCADA UI (CYBER-CYAN THEME CSS)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: #06090E;
        color: #C1C9D6;
    }

    [data-testid="stSidebar"] {
        background-color: #0B1017;
        border-right: 1px solid #16222F;
    }

    h1, h2, h3, h4 {
        color: #00F2FE !important;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.5px;
    }

    /* Glassmorphism Metric Cards */
    .metric-card {
        background: rgba(15, 23, 36, 0.7);
        border: 1px solid rgba(0, 242, 254, 0.15);
        border-radius: 12px;
        padding: 18px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(0, 242, 254, 0.5);
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #00F2FE;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-unit {
        font-size: 0.9rem;
        color: #94A3B8;
    }

    /* Neon Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
        color: #000000 !important;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00F2FE 0%, #3A7BD5 100%);
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.6);
        transform: translateY(-1px);
    }

    /* Status Indicator Badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .status-optimal { background: rgba(0, 255, 136, 0.15); color: #00FF88; border: 1px solid #00FF88; }
    .status-warning { background: rgba(255, 170, 0, 0.15); color: #FFAA00; border: 1px solid #FFAA00; }

    /* Customizing Sliders & Selectboxes */
    .stSlider > div { color: #00F2FE; }
    div[data-baseweb="select"] > div {
        background-color: #0F1724 !important;
        border-color: #16222F !important;
        color: #00F2FE !important;
    }
</style>
""", unsafe_allow_html=True)

# Supabase Initialization
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))

@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Session Management
if "user" not in st.session_state:
    st.session_state.user = None

query_params = st.query_params
token_from_url = query_params.get("session_token", None)

if token_from_url and st.session_state.user is None and supabase:
    try:
        res = supabase.auth.get_user(token_from_url)
        if res and res.user:
            st.session_state.user = res.user
    except Exception:
        st.query_params.clear()

# Sidebar Authentication Portal
st.sidebar.markdown("## 🔐 AUTHENTICATION")

if st.session_state.user is None:
    auth_mode = st.sidebar.radio("Mode", ["Sign In", "Sign Up"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if auth_mode == "Sign Up" and st.sidebar.button("Create Account"):
        try:
            supabase.auth.sign_up({"email": email, "password": password})
            st.sidebar.success("Account Created! You can now Sign In.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    elif auth_mode == "Sign In" and st.sidebar.button("Establish Link"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            if res.session:
                st.query_params["session_token"] = res.session.access_token
            st.rerun()
        except Exception:
            st.sidebar.error("Invalid Credentials.")
else:
    st.sidebar.markdown(f"🟢 **CONNECTED:** `{st.session_state.user.email}`")
    if st.sidebar.button("Terminate Session"):
        supabase.auth.sign_out()
        st.query_params.clear()
        st.session_state.user = None
        st.rerun()

if st.session_state.user is None:
    st.title("⚡ NEXT-GEN SCADA & PID DIGITAL TWIN")
    st.info("🔒 Authentication required to establish telemetry link with industrial twin.")
    st.stop()

# ---------------------------------------------------------
# CONTROL PANEL & SYSTEM DYNAMICS
# ---------------------------------------------------------
st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>⚡ SCADA DIGITAL TWIN ENGINE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; margin-bottom: 25px;'>Industrial Closed-Loop Controller & High-Speed Dynamic Simulator</p>", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("## 🎛️ PROCESS CONFIG")

process_type = st.sidebar.selectbox(
    "Active Process Loop",
    ["Thermal Furnace (°C)", "Liquid Level Tank (m)", "DC Motor Speed (RPM)", "Gas Tank Pressure (bar)"]
)

configs = {
    "Thermal Furnace (°C)": {"unit": "°C", "default_sp": 150.0, "max_sp": 300.0, "a_factor": 0.08, "loss_factor": 0.02, "ku": 4.5, "tu": 12.0},
    "Liquid Level Tank (m)": {"unit": "m", "default_sp": 8.0, "max_sp": 20.0, "a_factor": 0.12, "loss_factor": 0.03, "ku": 3.2, "tu": 8.5},
    "DC Motor Speed (RPM)": {"unit": "RPM", "default_sp": 1500.0, "max_sp": 3000.0, "a_factor": 15.0, "loss_factor": 0.5, "ku": 0.8, "tu": 1.2},
    "Gas Tank Pressure (bar)": {"unit": "bar", "default_sp": 6.0, "max_sp": 15.0, "a_factor": 0.05, "loss_factor": 0.01, "ku": 5.0, "tu": 15.0}
}
cfg = configs[process_type]

# Preset Tuning Buttons
st.sidebar.markdown("### 🎯 Quick PID Presets")
col_p1, col_p2 = st.sidebar.columns(2)
if col_p1.button("Smooth PID"):
    st.session_state.kp, st.session_state.ki, st.session_state.kd = 1.2, 0.1, 0.05
if col_p2.button("Fast PID"):
    st.session_state.kp, st.session_state.ki, st.session_state.kd = 4.5, 0.8, 0.3

# Controller Sliders
st.sidebar.markdown("### 🛠️ PID Gains & Control")
Kp = st.sidebar.slider("Proportional (Kp)", 0.0, 10.0, float(st.session_state.get("kp", 2.5)), 0.1)
Ki = st.sidebar.slider("Integral (Ki)", 0.0, 2.0, float(st.session_state.get("ki", 0.4)), 0.05)
Kd = st.sidebar.slider("Derivative (Kd)", 0.0, 2.0, float(st.session_state.get("kd", 0.1)), 0.01)
target_setpoint = st.sidebar.slider(f"Target Setpoint ({cfg['unit']})", 0.0, cfg["max_sp"], cfg["default_sp"], 0.5)

st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ ADVANCED MODES")
control_mode = st.sidebar.radio("Control Mode", ["Automatic (PID Closed-Loop)", "Manual Override (Direct Duty Cycle)"])
manual_output = st.sidebar.slider("Manual Output Duty Cycle (%)", 0.0, 100.0, 50.0) if "Manual" in control_mode else 0.0

enable_noise = st.sidebar.checkbox("Inject Environmental Turbulence")
noise_level = st.sidebar.slider("Turbulence Intensity (%)", 0.0, 5.0, 1.2, 0.1) if enable_noise else 0.0

# ---------------------------------------------------------
# SIMULATION ENGINE
# ---------------------------------------------------------
dt, steps = 0.05, 400
prev_err, integral, pv_value = 0.0, 0.0, 0.0
time_b, pv_b, sp_b, u_b = [], [], [], []

for step in range(steps):
    t = step * dt
    err = target_setpoint - pv_value
    
    if "Automatic" in control_mode:
        integral += 0.5 * Ki * dt * err
        integral = max(0.0, min(100.0, integral))
        deriv = Kd * (err - prev_err) / dt
        u = max(0.0, min(100.0, (Kp * err + integral + deriv)))
    else:
        u = manual_output

    prev_err = err
    noise = random.gauss(0, noise_level) if enable_noise else 0.0
    pv_value = max(0.0, pv_value + (u * cfg["a_factor"] - pv_value * cfg["loss_factor"]) * dt + noise)
    
    time_b.append(t)
    pv_b.append(pv_value)
    sp_b.append(target_setpoint)
    u_b.append(u)

# Performance Metrics Calculation
max_pv = max(pv_b)
overshoot = max(0.0, ((max_pv - target_setpoint) / target_setpoint) * 100) if target_setpoint > 0 else 0.0
steady_error = abs(target_setpoint - pv_b[-1])

# ---------------------------------------------------------
# DASHBOARD TELEMETRY DISPLAY
# ---------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Active System</div>
        <div class="metric-value">{process_type.split()[0]}</div>
        <div class="metric-unit">Industrial Loop</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Current Process Value</div>
        <div class="metric-value" style="color:#00F2FE;">{pv_b[-1]:.2f} <span class="metric-unit">{cfg['unit']}</span></div>
        <div class="status-badge status-optimal">Live Telemetry</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Max Overshoot</div>
        <div class="metric-value" style="color:{'#FF0055' if overshoot > 15 else '#00FF88'};">{overshoot:.1f}%</div>
        <div class="metric-unit">Transient Spike</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Steady State Error</div>
        <div class="metric-value" style="color:{'#FFAA00' if steady_error > 1.0 else '#00FF88'};">{steady_error:.2f} <span class="metric-unit">{cfg['unit']}</span></div>
        <div class="status-badge {'status-optimal' if steady_error < 1.0 else 'status-warning'}">Loop Precision</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# HIGH-TECH PLOTLY CHART
# ---------------------------------------------------------
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, subplot_titles=("PROCESS VARIABLE vs SETPOINT", "ACTUATOR CONTROL OUTPUT (%)"))

# Plot 1: PV and SP
fig.add_trace(go.Scatter(x=time_b, y=sp_b, mode='lines', name='Setpoint Target', line=dict(color='#FF0055', width=2, dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=time_b, y=pv_b, mode='lines', name='Process Variable (PV)', line=dict(color='#00F2FE', width=3)), row=1, col=1)

# Plot 2: Control Signal U
fig.add_trace(go.Scatter(x=time_b, y=u_b, mode='lines', name='Control Signal (U)', line=dict(color='#00FF88', width=2), fill='tozeroy', fillcolor='rgba(0,255,136,0.05)'), row=2, col=1)

fig.update_layout(
    height=550,
    paper_bgcolor='#06090E',
    plot_bgcolor='#0B1017',
    font=dict(color='#94A3B8', family='JetBrains Mono'),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#16222F', row=1, col=1)
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#16222F', title_text="Time (Seconds)", row=2, col=1)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#16222F', title_text=f"State ({cfg['unit']})", row=1, col=1)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#16222F', title_text="Output Duty (%)", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# DATA EXPORT & CLOUD LOGGING
# ---------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    if st.button("💾 SAVE RUN TO SUPABASE"):
        if supabase:
            try:
                data = {"user_id": st.session_state.user.id, "setpoint": target_setpoint, "kp": Kp, "ki": Ki, "kd": Kd}
                supabase.table("pid_simulations").insert(data).execute()
                st.success("Telemetry successfully archived in cloud database!")
            except Exception as e:
                st.error(f"Failed to log run: {e}")

with col_b:
    df_telemetry = pd.DataFrame({"Time_s": time_b, "Setpoint": sp_b, "Process_Variable": pv_b, "Control_Signal": u_b})
    csv_data = df_telemetry.to_csv(index=False).encode("utf-8")
    st.download_button("📥 EXPORT TELEMETRY CSV", csv_data, f"scada_run_{process_type.split()[0]}.csv", "text/csv")

# Historical Records Display
st.markdown("---")
st.markdown("### 📊 HISTORICAL CALIBRATION LOGS")

if st.button("🔄 FETCH RECENT CLOUD LOGS"):
    if supabase:
        try:
            res = supabase.table("pid_simulations").select("*").eq("user_id", st.session_state.user.id).execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data)[["id", "created_at", "setpoint", "kp", "ki", "kd"]], use_container_width=True)
            else:
                st.info("No logs recorded for this account yet.")
        except Exception as e:
            st.error(f"Cloud fetch error: {e}")