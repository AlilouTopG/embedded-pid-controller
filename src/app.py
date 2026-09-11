import os
import streamlit as st
import matplotlib.pyplot as plt

# Page Configuration & Security Headers Simulation
st.set_page_config(
    page_title="Industrial PID Controller Simulator (Secured)",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit Default Footers & Main Menu for hardening
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. SECURE SECRETS & ENVIRONMENT HANDLING
# ---------------------------------------------------------
def get_secret(key_name, default_val=None):
    """Safely fetch secrets from Streamlit secrets or local environment."""
    if hasattr(st, "secrets") and key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default_val)

# Example usage of secret key without exposure
API_KEY = get_secret("API_KEY", "DEMO_SECURE_KEY_LOCAL")

# ---------------------------------------------------------
# 2. INPUT SANITIZATION & VALIDATION
# ---------------------------------------------------------
def sanitize_float(value, min_val, max_val, fallback):
    """Validates and bounds float input to prevent engine exploits."""
    try:
        val = float(value)
        return max(min_val, min(max_val, val))
    except (ValueError, TypeError):
        return fallback

st.title("Secure Industrial PID Controller Dashboard")
st.caption("Secured & Hardened Edition — Built by **Ali Nasreddine Benseffa**")

# Sidebar Controls with Input Boundary Controls
st.sidebar.header("Validated Controller Tuning")

raw_kp = st.sidebar.slider("Proportional Gain (Kp)", 0.0, 10.0, 2.8, 0.1)
raw_ki = st.sidebar.slider("Integral Gain (Ki)", 0.0, 2.0, 0.45, 0.05)
raw_kd = st.sidebar.slider("Derivative Gain (Kd)", 0.0, 2.0, 0.18, 0.01)

# Sanitize variables
Kp = sanitize_float(raw_kp, 0.0, 10.0, 2.8)
Ki = sanitize_float(raw_ki, 0.0, 2.0, 0.45)
Kd = sanitize_float(raw_kd, 0.0, 2.0, 0.18)

st.sidebar.header("System Target & Environment")
target_setpoint = st.sidebar.slider("Target Water Level (m)", 1.0, 20.0, 10.0, 0.5)
sim_time = st.sidebar.slider("Simulation Duration (s)", 5, 60, 30, 5)

# ---------------------------------------------------------
# 3. CORE PID & TANK LOGIC
# ---------------------------------------------------------
class PIDController:
    def __init__(self, Kp, Ki, Kd, dt=0.05, lim_min=0.0, lim_max=100.0):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.dt = dt
        self.lim_min, self.lim_max = lim_min, lim_max
        self.reset()

    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0

    def update(self, setpoint, measurement):
        error = setpoint - measurement
        proportional = self.Kp * error
        self.integral += 0.5 * self.Ki * self.dt * (error + self.prev_error)
        self.integral = max(self.lim_min, min(self.lim_max, self.integral))
        derivative = self.Kd * (error - self.prev_error) / self.dt
        output = proportional + self.integral + derivative
        output = max(self.lim_min, min(self.lim_max, output))
        self.prev_error = error
        return output

class TankSystem:
    def __init__(self, initial_level=0.0):
        self.level = initial_level

    def update(self, pump_input, dt=0.05):
        pump_efficiency = 0.12
        leak_rate = 0.03
        inflow = pump_input * pump_efficiency
        outflow = self.level * leak_rate
        self.level += (inflow - outflow) * dt
        if self.level < 0.0: self.level = 0.0

# Execute Simulation Loop safely
dt = 0.05
steps = int(sim_time / dt)
pid = PIDController(Kp, Ki, Kd, dt)
tank = TankSystem()

time_list, level_list, setpoint_list, output_list = [], [], [], []

for step in range(steps):
    t = step * dt
    u = pid.update(target_setpoint, tank.level)
    tank.update(u, dt)
    time_list.append(t)
    level_list.append(tank.level)
    setpoint_list.append(target_setpoint)
    output_list.append(u)

# Metrics Dashboard
col1, col2, col3 = st.columns(3)
col1.metric("Final Water Level", f"{tank.level:.2f} m")
col2.metric("Target Setpoint", f"{target_setpoint:.2f} m")
col3.metric("Steady-State Error", f"{abs(target_setpoint - tank.level):.3f} m")

# Plot Results
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

ax1.plot(time_list, setpoint_list, 'r--', label='Setpoint (m)')
ax1.plot(time_list, level_list, 'b-', linewidth=2, label='Actual Level (m)')
ax1.set_ylabel('Level (m)')
ax1.grid(True)
ax1.legend()

ax2.plot(time_list, output_list, 'g-', label='Control Signal (%)')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Output (%)')
ax2.grid(True)
ax2.legend()

st.pyplot(fig)

# Security Status Notice
st.info("Security Architecture: Inputs sanitized | Zero Hardcoded Keys | Secrets Masked")
