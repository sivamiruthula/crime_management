@echo off
title Crime Management System - Auto Runner

echo ==================================================
echo   🚓 Starting Crime Management System
echo ==================================================
echo.

REM --- Activate Python environment ---
call frontend_env\Scripts\activate

REM --- Start Streamlit backend in new window ---
echo Starting Backend (Streamlit)...
start cmd /k "cd /d D:\Crime-Management-System-main && call frontend_env\Scripts\activate && python -m streamlit run main_backend.py"

REM --- Start React frontend in new window ---
echo Starting Frontend (React)...
start cmd /k "cd /d D:\Crime-Management-System-main\frontend && npm start"

echo.
echo ✅ Both Backend and Frontend are starting...
echo Close this window after use.
pause
