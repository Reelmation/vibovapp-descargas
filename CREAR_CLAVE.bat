@echo off
cd /d "%~dp0"
python generar_clave.py
if errorlevel 1 pause
