@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul && (py instalar_neurotrack.py) || (python instalar_neurotrack.py)
if errorlevel 1 (
  echo.
  echo Nao foi possivel instalar. Verifique se o Python esta instalado.
  pause
)
