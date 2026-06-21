@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

echo Starting Whisper Transcriber...
echo.

rem Start backend minimized
start "Whisper Backend" /MIN cmd /c "cd /d %SCRIPT_DIR%backend && venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude workspace/ --reload-exclude uploads/ --reload-exclude recordings/ --reload-exclude exports/ --reload-exclude venv/ --reload-exclude __pycache__/"

rem Start frontend minimized  
start "Whisper Frontend" /MIN cmd /c "cd /d %SCRIPT_DIR%frontend && npx vite --host"

rem Wait for servers to start
timeout /t 5 >nul

rem Open browser to the app
start "" "http://localhost:5173"

echo App is running at http://localhost:5173
endlocal
