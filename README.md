# Discrete PID Controller Engine in C

An embedded-C implementation of a **Discrete Proportional-Integral-Derivative (PID) Controller** featuring Anti-Windup integral protection, output signal saturation limits, and dynamic simulation for industrial plant control loops.

---

## Engineering Specifications & Architecture

### 1. Control Loop Equation
The discrete-time controller utilizes the parallel form equation with trapezoidal integration:

u(t) = Kp * e(t) + Ki * integral(e(t)) + Kd * de(t)/dt

### 2. Embedded Safety Features
- **Anti-Windup Mechanism:** Clamps the internal integral accumulator to prevent overshoot caused by actuator saturation.
- **Output Saturation Limits:** Restricts the output control signal u(t) within physical limits (e.g., PWM signal range 0% to 100%).
- **Zero-Allocation Execution:** Designed for constrained microcontroller hardware (STM32, AVR, ESP32) with zero dynamic memory allocations (malloc).

---

## Building & Running the Simulation

### Prerequisites
- GCC Compiler Toolchain
- Make build automation tool

### Compilation and Execution

    git clone https://github.com/your-username/embedded-pid-controller.git
    cd embedded-pid-controller
    make run
