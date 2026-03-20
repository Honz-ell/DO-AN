"""
compare_models.py - So sánh kết quả giữa ARIMA và XGBoost
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# =============================================
# PHẦN 1: FEATURE ENGINEERING
# =============================================

def create_features(df):
    """Tạo features cho mô hình dự báo"""
    df = df.copy()
    
    # Lag features
    df['lag_1'] = df['aqi'].shift(1)
    df['lag_2'] = df['aqi'].shift(2)
    df['lag_3'] = df['aqi'].shift(3)
    df['lag_6'] = df['aqi'].shift(6)
    df['lag_12'] = df['aqi'].shift(12)
    df['lag_24'] = df['aqi'].shift(24)
    
    # Time features
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Rolling statistics
    df['rolling_mean_6h'] = df['aqi'].rolling(window=6).mean()
    df['rolling_mean_12h'] = df['aqi'].rolling(window=12).mean()
    df['rolling_mean_24h'] = df['aqi'].rolling(window=24).mean()
    
    return df.dropna()

def load_data_from_db(city):
    """Đọc dữ liệu từ database"""
    import sqlite3
    from database import get_connection
    
    conn = get_connection()
    query = f"""
        SELECT timestamp, aqi 
        FROM aqi_readings 
        WHERE city = '{city}'
        ORDER BY timestamp
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# =============================================
# PHẦN 2: MÔ HÌNH ARIMA
# =============================================

from statsmodels.tsa.arima.model import ARIMA

def train_arima(train_data, test_data):
    """Huấn luyện ARIMA và dự báo"""
    try:
        model = ARIMA(train_data, order=(1,0,1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=len(test_data))
        
        rmse = np.sqrt(mean_squared_error(test_data, forecast))
        mae = mean_absolute_error(test_data, forecast)
        mape = np.mean(np.abs((test_data - forecast) / test_data)) * 100
        
        return {
            'forecast': forecast,
            'rmse': rmse,
            'mae': mae,
            'mape': mape
        }
    except:
        return None

# =============================================
# PHẦN 3: MÔ HÌNH XGBOOST
# =============================================

import xgboost as xgb
from sklearn.model_selection import train_test_split

def train_xgboost(df):
    """Huấn luyện XGBoost và dự báo"""
    try:
        # Tạo features
        df_features = create_features(df)
        
        # Chuẩn bị dữ liệu
        feature_cols = ['lag_1', 'lag_2', 'lag_3', 'lag_6', 'lag_12', 'lag_24',
                       'hour', 'day_of_week', 'is_weekend',
                       'rolling_mean_6h', 'rolling_mean_12h', 'rolling_mean_24h']
        
        X = df_features[feature_cols]
        y = df_features['aqi']
        
        # Chia train/test
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Huấn luyện
        model = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1)
        model.fit(X_train, y_train)
        
        # Dự báo
        y_pred = model.predict(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        return {
            'forecast': y_pred,
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'feature_importance': dict(zip(feature_cols, model.feature_importances_))
        }
    except Exception as e:
        print(f"   ❌ Lỗi XGBoost: {e}")
        return None

# =============================================
# PHẦN 4: SO SÁNH KẾT QUẢ
# =============================================

def compare_models():
    """So sánh ARIMA và XGBoost cho 5 tỉnh"""
    print("="*70)
    print("🔬 BẮT ĐẦU SO SÁNH MÔ HÌNH DỰ BÁO AQI")
    print("="*70)
    
    cities = ['Hanoi', 'Haiphong', 'Danang', 'HCMC', 'Cantho']
    city_names = {
        'Hanoi': 'Hà Nội',
        'Haiphong': 'Hải Phòng',
        'Danang': 'Đà Nẵng',
        'HCMC': 'TP.HCM',
        'Cantho': 'Cần Thơ'
    }
    
    results = []
    
    for city in cities:
        print(f"\n📊 Đang xử lý {city_names.get(city, city)}...")
        
        # Đọc dữ liệu
        df = load_data_from_db(city)
        
        if len(df) < 50:
            print(f"   ⚠️ Không đủ dữ liệu (chỉ {len(df)} records)")
            continue
        
        # Chuẩn bị dữ liệu cho ARIMA
        values = df['aqi'].values
        split_idx = int(len(values) * 0.8)
        train, test = values[:split_idx], values[split_idx:]
        
        # ARIMA
        print(f"   📈 Đang huấn luyện ARIMA...")
        arima_result = train_arima(train, test)
        
        # XGBoost
        print(f"   📊 Đang huấn luyện XGBoost...")
        xgb_result = train_xgboost(df)
        
        if arima_result and xgb_result:
            results.append({
                'city': city,
                'ARIMA_RMSE': round(arima_result['rmse'], 2),
                'XGB_RMSE': round(xgb_result['rmse'], 2),
                'ARIMA_MAE': round(arima_result['mae'], 2),
                'XGB_MAE': round(xgb_result['mae'], 2),
                'ARIMA_MAPE': round(arima_result['mape'], 2),
                'XGB_MAPE': round(xgb_result['mape'], 2),
                'Tốt hơn': 'XGBoost' if xgb_result['rmse'] < arima_result['rmse'] else 'ARIMA'
            })
            
            print(f"   ✅ ARIMA - RMSE: {arima_result['rmse']:.2f}")
            print(f"   ✅ XGBoost - RMSE: {xgb_result['rmse']:.2f}")
    
    # Tổng kết
    if results:
        df_results = pd.DataFrame(results)
        
        print("\n" + "="*70)
        print("📊 BẢNG SO SÁNH KẾT QUẢ")
        print("="*70)
        print(df_results.to_string(index=False))
        
        # Lưu file
        df_results.to_csv('model_comparison_results.csv', index=False)
        print("\n💾 Đã lưu kết quả vào 'model_comparison_results.csv'")
        
        # Tính trung bình
        print("\n📈 TRUNG BÌNH CHUNG:")
        print(f"   ARIMA - RMSE: {df_results['ARIMA_RMSE'].mean():.2f}")
        print(f"   XGBoost - RMSE: {df_results['XGB_RMSE'].mean():.2f}")
    else:
        print("\n❌ Không có kết quả để so sánh")

if __name__ == "__main__":
    compare_models()