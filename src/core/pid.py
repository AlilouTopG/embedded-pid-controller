class IndustrialPID:
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
