#ifndef PID_H
#define PID_H

#include <stdbool.h>

/**
 * @brief Structure containing PID controller parameters and state.
 */
typedef struct {
    // Controller Gains
    double Kp;              // Proportional Gain
    double Ki;              // Integral Gain
    double Kd;              // Derivative Gain

    // Controller Memory (State variables)
    double prev_error;      // Previous error value for derivative
    double integral;        // Accumulated integral sum

    // Output Saturation Limits (Anti-windup & Physical limits)
    double lim_min;         // Minimum controller output
    double lim_max;         // Maximum controller output

    // Anti-Windup Limits for Integral term
    double lim_min_int;
    double lim_max_int;

    // Sampling time in seconds
    double dt;
} PIDController;

// Function Declarations
void PID_Init(PIDController *pid, double Kp, double Ki, double Kd, 
              double dt, double lim_min, double lim_max);

double PID_Update(PIDController *pid, double setpoint, double measurement);

void PID_Reset(PIDController *pid);

#endif // PID_H
