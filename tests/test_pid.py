import pytest

class PIDController:
    def __init__(self, Kp, Ki, Kd, dt=0.05, lim_min=0.0, lim_max=100.0):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.dt = dt
        self.lim_min, self.lim_max = lim_min, lim_max
        self.prev_error = 0.0
        self.integral = 0.0

    def update(self, setpoint, measurement):
        error = setpoint - measurement
        proportional = self.Kp * error
        self.integral += 0.5 * self.Ki * self.dt * (error + self.prev_error)
        self.integral = max(self.lim_min, min(self.lim_max, self.integral))
        derivative = self.Kd * (error - self.prev_error) / self.dt
        return max(self.lim_min, min(self.lim_max, proportional + self.integral + derivative))

def test_pid_zero_error():
    pid = PIDController(1.0, 0.1, 0.05)
    assert pid.update(10.0, 10.0) == 0.0

def test_pid_output_limits():
    pid = PIDController(100.0, 10.0, 1.0, lim_min=0.0, lim_max=100.0)
    output = pid.update(100.0, 0.0)
    assert output == 100.0
