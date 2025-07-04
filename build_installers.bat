@echo off
echo Building System Maintenance Tools Installers
echo ============================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install cx_Freeze

REM Create all installers
echo Creating installers...
python create_installer.py all

echo.
echo Build process completed!
echo Check the 'installers' directory for generated files.
pause
