import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client, Client

st.set_page_config(page_title='Universal Industrial PID Control Platform', page_icon='⚙️', layout='wide')

SUPABASE_URL = st.secrets.get('SUPABASE_URL', os.getenv('SUPABASE_URL', ''))
SUPABASE_KEY = st.secrets.get('SUPABASE_KEY', os.getenv('SUPABASE_KEY', ''))

@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.warning('⚠️ Supabase Credentials missing in Secrets!')
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if 'user' not in st.session_state:
    st.session_state.user = None

st.sidebar.title('🔐 Enterprise Auth Portal')

if st.session_state.user is None:
    auth_mode = st.sidebar.radio('Choose Action', ['Sign In', 'Sign Up'])
    email = st.sidebar.text_input('Email')
    password = st.sidebar.text_input('Password', type='password')

    if auth_mode == 'Sign Up':
        if st.sidebar.button('Create Account'):
            try:
                res = supabase.auth.sign_up({'email': email, 'password': password})
                st.sidebar.success('Account created! Check email or Sign In.')
            except Exception as e:
                st.sidebar.error(f'Error: {e}')
    elif auth_mode == 'Sign In':
        if st.sidebar.button('Login'):
            try:
                res = supabase.auth.sign_in_with_password({'email': email, 'password': password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.sidebar.error('Invalid Email or Password.')
else:
    st.sidebar.success(f'Logged in as:\n**{st.session_state.user.email}**')
    if st.sidebar.button('Logout'):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

if st.session_state.user is None:
    st.title('🔒 Universal Industrial PID Control Platform')
    st.info('Please Sign In or Create an Account from the sidebar to access the Multi-Process Simulator.')
    st.stop()

# ---------------------------------------------------------
# MULTI-PROCESS SYSTEM CONFIGURATION
# ---------------------------------------------------------
st.title('⚙️ Universal Industrial PID Control Platform')
st.caption(f'Authenticated User ID: `{st.session_state.user.id}` | Engine: **Multi-Physical Twin**')

st.sidebar.markdown('---')
st.sidebar.subheader('🎛️ Process Selection & Dynamics')

process_type = st.sidebar.selectbox(
    'Select Industrial System',
    ['Thermal Furnace (°C)', 'Liquid Level Tank (m)', 'DC Motor Speed (RPM)', 'Gas Tank Pressure (bar)']
)

# Configuration mapping based on selected process
configs = {
    'Thermal Furnace (°C)': {'unit': '°C', 'default_sp': 150.0, 'max_sp': 300.0, 'a_factor': 0.08, 'loss_factor': 0.02},
    'Liquid Level Tank (m)': {'unit': 'm', 'default_sp': 8.0, 'max_sp': 20.0, 'a_factor': 0.12, 'loss_factor': 0.03},
    'DC Motor Speed (RPM)': {'unit': 'RPM', 'default_sp': 1500.0, 'max_sp': 3000.0, 'a_factor': 15.0, 'loss_factor': 0.5},
    'Gas Tank Pressure (bar)': {'unit': 'bar', 'default_sp': 6.0, 'max_sp': 15.0, 'a_factor': 0.05, 'loss_factor': 0.01}
}

cfg = configs[process_type]

# Controller Calibration Sliders
st.sidebar.subheader('🎛️ PID Controller Calibration')
Kp = st.sidebar.slider('Proportional Gain (Kp)', 0.0, 10.0, 2.5, 0.1)
Ki = st.sidebar.slider('Integral Gain (Ki)', 0.0, 2.0, 0.4, 0.05)
Kd = st.sidebar.slider('Derivative Gain (Kd)', 0.0, 2.0, 0.1, 0.01)
target_setpoint = st.sidebar.slider(f'Target Setpoint ({cfg["unit"]})', 0.0, cfg['max_sp'], cfg['default_sp'], 0.5)

# ---------------------------------------------------------
# UNIVERSAL PID SIMULATION ENGINE
# ---------------------------------------------------------
dt, steps = 0.05, 400
prev_err, integral, pv_value = 0.0, 0.0, 0.0
time_b, pv_b, sp_b, u_b = [], [], [], []

for step in range(steps):
    t = step * dt
    err = target_setpoint - pv_value
    integral += 0.5 * Ki * dt * err
    integral = max(0.0, min(100.0, integral))
    deriv = Kd * (err - prev_err) / dt
    u = max(0.0, min(100.0, (Kp * err + integral + deriv)))
    prev_err = err
    
    # Process Physics Response Equations
    pv_value = max(0.0, pv_value + (u * cfg['a_factor'] - pv_value * cfg['loss_factor']) * dt)
    
    time_b.append(t)
    pv_b.append(pv_value)
    sp_b.append(target_setpoint)
    u_b.append(u)

# Telemetry Display
col1, col2, col3, col4 = st.columns(4)
col1.metric('Active System', process_type.split()[0])
col2.metric('Current Value', f'{pv_value:.2f} {cfg["unit"]}')
col3.metric('Target Setpoint', f'{target_setpoint:.2f} {cfg["unit"]}')
col4.metric('Error Gap', f'{abs(target_setpoint - pv_value):.2f} {cfg["unit"]}')

# Real-time Visualizations
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

ax1.plot(time_b, sp_b, 'r--', label=f'Target Setpoint ({cfg["unit"]})', linewidth=2)
ax1.plot(time_b, pv_b, 'b-', label=f'Process Variable ({cfg["unit"]})', linewidth=2)
ax1.set_ylabel(f'Process State ({cfg["unit"]})')
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='lower right')

ax2.plot(time_b, u_b, 'g-', label='Control Signal Output (%)', linewidth=1.5)
ax2.set_xlabel('Time (seconds)')
ax2.set_ylabel('PWM / Valve Actuation (%)')
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='lower right')

plt.suptitle(f'Dynamic Response & Actuation: {process_type}', fontsize=12)
st.pyplot(fig)

# Database Storage Feature
if st.button('💾 Save Process Calibration Run to Cloud Database'):
    try:
        data = {
            'user_id': st.session_state.user.id,
            'setpoint': target_setpoint,
            'kp': Kp,
            'ki': Ki,
            'kd': Kd
        }
        supabase.table('pid_simulations').insert(data).execute()
        st.success('Successfully saved calibration data to Supabase PostgreSQL!')
    except Exception as e:
        st.error(f'Failed to save data: {e}')
