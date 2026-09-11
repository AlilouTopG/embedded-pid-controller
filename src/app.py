import os
import random
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client, Client
import extra_streamlit_components as stx

st.set_page_config(
    page_title="Universal Industrial PID Platform & SCADA Twin",
    page_icon="⚙️",
    layout="wide"
)

# ---------------------------------------------------------
# COOKIE MANAGER FOR PERSISTENT AUTH
# ---------------------------------------------------------
@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))

@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.warning("⚠️ Supabase Credentials missing in Secrets!")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Restore session from Cookie if available
session_token = cookie_manager.get(cookie="sb_session_token")

if "user" not in st.session_state:
    st.session_state.user = None

if session_token and st.session_state.user is None:
    try:
        res = supabase.auth.get_user(session_token)
        if res and res.user:
            st.session_state.user = res.user
    except Exception:
        cookie_manager.delete("sb_session_token")

st.sidebar.title("🔐 Enterprise Auth Portal")

if st.session_state.user is None:
    auth_mode = st.sidebar.radio("Choose Action", ["Sign In", "Sign Up"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if auth_mode == "Sign Up":
        if st.sidebar.button("Create Account"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Account created! Check email or Sign In.")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    elif auth_mode == "Sign In":
        if st.sidebar.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                if res.session:
                    cookie_manager.set("sb_session_token", res.session.access_token, key="set_token")
                st.rerun()
            except Exception as e:
                st.sidebar.error("Invalid Email or Password.")
else:
    st.sidebar.success(f"Logged in as:\n**{st.session_state.user.email}**")
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        cookie_manager.delete("sb_session_token", key="del_token")
        st.session_state.user = None
        st.rerun()

if st.session_state.user is None:
    st.title("🔒 Universal Industrial PID Control Platform")
    st.info("Please Sign In or Create an Account from the sidebar to access the Multi-Process Simulator.")
    st.stop()

# ---------------------------------------------------------
# MULTI-PROCESS CONFIGURATION & AUTO-TUNING
# ---------------------------------------------------------
st.title("⚙️ Universal Industrial PID Control Platform & Digital Twin")
st.caption(f"Authenticated User ID: `{st.session_state.user.id}` | Architecture: **Multi-Physical Twin & RLS Secured**")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Process Dynamics & Control")

process_type = st.sidebar.selectbox(
    "Select Industrial System",
    ["Thermal Furnace (°C)", "Liquid Level Tank (m)", "DC Motor Speed (RPM)", "Gas Tank Pressure (bar)"]
)

configs = {
    "Thermal Furnace (°C)": {"unit": "°C", "default_sp": 150.0, "max_sp": 300.0, "a_factor": 0.08, "loss_factor": 0.02, "ku": 4.5, "tu": 12.0},
    "Liquid Level Tank (m)": {"unit": "m", "default_sp": 8.0, "max_sp": 20.0, "a_factor": 0.12, "loss_factor": 0.03, "ku": 3.2, "tu": 8.5},
    "DC Motor Speed (RPM)": {"unit": "RPM", "default_sp": 1500.0, "max_sp": 3000.0, "a_factor": 15.0, "loss_factor": 0.5, "ku": 0.8, "tu": 1.2},
    "Gas Tank Pressure (bar)": {"unit": "bar", "default_sp": 6.0, "max_sp": 15.0, "a_factor": 0.05, "loss_factor": 0.01, "ku": 5.0, "tu": 15.0}
}

cfg = configs[process_type]

# Auto-Tuner Assistant Expander
with st.sidebar.expander("📐 Ziegler-Nichols Auto-Tuner Helper"):
    st.markdown(f"Estimated parameters for **{process_type.split()[0]}**:")
    ku = cfg["ku"]
    tu = cfg["tu"]
    st.caption(f"Ultimate Gain (Ku): {ku} | Ultimate Period (Tu): {tu}s")
    if st.button("Apply Ziegler-Nichols PID"):
        st.session_state["recommended_kp"] = round(0.6 * ku, 2)
        st.session_state["recommended_ki"] = round(2.0 * (0.6 * ku) / tu, 2)
        st.session_state["recommended_kd"] = round((0.6 * ku) * tu / 8.0, 2)
        st.success("Values calculated! Adjust sliders below to match.")

# Controller Sliders
kp_default = st.session_state.get("recommended_kp", 2.5)
ki_default = st.session_state.get("recommended_ki", 0.4)
kd_default = st.session_state.get("recommended_kd", 0.1)

Kp = st.sidebar.slider("Proportional Gain (Kp)", 0.0, 10.0, float(kp_default), 0.1)
Ki = st.sidebar.slider("Integral Gain (Ki)", 0.0, 2.0, float(ki_default), 0.05)
Kd = st.sidebar.slider("Derivative Gain (Kd)", 0.0, 2.0, float(kd_default), 0.01)
target_setpoint = st.sidebar.slider(f"Target Setpoint ({cfg['unit']})", 0.0, cfg["max_sp"], cfg["default_sp"], 0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("⚠️ Environmental Disturbance")
enable_noise = st.sidebar.checkbox("Inject Process Noise / Turbulence")
noise_level = st.sidebar.slider("Noise Amplitude (%)", 0.0, 5.0, 1.0, 0.2) if enable_noise else 0.0

# ---------------------------------------------------------
# SIMULATION ENGINE & PHYSICS RESPONSE
# ---------------------------------------------------------
dt, steps = 0.05, 400
prev_err, integral, pv_value = 0.0, 0.0, 0.0
time_b, pv_b, sp_b, u_b = [], [], [], []

for step in range(steps):
    t = step * dt
    err = target_setpoint - pv_value
    integral += 0.5 * Ki * dt * err
    integral = max(0.0, min(100.0, integral))
    deriv = Kd * (err - prev_err) / dt
    u = max(0.0, min(100.0, (Kp * err + integral + deriv)))
    prev_err = err
    
    noise = random.gauss(0, noise_level) if enable_noise else 0.0
    pv_value = max(0.0, pv_value + (u * cfg["a_factor"] - pv_value * cfg["loss_factor"]) * dt + noise)
    
    time_b.append(t)
    pv_b.append(pv_value)
    sp_b.append(target_setpoint)
    u_b.append(u)

# Telemetry Overview
col1, col2, col3, col4 = st.columns(4)
col1.metric("Active System", process_type.split()[0])
col2.metric("Current PV", f"{pv_value:.2f} {cfg['unit']}")
col3.metric("Target SP", f"{target_setpoint:.2f} {cfg['unit']}")
col4.metric("Steady Error", f"{abs(target_setpoint - pv_value):.2f} {cfg['unit']}")

# Real-time Visualizations
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

ax1.plot(time_b, sp_b, "r--", label=f"Target Setpoint ({cfg['unit']})", linewidth=2)
ax1.plot(time_b, pv_b, "b-", label=f"Process Variable ({cfg['unit']})", linewidth=2)
ax1.set_ylabel(f"Process State ({cfg['unit']})")
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.legend(loc="lower right")

ax2.plot(time_b, u_b, "g-", label="Control Signal Output (%)", linewidth=1.5)
ax2.set_xlabel("Time (seconds)")
ax2.set_ylabel("Actuation Duty Cycle (%)")
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="lower right")

plt.suptitle(f"Dynamic Response & SCADA Telemetry: {process_type}", fontsize=12)
st.pyplot(fig)

# Data Actions
df_telemetry = pd.DataFrame({"Time_s": time_b, "Setpoint": sp_b, "Process_Variable": pv_b, "Control_Signal": u_b})
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("💾 Save Calibration to Cloud Database"):
        try:
            data = {
                "user_id": st.session_state.user.id,
                "setpoint": target_setpoint,
                "kp": Kp,
                "ki": Ki,
                "kd": Kd
            }
            supabase.table("pid_simulations").insert(data).execute()
            st.success("Saved calibration telemetry to Supabase PostgreSQL!")
        except Exception as e:
            st.error(f"Failed to save data: {e}")

with col_btn2:
    csv_data = df_telemetry.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export Telemetry Run (CSV)", csv_data, f"pid_telemetry_{process_type.split()[0]}.csv", "text/csv")

# ---------------------------------------------------------
# HISTORICAL SUPABASE LOGS DISPLAY
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Historical Calibration Logs (Supabase RLS Protected)")

if st.button("🔄 Fetch My Saved Runs"):
    try:
        response = supabase.table("pid_simulations").select("*").eq("user_id", st.session_state.user.id).execute()
        logs = response.data
        if logs:
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs[["id", "created_at", "setpoint", "kp", "ki", "kd"]], use_container_width=True)
        else:
            st.info("No prior simulation logs found for your account.")
    except Exception as e:
        st.error(f"Error fetching logs: {e}")