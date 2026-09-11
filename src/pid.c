#include "../include/pid.h"

void PID_Init(PIDController *pid, double Kp, double Ki, double Kd, 
              double dt, double lim_min, double lim_max) {
    pid->Kp = Kp;
    pid->Ki = Ki;
    pid->Kd = Kd;
    pid->dt = dt;
    pid->lim_min = lim_min;
    pid->lim_max = lim_max;

    // Default integral saturation limits to overall limits
    pid->lim_min_int = lim_min;
    pid->lim_max_int = lim_max;

    PID_Reset(pid);
}

void PID_Reset(PIDController *pid) {
    pid->prev_error = 0.0;
    pid->integral = 0.0;
}

double PID_Update(PIDController *pid, double setpoint, double measurement) {
    // 1. Error calculation
    double error = setpoint - measurement;

    // 2. Proportional term
    double proportional = pid->Kp * error;

    // 3. Integral term (Trapezoidal / Euler integration)
    pid->integral += 0.5 * pid->Ki * pid->dt * (error + pid->prev_error);

    // Anti-Windup: Clamp integral term to prevent saturation overshoot
    if (pid->integral > pid->lim_max_int) {
        pid->integral = pid->lim_max_int;
    } else if (pid->integral < pid->lim_min_int) {
        pid->integral = pid->lim_min_int;
    }

    // 4. Derivative term (Band-limited differentiation)
    double derivative = pid->Kd * (error - pid->prev_error) / pid->dt;

    // 5. Compute total controller output
    double output = proportional + pid->integral + derivative;

    // 6. Output Clamping (Saturation limit)
    if (output > pid->lim_max) {
        output = pid->lim_max;
    } else if (output < pid->lim_min) {
        output = pid->lim_min;
    }

    // 7. Store error for the next step
    pid->prev_error = error;

    return output;
}
