"""
Embedded PID Controller Logic & Simulation (Pure Python Implementation)
Mirrors Discrete C-logic with Anti-Windup & Saturation Clamping.
"""

class PIDController:
    def __init__(self, Kp, Ki, Kd, dt, lim_min, lim_max):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt
        self.lim_min = lim_min
        self.lim_max = lim_max
        self.lim_min_int = lim_min
        self.lim_max_int = lim_max
        self.reset()

    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0

    def update(self, setpoint, measurement):
        error = setpoint - measurement
        proportional = self.Kp * error
        
        # Integral calculation with Anti-Windup
        self.integral += 0.5 * self.Ki * self.dt * (error + self.prev_error)
        self.integral = max(self.lim_min_int, min(self.lim_max_int, self.integral))

        # Derivative calculation
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
        if self.level < 0.0:
            self.level = 0.0

def main():
    dt = 0.1
    pid = PIDController(Kp=2.5, Ki=0.4, Kd=0.15, dt=dt, lim_min=0.0, lim_max=100.0)
    tank = TankSystem(initial_level=0.0)
    target_setpoint = 10.0

    print("=" * 72)
    print("   EMBEDDED PID CONTROLLER SIMULATION — INDUSTRIAL TANK LEVEL CONTROL   ")
    print("=" * 72)
    print(f"{'Time (s)':<10} | {'Setpoint (m)':<14} | {'Actual Level (m)':<16} | {'Control Output (%)':<18}")
    print("-" * 72)

    for step in range(201):
        current_time = step * dt
        control_signal = pid.update(target_setpoint, tank.level)

        if step % 10 == 0:
            print(f"{current_time:<10.1f} | {target_setpoint:<14.2f} | {tank.level:<16.2f} | {control_signal:<18.2f}")

        tank.update(control_signal, dt)

    print("=" * 72)
    print("Simulation completed successfully.")

if __name__ == "__main__":
    main()
