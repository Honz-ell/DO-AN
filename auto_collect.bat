@echo off
cd /d D:\đồ án ngành
echo ===== He Thong Giam Sat Tu Dong =====
echo  START: %date% %time%
echo.

set /a count=1
:loop
echo.
echo ===== COUNT %count% =====
echo TIME: %time%
echo.

echo  Thu thap du lieu...
python producer.py

echo  Xu ly du lieu...
python consumer.py

echo  Kiem tra canh bao...
python alert.py

echo  wait 1 hour (3600 giây)...
timeout /t 3600

set /a count+=1
goto loop