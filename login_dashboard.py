"""
login_dashboard.py - Dashboard có đăng nhập và cảnh báo cá nhân
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection
from auth_database import register_user, login_user, get_user_cities, update_user_city
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# Cấu hình trang
st.set_page_config(
    page_title="AQI Monitor - Đăng nhập",
    page_icon="🌍",
    layout="wide"
)

# Khởi tạo session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.email = None

# Hàm gửi email cảnh báo
def send_alert_email(to_email, city, aqi, message):
    """Gửi email cảnh báo"""
    try:
        msg = MIMEText(f"""
        🌍 CẢNH BÁO CHẤT LƯỢNG KHÔNG KHÍ
        
        Kính gửi {st.session_state.username},
        
        Hệ thống phát hiện chất lượng không khí tại {city} đang ở mức nguy hại:
        
        - Thành phố: {city}
        - AQI: {aqi}
        - Thời gian: {datetime.now().strftime('%H:%M %d/%m/%Y')}
        - Mức độ: {message}
        
        Khuyến nghị: Hạn chế ra ngoài, đeo khẩu trang khi cần thiết.
        
        ---
        Hệ thống giám sát chất lượng không khí
        Đồ án Kỹ thuật dữ liệu
        """, 'plain', 'utf-8')
        
        msg['Subject'] = f"🚨 CẢNH BÁO AQI - {city}"
        msg['From'] = "nvhoang08052005@gmail.com"
        msg['To'] = to_email
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("nvhoang08052005@gmail.com", "iumx oozu ljos mrpw")
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Lỗi gửi email: {e}")
        return False

# Kiểm tra và gửi cảnh báo
def check_and_alert(user_id, email):
    """Kiểm tra AQI và gửi cảnh báo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy các thành phố user theo dõi
    cities = get_user_cities(user_id)
    
    alerts = []
    for city, threshold in cities:
        cursor.execute("""
            SELECT aqi, timestamp FROM aqi_readings
            WHERE city = ? AND aqi > ?
            ORDER BY timestamp DESC LIMIT 1
        """, (city, threshold))
        
        result = cursor.fetchone()
        if result:
            alerts.append((city, result[0], result[1]))
    
    conn.close()
    
    if alerts:
        for city, aqi, ts in alerts:
            message = "Xấu" if aqi <= 200 else "Rất xấu" if aqi <= 300 else "Nguy hại"
            send_alert_email(email, city, aqi, message)
        
        st.success(f"✅ Đã gửi {len(alerts)} cảnh báo!")
    else:
        st.info("✅ Không có cảnh báo mới")

# Giao diện đăng nhập/đăng ký
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .login-box {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🌍 AQI Monitor</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("👤 Tên đăng nhập hoặc Email")
                password = st.text_input("🔐 Mật khẩu", type="password")
                submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
                
                if submitted:
                    user = login_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.email = user[2]
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Sai tên đăng nhập hoặc mật khẩu!")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("👤 Tên đăng nhập")
                new_email = st.text_input("📧 Email")
                new_password = st.text_input("🔐 Mật khẩu", type="password")
                confirm_password = st.text_input("🔐 Nhập lại mật khẩu", type="password")
                
                submitted = st.form_submit_button("Đăng ký", use_container_width=True)
                
                if submitted:
                    if new_password != confirm_password:
                        st.error("Mật khẩu không khớp!")
                    elif len(new_password) < 6:
                        st.error("Mật khẩu phải có ít nhất 6 ký tự!")
                    else:
                        success, message = register_user(new_username, new_email, new_password)
                        if success:
                            st.success("Đăng ký thành công! Vui lòng đăng nhập.")
                        else:
                            st.error(message)

# Giao diện chính sau khi đăng nhập
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"## 👋 Xin chào, {st.session_state.username}!")
        st.markdown(f"📧 {st.session_state.email}")
        st.markdown("---")
        
        # Quản lý thành phố theo dõi
        st.markdown("### 🏙️ Thành phố theo dõi")
        
        cities = get_user_cities(st.session_state.user_id)
        
        for city, threshold in cities:
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"📍 {city}")
            with col2:
                st.write(f"⚠️ >{threshold}")
        
        if st.button("🚪 Đăng xuất"):
            st.session_state.logged_in = False
            st.rerun()
    
    # Main content
    st.markdown(f"## 🌍 Dashboard cá nhân - {st.session_state.username}")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Tổng quan", "⚙️ Cài đặt cảnh báo", "📜 Lịch sử"])
    
    with tab1:
        # Hiển thị AQI cho các thành phố theo dõi
        conn = get_connection()
        cursor = conn.cursor()
        
        cols = st.columns(len(cities))
        
        for idx, (city, threshold) in enumerate(cities):
            cursor.execute("""
                SELECT aqi, temperature, timestamp FROM aqi_readings
                WHERE city = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (city,))
            
            result = cursor.fetchone()
            if result:
                aqi, temp, ts = result
                
                # Xác định màu sắc
                if aqi <= 50: color = "#00E400"
                elif aqi <= 100: color = "#FFFF00"
                elif aqi <= 150: color = "#FF7E00"
                elif aqi <= 200: color = "#FF0000"
                else: color = "#8F3F97"
                
                with cols[idx]:
                    st.markdown(f"""
                    <div style="
                        background: white;
                        padding: 1rem;
                        border-radius: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        text-align: center;
                    ">
                        <h3>{city}</h3>
                        <h1 style="color: {color};">{aqi}</h1>
                        <p>🌡️ {temp}°C</p>
                        <p>⚠️ Ngưỡng: >{threshold}</p>
                        <p><small>{ts}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
        
        conn.close()
    
    with tab2:
        st.markdown("### ⚙️ Cài đặt ngưỡng cảnh báo")
        
        for city, current_threshold in cities:
            col1, col2 = st.columns([1,2])
            with col1:
                st.write(f"📍 {city}")
            with col2:
                new_threshold = st.slider(
                    f"Ngưỡng cảnh báo {city}",
                    min_value=50,
                    max_value=300,
                    value=current_threshold,
                    step=10,
                    key=f"slider_{city}"
                )
                if new_threshold != current_threshold:
                    update_user_city(st.session_state.user_id, city, new_threshold)
                    st.success(f"✅ Đã cập nhật ngưỡng {city} thành {new_threshold}")
        
        if st.button("🚨 Kiểm tra và gửi cảnh báo ngay"):
            with st.spinner("Đang kiểm tra..."):
                check_and_alert(st.session_state.user_id, st.session_state.email)
    
    with tab3:
        st.markdown("### 📜 Lịch sử cảnh báo")
        # TODO: Hiển thị lịch sử cảnh báo từ bảng alert_history
        st.info("Tính năng đang phát triển")