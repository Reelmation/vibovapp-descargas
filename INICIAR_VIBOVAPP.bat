@echo off
cd /d "%~dp0"
echo Revisando que todo este instalado (la primera vez tarda un poco)...
python -m pip install --quiet flask pillow
if errorlevel 1 (
  echo.
  echo No pude instalar las librerias. Revisa que Python este instalado y que tengas internet.
  pause
  exit /b
)
python iniciar.py
pause
