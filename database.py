"""
database.py - Quản lý kết nối và schema SQLite cho đồ án AQI
"""

import sqlite3
import json
from datetime import datetime
import os

DB_FILE = "aqi_pipeline.db"

def init_database():
    """Khởi tạo database với 2 bảng: queue và readings"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Bảng 1: Hàng đợi (queue) - thay thế Kafka
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            city TEXT NOT NULL,
            raw_data TEXT NOT NULL,  -- JSON string từ API
            processed INTEGER DEFAULT 0,  -- 0: chưa xử lý, 1: đã xử lý
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Bảng 2: Dữ liệu AQI đã xử lý - thay thế TimescaleDB
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aqi_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            city TEXT NOT NULL,
            aqi INTEGER,
            temperature REAL,
            humidity INTEGER,
            main_pollutant TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Index để tăng tốc truy vấn
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_processed ON message_queue(processed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_city_time ON aqi_readings(city, timestamp)")
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_FILE}")

def get_connection():
    """Trả về kết nối SQLite"""
    return sqlite3.connect(DB_FILE)

if __name__ == "__main__":
    init_database()