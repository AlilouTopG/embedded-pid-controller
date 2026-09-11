# ⚙️ Universal Embedded PID Digital Twin Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://embedded-pi-id-controller-kg9raqkqghr7pxmmoudwccggn.streamlit.app)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%20%26%20Auth-green)](https://supabase.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)

An enterprise-grade, cloud-deployed industrial control system simulator and **Digital Twin platform**. It features multi-physics simulation engines, secure user authentication via **Supabase Auth**, and persistent cloud storage protected by **Row-Level Security (RLS)** policies.

---

## 🌟 Key Features

* **🔐 Enterprise-Grade Authentication:** Full signup, login, and session persistence using Supabase Auth.
* **🛡️ Row-Level Security (RLS):** Database isolation ensuring users strictly access their own calibration telemetry.
* **🎛️ Multi-Physical Process Dynamics:**
  * **Thermal Furnace (°C):** Heater duty vs. environmental thermal dissipation.
  * **Liquid Level Tank (m):** Inflow valve vs. hydrostatic discharge dynamics.
  * **DC Motor Speed (RPM):** Fast transient electrical responses with rotational inertia.
  * **Gas Tank Pressure (bar):** Compressible gas vessel dynamics under valve actuation.
* **📊 Dual-Axis Real-Time Telemetry:** Live plotting of Process Variables (PV) against Setpoints (SP) and Actuation Signal Outputs (PWM/Valve %).
* **💾 Persistent Cloud Storage:** Direct integration with Supabase PostgreSQL for logging process calibrations.

---

## 🛠️ Architecture & Tech Stack

* **Frontend & UX:** Streamlit (Custom responsive dashboard layout)
* **Mathematical Engine:** Dynamic System Difference Equations (Discrete-Time Physics)
* **Backend & Database:** Supabase (PostgreSQL, Supabase GoTrue Auth, RLS Policies)
* **Data Visualization:** Matplotlib & Pandas
* **CI/CD & Cloud:** Streamlit Cloud with Environment Secrets management
































---

## 🚀 Live Demo

Access the hosted application live:
👉 [Universal PID Control Platform](https://embedded-pi-id-controller-kg9raqkqghr7pxmmoudwccggn.streamlit.app)
