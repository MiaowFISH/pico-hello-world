@echo off
REM Windows批处理脚本 - 快速部署到Pico
cd /d "%~dp0.."
python tools\deploy.py %*
