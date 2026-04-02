"""
login_dashboard_pro.py - Dashboard có đăng nhập, dark theme, bản đồ, dự báo, lịch sử cảnh báo
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
import hashlib

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
# CUSTOM CSS - DARK THEME (giữ nguyên như cũ)
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
    """Send alert email with clean HTML"""
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
    """Ghi cảnh báo vào bảng alert_history"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alert_history (user_id, city, aqi, sent_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, city, aqi, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_alert_history(user_id):
    """Lấy lịch sử cảnh báo của user"""
    conn = get_connection()
    df = pd.read_sql("""
        SELECT city, aqi, sent_at FROM alert_history
        WHERE user_id = ?
        ORDER BY sent_at DESC
        LIMIT 50
    """, conn, params=(user_id,))
    conn.close()
    return df

def load_forecast_results():
    """Đọc kết quả so sánh mô hình từ file CSV"""
    try:
        df = pd.read_csv('model_comparison_results.csv')
        return df
    except:
        return None

# =============================================
# MAP GENERATION
# =============================================
def generate_vietnam_map(cities_data):
    """Tạo bản đồ Việt Nam với màu sắc theo AQI"""
    # Tọa độ trung tâm Việt Nam
    map_center = [16.0, 108.0]
    m = folium.Map(location=map_center, zoom_start=5.5, tiles='CartoDB dark_matter')
    
    for city, aqi, lat, lon in cities_data:
        color = get_aqi_color(aqi)
        popup_text = f"<b>{city}</b><br>AQI: {aqi}<br>Mức: {get_aqi_level(aqi)}"
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
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
    tab1, tab2, tab3, tab4 = st.tabs(["📈 OVERVIEW", "🗺️ MAP", "📊 FORECAST", "📜 HISTORY"])
    
    with tab1:
        # Fetch latest AQI for user's cities
        conn = get_connection()
        cursor = conn.cursor()
        alerts_to_send = []
        
        cols = st.columns(len(cities))
        for idx, (city, threshold) in enumerate(cities):
            cursor.execute("""
                SELECT aqi, temperature, timestamp FROM aqi_readings
                WHERE city = ? ORDER BY timestamp DESC LIMIT 1
            """, (city,))
            result = cursor.fetchone()
            if result:
                aqi, temp, ts = result
                level = get_aqi_level(aqi)
                aqi_class = get_aqi_class(aqi)
                if aqi > threshold and not st.session_state.alert_sent:
                    alerts_to_send.append((city, aqi, level))
                with cols[idx]:
                    st.markdown(f"""
                    <div class="card" style="text-align: center;">
                        <h3>{city}</h3>
                        <div class="aqi-value {aqi_class}">{aqi}</div>
                        <div style="color: #666;">{level}</div>
                        <div style="display: flex; justify-content: center; gap: 1rem; margin: 1rem 0;">
                            <span class="stat-box">🌡️ {temp}°C</span>
                            <span class="stat-box">⚠️ >{threshold}</span>
                        </div>
                        <div style="color: #666; font-size: 0.8rem;">{convert_to_vn_time(ts)}</div>
                    </div>
                    """, unsafe_allow_html=True)
        conn.close()
        
        if alerts_to_send and not st.session_state.alert_sent:
            with st.spinner("Sending alerts..."):
                for city, aqi, level in alerts_to_send:
                    if send_alert_email(st.session_state.email, city, aqi, level):
                        log_alert_to_db(st.session_state.user_id, city, aqi)
                        time.sleep(1)
                st.session_state.alert_sent = True
                st.success(f"✅ {len(alerts_to_send)} alert(s) sent")
    
    with tab2:
        st.markdown("### 🗺️ Air Quality Map")
        # Lấy dữ liệu mới nhất cho tất cả thành phố (có tọa độ)
        conn = get_connection()
        all_cities_df = pd.read_sql("""
            SELECT aqi, city, temperature FROM aqi_readings
            WHERE (city, timestamp) IN (
                SELECT city, MAX(timestamp) FROM aqi_readings GROUP BY city
            )
        """, conn)
        conn.close()
        # Gắn tọa độ (từ danh sách mặc định)
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
        st.markdown("### 📊 Model Comparison (ARIMA vs XGBoost)")
        forecast_df = load_forecast_results()
        if forecast_df is not None and not forecast_df.empty:
            # Hiển thị bảng
            st.dataframe(forecast_df, use_container_width=True)
            # Biểu đồ so sánh RMSE
            fig = go.Figure()
            fig.add_trace(go.Bar(name='ARIMA', x=forecast_df['city'], y=forecast_df['ARIMA_RMSE'], marker_color='blue'))
            fig.add_trace(go.Bar(name='XGBoost', x=forecast_df['city'], y=forecast_df['XGB_RMSE'], marker_color='red'))
            fig.update_layout(title='RMSE Comparison', xaxis_title='City', yaxis_title='RMSE', barmode='group', template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
            # Thống kê
            avg_arima = forecast_df['ARIMA_RMSE'].mean()
            avg_xgb = forecast_df['XGB_RMSE'].mean()
            st.metric("Average RMSE - ARIMA", f"{avg_arima:.2f}")
            st.metric("Average RMSE - XGBoost", f"{avg_xgb:.2f}")
        else:
            st.info("Forecast results not available. Please run compare_models.py first.")
    
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