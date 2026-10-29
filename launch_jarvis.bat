@echo off
rem Launch Jarvis with the project virtual environment when present.
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0main.py" %*
