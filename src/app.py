import time
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from core.pid import IndustrialPID

# 1. تهيئة الصفحة والسمة الهندسية
st.set_page_config(
    page_title="APEX-SCADA | Industrial PID Telemetry Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تخصيص واجهة Cyberpunk / OLED Dark الصناعية
st.markdown(
    """
<style>
    .stApp {
        background-color: #080808;
        color: #E2E8F0;
        font-family: 'JetBrains Mono', 'Segoe UI', monospace;
    }
    .stSidebar {
        background-color: #0E0E10 !important;
        border-right: 1px solid #1A1F2C;
    }
    .metric-card {
        background: #111318;
        border: 1px solid #1E2638;
        border-left: 4px solid #00E5FF;
        padding: 14px;
        border-radius: 6px;
        box-shadow: 0 4px 20px rgba(0, 229, 255, 0.05);
    }
    .status-badge-online {
        background-color: rgba(0, 230, 118, 0.15);
        color: #00E676;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid #00E676;
        font-size: 0.78rem;
        font-weight: bold;
    }
    .status-badge-warn {
        background-color: rgba(255, 61, 0, 0.15);
        color: #FF3D00;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid #FF3D00;
        font-size: 0.78rem;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- شريط التحكم الجانبي (Industrial SCADA Control Panel) ---
st.sidebar.markdown("### 🎛️ لوحة تحكم النظام (SCADA Console)")

mode = st.sidebar.radio(
    "وضع التشغيل (Operation Mode):",
    ["محاكاة فيزيائية رقمية (Digital Twin)", "بوابة عتاد Modbus TCP (Hardware Link)"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚡ معاملات ضبط المتحكم (PID Tuning)")
col_p1, col_p2 = st.sidebar.columns(2)
kp = col_p1.number_input("Kp (Proportional)", min_value=0.0, max_value=50.0, value=2.8, step=0.1)
ki = col_p2.number_input("Ki (Integral)", min_value=0.0, max_value=20.0, value=0.65, step=0.05)
kd = col_p1.number_input("Kd (Derivative)", min_value=0.0, max_value=10.0, value=0.18, step=0.01)
sp = col_p2.number_input("Setpoint (SP)", min_value=0.0, max_value=100.0, value=65.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚙️ ديناميكا المنظومة الفيزيائية (Plant Dynamics)")
tau = st.sidebar.slider("ثابت الاستجابة الزمني (Time Constant τ)", 0.5, 10.0, 2.2, step=0.1)
dead_time = st.sidebar.slider("التأخير الزمني للنظام (Dead Time L)", 0.0, 3.0, 0.3, step=0.1)
disturbance = st.sidebar.slider("اضطراب خارجي مفاجئ (Disturbance %)", -25.0, 25.0, 0.0, step=1.0)
sim_duration = st.sidebar.select_slider(
    "مدة دورة المراقبة (ثانية):", options=[10, 20, 30, 50], value=20
)

# زر إعادة المزامنة
if st.sidebar.button("🚨 تصفير وإعادة مزامنة المنظومة"):
    st.rerun()

# --- محرك الحسابات الرياضية والمحاكاة ---
dt = 0.05
steps = int(sim_duration / dt)
delay_steps = int(dead_time / dt)

controller = IndustrialPID(
    kp=kp,
    ki=ki,
    kd=kd,
    setpoint=sp,
    output_limits=(0.0, 100.0),
    sample_time=dt,
)

time_arr = np.linspace(0, sim_duration, steps)
pv_arr = np.zeros(steps)
sp_arr = np.full(steps, sp)
mv_arr = np.zeros(steps)
p_term_arr = np.zeros(steps)
i_term_arr = np.zeros(steps)
d_term_arr = np.zeros(steps)

pv_current = 0.0
pv_history = [0.0] * (delay_steps + 1)
iae = 0.0  # Integral of Absolute Error

for i, t in enumerate(time_arr):
    # إشارة التحكم
    mv = controller.update(pv=pv_current, current_time=t)
    mv_arr[i] = mv

    # تفكيك مركبات PID للعرض التحليلي
    err = sp - pv_current
    p_term_arr[i] = kp * err
    i_term_arr[i] = controller._integral
    d_term_arr[i] = mv - p_term_arr[i] - i_term_arr[i]

    # حقن الاضطراب في منتصف الزمن
    dist_val = disturbance if t > (sim_duration / 2) else 0.0

    # محاكاة الاستجابة مع التأخير الزمني (FOPDT Model)
    pv_delayed = pv_history.pop(0)
    dpv = (pv_delayed - pv_current + dist_val) / tau * dt
    pv_current += dpv
    pv_history.append(mv)
    pv_arr[i] = pv_current

    iae += abs(err) * dt

# حساب مؤشرات الأداء الديناميكية
steady_pv = pv_arr[-1]
steady_err = abs(sp - steady_pv)
overshoot = max(0.0, (np.max(pv_arr) - sp) / sp * 100.0) if sp > 0 else 0.0

# زمن الاستقرار (Settling Time 2% band)
band = 0.02 * sp
settled_indices = np.where(np.abs(pv_arr - sp) > band)[0]
t_settling = time_arr[settled_indices[-1]] if len(settled_indices) > 0 and settled_indices[-1] < steps - 1 else time_arr[-1]

# --- ترويسة الواجهة والـ Status Indicators ---
h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    st.markdown("## ⚡ APEX-SCADA | Digital Twin & Telemetry Gateway")
    st.caption("Industrial Automation & Edge Control Platform | Real-Time Hardware Synchronizer")

with h_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if mode.startswith("محاكاة"):
        st.markdown('<span class="status-badge-online">● SIMULATION ENGINE ACTIVE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-warn">● MODBUS GATEWAY LINKED</span>', unsafe_allow_html=True)

# --- بطاقات القياس اللحظية (KPI Dashboard) ---
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("المتغير المقاس (PV)", f"{steady_pv:.2f} %", delta=f"{steady_pv-sp:.2f}")
kpi2.metric("القيمة المستهدفة (SP)", f"{sp:.2f} %")
kpi3.metric("خرج المشغل (MV)", f"{mv_arr[-1]:.2f} %")
kpi4.metric("التجاوز الأقصى (Overshoot)", f"{overshoot:.1f} %", delta=f"-{overshoot:.1f}%" if overshoot > 10 else "Optimal", delta_color="inverse")
kpi5.metric("مؤشر تراكم الخطأ (IAE)", f"{iae:.2f}")

st.markdown("---")

# --- تبويبات المنظومة الرئيسية (SCADA Tabs) ---
tab_scada, tab_breakdown, tab_data, tab_modbus = st.tabs([
    "📊 المخطط الحي (Live Response)",
    "🔬 تفكيك مركبات PID (P-I-D Spectrum)",
    "📋 سجل القياسات (Historian & CSV)",
    "🔌 بوابة Modbus للعتاد (PLC Gateway)"
])

# 1. التبويب الأول: مخطط الاستجابة الرئيسي
with tab_scada:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3],
        subplot_titles=("حلقة التحكم المغلقة (Closed-Loop Step Response)", "إشارة الخرج للمشغل (Manipulated Variable %)")
    )

    # نطاق التسامح (Tolerance Corridor ±2%)
    fig.add_trace(go.Scatter(
        x=np.concatenate([time_arr, time_arr[::-1]]),
        y=np.concatenate([sp_arr * 1.02, (sp_arr * 0.98)[::-1]]),
        fill='toself',
        fillcolor='rgba(0, 229, 255, 0.05)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="نطاق الدقة ±2%"
    ), row=1, col=1)

    # مسار Setpoint
    fig.add_trace(go.Scatter(
        x=time_arr, y=sp_arr,
        line=dict(color='#FFD700', width=2, dash='dash'),
        name="القيمة المستهدفة (SP)"
    ), row=1, col=1)

    # مسار Process Value
    fig.add_trace(go.Scatter(
        x=time_arr, y=pv_arr,
        line=dict(color='#00E5FF', width=3),
        name="القيمة الحالية (PV)"
    ), row=1, col=1)

    # إشارة الخرج MV
    fig.add_trace(go.Scatter(
        x=time_arr, y=mv_arr,
        line=dict(color='#FF3D00', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 61, 0, 0.08)',
        name="خرج التحكم (MV %)"
    ), row=2, col=1)

    fig.update_layout(
        paper_bgcolor='#080808',
        plot_bgcolor='#0E1015',
        font=dict(color='#A0AEC0', family='Courier New'),
        height=550,
        margin=dict(l=30, r=30, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1)
    )
    fig.update_xaxes(gridcolor='#1A202C', zerolinecolor='#1A202C')
    fig.update_yaxes(gridcolor='#1A202C', zerolinecolor='#1A202C')
    st.plotly_chart(fig, use_container_width=True)

# 2. التبويب الثاني: تفكيك وتحليل $P, I, D$
with tab_breakdown:
    fig_dec = go.Figure()
    fig_dec.add_trace(go.Scatter(x=time_arr, y=p_term_arr, name="مركبة التناسب (P-Action)", line=dict(color='#00E5FF', width=2)))
    fig_dec.add_trace(go.Scatter(x=time_arr, y=i_term_arr, name="مركبة التكامل (I-Action)", line=dict(color='#7C4DFF', width=2)))
    fig_dec.add_trace(go.Scatter(x=time_arr, y=d_term_arr, name="مركبة التفاضل (D-Action)", line=dict(color='#00E676', width=2)))
    fig_dec.update_layout(
        paper_bgcolor='#080808',
        plot_bgcolor='#0E1015',
        font=dict(color='#A0AEC0'),
        title="تفكيك إشارات التحكم الداخلية للمتحكم (P vs I vs D Terms)",
        xaxis=dict(title="الزمن (ثوانٍ)", gridcolor='#1A202C'),
        yaxis=dict(title="قيمة الجهد/الإشارة", gridcolor='#1A202C'),
        height=450
    )
    st.plotly_chart(fig_dec, use_container_width=True)

# 3. التبويب الثالث: سجل البيانات والتحميل
with tab_data:
    df_telemetry = pd.DataFrame({
        "Timestamp_s": np.round(time_arr, 2),
        "Setpoint_SP": np.round(sp_arr, 2),
        "Process_Value_PV": np.round(pv_arr, 2),
        "Control_Output_MV": np.round(mv_arr, 2),
        "Error": np.round(sp_arr - pv_arr, 2)
    })
    
    st.markdown("#### 📜 جدول السجلات اللحظية (Process Historian Buffer)")
    st.dataframe(df_telemetry.tail(15), use_container_width=True)

    csv_data = df_telemetry.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 تصدير السجلات الكاملة إلى ملف CSV",
        data=csv_data,
        file_name=f"scada_telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# 4. التبويب الرابع: إعدادات العتاد و Modbus TCP
with tab_modbus:
    st.markdown("#### 📡 تهيئة الاتصال بالحواكم الصناعية (PLC Gateway Configuration)")
    m_col1, m_col2 = st.columns(2)
    m_col1.text_input("عنوان الـ IP للـ PLC (Host):", value="192.168.1.100")
    m_col2.number_input("منفذ الاتصال (Modbus Port):", value=502)
    m_col1.number_input("سجل قراءة الحساس (Input Register - PV):", value=30001)
    m_col2.number_input("سجل كتابة المشغل (Holding Register - MV):", value=40001)
    
    if st.button("🔌 اختبار الاتصال بالعتاد (Ping Gateway)"):
        st.info("جارٍ فحص المنفذ الصناعي 502... (تأكد من تشغيل درايفر modbus_driver.py في الخلفية)")