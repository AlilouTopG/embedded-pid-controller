# ⚙️ Universal Embedded PID Digital Twin Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://embedded-pid-controller-kg9raqqjhr7pxmmodwcjjn.streamlit.app/?demo_role=engineer)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%20%26%20Auth-green)](https://supabase.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)

An industrial-grade control system simulator and **Digital Twin platform** designed for real-time process monitoring, PID calibration, and Hardware-in-the-Loop (HIL) testing. It combines multi-physics simulation engines, industrial telemetry gateways, secure user authentication via **Supabase Auth**, and persistent cloud storage protected by **Row-Level Security (RLS)**.

---

## 🚀 Live Demo

Experience the platform live in Control Engineer mode:  
👉 **[Launch NEXUS Operations Platform](https://embedded-pid-controller-kg9raqqjhr7pxmmodwcjjn.streamlit.app/?demo_role=engineer)**

---

## 🌟 Key Features

* **🎛️ Multi-Physical Process Dynamics (Digital Twin):**
  * **Thermal Furnace (°C):** Heater duty vs. ambient dissipation.
  * **Liquid Level Tank (m):** Inflow valve vs. hydrostatic discharge.
  * **DC Motor Speed (RPM):** Transient electrical response with rotational inertia.
  * **Gas Tank Pressure (bar):** Compressible gas vessel dynamics.
* **🌐 Industrial Telemetry & Gateways:**
  * **Modbus TCP:** Interface for industrial PLCs.
  * **MQTT IoT Gateway:** Real-time pub/sub telemetry streaming.
  * **Serial / USB:** Direct communication with microcontrollers (ESP32 / Arduino).
* **⚙️ Advanced PID Control & Tuning:**
  * Manual tuning for $K_p$, $K_i$, and $K_d$.
  * **Ziegler-Nichols Auto-Tune** (Classic, PI-Optimized, and Modern PID).
  * Actuator saturation limits with Anti-Windup protection.
* **📊 Dual-Axis Real-Time Telemetry & KPIs:**
  * Live tracking of Process Variable (PV) vs. Setpoint (SP) and PWM output.
  * Real-time metrics: Settling Time, Rise Time, Overshoot, and error integrals (IAE / ISE).
* **🔐 Enterprise Auth & Cloud Storage:**
  * User authentication via Supabase GoTrue.
  * Database isolation via PostgreSQL Row-Level Security (RLS).
  * Role-Based Access Control (Operator vs. Control Engineer).

---

## 🛠️ Architecture & Tech Stack

* **Frontend & Dashboard:** Streamlit, Plotly, Pandas
* **Simulation Engine:** Discrete-time difference equations (Python)
* **Backend & Database:** Supabase (PostgreSQL, Auth, RLS Policies)
* **Protocols:** Modbus TCP, MQTT, PySerial

---

## 💻 Quick Start (Run Locally)

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/AlilouTopG/embedded-pid-controller.git](https://github.com/AlilouTopG/embedded-pid-controller.git)
   cd embedded-pid-controller
