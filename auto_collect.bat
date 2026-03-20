@echo off
cd /d D:\đồ án ngành
echo ===== He Thong Giam Sat Tu Đong =====
echo Bắt đầu: %date% %time%
echo.

set /a count=1
:loop
echo.
echo ===== Lan chay thu%count% =====
echo Thời gian: %time%
echo.

echo 📥 Thu thập dữ liệu...
python producer.py

echo 🔄 Xử lý dữ liệu...
python consumer.py

echo 📧 Kiểm tra cảnh báo...
python alert.py

echo ⏰ Đợi 1 giờ (3600 giây)...
timeout /t 3600

set /a count+=1
goto loop