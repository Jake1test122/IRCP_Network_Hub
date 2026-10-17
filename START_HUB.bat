@echo off
setlocal
cd /d "%~dp0"
echo === ICRP NETWORK HUB ONLY ===
set /p "DISCORD_TOKEN=Paste bot TOKEN (not application ID): "
set /p "SERVER_ID=Paste NETWORK HUB server ID: "
if "%DISCORD_TOKEN%"=="" (echo Token missing & pause & exit /b 1)
if "%SERVER_ID%"=="" (echo Server ID missing & pause & exit /b 1)
python -m pip install -r requirements.txt
if errorlevel 1 (echo Package installation failed & pause & exit /b 1)
python main.py
pause
