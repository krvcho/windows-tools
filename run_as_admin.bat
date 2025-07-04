@echo off
echo Requesting administrator privileges...
powershell -Command "Start-Process python -ArgumentList 'main.py' -Verb RunAs"
pause
