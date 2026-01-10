@echo off
echo "Stopping Ollama..."
taskkill /F /IM ollama.exe
taskkill /F /IM ollama_app.exe

echo "Enabling OLLAMA_VULKAN=1..."
set OLLAMA_VULKAN=1
set OLLAMA_DEBUG=1

echo "Starting Ollama with Vulkan..."
start /B ollama serve > ollama_vulkan.log 2>&1

echo "Waiting..."
timeout /t 5

echo "Testing..."
ollama run llama3.2 "Am I using Vulkan?"
