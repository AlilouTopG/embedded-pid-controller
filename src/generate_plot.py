import os
import matplotlib.pyplot as plt

class PIDController:
    def __init__(self, Kp, Ki, Kd, dt, lim_min, lim_max):
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

    def update(self, pump_input_voltage, dt):
        pump_efficiency = 0.12
        leak_rate = 0.03
        inflow = pump_input_voltage * pump_efficiency
        outflow = self.level * leak_rate
        self.level += (inflow - outflow) * dt
        if self.level < 0.0: self.level = 0.0

# Simulation Setup
dt = 0.05
pid = PIDController(Kp=2.8, Ki=0.45, Kd=0.18, dt=dt, lim_min=0.0, lim_max=100.0)
tank = TankSystem(initial_level=0.0)
target_setpoint = 10.0

time_list, level_list, setpoint_list, output_list = [], [], [], []

for step in range(600):
    t = step * dt
    u = pid.update(target_setpoint, tank.level)
    tank.update(u, dt)
    
    time_list.append(t)
    level_list.append(tank.level)
    setpoint_list.append(target_setpoint)
    output_list.append(u)

# Plotting Results
plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.plot(time_list, setpoint_list, 'r--', label='Setpoint (m)')
plt.plot(time_list, level_list, 'b-', linewidth=2, label='Actual Water Level (m)')
plt.ylabel('Level (m)')
plt.title('Embedded PID Controller - Tank Level System Step Response')
plt.grid(True)
plt.legend()

plt.subplot(2, 1, 2)
plt.plot(time_list, output_list, 'g-', label='Control Signal / Pump PWM (%)')
plt.xlabel('Time (s)')
plt.ylabel('Output (%)')
plt.grid(True)
plt.legend()

plt.tight_layout()
output_img = r"E:\embedded-pid-controller\assets\response_plot.png"
plt.savefig(output_img, dpi=300)
print(f"Response plot successfully saved to: {output_img}")
