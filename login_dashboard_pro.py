"""
login_dashboard_pro.py - Dashboard có đăng nhập, dark theme, bản đồ, dự báo AQI 24h, lịch sử cảnh báo
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from database import get_connection
from auth_database import register_user, login_user, get_user_cities, update_user_city
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')

# =============================================
# PAGE CONFIG
# =============================================
st.set_page_config(
    page_title="AQI Vietnam",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# CUSTOM CSS - DARK THEME
# =============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { background-color: #0a0a0a !important; font-family: 'Inter', sans-serif; }
    .stApp, .main, .block-container { background-color: #0a0a0a !important; color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 500 !important; }
    p, span, div, label { color: #ffffff !important; }
    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 0.75rem !important;
    }
    .stTextInput > div > div > input:focus { border-color: #666666 !important; }
    .stButton > button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover { background-color: #333333 !important; border-color: #666666 !important; }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a1a !important;
        border-radius: 50px !important;
        padding: 0.25rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
        border-radius: 50px !important;
        padding: 0.5rem 2rem !important;
    }
    .stTabs [aria-selected="true"] { background-color: #333333 !important; }
    .card {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    .card:hover { border-color: #666666 !important; }
    .login-container {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 16px !important;
        padding: 2.5rem !important;
        max-width: 450px !important;
        margin: 2rem auto !important;
    }
    .aqi-value { font-size: 3rem !important; font-weight: 700 !important; line-height: 1 !important; margin: 0.5rem 0 !important; }
    .aqi-good { color: #4caf50 !important; }
    .aqi-moderate { color: #ff9800 !important; }
    .aqi-unhealthy { color: #f44336 !important; }
    .aqi-very-unhealthy { color: #9c27b0 !important; }
    .aqi-hazardous { color: #b71c1c !important; }
    .stat-box {
        background-color: #0a0a0a !important;
        border: 1px solid #333333 !important;
        border-radius: 20px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
        color: #ffffff !important;
    }
    .alert-success { background-color: #1e3a1e !important; color: #8bc34a !important; padding: 1rem !important; border-radius: 8px !important; border-left: 4px solid #8bc34a !important; }
    .alert-error { background-color: #3a1e1e !important; color: #ff6b6b !important; padding: 1rem !important; border-radius: 8px !important; border-left: 4px solid #ff6b6b !important; }
    .alert-info { background-color: #1e2a3a !important; color: #64b5f6 !important; padding: 1rem !important; border-radius: 8px !important; border-left: 4px solid #64b5f6 !important; }
    .footer { text-align: center !important; padding: 2rem !important; color: #666666 !important; font-size: 0.85rem !important; border-top: 1px solid #333333 !important; margin-top: 3rem !important; }
    hr { border-color: #333333 !important; }
    .stSelectbox > div > div { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #333333 !important; }
    .stSlider > div > div { color: #ffffff !important; }
    .stCheckbox > div > label { color: #ffffff !important; }
    a { color: #ffffff !important; text-decoration: none !important; }
    a:hover { color: #cccccc !important; }
</style>
""", unsafe_allow_html=True)

# =============================================
# SESSION STATE
# =============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.alert_sent = False

# =============================================
# HELPER FUNCTIONS
# =============================================
def convert_to_vn_time(ts):
    try:
        ts_str = ts.replace('T', ' ').replace('Z', '').split('.')[0]
        dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        vn_dt = dt + timedelta(hours=7)
        return vn_dt.strftime('%H:%M %d/%m/%Y')
    except:
        return ts

def get_aqi_color(aqi):
    if aqi <= 50: return "#4caf50"
    elif aqi <= 100: return "#ff9800"
    elif aqi <= 150: return "#f44336"
    elif aqi <= 200: return "#9c27b0"
    else: return "#b71c1c"

def get_aqi_level(aqi):
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Moderate"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "Unhealthy"
    elif aqi <= 300: return "Very Unhealthy"
    else: return "Hazardous"

def get_aqi_class(aqi):
    if aqi <= 50: return "aqi-good"
    elif aqi <= 100: return "aqi-moderate"
    elif aqi <= 150: return "aqi-unhealthy"
    elif aqi <= 200: return "aqi-very-unhealthy"
    else: return "aqi-hazardous"

def send_alert_email(to_email, city, aqi, level):
    try:
        color = get_aqi_color(aqi)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; }}
            .container {{ border: 1px solid #eaeaea; border-radius: 12px; padding: 2rem; margin: 2rem auto; }}
            .header {{ text-align: center; margin-bottom: 2rem; }}
            .aqi-number {{ font-size: 4rem; font-weight: 700; color: {color}; line-height: 1; text-align: center; }}
            .info-table {{ width: 100%; margin: 2rem 0; border-collapse: collapse; }}
            .info-table td {{ padding: 0.75rem; border-bottom: 1px solid #eaeaea; }}
            .recommendations {{ background: #f5f5f5; padding: 1.5rem; border-radius: 8px; margin: 2rem 0; }}
            .footer {{ text-align: center; color: #999; font-size: 0.85rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eaeaea; }}
        </style></head>
        <body>
            <div class="container">
                <div class="header"><h2>🌍 Air Quality Alert</h2></div>
                <p>Hello <strong>{st.session_state.username}</strong>,</p>
                <p>The air quality in <strong>{city}</strong> has exceeded your alert threshold.</p>
                <div class="aqi-number">{aqi}</div>
                <p style="text-align:center">AQI - {level}</p>
                <table class="info-table">
                    <tr><td>City:</td><td><strong>{city}</strong></td></tr>
                    <tr><td>AQI:</td><td><strong style="color:{color}">{aqi}</strong></td></tr>
                    <tr><td>Time:</td><td>{datetime.now().strftime('%H:%M %d/%m/%Y')}</td></tr>
                </table>
                <div class="recommendations">
                    <strong>📋 Recommendations:</strong>
                    <ul><li>Limit outdoor activities</li><li>Wear a mask if going outside</li><li>Keep windows closed</li><li>Use air purifier if available</li></ul>
                </div>
                <div class="footer"><p>© 2026 AQI Vietnam - Air Quality Monitoring System<br>This is an automated message, please do not reply.</p></div>
            </div>
        </body>
        </html>
        """
        msg = MIMEMultipart()
        msg['From'] = "nvhoang08052005@gmail.com"
        msg['To'] = to_email
        msg['Subject'] = f"🌍 AQI Alert - {city} - {datetime.now().strftime('%d/%m/%Y')}"
        msg.attach(MIMEText(html, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("nvhoang08052005@gmail.com", "iumx oozu ljos mrpw")
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

def log_alert_to_db(user_id, city, aqi):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alert_history (user_id, city, aqi, sent_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, city, aqi, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_alert_history(user_id):
    conn = get_connection()
    df = pd.read_sql("""
        SELECT city, aqi, sent_at FROM alert_history
        WHERE user_id = ?
        ORDER BY sent_at DESC
        LIMIT 50
    """, conn, params=(user_id,))
    conn.close()
    return df

def generate_forecast(city, hours=24):
    """Tạo dự báo AQI cho thành phố trong `hours` giờ tới sử dụng ARIMA"""
    conn = get_connection()
    query = """
        SELECT timestamp, aqi FROM aqi_readings
        WHERE city = ?
        ORDER BY timestamp
    """
    df = pd.read_sql(query, conn, params=(city,))
    conn.close()
    if len(df) < 10:
        return None
    # Lấy chuỗi AQI
    ts = df['aqi'].values
    try:
        # Fit ARIMA(1,0,1) đơn giản
        model = ARIMA(ts, order=(1,0,1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=hours)
        # Tạo timestamp cho các giờ tới (giờ hiện tại + 1,2,...)
        last_time = pd.to_datetime(df['timestamp'].iloc[-1])
        # Làm tròn lên giờ tiếp theo
        next_hour = last_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        future_times = [next_hour + timedelta(hours=i) for i in range(hours)]
        return pd.DataFrame({'timestamp': future_times, 'aqi': forecast})
    except Exception as e:
        print(f"Forecast error for {city}: {e}")
        return None

# =============================================
# MAP GENERATION
# =============================================
def generate_vietnam_map(cities_data):
    map_center = [16.0, 108.0]
    m = folium.Map(location=map_center, zoom_start=5.5, tiles='CartoDB dark_matter')
    for city, aqi, lat, lon in cities_data:
        color = get_aqi_color(aqi)
        popup_text = f"<b>{city}</b><br>AQI: {aqi}<br>Mức: {get_aqi_level(aqi)}"
        folium.CircleMarker(
            location=[lat, lon],
            radius=12,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=popup_text,
            tooltip=city
        ).add_to(m)
    return m

# =============================================
# LOGIN PAGE
# =============================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="font-size: 2.5rem;">🌍</h1>
                <h2 style="margin: 1rem 0 0;">AQI Vietnam</h2>
                <p style="color: #666;">Air Quality Monitoring System</p>
            </div>
            """, unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["LOGIN", "REGISTER"])
            with tab1:
                with st.form("login_form"):
                    st.markdown("### Welcome Back")
                    username = st.text_input("Username or Email", placeholder="Enter your username or email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button("LOG IN", use_container_width=True)
                    if submitted:
                        user = login_user(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user[0]
                            st.session_state.username = user[1]
                            st.session_state.email = user[2]
                            st.session_state.alert_sent = False
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
            with tab2:
                with st.form("register_form"):
                    st.markdown("### Create Account")
                    new_username = st.text_input("Username", placeholder="Choose a username")
                    new_email = st.text_input("Email", placeholder="Enter your email")
                    new_password = st.text_input("Password", type="password", placeholder="Create a password")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                    submitted = st.form_submit_button("REGISTER", use_container_width=True)
                    if submitted:
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters")
                        else:
                            success, message = register_user(new_username, new_email, new_password)
                            if success:
                                st.success("Registration successful! Please login.")
                            else:
                                st.error(message)
            st.markdown('</div>', unsafe_allow_html=True)

# =============================================
# MAIN DASHBOARD
# =============================================
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 1.5rem; text-align: center; background-color: #1a1a1a; border-radius: 12px; margin-bottom: 1rem;">
            <div style="width: 60px; height: 60px; background-color: #333333; border-radius: 50%; margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 2rem;">👤</span>
            </div>
            <h3 style="margin: 1rem 0 0.25rem;">{st.session_state.username}</h3>
            <p style="color: #666;">{st.session_state.email}</p>
        </div>
        """, unsafe_allow_html=True)
        
        cities = get_user_cities(st.session_state.user_id)
        st.markdown("### 📍 Monitored Cities")
        for city, threshold in cities:
            st.markdown(f"""
            <div style="background-color: #1a1a1a; border: 1px solid #333333; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;">
                <strong>{city}</strong>
                <span style="float: right; color: #ff6b6b;">⚠️ >{threshold}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    # Main content
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h1>📊 Dashboard</h1>
        <p style="color: #666;">Welcome back, {st.session_state.username} | {datetime.now().strftime('%H:%M %d/%m/%Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 OVERVIEW", "🗺️ MAP", "📊 COMPARE", "📜 HISTORY"])
    
    with tab1:
        st.markdown("### 📊 Chất lượng không khí hiện tại")
        conn = get_connection()
        cursor = conn.cursor()
        alerts_to_send = []

        # Chia cột theo số lượng thành phố
        cols = st.columns(len(cities))
        for idx, (city, threshold) in enumerate(cities):
            cursor.execute("""
                SELECT aqi, temperature, humidity, timestamp 
                FROM aqi_readings 
                WHERE city = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (city,))
            result = cursor.fetchone()
            if result:
                aqi, temp, humidity, ts = result
                level = get_aqi_level(aqi)
                aqi_class = get_aqi_class(aqi)
                if aqi > threshold and not st.session_state.alert_sent:
                    alerts_to_send.append((city, aqi, level))
                
                with cols[idx]:
                    # Card dọc
                    st.markdown(f"""
                    <div class="card" style="text-align: center; padding: 1rem;">
                        <h3 style="margin-bottom: 0.5rem;">{city}</h3>
                        <div class="aqi-value {aqi_class}" style="font-size: 2.5rem;">{aqi}</div>
                        <div style="color: #aaa; margin-bottom: 0.5rem;">{level}</div>
                        <div style="display: flex; flex-direction: column; gap: 0.3rem; margin: 0.5rem 0;">
                            <span class="stat-box">🌡️ Nhiệt độ: {temp}°C</span>
                            <span class="stat-box">💧 Độ ẩm: {humidity}%</span>
                            <span class="stat-box">⚠️ Ngưỡng: >{threshold}</span>
                        </div>
                        <div style="color: #666; font-size: 0.7rem;">Cập nhật: {convert_to_vn_time(ts)}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                with cols[idx]:
                    st.markdown(f"""
                    <div class="card" style="text-align: center;">
                        <h3>{city}</h3>
                        <p>Chưa có dữ liệu</p>
                    </div>
                    """, unsafe_allow_html=True)
        conn.close()

        if alerts_to_send and not st.session_state.alert_sent:
            with st.spinner("Đang gửi cảnh báo..."):
                for city, aqi, level in alerts_to_send:
                    if send_alert_email(st.session_state.email, city, aqi, level):
                        log_alert_to_db(st.session_state.user_id, city, aqi)
                        time.sleep(1)
                st.session_state.alert_sent = True
                st.success(f"✅ Đã gửi {len(alerts_to_send)} cảnh báo")
    
    with tab2:
        st.markdown("### 🗺️ Air Quality Map")
        conn = get_connection()
        all_cities_df = pd.read_sql("""
            SELECT aqi, city FROM aqi_readings
            WHERE (city, timestamp) IN (
                SELECT city, MAX(timestamp) FROM aqi_readings GROUP BY city
            )
        """, conn)
        conn.close()
        coords = {
            'Hanoi': (21.0285, 105.8542), 'Haiphong': (20.8449, 106.6881),
            'Danang': (16.0544, 108.2022), 'HCMC': (10.8231, 106.6297),
            'Cantho': (10.0452, 105.7469)
        }
        map_data = []
        for _, row in all_cities_df.iterrows():
            city = row['city']
            if city in coords:
                map_data.append((city, row['aqi'], coords[city][0], coords[city][1]))
        if map_data:
            vn_map = generate_vietnam_map(map_data)
            folium_static(vn_map, width=800, height=500)
        else:
            st.info("No data available for map")
    
    with tab3:
        st.markdown("### 📈 Xu hướng AQI 7 ngày qua & Xếp hạng thành phố")
    
        # Lấy dữ liệu 7 ngày gần nhất cho tất cả các thành phố của user
        conn = get_connection()
        # Lấy danh sách thành phố của user
        user_cities = [c[0] for c in cities]
        if not user_cities:
            st.info("Không có thành phố nào được theo dõi.")
            st.stop()
        else:
            placeholders = ','.join(['?']*len(user_cities))
            query = f"""
                SELECT city, aqi, timestamp 
                FROM aqi_readings 
                WHERE city IN ({placeholders})
                AND timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp ASC
            """
            df = pd.read_sql(query, conn, params=user_cities)
            conn.close()
            
            if df.empty:
                st.warning("Không có dữ liệu trong 7 ngày qua.")
            else:
                # Chuyển timestamp sang datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Thêm cột giờ VN (chỉ để hiển thị nếu cần)
                df['time_vn'] = df['timestamp'].apply(lambda x: x + timedelta(hours=7))
                
                # 1. Biểu đồ xu hướng AQI
                fig = px.line(df, x='time_vn', y='aqi', color='city',
                            title='Diễn biến AQI 7 ngày qua',
                            labels={'time_vn': 'Thời gian (VN)', 'aqi': 'AQI', 'city': 'Thành phố'})
                fig.update_layout(
                    template='plotly_dark',
                    height=500,
                    paper_bgcolor="#0f1117",
                    plot_bgcolor="#0f1117"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 2. Xếp hạng các thành phố theo AQI mới nhất
                # Lấy bản ghi mới nhất của mỗi thành phố
                latest = df.sort_values('timestamp').groupby('city').last().reset_index()
                latest = latest.sort_values('aqi', ascending=False)  # xếp hạng từ cao xuống thấp
                
                # Thêm cột màu sắc và mức độ
                def get_level(aqi):
                    if aqi <= 50: return "Tốt"
                    elif aqi <= 100: return "Trung bình"
                    elif aqi <= 150: return "Kém"
                    elif aqi <= 200: return "Xấu"
                    else: return "Rất xấu"
                
                latest['level'] = latest['aqi'].apply(get_level)
                
                # Hiển thị bảng xếp hạng
                st.subheader("🏆 Xếp hạng chất lượng không khí hiện tại")
                display_df = latest[['city', 'aqi', 'level']].rename(columns={'city': 'Thành phố', 'aqi': 'AQI', 'level': 'Mức độ'})
                # Thêm thanh tiến trình màu
                st.dataframe(display_df, use_container_width=True)
                
                # Tùy chọn: bar chart cho xếp hạng
                fig2 = px.bar(latest, x='city', y='aqi', color='aqi',
                            color_continuous_scale='RdYlGn_r',
                            title='So sánh AQI hiện tại giữa các thành phố',
                            labels={'city': 'Thành phố', 'aqi': 'AQI'})
                fig2.update_layout(
                    template='plotly_dark',
                    height=400,
                    paper_bgcolor="#0f1117",
                    plot_bgcolor="#0f1117"
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # Giải thích
                with st.expander("ℹ️ Ghi chú"):
                    st.markdown("""
                    - **Xu hướng 7 ngày**: Đường biểu diễn AQI theo thời gian.
                    - **Xếp hạng**: Dựa trên giá trị AQI mới nhất của mỗi thành phố.
                    - **Màu sắc**: Xanh (tốt) → Vàng → Cam → Đỏ (xấu).
                    - Dữ liệu được cập nhật mỗi giờ từ IQAir API.
                    """)
    with tab4:
        st.markdown("### 📜 Alert History")
        history_df = get_alert_history(st.session_state.user_id)
        if not history_df.empty:
            history_df['sent_at'] = pd.to_datetime(history_df['sent_at']).dt.strftime('%H:%M %d/%m/%Y')
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No alerts have been sent yet.")
# =============================================
# FOOTER
# =============================================
st.markdown("""
<div class="footer">
    <p>© 2026 AQI Vietnam - Air Quality Monitoring System</p>
    <p>Data Engineering Project - PTIT</p>
</div>
""", unsafe_allow_html=True)