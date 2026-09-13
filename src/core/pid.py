import time
from typing import Optional, Tuple


class IndustrialPID:
    """Industrial-grade PID Controller with Anti-Windup and Derivative-on-Measurement."""

    def __init__(
        self,
        kp: float = 1.0,
        ki: float = 0.0,
        kd: float = 0.0,
        setpoint: float = 0.0,
        output_limits: Tuple[float, float] = (0.0, 100.0),
        sample_time: float = 0.05,
    ):
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.setpoint = float(setpoint)
        self.out_min, self.out_max = output_limits
        self.sample_time = float(sample_time)

        # Internal state
        self._last_time = time.monotonic()
        self._integral = 0.0
        self._last_pv: Optional[float] = None
        self._last_output = 0.0

    def reset(self) -> None:
        """Reset internal states for safe bumpless transfer."""
        self._integral = 0.0
        self._last_pv = None
        self._last_output = 0.0
        self._last_time = time.monotonic()

    def update(self, pv: float, current_time: Optional[float] = None) -> float:
        """Compute PID output based on Process Variable (PV)."""
        now = current_time if current_time is not None else time.monotonic()
        dt = now - self._last_time

        # If dt is zero or negligible, avoid division by zero
        if dt <= 0.0:
            dt = 1e-4

        error = self.setpoint - pv

        # 1. Proportional Term
        p_term = self.kp * error

        # 2. Derivative Term (Derivative on PV to eliminate derivative kick)
        if self._last_pv is not None and dt > 0:
            d_pv = pv - self._last_pv
            d_term = -self.kd * (d_pv / dt)
        else:
            d_term = 0.0

        # 3. Integral Term with Anti-Windup Clamping
        unsaturated_output = p_term + self._integral + d_term

        clamped = (unsaturated_output > self.out_max) or (unsaturated_output < self.out_min)
        same_direction = (error > 0 and unsaturated_output >= self.out_max) or (
            error < 0 and unsaturated_output <= self.out_min
        )

        if not (clamped and same_direction):
            self._integral += self.ki * error * dt

        # Output calculation & saturation
        output = p_term + self._integral + d_term
        output = max(self.out_min, min(self.out_max, output))

        # State updates
        self._last_pv = pv
        self._last_time = now
        self._last_output = output

        return output