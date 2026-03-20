"""
consumer.py - Đọc từ message_queue, xử lý và lưu vào aqi_readings
"""

import sqlite3
import json
from datetime import datetime
import time
from database import get_connection

def process_message(row):
    """Xử lý một message: trích xuất thông tin từ raw_data"""
    queue_id, timestamp, city, raw_data_str, processed, created_at = row
    
    try:
        # Parse JSON
        raw_data = json.loads(raw_data_str)
        
        # Trích xuất thông tin
        pollution = raw_data['data']['current']['pollution']
        weather = raw_data['data']['current']['weather']
        
        processed_data = {
            'timestamp': pollution['ts'],
            'city': city,
            'aqi': pollution['aqius'],
            'temperature': weather['tp'],
            'humidity': weather['hu'],
            'main_pollutant': pollution.get('mainus', 'p2'),
            'original_queue_id': queue_id
        }
        
        return True, processed_data
    except Exception as e:
        return False, str(e)

def save_to_readings(data):
    """Lưu dữ liệu đã xử lý vào aqi_readings"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO aqi_readings 
        (timestamp, city, aqi, temperature, humidity, main_pollutant)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data['timestamp'],
        data['city'],
        data['aqi'],
        data['temperature'],
        data['humidity'],
        data['main_pollutant']
    ))
    
    reading_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reading_id

def mark_as_processed(queue_id):
    """Đánh dấu message đã xử lý"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE message_queue 
        SET processed = 1 
        WHERE id = ?
    """, (queue_id,))
    
    conn.commit()
    conn.close()

def process_queue():
    """Xử lý tất cả message chưa được xử lý"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy các message chưa xử lý
    cursor.execute("""
        SELECT id, timestamp, city, raw_data, processed, created_at
        FROM message_queue
        WHERE processed = 0
        ORDER BY id ASC
    """)
    
    messages = cursor.fetchall()
    conn.close()
    
    if not messages:
        print("📭 Không có message nào trong queue")
        return
    
    print(f"\n📨 Tìm thấy {len(messages)} message cần xử lý")
    
    processed_count = 0
    error_count = 0
    
    for msg in messages:
        print(f"\n🔄 Đang xử lý message ID: {msg[0]} - {msg[2]}")
        
        success, result = process_message(msg)
        
        if success:
            # Lưu vào readings
            reading_id = save_to_readings(result)
            # Đánh dấu queue đã xử lý
            mark_as_processed(msg[0])
            
            print(f"   ✅ Đã lưu vào readings (ID: {reading_id})")
            print(f"   📊 AQI: {result['aqi']}, {result['temperature']}°C")
            processed_count += 1
        else:
            print(f"   ❌ Lỗi xử lý: {result}")
            error_count += 1
    
    print(f"\n📊 KẾT QUẢ: {processed_count} thành công, {error_count} lỗi")

if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"🔄 CONSUMER - XỬ LÝ QUEUE - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    process_queue()
    
    # Nếu muốn chạy liên tục:
    # while True:
    #     process_queue()
    #     print("\n⏰ Đợi 10 giây...")
    #     time.sleep(10)