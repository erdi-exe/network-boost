@echo off
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

python -m pip install -r requirements.txt
cls
python boost_net.py
pause
