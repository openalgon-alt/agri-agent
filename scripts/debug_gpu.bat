@echo off
echo "Stopping any running Ollama instances..."
taskkill /F /IM ollama.exe
taskkill /F /IM ollama_app.exe

echo "Setting AMD GPU Environment Variable..."
set HSA_OVERRIDE_GFX_VERSION=10.3.0
set OLLAMA_VULKAN=1
set OLLAMA_DEBUG=1

echo "Starting Ollama Server (Logging to ollama_debug.log)..."
start /B ollama serve > ollama_debug.log 2>&1

echo "Waiting for server to start..."
timeout /t 5

echo "Triggering Model Load (This will print to log)..."
ollama run qwen3-vl "Test GPU usage."

echo "Checking Logs for GPU Offload..."
findstr "partial offload" ollama_debug.log
findstr "gpu" ollama_debug.log

echo "---------------------------------------------------"
echo "If you see 'offload' or 'gpu' above, it is working!"
echo "Check ollama_debug.log for full details."
pause
