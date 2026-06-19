@echo off
echo Starting Whisper Transcriber...
echo.
echo Starting backend on http://localhost:8000
start "Whisper Backend" cmd /c "cd /d C:\Whisper\backend && venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo Starting frontend on http://localhost:5173
start "Whisper Frontend" cmd /c "cd /d C:\Whisper\frontend && npx vite --host"
timeout /t 3 >nul
start http://localhost:5173
echo.
echo App is running. Close the two terminal windows to stop.
