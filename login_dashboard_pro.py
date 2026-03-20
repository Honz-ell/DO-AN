"""
login_dashboard_fixed.py - Dark theme interface with white text
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection
from auth_database import register_user, login_user, get_user_cities, update_user_city
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

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
# CUSTOM CSS - DARK THEME WITH WHITE TEXT
# =============================================
st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global dark theme */
    .stApp {
        background-color: #0a0a0a !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Override Streamlit default colors */
    .stApp, .main, .block-container {
        background-color: #0a0a0a !important;
        color: #ffffff !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* Text */
    p, span, div, label {
        color: #ffffff !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 0.75rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #666666 !important;
        box-shadow: none !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #333333 !important;
        border-color: #666666 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a1a !important;
        border-radius: 50px !important;
        padding: 0.25rem !important;
        gap: 0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
        border-radius: 50px !important;
        padding: 0.5rem 2rem !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #333333 !important;
    }
    
    /* Cards */
    .card {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    .card:hover {
        border-color: #666666 !important;
    }
    
    /* Login container */
    .login-container {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 16px !important;
        padding: 2.5rem !important;
        max-width: 450px !important;
        margin: 2rem auto !important;
    }
    
    /* AQI indicators */
    .aqi-value {
        font-size: 3rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
        margin: 0.5rem 0 !important;
    }
    
    .aqi-good { color: #4caf50 !important; }
    .aqi-moderate { color: #ff9800 !important; }
    .aqi-unhealthy { color: #f44336 !important; }
    .aqi-very-unhealthy { color: #9c27b0 !important; }
    .aqi-hazardous { color: #b71c1c !important; }
    
    /* Stats */
    .stat-box {
        background-color: #0a0a0a !important;
        border: 1px solid #333333 !important;
        border-radius: 20px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
        color: #ffffff !important;
    }
    
    /* Alerts */
    .alert-success {
        background-color: #1e3a1e !important;
        color: #8bc34a !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border-left: 4px solid #8bc34a !important;
    }
    
    .alert-error {
        background-color: #3a1e1e !important;
        color: #ff6b6b !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border-left: 4px solid #ff6b6b !important;
    }
    
    .alert-info {
        background-color: #1e2a3a !important;
        color: #64b5f6 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border-left: 4px solid #64b5f6 !important;
    }
    
    /* Sidebar */
    .css-1d391kg, .css-1wrcr25 {
        background-color: #0a0a0a !important;
    }
    
    .sidebar-content {
        background-color: #1a1a1a !important;
        border-right: 1px solid #333333 !important;
    }
    
    /* Footer */
    .footer {
        text-align: center !important;
        padding: 2rem !important;
        color: #666666 !important;
        font-size: 0.85rem !important;
        border-top: 1px solid #333333 !important;
        margin-top: 3rem !important;
    }
    
    /* Dividers */
    hr {
        border-color: #333333 !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
    }
    
    /* Sliders */
    .stSlider > div > div {
        color: #ffffff !important;
    }
    
    /* Checkbox */
    .stCheckbox > div > label {
        color: #ffffff !important;
    }
    
    /* Links */
    a {
        color: #ffffff !important;
        text-decoration: none !important;
    }
    
    a:hover {
        color: #cccccc !important;
    }
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
# EMAIL FUNCTION
# =============================================
def send_alert_email(to_email, city, aqi, level):
    """Send alert email with clean HTML"""
    try:
        # Color based on AQI
        if aqi <= 50:
            color = "#4caf50"
            level_text = "Good"
        elif aqi <= 100:
            color = "#ff9800"
            level_text = "Moderate"
        elif aqi <= 150:
            color = "#f44336"
            level_text = "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            color = "#9c27b0"
            level_text = "Unhealthy"
        else:
            color = "#b71c1c"
            level_text = "Very Unhealthy"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .container {{
                    border: 1px solid #eaeaea;
                    border-radius: 12px;
                    padding: 2rem;
                    margin: 2rem auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 2rem;
                }}
                .aqi-display {{
                    text-align: center;
                    margin: 2rem 0;
                }}
                .aqi-number {{
                    font-size: 4rem;
                    font-weight: 700;
                    color: {color};
                    line-height: 1;
                }}
                .aqi-label {{
                    font-size: 1rem;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .info-table {{
                    width: 100%;
                    margin: 2rem 0;
                    border-collapse: collapse;
                }}
                .info-table td {{
                    padding: 0.75rem;
                    border-bottom: 1px solid #eaeaea;
                }}
                .info-table td:first-child {{
                    font-weight: 600;
                    width: 120px;
                }}
                .recommendations {{
                    background: #f5f5f5;
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin: 2rem 0;
                }}
                .footer {{
                    text-align: center;
                    color: #999;
                    font-size: 0.85rem;
                    margin-top: 2rem;
                    padding-top: 1rem;
                    border-top: 1px solid #eaeaea;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🌍 Air Quality Alert</h2>
                </div>
                
                <p>Hello <strong>{st.session_state.username}</strong>,</p>
                
                <p>The air quality in <strong>{city}</strong> has exceeded your alert threshold.</p>
                
                <div class="aqi-display">
                    <div class="aqi-number">{aqi}</div>
                    <div class="aqi-label">AQI - {level_text}</div>
                </div>
                
                <table class="info-table">
                    <tr>
                        <td>City:</td>
                        <td><strong>{city}</strong></td>
                    </tr>
                    <tr>
                        <td>AQI:</td>
                        <td><strong style="color: {color};">{aqi}</strong></td>
                    </tr>
                    <tr>
                        <td>Level:</td>
                        <td>{level_text}</td>
                    </tr>
                    <tr>
                        <td>Time:</td>
                        <td>{datetime.now().strftime('%H:%M %d/%m/%Y')}</td>
                    </tr>
                </table>
                
                <div class="recommendations">
                    <strong>📋 Recommendations:</strong>
                    <ul style="margin-top: 0.5rem;">
                        <li>Limit outdoor activities</li>
                        <li>Wear a mask if going outside</li>
                        <li>Keep windows closed</li>
                        <li>Use air purifier if available</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>© 2026 AQI Vietnam - Air Quality Monitoring System</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
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
                    st.markdown("Please login to continue.")
                    
                    username = st.text_input("Username or Email", placeholder="Enter your username or email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        remember = st.checkbox("Remember me")
                    with col_b:
                        st.markdown("[Forgot password?](#)")
                    
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
                    st.markdown("Sign up to receive air quality alerts.")
                    
                    new_username = st.text_input("Username", placeholder="Choose a username")
                    new_email = st.text_input("Email", placeholder="Enter your email")
                    new_password = st.text_input("Password", type="password", placeholder="Create a password")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                    
                    st.markdown("""
                    <small style="color: #666;">
                    By signing up, you agree to our 
                    <a href="#">Terms of Service</a> and 
                    <a href="#">Privacy Policy</a>.
                    </small>
                    """, unsafe_allow_html=True)
                    
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
        
        # Get user's cities
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
    tab1, tab2, tab3 = st.tabs(["📈 OVERVIEW", "⚙️ SETTINGS", "📜 HISTORY"])
    
    with tab1:
        # Get latest AQI data
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create columns for cities
        cols = st.columns(len(cities))
        
        alerts_to_send = []
        
        for idx, (city, threshold) in enumerate(cities):
            cursor.execute("""
                SELECT aqi, temperature, timestamp FROM aqi_readings
                WHERE city = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (city,))
            
            result = cursor.fetchone()
            if result:
                aqi, temp, ts = result
                
                # Determine AQI class
                if aqi <= 50:
                    aqi_class = "aqi-good"
                    level = "Good"
                elif aqi <= 100:
                    aqi_class = "aqi-moderate"
                    level = "Moderate"
                elif aqi <= 150:
                    aqi_class = "aqi-unhealthy"
                    level = "Unhealthy"
                elif aqi <= 200:
                    aqi_class = "aqi-very-unhealthy"
                    level = "Very Unhealthy"
                else:
                    aqi_class = "aqi-hazardous"
                    level = "Hazardous"
                
                # Check if alert needed
                if aqi > threshold and not st.session_state.alert_sent:
                    alerts_to_send.append((city, aqi, level))
                
                with cols[idx]:
                    st.markdown(f"""
                    <div class="card" style="text-align: center;">
                        <h3 style="margin: 0;">{city}</h3>
                        <div class="aqi-value {aqi_class}">{aqi}</div>
                        <div style="color: #666; margin-bottom: 1rem;">{level}</div>
                        <div style="display: flex; justify-content: center; gap: 1rem; margin: 1rem 0;">
                            <span class="stat-box">🌡️ {temp}°C</span>
                            <span class="stat-box">⚠️ >{threshold}</span>
                        </div>
                        <div style="color: #666; font-size: 0.8rem;">
                            {ts}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        conn.close()
        
        # Send alerts
        if alerts_to_send and not st.session_state.alert_sent:
            with st.spinner("Sending alerts..."):
                success_count = 0
                for city, aqi, level in alerts_to_send:
                    if send_alert_email(st.session_state.email, city, aqi, level):
                        success_count += 1
                    time.sleep(1)
                
                if success_count == len(alerts_to_send):
                    st.session_state.alert_sent = True
                    st.markdown(f"""
                    <div class="alert-success" style="margin-top: 2rem;">
                        ✅ {success_count} alert{'s' if success_count > 1 else ''} sent successfully
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="alert-error" style="margin-top: 2rem;">
                        ❌ Failed to send some alerts
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### ⚙️ Alert Settings")
        st.markdown("Adjust alert thresholds for each city.")
        
        for city, current_threshold in cities:
            with st.expander(f"📍 {city}"):
                new_threshold = st.slider(
                    f"Alert threshold for {city}",
                    min_value=50,
                    max_value=300,
                    value=current_threshold,
                    step=10,
                    key=f"slider_{city}"
                )
                if new_threshold != current_threshold:
                    update_user_city(st.session_state.user_id, city, new_threshold)
                    st.session_state.alert_sent = False
                    st.success(f"✅ Threshold for {city} updated to {new_threshold}")
        
        if st.button("🔄 Check and Send Alerts Now", use_container_width=True):
            st.session_state.alert_sent = False
            st.rerun()
    
    with tab3:
        st.markdown("### 📜 Alert History")
        st.markdown("""
        <div class="alert-info">
            ℹ️ Alert history feature coming soon
        </div>
        """, unsafe_allow_html=True)

# =============================================
# FOOTER
# =============================================
st.markdown("""
<div class="footer">
    <p>© 2026 AQI Vietnam - Air Quality Monitoring System</p>
    <p>Data Engineering Project - PTIT</p>
</div>
""", unsafe_allow_html=True)