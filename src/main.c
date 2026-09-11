#include <stdio.h>
#include <unistd.h>
#include "../include/pid.h"

// Simulated System Process (First Order System)
typedef struct {
    double level;       // Current Tank Water Level (meters)
    double flow_out;    // Constant discharge flow
} TankSystem;

void System_Update(TankSystem *tank, double pump_input_voltage, double dt) {
    // Model parameters: Pump constant and natural drain
    double pump_efficiency = 0.12; 
    double leak_rate = 0.03;

    double inflow = pump_input_voltage * pump_efficiency;
    double outflow = tank->level * leak_rate;

    // Differential Equation: dLevel/dt = Inflow - Outflow
    tank->level += (inflow - outflow) * dt;

    if (tank->level < 0.0) tank->level = 0.0; // Level cannot be negative
}

int main() {
    // Controller Configuration
    double dt = 0.1; // 100 ms loop time
    PIDController pid;
    PID_Init(&pid, 2.5, 0.4, 0.15, dt, 0.0, 100.0); // Pump PWM Duty Cycle (0-100%)

    // Plant System Initial State
    TankSystem tank = {.level = 0.0, .flow_out = 0.0};
    double target_setpoint = 10.0; // Desired level = 10.0 meters

    printf("========================================================================\n");
    printf("   EMBEDDED PID CONTROLLER SIMULATION - INDUSTRIAL TANK LEVEL CONTROL   \n");
    printf("========================================================================\n");
    printf("Time (s) | Setpoint (m) | Actual Level (m) | Control Output (%%)\n");
    printf("---------+--------------+------------------+--------------------\n");

    // Run Simulation Loop for 20 Seconds (200 steps)
    for (int step = 0; step <= 200; step++) {
        double current_time = step * dt;

        // Calculate control signal
        double control_signal = PID_Update(&pid, target_setpoint, tank.level);

        // Print values every 1 second (every 10 steps)
        if (step % 10 == 0) {
            printf("%7.1f  | %12.2f | %16.2f | %18.2f\n", 
                   current_time, target_setpoint, tank.level, control_signal);
        }

        // Apply control output to simulated hardware
        System_Update(&tank, control_signal, dt);
    }

    printf("========================================================================\n");
    printf("Simulation completed successfully.\n");

    return 0;
}
