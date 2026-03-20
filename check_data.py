"""
check_data.py - Kiểm tra dữ liệu trong SQLite
"""

import sqlite3
import pandas as pd
from database import get_connection

def check_queue():
    """Xem queue có bao nhiêu message"""
    conn = get_connection()
    
    df_queue = pd.read_sql("""
        SELECT 
            COUNT(*) as total_messages,
            SUM(CASE WHEN processed=0 THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN processed=1 THEN 1 ELSE 0 END) as processed
        FROM message_queue
    """, conn)
    
    print("\n📊 THỐNG KÊ QUEUE:")
    print(df_queue.to_string(index=False))
    
    conn.close()

def check_readings():
    """Xem dữ liệu readings"""
    conn = get_connection()
    
    df_readings = pd.read_sql("""
        SELECT 
            city,
            COUNT(*) as so_luong,
            ROUND(AVG(aqi), 1) as aqi_tb,
            MAX(aqi) as aqi_max,
            MIN(aqi) as aqi_min,
            ROUND(AVG(temperature), 1) as nhiet_do_tb
        FROM aqi_readings
        GROUP BY city
    """, conn)
    
    print("\n📊 THỐNG KÊ READINGS:")
    print(df_readings.to_string(index=False))
    
    # Xem 5 bản ghi mới nhất
    df_latest = pd.read_sql("""
        SELECT timestamp, city, aqi, temperature, humidity
        FROM aqi_readings
        ORDER BY id DESC
        LIMIT 5
    """, conn)
    
    print("\n📋 5 BẢN GHI MỚI NHẤT:")
    print(df_latest.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    check_queue()
    check_readings()