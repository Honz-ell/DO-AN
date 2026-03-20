"""
dashboard_pro.py - Dashboard AQI chuyên nghiệp với nhiều tính năng nâng cao
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import streamlit_folium
from database import get_connection
from datetime import datetime, timedelta
import time

# Cấu hình trang
st.set_page_config(
    page_title="AQI Vietnam Pro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .aqi-good { color: #00E400; }
    .aqi-moderate { color: #FFFF00; }
    .aqi-unhealthy-sensitive { color: #FF7E00; }
    .aqi-unhealthy { color: #FF0000; }
    .aqi-very-unhealthy { color: #8F3F97; }
    .aqi-hazardous { color: #7E0023; }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Cache dữ liệu
@st.cache_data(ttl=300)  # Cache 5 phút
def load_cities():
    """Load danh sách thành phố"""
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT city FROM aqi_readings ORDER BY city", conn)
    conn.close()
    return df['city'].tolist()

@st.cache_data(ttl=300)
def load_latest_aqi(cities):
    """Load AQI mới nhất cho các thành phố"""
    conn = get_connection()
    placeholders = ','.join(['?'] * len(cities))
    query = f"""
        SELECT city, aqi, timestamp, temperature, humidity
        FROM aqi_readings
        WHERE (city, timestamp) IN (
            SELECT city, MAX(timestamp)
            FROM aqi_readings
            WHERE city IN ({placeholders})
            GROUP BY city
        )
    """
    df = pd.read_sql(query, conn, params=cities)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_historical(city, days=7):
    """Load dữ liệu lịch sử"""
    conn = get_connection()
    from_date = (datetime.now() - timedelta(days=days)).isoformat()
    df = pd.read_sql(f"""
        SELECT timestamp, aqi, temperature, humidity
        FROM aqi_readings
        WHERE city = '{city}'
        AND timestamp >= '{from_date}'
        ORDER BY timestamp
    """, conn)
    conn.close()
    return df

# Header
st.markdown("""
<div class="main-header">
    <h1>🌍 GIÁM SÁT CHẤT LƯỢNG KHÔNG KHÍ VIỆT NAM</h1>
    <p>Dữ liệu thời gian thực từ Open-Meteo API - Cập nhật mỗi giờ</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🔍 Bộ lọc nâng cao")
    
    # Load cities
    all_cities = load_cities()
    
    # Tạo tabs trong sidebar
    tab1, tab2 = st.tabs(["🏙️ Thành phố", "⚙️ Cấu hình"])
    
    with tab1:
        # Filter theo vùng
        region = st.selectbox(
            "🌏 Chọn vùng",
            ["Tất cả", "Miền Bắc", "Miền Trung", "Miền Nam"]
        )
        
        # Định nghĩa các vùng
        north = ['Hanoi', 'Haiphong']
        central = ['Danang']
        south = ['HCMC', 'Cantho']
        
        if region == "Miền Bắc":
            available = [c for c in all_cities if c in north]
        elif region == "Miền Trung":
            available = [c for c in all_cities if c in central]
        elif region == "Miền Nam":
            available = [c for c in all_cities if c in south]
        else:
            available = all_cities
        
        selected_cities = st.multiselect(
            "🏙️ Chọn thành phố",
            available,
            default=available[:min(3, len(available))]
        )
    
    with tab2:
        days = st.slider("📅 Số ngày hiển thị", 1, 30, 7)
        chart_height = st.slider("📊 Chiều cao biểu đồ", 300, 800, 500)
        auto_refresh = st.checkbox("🔄 Tự động làm mới", value=False)
        if auto_refresh:
            refresh_interval = st.slider("⏱️ Tần suất (giây)", 10, 300, 60)
    
    st.markdown("---")
    st.markdown(f"🕒 Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')}")

if not selected_cities:
    st.warning("👆 Vui lòng chọn ít nhất 1 thành phố từ sidebar")
    st.stop()

# Load dữ liệu
with st.spinner("🔄 Đang tải dữ liệu..."):
    latest_df = load_latest_aqi(selected_cities)

# Metrics cards
st.markdown("## 📊 Tổng quan nhanh")
cols = st.columns(len(selected_cities))

for idx, city in enumerate(selected_cities):
    city_data = latest_df[latest_df['city'] == city]
    if not city_data.empty:
        aqi = city_data.iloc[0]['aqi']
        temp = city_data.iloc[0]['temperature']
        time_str = pd.to_datetime(city_data.iloc[0]['timestamp']).strftime('%H:%M %d/%m')
        
        # Xác định màu và mức độ
        if aqi <= 50:
            color = "#00E400"
            level = "Tốt"
        elif aqi <= 100:
            color = "#FFFF00"
            level = "Trung bình"
        elif aqi <= 150:
            color = "#FF7E00"
            level = "Kém"
        elif aqi <= 200:
            color = "#FF0000"
            level = "Xấu"
        elif aqi <= 300:
            color = "#8F3F97"
            level = "Rất xấu"
        else:
            color = "#7E0023"
            level = "Nguy hại"
        
        with cols[idx]:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: {color};">{city}</h3>
                <h1 style="font-size: 3rem; color: {color};">{aqi}</h1>
                <p>{level}</p>
                <p>🌡️ {temp}°C</p>
                <p><small>{time_str}</small></p>
            </div>
            """, unsafe_allow_html=True)

# Biểu đồ chính
st.markdown("## 📈 Diễn biến AQI theo thời gian")

# Tạo tabs cho các loại biểu đồ
chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 Line Chart", "📉 Bar Chart", "📦 Box Plot"])

for city in selected_cities:
    df = load_historical(city, days)
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['date'] = df['timestamp'].dt.date
        
        with chart_tab1:
            fig1 = px.line(df, x='timestamp', y='aqi', 
                          title=f'{city} - AQI theo thời gian',
                          labels={'aqi': 'AQI', 'timestamp': 'Thời gian'})
            fig1.update_layout(height=chart_height)
            st.plotly_chart(fig1, use_container_width=True)
        
        with chart_tab2:
            fig2 = px.bar(df, x='timestamp', y='aqi',
                         title=f'{city} - Phân bố AQI theo giờ',
                         labels={'aqi': 'AQI', 'timestamp': 'Thời gian'})
            fig2.update_layout(height=chart_height)
            st.plotly_chart(fig2, use_container_width=True)
        
        with chart_tab3:
            fig3 = px.box(df, x='hour', y='aqi',
                         title=f'{city} - Thống kê AQI theo giờ trong ngày',
                         labels={'aqi': 'AQI', 'hour': 'Giờ'})
            fig3.update_layout(height=chart_height)
            st.plotly_chart(fig3, use_container_width=True)

# Thống kê chi tiết
st.markdown("## 📊 Thống kê chi tiết")

# Tạo bảng thống kê
stats_data = []
for city in selected_cities:
    df = load_historical(city, days)
    if not df.empty:
        stats_data.append({
            'Thành phố': city,
            'Số records': len(df),
            'AQI TB': f"{df['aqi'].mean():.1f}",
            'AQI Max': df['aqi'].max(),
            'AQI Min': df['aqi'].min(),
            'Nhiệt độ TB': f"{df['temperature'].mean():.1f}°C",
            'Độ ẩm TB': f"{df['humidity'].mean():.0f}%"
        })

stats_df = pd.DataFrame(stats_data)
st.dataframe(stats_df, use_container_width=True, hide_index=True)

# Tự động làm mới
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; padding: 2rem;">
    <p>🌍 Hệ thống giám sát chất lượng không khí - Đồ án Kỹ thuật dữ liệu</p>
    <p>📊 Dữ liệu được cập nhật mỗi giờ từ Open-Meteo API</p>
    <p>🔄 Tự động làm mới mỗi {} giây</p>
</div>
""".format(refresh_interval if auto_refresh else 0), unsafe_allow_html=True)