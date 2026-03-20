"""
auth_database.py - Quản lý người dùng cho hệ thống cảnh báo AQI
"""

import sqlite3
import hashlib
import os
from database import get_connection

def init_auth_db():
    """Tạo bảng users nếu chưa có"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tạo bảng users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Tạo bảng user_cities (theo dõi thành phố)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city TEXT NOT NULL,
            alert_threshold INTEGER DEFAULT 150,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, city)
        )
    """)
    
    # Tạo bảng alert_history (lịch sử cảnh báo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city TEXT NOT NULL,
            aqi INTEGER NOT NULL,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database auth initialized")

def hash_password(password):
    """Mã hóa mật khẩu"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    """Đăng ký người dùng mới"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        hashed = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        """, (username, email, hashed))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Tự động thêm các thành phố mặc định
        default_cities = ['Hanoi', 'Haiphong', 'Danang', 'HCMC', 'Cantho']
        for city in default_cities:
            cursor.execute("""
                INSERT INTO user_cities (user_id, city)
                VALUES (?, ?)
            """, (user_id, city))
        
        conn.commit()
        return True, user_id
    except sqlite3.IntegrityError:
        return False, "Username hoặc email đã tồn tại"
    finally:
        conn.close()

def login_user(username, password):
    """Đăng nhập"""
    conn = get_connection()
    cursor = conn.cursor()
    
    hashed = hash_password(password)
    cursor.execute("""
        SELECT id, username, email FROM users
        WHERE (username = ? OR email = ?) AND password = ? AND is_active = 1
    """, (username, username, hashed))
    
    user = cursor.fetchone()
    if user:
        # Cập nhật last_login
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user[0],))
        conn.commit()
    
    conn.close()
    return user

def get_user_cities(user_id):
    """Lấy danh sách thành phố user theo dõi"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT city, alert_threshold FROM user_cities
        WHERE user_id = ? AND is_active = 1
    """, (user_id,))
    
    cities = cursor.fetchall()
    conn.close()
    return cities

def update_user_city(user_id, city, threshold):
    """Cập nhật ngưỡng cảnh báo cho thành phố"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE user_cities SET alert_threshold = ?
        WHERE user_id = ? AND city = ?
    """, (threshold, user_id, city))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_auth_db()
    print("✅ Auth database ready!")