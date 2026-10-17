@echo off
cd /d "%~dp0"
if "%DISCORD_TOKEN%"=="" set /p DISCORD_TOKEN=Discord bot token (hidden input not supported - prefer environment variables): 
if "%ICRP_SERVER_ID%"=="" set /p ICRP_SERVER_ID=ICRP Community server ID: 
py -m pip install -r requirements_icrp_community.txt
py icrp_community_bot.py
pause
