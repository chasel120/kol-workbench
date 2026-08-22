@echo off
cd /d "%~dp0"
echo Starting KOL Management Workbench...
echo URL: http://127.0.0.1:8766
start "" "http://127.0.0.1:8766"
python -m agent_runtime.server
pause
