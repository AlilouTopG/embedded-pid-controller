import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client, Client

st.set_page_config(page_title='Industrial PID Controller', page_icon='🛡️', layout='wide')

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

st.sidebar.title('🔐 Account Access')

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
    st.title('🔒 Industrial PID Controller Platform')
    st.info('Please Sign In or Create a Real Account from the sidebar to access the simulator.')
    st.stop()

st.title('⚙️ Industrial PID Digital Twin (RLS Secured)')
st.caption(f'Authenticated User ID: {st.session_state.user.id}')

Kp = st.sidebar.slider('Proportional Gain (Kp)', 0.0, 10.0, 2.8, 0.1)
Ki = st.sidebar.slider('Integral Gain (Ki)', 0.0, 2.0, 0.45, 0.05)
Kd = st.sidebar.slider('Derivative Gain (Kd)', 0.0, 2.0, 0.18, 0.01)
target_setpoint = st.sidebar.slider('Target Water Level (m)', 1.0, 20.0, 10.0, 0.5)

dt, steps = 0.05, 400
prev_err, integral, level = 0.0, 0.0, 0.0
time_b, level_b, sp_b = [], [], []

for step in range(steps):
    t = step * dt
    err = target_setpoint - level
    integral += 0.5 * Ki * dt * err
    deriv = Kd * (err - prev_err) / dt
    u = max(0.0, min(100.0, (Kp * err + integral + deriv)))
    prev_err = err
    level = max(0.0, level + (u * 0.12 - level * 0.03) * dt)
    time_b.append(t)
    level_b.append(level)
    sp_b.append(target_setpoint)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(time_b, sp_b, 'r--', label='Target Setpoint')
ax.plot(time_b, level_b, 'b-', label='Water Level')
ax.grid(True)
ax.legend()
st.pyplot(fig)

if st.button('💾 Save Simulation Run to Cloud Database'):
    try:
        data = {'user_id': st.session_state.user.id, 'setpoint': target_setpoint, 'kp': Kp, 'ki': Ki, 'kd': Kd}
        supabase.table('pid_simulations').insert(data).execute()
        st.success('Successfully saved run with Row Level Security enforcement!')
    except Exception as e:
        st.error(f'Failed to save data: {e}')
