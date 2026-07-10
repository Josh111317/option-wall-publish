@echo off
cd /d D:\codex\options\option_wall_publish

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8502" ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>nul

D:\anaconda3\python.exe -m streamlit run publish_app.py --server.port 8502
pause
