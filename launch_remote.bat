@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.10 or later from python.org.
  pause
  exit /b 1
)
py -m pip show broadlink >nul 2>&1
if errorlevel 1 (
  echo Installing BroadLink library...
  py -m pip install -r "%~dp0requirements.txt"
)
py "%~dp0sony_trinitron_remote.py"
if errorlevel 1 pause
