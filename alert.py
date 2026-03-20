"""
alert.py - Gửi email cảnh báo AQI cho 5 tỉnh
Mỗi tỉnh chỉ gửi 1 bản ghi mới nhất
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import get_connection
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Cấu hình email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "nvhoang08052005@gmail.com"
SENDER_PASSWORD = "iumx oozu ljos mrpw"
RECEIVER_EMAIL = "nvhoang08052005@gmail.com"

# Danh sách 5 tỉnh cần theo dõi
CITIES = ['Hanoi', 'Haiphong', 'Danang', 'HCMC', 'Cantho']
CITY_NAMES = {
    'Hanoi': 'Hà Nội',
    'Haiphong': 'Hải Phòng',
    'Danang': 'Đà Nẵng',
    'HCMC': 'TP.HCM',
    'Cantho': 'Cần Thơ'
}

def convert_to_vn_time(ts):
    """Chuyển đổi thời gian UTC sang giờ Việt Nam"""
    try:
        ts_str = ts.replace('T', ' ').replace('Z', '').split('.')[0]
        dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        vn_dt = dt + timedelta(hours=7)
        return vn_dt.strftime('%H:%M %d/%m/%Y')
    except:
        return ts

def get_aqi_level(aqi):
    """Xác định mức độ AQI"""
    if aqi <= 50: return "🟢 Tốt"
    elif aqi <= 100: return "🟡 Trung bình"
    elif aqi <= 150: return "🟠 Kém"
    elif aqi <= 200: return "🔴 Xấu"
    elif aqi <= 300: return "🟣 Rất xấu"
    else: return "⚫ Nguy hại"

def get_latest_aqi():
    """Lấy AQI mới nhất cho 5 tỉnh"""
    conn = get_connection()
    cursor = conn.cursor()
    
    results = []
    for city in CITIES:
        cursor.execute("""
            SELECT aqi, timestamp 
            FROM aqi_readings 
            WHERE city = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (city,))
        
        row = cursor.fetchone()
        if row:
            results.append({
                'city': city,
                'aqi': row[0],
                'timestamp': row[1]
            })
    
    conn.close()
    return results

def send_alert():
    """Gửi email với AQI mới nhất của 5 tỉnh"""
    data = get_latest_aqi()
    
    if not data:
        print("❌ Không có dữ liệu")
        return False
    
    # Tạo bảng HTML
    rows = ""
    for item in data:
        city_name = CITY_NAMES.get(item['city'], item['city'])
        display_time = convert_to_vn_time(item['timestamp'])
        level = get_aqi_level(item['aqi'])
        
        # Màu sắc theo AQI
        if item['aqi'] > 150:
            color = "#FF0000"  # Đỏ
        elif item['aqi'] > 100:
            color = "#FF4500"  # Cam đỏ
        elif item['aqi'] > 50:
            color = "#FFA500"  # Cam
        else:
            color = "#00FF00"  # Xanh lá
        
        rows += f"""
        <tr>
            <td><strong>{city_name}</strong></td>
            <td style="color: {color}; font-weight: bold;">{item['aqi']}</td>
            <td>{display_time}</td>
            <td>{level}</td>
        </tr>
        """
    
    # Tạo HTML
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th {{ background-color: #4CAF50; color: white; padding: 12px; }}
            td {{ padding: 10px; border: 1px solid #ddd; text-align: center; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .header {{ color: #333; }}
            .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h2 style="color: #333;">🌍 BÁO CÁO CHẤT LƯỢNG KHÔNG KHÍ 5 TỈNH</h2>
        <p>Dữ liệu mới nhất từ IQAir API - <strong>{datetime.now().strftime('%H:%M %d/%m/%Y')}</strong></p>
        
        <table>
            <tr>
                <th>Thành phố</th>
                <th>AQI</th>
                <th>Thời gian (VN)</th>
                <th>Mức độ</th>
            </tr>
            {rows}
        </table>
        
        <p class="footer">
            📧 Email được gửi tự động từ hệ thống giám sát AQI<br>
            Hệ thống giám sát chất lượng không khí - Đồ án Kỹ thuật dữ liệu
        </p>
    </body>
    </html>
    """
    
    # Gửi email
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🌍 BÁO CÁO AQI 5 TỈNH - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Đã gửi email báo cáo 5 tỉnh")
        print(f"   📊 Chi tiết:")
        for item in data:
            print(f"   - {CITY_NAMES[item['city']]}: AQI {item['aqi']}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False

def check_and_alert():
    """Hàm chạy kiểm tra và gửi báo cáo"""
    print(f"\n{'='*60}")
    print(f"🔍 BÁO CÁO AQI 5 TỈNH - {datetime.now().strftime('%H:%M %d/%m/%Y')}")
    print(f"{'='*60}")
    return send_alert()

if __name__ == "__main__":
    check_and_alert()