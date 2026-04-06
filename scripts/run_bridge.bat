@echo off
cd /d "%~dp0.."
echo Run from repo root after configuring bridge.env
python scripts\serial_bridge.py
pause
