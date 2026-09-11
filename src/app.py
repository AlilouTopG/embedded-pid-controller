import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Industrial PID Controller Simulator", layout="wide")

st.title("Industrial PID Controller & Tank Level Simulator")
st.markdown("Developed by **Ali Nasreddine Benseffa** — Automation Engineering")

# Sidebar Controls
st.sidebar.header("PID Controller Parameters")
Kp = st.sidebar.slider("Proportional Gain (Kp)", 0.0, 10.0, 2.8, 0.1)
Ki = st.sidebar.slider("Integral Gain (Ki)", 0.0, 2.0, 0.45, 0.05)
Kd = st.sidebar.slider("Derivative Gain (Kd)", 0.0, 2.0, 0.18, 0.01)

st.sidebar.header("System Setpoint & Simulation")
target_setpoint = st.sidebar.slider("Target Water Level (m)", 1.0, 20.0, 10.0, 0.5)
sim_time = st.sidebar.slider("Simulation Time (seconds)", 10, 60, 30, 5)

# PID & System Logic
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

    def update(self, pump_input_voltage, dt=0.05):
        pump_efficiency = 0.12
        leak_rate = 0.03
        inflow = pump_input_voltage * pump_efficiency
        outflow = self.level * leak_rate
        self.level += (inflow - outflow) * dt
        if self.level < 0.0: self.level = 0.0

# Run Simulation
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

# Display Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Final Water Level", f"{tank.level:.2f} m")
col2.metric("Target Setpoint", f"{target_setpoint:.2f} m")
col3.metric("Steady-State Error", f"{abs(target_setpoint - tank.level):.3f} m")

# Plot Graphics
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

ax1.plot(time_list, setpoint_list, 'r--', label='Target Setpoint (m)')
ax1.plot(time_list, level_list, 'b-', linewidth=2, label='Actual Water Level (m)')
ax1.set_ylabel('Level (m)')
ax1.grid(True)
ax1.legend()

ax2.plot(time_list, output_list, 'g-', label='Control Signal / Pump Output (%)')
ax2.set_xlabel('Time (seconds)')
ax2.set_ylabel('Output (%)')
ax2.grid(True)
ax2.legend()

st.pyplot(fig)
