"""
producer.py - Thu thập dữ liệu AQI và đẩy vào message_queue
"""

import requests
import json
from datetime import datetime
import sqlite3
import time
from alert import convert_to_vn_time
from database import get_connection
import hashlib
import json
# Cấu hình
API_KEY = "9dd5c1c6-ddcb-4988-abc0-edac0dd63773"
CITIES = [
    # Miền Bắc (2 tỉnh)
    {"name": "Hanoi", "name_vn": "Hà Nội", "lat": 21.0285, "lon": 105.8542},
    {"name": "Haiphong", "name_vn": "Hải Phòng", "lat": 20.8449, "lon": 106.6881},
    
    # Miền Trung (1 tỉnh)
    {"name": "Danang", "name_vn": "Đà Nẵng", "lat": 16.0544, "lon": 108.2022},
    
    # Miền Nam (2 tỉnh)
    {"name": "HCMC", "name_vn": "TP. Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297},
    {"name": "Cantho", "name_vn": "Cần Thơ", "lat": 10.0452, "lon": 105.7469},
]

def fetch_aqi(city):
    """Lấy dữ liệu từ IQAir API"""
    url = "http://api.airvisual.com/v2/nearest_city"
    params = {
        "lat": city["lat"],
        "lon": city["lon"],
        "key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Lỗi {response.status_code}"
    except Exception as e:
        return False, str(e)

def save_to_queue(city_name, raw_data):
    """Lưu dữ liệu vào message_queue, tránh trùng lặp"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tạo hash để kiểm tra trùng
    data_hash = hashlib.md5(json.dumps(raw_data).encode()).hexdigest()
    
    # Kiểm tra xem đã có chưa
    cursor.execute("""
        SELECT id FROM message_queue 
        WHERE city = ? AND raw_data LIKE ? 
        ORDER BY id DESC LIMIT 1
    """, (city_name, f'%{data_hash}%'))
    
    if cursor.fetchone():
        print(f"   ⚠️ Dữ liệu {city_name} đã tồn tại, bỏ qua")
        conn.close()
        return None
    
    cursor.execute("""
        INSERT INTO message_queue (timestamp, city, raw_data)
        VALUES (?, ?, ?)
    """, (
        datetime.now().isoformat(),
        city_name,
        json.dumps(raw_data, ensure_ascii=False)
    ))
    
    conn.commit()
    conn.close()
    return cursor.lastrowid


def collect_and_queue():
    """Thu thập dữ liệu và đẩy vào queue"""
    print(f"\n{'='*60}")
    print(f"🔄 BẮT ĐẦU THU THẬP - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    for city in CITIES:
        print(f"\n📍 {city['name_vn']}")
        
        success, result = fetch_aqi(city)
        
        if success:
            # 👇 THAY TOÀN BỘ PHẦN LOG CŨ BẰNG CODE NÀY
            api_timestamp = result['data']['current']['pollution']['ts']
            current_hour = datetime.now().hour
            current_minute = datetime.now().minute
            api_hour = datetime.fromisoformat(api_timestamp.replace('Z', '+00:00')).hour
            
            print(f"   🕒 API timestamp: {api_timestamp}")
            print(f"   ⏰ Giờ hiện tại: {current_hour}:{current_minute:02d}")
            print(f"   🔄 API giờ: {api_hour}")
            
            if current_hour != api_hour:
                print(f"   ⚠️ API chưa cập nhật cho giờ {current_hour}")
            # 👆 KẾT THÚC PHẦN LOG MỚI
            
            aqi = result['data']['current']['pollution']['aqius']
            queue_id = save_to_queue(city['name'], result)
            print(f"   ✅ AQI: {aqi}")
            print(f"   📥 Đã lưu vào queue (ID: {queue_id})")
        else:
            print(f"   ❌ Lỗi: {result}")
        
        time.sleep(3)
    
    print(f"\n{'='*60}")
    print(f"✅ HOÀN THÀNH")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Chạy 1 lần để test
    collect_and_queue()
    
    # Nếu muốn chạy tự động mỗi giờ, bỏ comment:
    # while True:
    #     collect_and_queue()
    #     print("\n⏰ Chờ 1 giờ...")
    #     time.sleep(3600)