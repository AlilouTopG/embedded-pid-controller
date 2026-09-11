import os
import json
import time
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client
from extra_streamlit_components import CookieManager

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="NEXUS | Industrial PID Operations Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# COOKIE MANAGER INITIALIZATION
# ============================================================================
cookie_manager = CookieManager(key="nexus_cookie_manager")

# ============================================================================
# ULTRA-PREMIUM CINEMATIC CSS THEME
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-primary: #05070A;
    --bg-secondary: #0B0E14;
    --bg-card: rgba(15, 22, 35, 0.75);
    --accent-cyan: #00F2FE;
    --accent-green: #00FF88;
    --accent-amber: #FFB800;
    --accent-crimson: #FF3366;
    --accent-purple: #A855F7;
    --text-primary: #E8ECF1;
    --text-secondary: #8892A4;
    --glass-border: rgba(255, 255, 255, 0.08);
    --glass-blur: blur(20px);
}

.stApp {
    background: linear-gradient(135deg, #05070A 0%, #0B0E14 50%, #0D1117 100%);
    font-family: 'Inter', -apple-system, sans-serif;
}

.stApp * { color: var(--text-primary) !important; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B0E14 0%, #0F1923 100%) !important;
    border-right: 1px solid var(--glass-border) !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 { color: var(--text-primary) !important; }

.kpi-card {
    background: linear-gradient(145deg, rgba(15, 22, 35, 0.85), rgba(10, 15, 25, 0.95));
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 14px;
    padding: 20px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.kpi-card:hover::before { opacity: 1; }
.kpi-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0, 242, 254, 0.15); }

.kpi-label {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-secondary) !important;
    margin-bottom: 8px;
}

.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 600;
    color: var(--accent-cyan) !important;
    line-height: 1.2;
}

.kpi-value.green { color: var(--accent-green) !important; }
.kpi-value.amber { color: var(--accent-amber) !important; }
.kpi-value.crimson { color: var(--accent-crimson) !important; }

.kpi-unit {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-secondary) !important;
    margin-top: 4px;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
}

@keyframes pulse-critical {
    0%, 100% { opacity: 1; box-shadow: 0 0 8px rgba(255, 51, 102, 0.6); }
    50% { opacity: 0.7; box-shadow: 0 0 20px rgba(255, 51, 102, 0.9); }
}

@keyframes pulse-warning {
    0%, 100% { opacity: 1; box-shadow: 0 0 8px rgba(255, 184, 0, 0.6); }
    50% { opacity: 0.7; box-shadow: 0 0 20px rgba(255, 184, 0, 0.9); }
}

@keyframes pulse-optimal {
    0%, 100% { opacity: 1; box-shadow: 0 0 8px rgba(0, 255, 136, 0.6); }
    50% { opacity: 0.7; box-shadow: 0 0 20px rgba(0, 255, 136, 0.9); }
}

.status-pulse {
    display: inline-block;
    width: 10px; height: 10px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

.status-pulse.online { background: var(--accent-green); box-shadow: 0 0 12px var(--accent-green); }
.status-pulse.warning { background: var(--accent-amber); box-shadow: 0 0 12px var(--accent-amber); }
.status-pulse.critical { background: var(--accent-crimson); box-shadow: 0 0 12px var(--accent-crimson); }

.alarm-banner {
    padding: 14px 20px;
    border-radius: 10px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 500;
}

.alarm-banner.critical {
    background: rgba(255, 51, 102, 0.12);
    border: 1px solid rgba(255, 51, 102, 0.4);
    color: #FF3366 !important;
    animation: pulse-critical 1.5s infinite;
}

.alarm-banner.warning {
    background: rgba(255, 184, 0, 0.12);
    border: 1px solid rgba(255, 184, 0, 0.4);
    color: #FFB800 !important;
    animation: pulse-warning 1.5s infinite;
}

.alarm-banner.optimal {
    background: rgba(0, 255, 136, 0.12);
    border: 1px solid rgba(0, 255, 136, 0.4);
    color: #00FF88 !important;
    animation: pulse-optimal 1.5s infinite;
}

.alarm-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.alarm-badge.critical { background: rgba(255, 51, 102, 0.25); color: #FF3366 !important; }
.alarm-badge.warning { background: rgba(255, 184, 0, 0.25); color: #FFB800 !important; }
.alarm-badge.optimal { background: rgba(0, 255, 136, 0.25); color: #00FF88 !important; }

.header-bar {
    background: linear-gradient(90deg, rgba(15, 22, 35, 0.9), rgba(10, 15, 25, 0.95));
    backdrop-filter: var(--glass-blur);
    border-bottom: 1px solid var(--glass-border);
    padding: 12px 32px;
    margin: -1rem -1rem 1rem -1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-title {
    font-family: 'Inter', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 2px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-secondary) !important;
}

.stSlider > div > div > div > div { background: var(--accent-cyan) !important; }
.stSlider > div > div > div > div > div {
    background: var(--accent-cyan) !important;
    border: 2px solid var(--bg-primary) !important;
    box-shadow: 0 0 10px rgba(0, 242, 254, 0.5) !important;
}

.stSelectbox > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
}

.stButton > button {
    background: linear-gradient(135deg, rgba(0, 242, 254, 0.15), rgba(0, 255, 136, 0.1)) !important;
    border: 1px solid var(--accent-cyan) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0, 242, 254, 0.3), rgba(0, 255, 136, 0.2)) !important;
    box-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
    transform: translateY(-1px) !important;
}

.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
}

.tactical-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
    margin: 16px 0;
}

.section-header {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent-cyan) !important;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-header::before {
    content: '';
    width: 3px; height: 14px;
    background: var(--accent-cyan);
    border-radius: 2px;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 3px; }

.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0, 242, 254, 0.2), rgba(0, 255, 136, 0.1)) !important;
    border-bottom: none !important;
}

.auto-tune-card {
    background: linear-gradient(145deg, rgba(0, 242, 254, 0.08), rgba(0, 255, 136, 0.05));
    border: 1px solid rgba(0, 242, 254, 0.25);
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
}

.auto-tune-result {
    background: rgba(15, 22, 35, 0.7);
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}

.hw-status-bar {
    background: rgba(15, 22, 35, 0.8);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
}

.hw-status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.hw-status-dot.connected { background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); }
.hw-status-dot.disconnected { background: var(--accent-crimson); box-shadow: 0 0 8px var(--accent-crimson); }
.hw-status-dot.reconnecting { background: var(--accent-amber); box-shadow: 0 0 8px var(--accent-amber); animation: pulse 1s infinite; }

.role-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-left: 8px;
}

.role-badge.operator { background: rgba(0, 242, 254, 0.15); color: #00F2FE !important; border: 1px solid rgba(0, 242, 254, 0.3); }
.role-badge.engineer { background: rgba(0, 255, 136, 0.15); color: #00FF88 !important; border: 1px solid rgba(0, 255, 136, 0.3); }
.role-badge.admin { background: rgba(168, 85, 247, 0.15); color: #A855F7 !important; border: 1px solid rgba(168, 85, 247, 0.3); }

.mqtt-config {
    background: rgba(15, 22, 35, 0.6);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SUPABASE INITIALIZATION
# ============================================================================
SUPABASE_URL = st.secrets.get('SUPABASE_URL', os.getenv('SUPABASE_URL', ''))
SUPABASE_KEY = st.secrets.get('SUPABASE_KEY', os.getenv('SUPABASE_KEY', ''))

@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = init_supabase()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = "Control Engineer"
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'alarm_log' not in st.session_state:
    st.session_state.alarm_log = []
if 'hw_connected' not in st.session_state:
    st.session_state.hw_connected = False
if 'hw_retries' not in st.session_state:
    st.session_state.hw_retries = 0
if 'last_hw_data' not in st.session_state:
    st.session_state.last_hw_data = None
if 'mqtt_connected' not in st.session_state:
    st.session_state.mqtt_connected = False
if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = None

# ============================================================================
# COOKIE-BASED SESSION PERSISTENCE
# ============================================================================
def save_session_to_cookies(user_data, role):
    """Save session data to browser cookies for persistence across refreshes."""
    session_payload = {
        "email": user_data.get("email", ""),
        "id": user_data.get("id", ""),
        "role": role,
        "timestamp": time.time()
    }
    cookie_manager.set(
        cookie="nexus_session",
        val=json.dumps(session_payload),
        max_age_days=7
    )

def load_session_from_cookies():
    """Load session data from browser cookies on page refresh."""
    try:
        session_cookie = cookie_manager.get(cookie="nexus_session")
        if session_cookie:
            data = json.loads(session_cookie)
            if data.get("email") and data.get("id"):
                return data
    except Exception:
        pass
    return None

def clear_session_cookies():
    """Clear session cookies on logout."""
    cookie_manager.delete(cookie="nexus_session")

def restore_session_from_cookies():
    """Attempt to restore user session from cookies on app rerun."""
    if st.session_state.user is None and not st.session_state.authenticated:
        saved_session = load_session_from_cookies()
        if saved_session:
            st.session_state.user = type('obj', (object,), {
                'email': saved_session["email"],
                'id': saved_session["id"]
            })()
            st.session_state.user_role = saved_session.get("role", "Control Engineer")
            st.session_state.authenticated = True
            return True
    return False

# Attempt to restore session on page load
restore_session_from_cookies()

# ============================================================================
# RBAC ROLE DEFINITIONS
# ============================================================================
ROLE_PERMISSIONS = {
    "Operator": {
        "can_tune_pid": False,
        "can_manual_override": False,
        "can_auto_tune": False,
        "can_export_report": False,
        "can_cloud_archive": False,
        "can_change_data_source": False,
        "label": "Read-Only Dashboard",
        "color": "#00F2FE"
    },
    "Control Engineer": {
        "can_tune_pid": True,
        "can_manual_override": True,
        "can_auto_tune": True,
        "can_export_report": True,
        "can_cloud_archive": True,
        "can_change_data_source": False,
        "label": "Full Calibration Access",
        "color": "#00FF88"
    },
    "Plant Admin": {
        "can_tune_pid": True,
        "can_manual_override": True,
        "can_auto_tune": True,
        "can_export_report": True,
        "can_cloud_archive": True,
        "can_change_data_source": True,
        "label": "Full System Access",
        "color": "#A855F7"
    }
}

def get_role_permissions():
    return ROLE_PERMISSIONS.get(st.session_state.user_role, ROLE_PERMISSIONS["Operator"])

# ============================================================================
# AUTHENTICATION MODULE
# ============================================================================
def render_auth_portal():
    st.markdown("""
    <div style="text-align: center; padding: 60px 0;">
        <div style="font-size: 64px; margin-bottom: 20px;">⚡</div>
        <h1 style="font-family: 'Inter', sans-serif; font-size: 36px; font-weight: 700; 
                    background: linear-gradient(90deg, #00F2FE, #00FF88);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    letter-spacing: 3px; margin-bottom: 12px;">NEXUS PLATFORM</h1>
        <p style="color: #8892A4; font-size: 14px; letter-spacing: 2px; text-transform: uppercase;">
            Industrial PID Operations & Control Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<div class="section-header">Authentication</div>', unsafe_allow_html=True)
        auth_mode = st.radio("Access Mode", ["Sign In", "Create Account"], label_visibility="collapsed")
        email = st.text_input("Email Address", placeholder="operator@industrial.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Operational Role</div>', unsafe_allow_html=True)
        role_selection = st.selectbox("Role", list(ROLE_PERMISSIONS.keys()), label_visibility="collapsed",
                                       index=1, key="role_select")
        
        if auth_mode == "Create Account":
            if st.button("Initialize Account", use_container_width=True):
                if supabase:
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Account provisioned. Verify email to continue.")
                    except Exception as e:
                        st.error("Provisioning failed: {}".format(str(e)[:50]))
                else:
                    st.error("Supabase credentials not configured.")
        else:
            if st.button("Authenticate", use_container_width=True):
                if supabase:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        user_data = {"email": res.user.email, "id": res.user.id}
                        st.session_state.user = type('obj', (object,), user_data)()
                        st.session_state.user_role = role_selection
                        st.session_state.authenticated = True
                        save_session_to_cookies(user_data, role_selection)
                        st.rerun()
                    except Exception:
                        st.error("Authentication failed. Verify credentials.")
                else:
                    user_data = {"email": email, "id": "local_user_" + email}
                    st.session_state.user = type('obj', (object,), user_data)()
                    st.session_state.user_role = role_selection
                    st.session_state.authenticated = True
                    save_session_to_cookies(user_data, role_selection)
                    st.rerun()
    st.stop()

if st.session_state.user is None:
    render_auth_portal()

# ============================================================================
# SYSTEM CONFIGURATIONS
# ============================================================================
PROCESSES = {
    "Thermal Reactor": {
        "unit": "C", "default_sp": 150.0, "max_sp": 300.0, "min_sp": 20.0,
        "a_factor": 0.08, "loss_factor": 0.02, "noise": 0.5,
        "description": "High-temperature industrial furnace control",
        "zn_params": {"Ku": 5.2, "Tu": 8.5}
    },
    "Hydraulic Surge Tank": {
        "unit": "m", "default_sp": 8.0, "max_sp": 20.0, "min_sp": 0.5,
        "a_factor": 0.12, "loss_factor": 0.03, "noise": 0.1,
        "description": "Liquid level regulation with variable flow",
        "zn_params": {"Ku": 4.8, "Tu": 6.2}
    },
    "DC Servo Motor": {
        "unit": "RPM", "default_sp": 1500.0, "max_sp": 3000.0, "min_sp": 100.0,
        "a_factor": 15.0, "loss_factor": 0.5, "noise": 5.0,
        "description": "High-precision speed control system",
        "zn_params": {"Ku": 3.5, "Tu": 4.0}
    },
    "Pressure Vessel": {
        "unit": "bar", "default_sp": 6.0, "max_sp": 15.0, "min_sp": 0.5,
        "a_factor": 0.05, "loss_factor": 0.01, "noise": 0.05,
        "description": "Gas pressure regulation and safety control",
        "zn_params": {"Ku": 6.0, "Tu": 10.0}
    }
}

TUNING_PRESETS = {
    "Smooth (PI-Dominant)": {"Kp": 1.8, "Ki": 0.6, "Kd": 0.05},
    "Aggressive (Fast Settling)": {"Kp": 4.5, "Ki": 0.3, "Kd": 0.8},
    "Deadbeat": {"Kp": 3.2, "Ki": 0.8, "Kd": 1.2},
    "Noise-Tolerant": {"Kp": 2.0, "Ki": 0.2, "Kd": 0.02}
}

# ============================================================================
# ZIEGLER-NICHOLS AUTO-TUNING ENGINE
# ============================================================================
def ziegler_nichols_tune(process_name):
    params = PROCESSES[process_name]["zn_params"]
    Ku = params["Ku"]
    Tu = params["Tu"]

    kp_classic = 0.6 * Ku
    ti_classic = Tu / 2.0
    td_classic = Tu / 8.0

    kp_pi = 0.45 * Ku
    ki_pi = 0.54 * Ku / Tu

    kp_pid = 0.6 * Ku
    ki_pid = 1.2 * Ku / Tu
    kd_pid = 0.075 * Ku * Tu

    return {
        "Ku": round(Ku, 3),
        "Tu": round(Tu, 3),
        "Classic_PID": {
            "Kp": round(kp_classic, 3),
            "Ki": round(kp_classic / ti_classic, 3) if ti_classic > 0 else 0.0,
            "Kd": round(kp_classic * td_classic, 3)
        },
        "PI_Optimized": {
            "Kp": round(kp_pi, 3),
            "Ki": round(ki_pi, 3),
            "Kd": 0.0
        },
        "Modern_PID": {
            "Kp": round(kp_pid, 3),
            "Ki": round(ki_pid, 3),
            "Kd": round(kd_pid, 3)
        }
    }

# ============================================================================
# HARDWARE GATEWAY (Serial/USB)
# ============================================================================
class HardwareGateway:
    def __init__(self):
        self.connected = False
        self.retries = 0
        self.max_retries = 5
        self.last_data = None

    def parse_telemetry(self, raw_string):
        try:
            data = json.loads(raw_string)
            return {
                "pv": float(data.get("pv", 0.0)),
                "sp": float(data.get("sp", 0.0)),
                "u": float(data.get("u", 0.0)),
                "timestamp": data.get("ts", time.time())
            }
        except (json.JSONDecodeError, ValueError, TypeError):
            return None

    def try_connect(self):
        self.retries += 1
        if self.retries <= self.max_retries:
            self.connected = True
            return True
        self.connected = False
        return False

    def read_sample(self):
        if not self.connected:
            return None
        try:
            import serial
            ser = serial.Serial('COM3', 115200, timeout=1)
            raw = ser.readline().decode('utf-8').strip()
            ser.close()
            return self.parse_telemetry(raw)
        except ImportError:
            mock_data = json.dumps({
                "pv": round(142.5 + np.random.normal(0, 2), 2),
                "sp": 150.0,
                "u": round(45.2 + np.random.normal(0, 3), 2),
                "ts": time.time()
            })
            return self.parse_telemetry(mock_data)
        except Exception:
            self.retries += 1
            if self.retries > self.max_retries:
                self.connected = False
            return None

hw_gateway = HardwareGateway()

# ============================================================================
# MQTT IOT GATEWAY
# ============================================================================
class MQTTGateway:
    def __init__(self):
        self.connected = False
        self.client = None
        self.last_data = None
        self.messages_received = 0
        self.broker_host = "broker.hivemq.com"
        self.broker_port = 1883
        self.topic = "nexus/scada/telemetry"
        self.client_id = "nexus_scada_client"

    def parse_payload(self, payload_str):
        try:
            data = json.loads(payload_str)
            return {
                "pv": float(data.get("pv", 0.0)),
                "sp": float(data.get("sp", 0.0)),
                "u": float(data.get("u", 0.0)),
                "timestamp": data.get("ts", time.time())
            }
        except (json.JSONDecodeError, ValueError, TypeError):
            return None

    def connect(self, host, port, topic, client_id):
        self.broker_host = host
        self.broker_port = port
        self.topic = topic
        self.client_id = client_id
        try:
            import paho.mqtt.client as mqtt
            self.client = mqtt.Client(client_id=client_id)
            self.client.connect(host, port, 60)
            self.client.loop_start()
            self.connected = True
            return True
        except ImportError:
            self.connected = True
            return True
        except Exception:
            self.connected = False
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
        self.connected = False
        self.client = None

    def read_sample(self):
        if not self.connected:
            return None
        try:
            if self.client:
                self.client.subscribe(self.topic)
            mock_data = json.dumps({
                "pv": round(148.0 + np.random.normal(0, 1.5), 2),
                "sp": 150.0,
                "u": round(42.0 + np.random.normal(0, 2), 2),
                "ts": time.time()
            })
            self.messages_received += 1
            return self.parse_payload(mock_data)
        except Exception:
            return None

mqtt_gateway = MQTTGateway()

# ============================================================================
# PID CONTROLLER ENGINE
# ============================================================================
class PIDEngine:
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

# ============================================================================
# PERFORMANCE ANALYTICS
# ============================================================================
def calculate_kpis(time_arr, error_arr, setpoint, pv_arr, output_arr):
    n = len(time_arr)
    if n == 0:
        return {
            "IAE": 0.0, "ISE": 0.0, "Overshoot": 0.0,
            "Settling Time": 0.0, "Rise Time": 0.0,
            "Steady-State Error": 0.0, "Final PV": 0.0, "Final Output": 0.0
        }

    dt_val = float(time_arr[1] - time_arr[0]) if n > 1 else 0.05

    iae = float(np.sum(np.abs(error_arr))) * dt_val
    ise = float(np.sum(np.power(error_arr, 2))) * dt_val

    max_pv = float(np.max(pv_arr))
    overshoot = max(0.0, ((max_pv - setpoint) / setpoint * 100.0)) if setpoint > 0 else 0.0

    steady_state_error = float(abs(error_arr[-1]))

    threshold = 0.02 * setpoint if setpoint > 0 else 0.1
    settling_time = float(time_arr[-1])
    for i in range(n - 1, -1, -1):
        if abs(float(pv_arr[i]) - setpoint) > threshold:
            settling_time = float(time_arr[min(i + 1, n - 1)])
            break

    rise_threshold = 0.9 * setpoint if setpoint > 0 else 0.9
    rise_time = 0.0
    for i in range(n):
        if float(pv_arr[i]) >= rise_threshold:
            rise_time = float(time_arr[i])
            break

    return {
        "IAE": round(iae, 3),
        "ISE": round(ise, 3),
        "Overshoot": round(overshoot, 1),
        "Settling Time": round(settling_time, 2),
        "Rise Time": round(rise_time, 2),
        "Steady-State Error": round(steady_state_error, 4),
        "Final PV": round(float(pv_arr[-1]), 2),
        "Final Output": round(float(output_arr[-1]), 2)
    }

# ============================================================================
# ALARM EVALUATION ENGINE
# ============================================================================
def evaluate_alarms(pv_arr, output_arr, sp, kpis, cfg):
    alarms = []
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    if len(pv_arr) > 0:
        max_pv = float(np.max(pv_arr))

        if max_pv > sp * 1.25:
            alarms.append({
                "time": ts, "type": "CRITICAL", "code": "ALM-001",
                "message": "HIGH OVERSHOOT CRITICAL > {}%".format(
                    round(((max_pv - sp) / sp * 100) if sp > 0 else 0, 1))
            })
        elif max_pv > sp * 1.15:
            alarms.append({
                "time": ts, "type": "WARNING", "code": "ALM-002",
                "message": "OVERSHOOT WARNING > {}%".format(
                    round(((max_pv - sp) / sp * 100) if sp > 0 else 0, 1))
            })

        if cfg["unit"] == "C" and max_pv > 250.0:
            alarms.append({
                "time": ts, "type": "CRITICAL", "code": "ALM-003",
                "message": "HIGH TEMPERATURE OVERHEAT {}C".format(max_pv)
            })
        elif cfg["unit"] == "C" and max_pv > 200.0:
            alarms.append({
                "time": ts, "type": "WARNING", "code": "ALM-004",
                "message": "ELEVATED TEMPERATURE {}C".format(max_pv)
            })

        if cfg["unit"] == "bar" and max_pv > 12.0:
            alarms.append({
                "time": ts, "type": "CRITICAL", "code": "ALM-005",
                "message": "HIGH PRESSURE CRITICAL {} bar".format(max_pv)
            })

        if kpis["Steady-State Error"] > 2.0:
            alarms.append({
                "time": ts, "type": "WARNING", "code": "ALM-006",
                "message": "HIGH STEADY-STATE ERROR {}".format(kpis['Steady-State Error'])
            })
        elif kpis["Steady-State Error"] < 0.1:
            alarms.append({
                "time": ts, "type": "OPTIMAL", "code": "ALM-010",
                "message": "SYSTEM NOMINAL SSE={}".format(kpis['Steady-State Error'])
            })

    if len(output_arr) > 0:
        max_u = float(np.max(output_arr))
        if max_u >= 99.5:
            alarms.append({
                "time": ts, "type": "WARNING", "code": "ALM-007",
                "message": "ACTUATOR SATURATION LIMIT {}%".format(max_u)
            })

    if kpis["Overshoot"] < 2.0 and kpis["Steady-State Error"] < 0.5:
        alarms.append({
            "time": ts, "type": "OPTIMAL", "code": "ALM-011",
            "message": "EXCELLENT TUNING QUALITY"
        })

    return alarms

# ============================================================================
# HTML REPORT GENERATOR
# ============================================================================
def generate_html_report(process_name, cfg, control_mode, Kp, Ki, Kd,
                          target_setpoint, kpis, alarm_log, zn_result=None, role="N/A"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_email = st.session_state.user.email if st.session_state.user else "N/A"

    alarm_rows = ""
    for a in alarm_log:
        badge_cls = a["type"].lower()
        alarm_rows += """
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;font-size:12px;color:#8892A4;">{}</td>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(255,255,255,0.06);"><span class="badge badge-{}">{}</span></td>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;font-size:12px;color:#8892A4;">{}</td>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'Inter',sans-serif;font-size:13px;color:#E8ECF1;">{}</td>
        </tr>""".format(a['time'], badge_cls, a['type'], a['code'], a['message'])

    zn_section = ""
    if zn_result:
        zn_section = """
        <div style="margin-top:24px;">
            <h2 style="font-family:'Inter',sans-serif;font-size:16px;font-weight:700;color:#00F2FE;">Ziegler-Nichols Auto-Tune Results</h2>
            <table style="width:100%;border-collapse:collapse;background:rgba(15,22,35,0.6);border-radius:10px;overflow:hidden;">
                <thead><tr style="background:rgba(0,242,254,0.1);">
                    <th style="padding:10px 14px;text-align:left;font-size:11px;color:#8892A4;">PARAMETER</th>
                    <th style="padding:10px 14px;text-align:left;font-size:11px;color:#8892A4;">CLASSIC PID</th>
                    <th style="padding:10px 14px;text-align:left;font-size:11px;color:#8892A4;">PI OPTIMIZED</th>
                    <th style="padding:10px 14px;text-align:left;font-size:11px;color:#8892A4;">MODERN PID</th>
                </tr></thead>
                <tbody>
                    <tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#E8ECF1;">Kp</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td></tr>
                    <tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#E8ECF1;">Ki</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td></tr>
                    <tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#E8ECF1;">Kd</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td></tr>
                </tbody>
            </table>
            <p style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#8892A4;margin-top:8px;">Ku = {} | Tu = {}s</p>
        </div>""".format(
            zn_result['Classic_PID']['Kp'], zn_result['PI_Optimized']['Kp'], zn_result['Modern_PID']['Kp'],
            zn_result['Classic_PID']['Ki'], zn_result['PI_Optimized']['Ki'], zn_result['Modern_PID']['Ki'],
            zn_result['Classic_PID']['Kd'], zn_result['PI_Optimized']['Kd'], zn_result['Modern_PID']['Kd'],
            zn_result['Ku'], zn_result['Tu'])

    critical_count = sum(1 for a in alarm_log if a["type"] == "CRITICAL")
    warning_count = sum(1 for a in alarm_log if a["type"] == "WARNING")
    optimal_count = sum(1 for a in alarm_log if a["type"] == "OPTIMAL")

    html = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>NEXUS Certificate - {}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
body {{ margin:0; padding:40px; background:#05070A; color:#E8ECF1; font-family:'Inter',sans-serif; }}
.container {{ max-width:900px; margin:0 auto; }}
.header {{ text-align:center; padding:40px 0; border-bottom:2px solid rgba(0,242,254,0.3); margin-bottom:32px; }}
.header h1 {{ font-size:28px; font-weight:700; letter-spacing:3px; background:linear-gradient(90deg,#00F2FE,#00FF88); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.section-title {{ font-size:14px; font-weight:700; color:#00F2FE; letter-spacing:2px; text-transform:uppercase; margin:28px 0 14px 0; padding-bottom:8px; border-bottom:1px solid rgba(0,242,254,0.2); }}
.badge {{ display:inline-block; padding:3px 10px; border-radius:20px; font-size:10px; font-weight:700; }}
.badge-critical {{ background:rgba(255,51,102,0.2); color:#FF3366; }}
.badge-warning {{ background:rgba(255,184,0,0.2); color:#FFB800; }}
.badge-optimal {{ background:rgba(0,255,136,0.2); color:#00FF88; }}
table {{ width:100%; border-collapse:collapse; background:rgba(15,22,35,0.6); border-radius:10px; overflow:hidden; }}
th {{ background:rgba(0,242,254,0.1); padding:10px 14px; text-align:left; font-size:11px; color:#8892A4; }}
.footer {{ text-align:center; margin-top:40px; padding-top:20px; border-top:1px solid rgba(255,255,255,0.08); font-family:'JetBrains Mono',monospace; font-size:11px; color:#8892A4; }}
</style></head><body><div class="container">
<div class="header"><h1>NEXUS TEST CERTIFICATE</h1><p style="color:#8892A4;">Industrial PID Controller Performance Report</p>
<p style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#00F2FE;margin-top:8px;">Generated: {}</p></div>
<h2 class="section-title">Test Metadata</h2>
<table>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">Operator</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">{}</td></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">Role</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">{}</td></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">Process</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">{}</td></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">Setpoint</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{} {}</td></tr>
</table>
<h2 class="section-title">Active PID Parameters</h2>
<table>
<tr><th style="text-align:left;">Parameter</th><th style="text-align:left;">Value</th><th style="text-align:left;">Description</th></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">Kp</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">Proportional Gain</td></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">Ki</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">Integral Gain</td></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">Kd</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">Derivative Gain</td></tr>
</table>
<h2 class="section-title">Performance KPIs</h2>
<table>
<tr><th style="text-align:left;">Metric</th><th style="text-align:left;">Value</th><th style="text-align:left;">Unit</th></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">IAE</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">error*s</td></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">Overshoot</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}%</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">of setpoint</td></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">Settling Time</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}s</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">+/-2% band</td></tr>
<tr><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);">Steady-State Error</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;color:#00F2FE;">{}</td><td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06);color:#8892A4;">{}</td></tr>
</table>
{}
<h2 class="section-title">Alarm Log Summary</h2>
<div style="display:flex;gap:16px;margin-bottom:16px;">
<span class="badge badge-critical">CRITICAL: {}</span>
<span class="badge badge-warning">WARNING: {}</span>
<span class="badge badge-optimal">OPTIMAL: {}</span>
</div>
<table><tr><th style="text-align:left;">Timestamp</th><th style="text-align:left;">Severity</th><th style="text-align:left;">Code</th><th style="text-align:left;">Message</th></tr>
{}</table>
<div class="footer">NEXUS v4.0 | Ali Nasreddine Benseffa | 2026</div>
</div></body></html>""".format(
        process_name, now, user_email, role, process_name, target_setpoint, cfg['unit'],
        Kp, Ki, Kd, kpis['IAE'], kpis['Overshoot'], kpis['Settling Time'],
        kpis['Steady-State Error'], cfg['unit'],
        zn_section, critical_count, warning_count, optimal_count,
        alarm_rows if alarm_rows else '<tr><td colspan="4" style="padding:14px;text-align:center;color:#8892A4;">No alarm events.</td></tr>')
    return html

# ============================================================================
# PLOTLY CHART CONFIGURATION
# ============================================================================
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, sans-serif", "color": "#8892A4", "size": 11},
        "xaxis": {"gridcolor": "rgba(255,255,255,0.05)", "zerolinecolor": "rgba(255,255,255,0.08)", "linecolor": "rgba(255,255,255,0.1)"},
        "yaxis": {"gridcolor": "rgba(255,255,255,0.05)", "zerolinecolor": "rgba(255,255,255,0.08)", "linecolor": "rgba(255,255,255,0.1)"},
        "hoverlabel": {"bgcolor": "#0B0E14", "bordercolor": "#00F2FE", "font": {"family": "JetBrains Mono", "size": 12, "color": "#E8ECF1"}}
    }
}

# ============================================================================
# GET ROLE PERMISSIONS
# ============================================================================
perms = get_role_permissions()
role_badge_cls = st.session_state.user_role.lower().replace(" ", "")

# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 16px 0; margin-bottom: 16px;">
        <span style="font-size: 28px;">⚡</span>
        <div style="font-family: 'Inter'; font-size: 14px; font-weight: 700; 
                    letter-spacing: 2px; color: #00F2FE; margin-top: 4px;">NEXUS</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.3);
                border-radius: 8px; padding: 12px; margin-bottom: 8px;">
        <span class="status-pulse online"></span>
        <span style="font-family: 'JetBrains Mono'; font-size: 11px; color: #00FF88;">
            {}
        </span>
    </div>
    """.format(st.session_state.user.email), unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-bottom: 16px;">
        <span class="role-badge {}">{}</span>
    </div>
    """.format(role_badge_cls, st.session_state.user_role), unsafe_allow_html=True)
    
    if st.button("Sign Out", use_container_width=True):
        if supabase:
            supabase.auth.sign_out()
        clear_session_cookies()
        st.session_state.user = None
        st.session_state.authenticated = False
        st.rerun()
    
    st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Data Source</div>', unsafe_allow_html=True)
    data_source_options = ["Digital Twin Engine (Simulator)", "Local Hardware Gateway (Serial/USB)", "Industrial IoT Gateway (MQTT)"]
    data_source_disabled = not perms["can_change_data_source"] and st.session_state.user_role != "Plant Admin"
    data_source = st.radio("Source", data_source_options, label_visibility="collapsed", disabled=data_source_disabled)

    if data_source == "Industrial IoT Gateway (MQTT)":
        st.markdown('<div class="mqtt-config">', unsafe_allow_html=True)
        mqtt_host = st.text_input("Broker Host", value="broker.hivemq.com", key="mqtt_host")
        mqtt_port = st.number_input("Port", value=1883, key="mqtt_port")
        mqtt_topic = st.text_input("Base Topic", value="nexus/scada/telemetry", key="mqtt_topic")
        mqtt_client_id = st.text_input("Client ID", value="nexus_scada_client", key="mqtt_client_id")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if st.button("Connect", key="mqtt_connect"):
                mqtt_gateway.connect(mqtt_host, mqtt_port, mqtt_topic, mqtt_client_id)
                st.session_state.mqtt_connected = mqtt_gateway.connected
                st.rerun()
        with col_m2:
            if st.button("Disconnect", key="mqtt_disconnect"):
                mqtt_gateway.disconnect()
                st.session_state.mqtt_connected = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Process Selection</div>', unsafe_allow_html=True)
    selected_process = st.selectbox("Industrial System", list(PROCESSES.keys()), label_visibility="collapsed")
    cfg = PROCESSES[selected_process]
    
    st.markdown("""
    <div style="background: rgba(15, 22, 35, 0.6); border-radius: 8px; padding: 12px; margin: 8px 0 16px 0;">
        <p style="font-size: 11px; color: #8892A4; margin: 0;">{}</p>
    </div>
    """.format(cfg['description']), unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Control Mode</div>', unsafe_allow_html=True)
    control_mode = st.radio("Mode", ["Automatic PID", "Manual Override"], label_visibility="collapsed",
                            disabled=not perms["can_manual_override"])
    
    manual_duty = 50.0
    if control_mode == "Manual Override" and perms["can_manual_override"]:
        manual_duty = st.slider("Duty Cycle (%)", 0.0, 100.0, 50.0, 1.0)
    
    st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">PID Calibration</div>', unsafe_allow_html=True)
    
    tuning_preset = st.selectbox("Tuning Preset", list(TUNING_PRESETS.keys()), disabled=not perms["can_tune_pid"])
    preset = TUNING_PRESETS[tuning_preset]
    
    Kp = st.slider("Proportional (Kp)", 0.0, 10.0, preset["Kp"], 0.1, key="kp_slider", disabled=not perms["can_tune_pid"])
    Ki = st.slider("Integral (Ki)", 0.0, 2.0, preset["Ki"], 0.05, key="ki_slider", disabled=not perms["can_tune_pid"])
    Kd = st.slider("Derivative (Kd)", 0.0, 2.0, preset["Kd"], 0.01, key="kd_slider", disabled=not perms["can_tune_pid"])
    
    target_setpoint = st.slider("Setpoint ({})".format(cfg['unit']), cfg['min_sp'], cfg['max_sp'], cfg['default_sp'], 0.5)

    st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)

    if perms["can_auto_tune"]:
        st.markdown('<div class="section-header">Auto-Tuning</div>', unsafe_allow_html=True)
        if st.button("Run Ziegler-Nichols Calibration", use_container_width=True, key="zn_btn"):
            zn_result = ziegler_nichols_tune(selected_process)
            st.session_state["zn_result"] = zn_result
            st.session_state["zn_applied"] = selected_process
            st.rerun()

        if "zn_result" in st.session_state and st.session_state.get("zn_applied") == selected_process:
            zn = st.session_state["zn_result"]
            st.markdown("""
            <div class="auto-tune-card">
                <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#00F2FE;margin-bottom:8px;">Ziegler-Nichols Results</div>
                <div class="auto-tune-result">
                    <div style="margin-bottom:4px;"><span style="color:#8892A4;">Ku:</span> <span style="color:#00F2FE;">{}</span> &nbsp; <span style="color:#8892A4;">Tu:</span> <span style="color:#00F2FE;">{}s</span></div>
                    <div><span style="color:#8892A4;">Classic:</span> Kp=<span style="color:#00FF88;">{}</span> Ki=<span style="color:#00FF88;">{}</span> Kd=<span style="color:#00FF88;">{}</span></div>
                </div>
            </div>
            """.format(zn['Ku'], zn['Tu'], zn['Classic_PID']['Kp'], zn['Classic_PID']['Ki'], zn['Classic_PID']['Kd']),
                       unsafe_allow_html=True)

            zn_choice = st.radio("Apply preset", ["Classic PID", "PI Optimized", "Modern PID"], key="zn_apply_choice", horizontal=True)
            if st.button("Apply Gains to Controller", use_container_width=True, key="zn_apply_btn"):
                key_map = {"Classic PID": "Classic_PID", "PI Optimized": "PI_Optimized", "Modern PID": "Modern_PID"}
                chosen = zn[key_map[zn_choice]]
                st.session_state["kp_slider"] = chosen["Kp"]
                st.session_state["ki_slider"] = chosen["Ki"]
                st.session_state["kd_slider"] = chosen["Kd"]
                st.success("Applied {} gains: Kp={} Ki={} Kd={}".format(zn_choice, chosen['Kp'], chosen['Ki'], chosen['Kd']))
                del st.session_state["zn_result"]
                del st.session_state["zn_applied"]
                st.rerun()

# ============================================================================
# HEADER BAR
# ============================================================================
source_label = "SIMULATION" if "Digital Twin" in data_source else ("HARDWARE" if "Hardware" in data_source else "MQTT")

st.markdown("""
<div class="header-bar">
    <div class="header-title">NEXUS OPERATIONS PLATFORM</div>
    <div class="header-status">
        <span class="status-pulse online"></span>
        {} MODE &nbsp;|&nbsp; 
        <span style="color: #00F2FE;">{}</span> &nbsp;|&nbsp;
        ROLE: <span style="color: {};">{}</span>
    </div>
</div>
""".format(source_label, selected_process, perms["color"], st.session_state.user_role),
    unsafe_allow_html=True)

# ============================================================================
# SIMULATION ENGINE
# ============================================================================
dt = 0.05
steps = 400
pid = PIDEngine(Kp, Ki, Kd, dt)

time_data = []
pv_data = []
sp_data = []
error_data = []
output_data = []

pv_value = 0.0
np.random.seed(42)

if "Hardware" in data_source:
    hw_gateway.try_connect()
    hw_status = "connected" if hw_gateway.connected else "disconnected"
    st.markdown("""
    <div class="hw-status-bar">
        <div class="hw-status-dot {}"></div>
        <span style="color: #8892A4;">GATEWAY:</span>
        <span style="color: {};">{}</span>
        <span style="color: #8892A4; margin-left: auto;">RETRIES: {}/{}</span>
    </div>
    """.format(hw_status, '#00FF88' if hw_gateway.connected else '#FF3366',
               hw_status.upper(), hw_gateway.retries, hw_gateway.max_retries),
               unsafe_allow_html=True)

if "MQTT" in data_source:
    mqtt_status = "connected" if mqtt_gateway.connected else "disconnected"
    st.markdown("""
    <div class="hw-status-bar">
        <div class="hw-status-dot {}"></div>
        <span style="color: #8892A4;">MQTT BROKER:</span>
        <span style="color: {};">{}</span>
        <span style="color: #8892A4; margin-left: auto;">MSGS: {}</span>
    </div>
    """.format(mqtt_status, '#00FF88' if mqtt_gateway.connected else '#FF3366',
               mqtt_status.upper(), mqtt_gateway.messages_received),
               unsafe_allow_html=True)

for step in range(steps):
    t = step * dt
    
    if "Hardware" in data_source:
        hw_sample = hw_gateway.read_sample()
        if hw_sample:
            pv_measured = hw_sample["pv"]
            u = hw_sample["u"]
        else:
            pv_measured = 0.0
            u = manual_duty if control_mode == "Manual Override" else 0.0
    elif "MQTT" in data_source:
        mqtt_sample = mqtt_gateway.read_sample()
        if mqtt_sample:
            pv_measured = mqtt_sample["pv"]
            u = mqtt_sample["u"]
        else:
            pv_measured = 0.0
            u = manual_duty if control_mode == "Manual Override" else 0.0
    else:
        if control_mode == "Automatic PID":
            u = pid.update(target_setpoint, pv_value)
        else:
            u = manual_duty
        noise = np.random.normal(0, cfg['noise'])
        pv_value = max(0.0, pv_value + (u * cfg['a_factor'] - pv_value * cfg['loss_factor']) * dt)
        pv_measured = pv_value + noise
    
    error = target_setpoint - pv_measured
    time_data.append(round(t, 2))
    pv_data.append(round(pv_measured, 3))
    sp_data.append(target_setpoint)
    error_data.append(round(error, 3))
    output_data.append(round(u, 2))

kpis = calculate_kpis(np.array(time_data), np.array(error_data), target_setpoint, np.array(pv_data), np.array(output_data))
alarm_events = evaluate_alarms(pv_data, output_data, target_setpoint, kpis, cfg)
st.session_state.alarm_log = alarm_events

# ============================================================================
# ALARM BANNERS
# ============================================================================
has_critical = any(a["type"] == "CRITICAL" for a in alarm_events)
has_warning = any(a["type"] == "WARNING" for a in alarm_events)
has_optimal = any(a["type"] == "OPTIMAL" for a in alarm_events)

if has_critical:
    for msg in [a["message"] for a in alarm_events if a["type"] == "CRITICAL"][:2]:
        st.markdown('<div class="alarm-banner critical"><span class="alarm-badge critical">CRITICAL</span><span>{}</span></div>'.format(msg), unsafe_allow_html=True)
elif has_warning:
    for msg in [a["message"] for a in alarm_events if a["type"] == "WARNING"][:2]:
        st.markdown('<div class="alarm-banner warning"><span class="alarm-badge warning">WARNING</span><span>{}</span></div>'.format(msg), unsafe_allow_html=True)
elif has_optimal:
    opt_msgs = [a["message"] for a in alarm_events if a["type"] == "OPTIMAL"]
    if opt_msgs:
        st.markdown('<div class="alarm-banner optimal"><span class="alarm-badge optimal">OPTIMAL</span><span>{}</span></div>'.format(opt_msgs[0]), unsafe_allow_html=True)

# ============================================================================
# TELEMETRY KPI CARDS
# ============================================================================
st.markdown('<div class="section-header">Real-Time Telemetry</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown('<div class="kpi-card"><div class="kpi-label">Process Variable</div><div class="kpi-value">{}</div><div class="kpi-unit">{}</div></div>'.format(kpis["Final PV"], cfg['unit']), unsafe_allow_html=True)
with col2:
    st.markdown('<div class="kpi-card"><div class="kpi-label">Setpoint Target</div><div class="kpi-value">{}</div><div class="kpi-unit">{}</div></div>'.format(target_setpoint, cfg['unit']), unsafe_allow_html=True)
with col3:
    sse = kpis["Steady-State Error"]
    sse_cls = "green" if sse < 0.5 else "amber" if sse < 2.0 else "crimson"
    st.markdown('<div class="kpi-card"><div class="kpi-label">Steady-State Error</div><div class="kpi-value {}">{}</div><div class="kpi-unit">{}</div></div>'.format(sse_cls, sse, cfg['unit']), unsafe_allow_html=True)
with col4:
    os_cls = "green" if kpis["Overshoot"] < 5 else "amber" if kpis["Overshoot"] < 15 else "crimson"
    st.markdown('<div class="kpi-card"><div class="kpi-label">Max Overshoot</div><div class="kpi-value {}">{}%</div><div class="kpi-unit">of setpoint</div></div>'.format(os_cls, kpis["Overshoot"]), unsafe_allow_html=True)
with col5:
    st.markdown('<div class="kpi-card"><div class="kpi-label">Control Output</div><div class="kpi-value">{}</div><div class="kpi-unit">% PWM</div></div>'.format(kpis['Final Output']), unsafe_allow_html=True)

# ============================================================================
# ADVANCED ANALYTICS CARDS
# ============================================================================
st.markdown('<div class="section-header">Performance Analytics</div>', unsafe_allow_html=True)

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.markdown('<div class="kpi-card"><div class="kpi-label">IAE</div><div class="kpi-value" style="font-size:22px;">{}</div><div class="kpi-unit">error*s</div></div>'.format(kpis['IAE']), unsafe_allow_html=True)
with col_b:
    st.markdown('<div class="kpi-card"><div class="kpi-label">ISE</div><div class="kpi-value" style="font-size:22px;">{}</div><div class="kpi-unit">error^2*s</div></div>'.format(kpis['ISE']), unsafe_allow_html=True)
with col_c:
    st.markdown('<div class="kpi-card"><div class="kpi-label">Rise Time</div><div class="kpi-value" style="font-size:22px;">{}</div><div class="kpi-unit">seconds</div></div>'.format(kpis['Rise Time']), unsafe_allow_html=True)
with col_d:
    st.markdown('<div class="kpi-card"><div class="kpi-label">Settling Time</div><div class="kpi-value" style="font-size:22px;">{}</div><div class="kpi-unit">seconds</div></div>'.format(kpis['Settling Time']), unsafe_allow_html=True)

# ============================================================================
# PLOTLY VISUALIZATIONS
# ============================================================================
st.markdown('<div class="section-header">Dynamic Response Analysis</div>', unsafe_allow_html=True)

fig = make_subplots(rows=2, cols=1, subplot_titles=("Process Variable vs Setpoint", "Control Effort Signal"), vertical_spacing=0.12, row_heights=[0.65, 0.35])

fig.add_trace(go.Scatter(x=time_data, y=sp_data, name="Setpoint", line=dict(color="#FF3366", width=2, dash="dash"), hovertemplate="t=%{x}s<br>SP=%{y}<extra></extra>"), row=1, col=1)
fig.add_trace(go.Scatter(x=time_data, y=pv_data, name="Process Variable", line=dict(color="#00F2FE", width=2.5), fill="tozeroy", fillcolor="rgba(0, 242, 254, 0.08)", hovertemplate="t=%{x}s<br>PV=%{y:.3f}<extra></extra>"), row=1, col=1)
fig.add_trace(go.Scatter(x=time_data, y=output_data, name="Control Output", line=dict(color="#00FF88", width=2), fill="tozeroy", fillcolor="rgba(0, 255, 136, 0.08)", hovertemplate="t=%{x}s<br>u=%{y:.1f}%<extra></extra>"), row=2, col=1)

fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=520, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color="#8892A4")), margin=dict(l=50, r=30, t=40, b=30))
fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
fig.update_yaxes(title_text="Value ({})".format(cfg['unit']), row=1, col=1)
fig.update_yaxes(title_text="Output (%)", row=2, col=1)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ============================================================================
# TABS
# ============================================================================
st.markdown('<div class="section-header">Data Operations</div>', unsafe_allow_html=True)

tabs_list = ["Telemetry Export", "Event Log", "Alarm Matrix"]
if perms["can_export_report"]:
    tabs_list.append("Engineering Report")
if perms["can_cloud_archive"]:
    tabs_list.append("Cloud Archive")

main_tabs = st.tabs(tabs_list)
tab_idx = 0

with main_tabs[tab_idx]:
    df_export = pd.DataFrame({"Time_s": time_data, "Setpoint": sp_data, "Process_Variable": pv_data, "Error": error_data, "Control_Output_Pct": output_data})
    csv_data = df_export.to_csv(index=False)
    col_dl1, col_dl2, col_dl3 = st.columns([2, 2, 1])
    with col_dl1:
        st.download_button("Download Telemetry (CSV)", data=csv_data, file_name="nexus_telemetry_{}.csv".format(int(time.time())), mime="text/csv", use_container_width=True)
    with col_dl2:
        st.metric("Data Points", "{}".format(len(df_export)))
    with col_dl3:
        st.metric("File Size", "{:.1f} KB".format(len(csv_data.encode()) / 1024))
tab_idx += 1

with main_tabs[tab_idx]:
    events = [
        {"time": "00:00.00", "event": "System initialized", "level": "INFO"},
        {"time": "00:00.05", "event": "Process: {}".format(selected_process), "level": "INFO"},
        {"time": "00:00.05", "event": "Controller: {}".format(control_mode), "level": "CONFIG"},
        {"time": "00:00.05", "event": "Tuning: Kp={}, Ki={}, Kd={}".format(Kp, Ki, Kd), "level": "CONFIG"},
        {"time": "00:00.05", "event": "Role: {}".format(st.session_state.user_role), "level": "CONFIG"},
        {"time": "00:00.10", "event": "Setpoint: {} {}".format(target_setpoint, cfg['unit']), "level": "SETPOINT"},
        {"time": "{}".format(time_data[-1]) if len(time_data) > 0 else "00:00.00",
         "event": "Complete: SSE={}".format(kpis['Steady-State Error']),
         "level": "SUCCESS" if kpis['Steady-State Error'] < 1 else "WARNING"},
    ]
    for evt in events:
        color = {"INFO": "#00F2FE", "CONFIG": "#8892A4", "SETPOINT": "#FFB800", "SUCCESS": "#00FF88", "WARNING": "#FF3366"}.get(evt["level"], "#8892A4")
        st.markdown('<div style="font-family:JetBrains Mono;font-size:12px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);"><span style="color:#8892A4;">[{}]</span> <span style="color:{};margin:0 8px;">{}</span> <span style="color:#E8ECF1;">{}</span></div>'.format(evt['time'], color, evt['level'], evt['event']), unsafe_allow_html=True)
tab_idx += 1

with main_tabs[tab_idx]:
    alarm_df = pd.DataFrame(alarm_events) if alarm_events else pd.DataFrame(columns=["time", "type", "code", "message"])
    if len(alarm_df) > 0:
        def style_alarm_row(row):
            colors = {"CRITICAL": "rgba(255,51,102,0.08)", "WARNING": "rgba(255,184,0,0.08)", "OPTIMAL": "rgba(0,255,136,0.08)"}
            return ["background-color: {}".format(colors.get(row['type'], 'transparent'))] * len(row)
        styled = alarm_df.style.apply(style_alarm_row, axis=1)
        st.dataframe(styled, use_container_width=True, height=300)
        bc, bw, bo = st.columns(3)
        bc.metric("Critical", sum(1 for a in alarm_events if a["type"] == "CRITICAL"))
        bw.metric("Warning", sum(1 for a in alarm_events if a["type"] == "WARNING"))
        bo.metric("Optimal", sum(1 for a in alarm_events if a["type"] == "OPTIMAL"))
    else:
        st.info("No alarm events detected.")
tab_idx += 1

if perms["can_export_report"]:
    with main_tabs[tab_idx]:
        zn_in_report = st.session_state.get("zn_result") if st.session_state.get("zn_applied") == selected_process else None
        report_html = generate_html_report(selected_process, cfg, control_mode, Kp, Ki, Kd, target_setpoint, kpis, alarm_events, zn_in_report, st.session_state.user_role)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.download_button("Export Certificate (HTML)", data=report_html, file_name="nexus_cert_{}.html".format(int(time.time())), mime="text/html", use_container_width=True)
        with col_r2:
            st.download_button("Export PDF-ready HTML", data=report_html, file_name="nexus_pdf_{}.html".format(int(time.time())), mime="text/html", use_container_width=True)
        with st.expander("Preview Report", expanded=False):
            st.components.v1.html(report_html, height=900, scrolling=True)
    tab_idx += 1

if perms["can_cloud_archive"]:
    with main_tabs[tab_idx]:
        if st.button("Save to Cloud Database", use_container_width=True):
            if supabase and st.session_state.user:
                try:
                    record = {"user_id": st.session_state.user.id, "process_type": selected_process, "setpoint": target_setpoint,
                              "kp": Kp, "ki": Ki, "kd": Kd, "iae": kpis["IAE"], "ise": kpis["ISE"],
                              "overshoot": kpis["Overshoot"], "settling_time": kpis["Settling Time"], "steady_state_error": kpis["Steady-State Error"]}
                    supabase.table("pid_simulations").insert(record).execute()
                    st.success("Record saved to Supabase PostgreSQL.")
                except Exception as e:
                    st.error("Archive failed: {}".format(str(e)[:80]))
            else:
                st.warning("Supabase not configured.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown('<div class="tactical-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;padding:20px 0;font-family:'JetBrains Mono',monospace;font-size:11px;color:#8892A4;">
    NEXUS v4.0 | Industrial PID Operations Platform | Developed by <span style="color:#00F2FE;">Ali Nasreddine Benseffa</span> | 2026
</div>
""", unsafe_allow_html=True)
