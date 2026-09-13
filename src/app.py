import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from core.pid import IndustrialPID

# إعداد الصفحة وتطبيق طابع الـ SCADA المظلم
st.set_page_config(
    page_title="Industrial PID & SCADA System",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تخصيص الواجهة بتصميم OLED / Cyberpunk
st.markdown(
    """
<style>
    .stApp {
        background-color: #0A0A0A;
        color: #E0E0E0;
    }
    .css-1d391kg, .stSidebar {
        background-color: #121212;
        border-right: 1px solid #1F1F1F;
    }
    h1, h2, h3 {
        color: #00E5FF !important;
        font-family: 'Courier New', monospace;
    }
    .metric-box {
        background: #141414;
        border-left: 3px solid #00E5FF;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("⚡ Industrial SCADA & PID Controller")
st.caption("Industrial automation engine & closed-loop response visualizer")

# --- الشريط الجانبي: إعدادات المتحكم والمحاكاة ---
st.sidebar.header("🎛️ بارامترات PID الصناعي")
kp = st.sidebar.number_input("الكسب التناسبي (Kp)", min_value=0.0, max_value=50.0, value=2.5, step=0.1)
ki = st.sidebar.number_input("الكسب التكاملي (Ki)", min_value=0.0, max_value=20.0, value=0.8, step=0.05)
kd = st.sidebar.number_input("الكسب التفاضلي (Kd)", min_value=0.0, max_value=10.0, value=0.15, step=0.01)

st.sidebar.markdown("---")
st.sidebar.header("🎯 معايير التشغيل (Setpoints)")
setpoint = st.sidebar.slider("القيمة المستهدفة (Setpoint)", min_value=0.0, max_value=100.0, value=60.0)
sim_steps = st.sidebar.slider("مدة المحاكاة (خطوات زمنية)", min_value=100, max_value=500, value=250)

# زر إعادة الضبط
if st.sidebar.button("🔄 إعادة ضبط المنظومة"):
    st.session_state.history = []
    st.rerun()

# --- محرك المحاكاة الفيزيائية (First-Order Process Model) ---
# نموذج استجابة فيزيائية لنظام حراري أو محرك: dy/dt = (-y + K*u) / tau
dt = 0.05
tau = 2.0     # الثابت الزمني للنظام (Time constant)
k_plant = 1.0 # معامل كسب النظام

pid = IndustrialPID(
    kp=kp,
    ki=ki,
    kd=kd,
    setpoint=setpoint,
    output_limits=(0.0, 100.0),
    sample_time=dt,
)

# تشغيل حلقة المحاكاة
pv = 0.0
time_records = []
pv_records = []
sp_records = []
mv_records = []

sim_time = 0.0
for step in range(sim_steps):
    # حساب إشارة التحكم (MV)
    mv = pid.update(pv=pv, current_time=sim_time)
    
    # محاكاة استجابة النظام الفيزيائي
    dpv = ((k_plant * mv) - pv) / tau * dt
    pv += dpv
    
    # تسجيل القياسات
    time_records.append(round(sim_time, 2))
    pv_records.append(pv)
    sp_records.append(setpoint)
    mv_records.append(mv)
    
    sim_time += dt

# --- مؤشرات SCADA الحية ---
col1, col2, col3, col4 = st.columns(4)
current_error = setpoint - pv_records[-1]

col1.metric("القيمة المقاسة (PV)", f"{pv_records[-1]:.2f}", delta=f"{pv_records[-1]-setpoint:.2f}")
col2.metric("القيمة المستهدفة (SP)", f"{setpoint:.2f}")
col3.metric("إشارة الخرج (MV)", f"{mv_records[-1]:.2f} %")
col4.metric("نسبة الخطأ (Error)", f"{current_error:.2f}", delta_color="inverse")

# --- المخطط البياني التفاعلي (Plotly SCADA View) ---
fig = go.Figure()

# منحنى Setpoint
fig.add_trace(go.Scatter(
    x=time_records,
    y=sp_records,
    mode='lines',
    name='Setpoint (SP)',
    line=dict(color='#FFD700', width=2, dash='dash')
))

# منحنى Process Variable (PV)
fig.add_trace(go.Scatter(
    x=time_records,
    y=pv_records,
    mode='lines',
    name='Process Value (PV)',
    line=dict(color='#00E5FF', width=2.5)
))

# منحنى خرج المتحكم (MV) على المحور الثانوي
fig.add_trace(go.Scatter(
    x=time_records,
    y=mv_records,
    mode='lines',
    name='Control Output (MV %)',
    line=dict(color='#FF3D00', width=1.5),
    yaxis='y2'
))

# تخصيص مظهر الرسم ليتطابق مع واجهات التحكم الصناعية
fig.update_layout(
    paper_bgcolor='#0A0A0A',
    plot_bgcolor='#121212',
    font=dict(color='#E0E0E0', family='Courier New'),
    title="Real-Time Dynamic Step Response",
    xaxis=dict(title="الزمن (ثانية)", gridcolor='#1F1F1F', zerolinecolor='#1F1F1F'),
    yaxis=dict(title="الاستجابة (PV / SP)", gridcolor='#1F1F1F', zerolinecolor='#1F1F1F'),
    yaxis2=dict(
        title="خرج التحكم (MV %)",
        overlaying='y',
        side='right',
        range=[0, 105],
        showgrid=False
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=60, b=40),
    height=500
)

st.plotly_chart(fig, use_container_width=True)