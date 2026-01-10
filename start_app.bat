@echo off
echo ===================================================
echo   STARTING REACT + FASTAPI AGENT
echo ===================================================

echo [1/4] Stopping Stale Ollama...
taskkill /F /IM ollama.exe 2>nul
taskkill /F /IM ollama_app.exe 2>nul

echo [2/4] Initializing GPU (RX 6600)...
set HSA_OVERRIDE_GFX_VERSION=10.3.0
set OLLAMA_VULKAN=1
start "Ollama GPU Server" /MIN /B ollama serve > ollama_gpu.log 2>&1
timeout /t 5 >nul

echo [3/4] Starting Backend (API)...
start "AgriBackend" cmd /k "call .venv\Scripts\activate && python -m uvicorn backend.main:app --reload --port 8000"

echo [2/2] Starting Frontend (UI)...
cd frontend
start "AgriFrontend" cmd /k "npm run dev"

echo Done! Open http://localhost:5173 in your browser.
pause
