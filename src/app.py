import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Industrial PID Simulation Platform",
    page_icon="",
    layout="wide"
)

# ---------------------------------------------------------
# 1. ROLE-BASED ACCESS CONTROL (RBAC) SIMULATION
# ---------------------------------------------------------
st.sidebar.title("Enterprise Portal")
user_role = st.sidebar.selectbox("Select User Role", ["Operator (Read-Only Tuning)", "Control Engineer (Full Access)"])

if user_role == "Control Engineer (Full Access)":
    st.sidebar.success("Mode: Full Calibration Enabled")
    Kp_val = st.sidebar.slider("Proportional Gain (Kp)", 0.0, 10.0, 2.8, 0.1)
    Ki_val = st.sidebar.slider("Integral Gain (Ki)", 0.0, 2.0, 0.45, 0.05)
    Kd_val = st.sidebar.slider("Derivative Gain (Kd)", 0.0, 2.0, 0.18, 0.01)
else:
    st.sidebar.info("Mode: Operator (Fixed PID Parameters)")
    Kp_val, Ki_val, Kd_val = 2.8, 0.45, 0.18
    st.sidebar.caption(f"Locked Gains -> Kp: {Kp_val} | Ki: {Ki_val} | Kd: {Kd_val}")

st.sidebar.markdown("---")
target_setpoint = st.sidebar.slider("Target Setpoint (m)", 1.0, 20.0, 10.0, 0.5)
sim_time = st.sidebar.slider("Simulation Duration (s)", 10, 100, 40, 5)

# ---------------------------------------------------------
# 2. PID & TANK ENGINE
# ---------------------------------------------------------
class PIDController:
    def __init__(self, Kp, Ki, Kd, dt=0.05):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.dt = dt
        self.prev_error = 0.0
        self.integral = 0.0

    def update(self, setpoint, measurement):
        error = setpoint - measurement
        p = self.Kp * error
        self.integral += 0.5 * self.Ki * self.dt * (error + self.prev_error)
        self.integral = max(0.0, min(100.0, self.integral))
        d = self.Kd * (error - self.prev_error) / self.dt
        self.prev_error = error
        return max(0.0, min(100.0, p + self.integral + d))

class TankSystem:
    def __init__(self):
        self.level = 0.0

    def update(self, pump_in, dt=0.05):
        inflow = pump_in * 0.12
        outflow = self.level * 0.03
        self.level = max(0.0, (self.level + (inflow - outflow) * dt))

# Run Simulation
dt = 0.05
steps = int(sim_time / dt)
pid = PIDController(Kp_val, Ki_val, Kd_val, dt)
tank = TankSystem()

time_b, level_b, sp_b, out_b = [], [], [], []
for step in range(steps):
    t = step * dt
    u = pid.update(target_setpoint, tank.level)
    tank.update(u, dt)
    time_b.append(t)
    level_b.append(tank.level)
    sp_b.append(target_setpoint)
    out_b.append(u)

# Dataframe for telemetry
df_telemetry = pd.DataFrame({
    "Time_s": time_b,
    "Setpoint_m": sp_b,
    "Water_Level_m": level_b,
    "Control_Output_Pct": out_b
})

st.title("Industrial PID Controller & Asset Digital Twin")
st.caption("Production Ready Engine | Developed by **Ali Nasreddine Benseffa**")

# Visual Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Level", f"{tank.level:.2f} m")
col2.metric("Target Level", f"{target_setpoint:.2f} m")
col3.metric("Error", f"{abs(target_setpoint - tank.level):.3f} m")
col4.metric("Role Logged", user_role.split()[0])

# Real-time Plots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5))
ax1.plot(time_b, sp_b, 'r--', label='Target Setpoint (m)')
ax1.plot(time_b, level_b, 'b-', label='Process Variable (m)')
ax1.grid(True)
ax1.legend()

ax2.plot(time_b, out_b, 'g-', label='Control Signal Output (%)')
ax2.grid(True)
ax2.legend()

st.pyplot(fig)

# Data Export Feature
st.markdown("### Operational Telemetry Data")
st.download_button(
    label="Export Simulation CSV Report",
    data=df_telemetry.to_csv(index=False),
    file_name="pid_simulation_telemetry.csv",
    mime="text/csv"
)
