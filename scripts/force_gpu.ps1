
Write-Host "Aggressively killing all Ollama processes..." -ForegroundColor Red
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "ollama_app" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Setting AMD Override & Vulkan..." -ForegroundColor Green
$env:HSA_OVERRIDE_GFX_VERSION = "10.3.0"
$env:OLLAMA_VULKAN = "1"
$env:OLLAMA_Debug = "1"

Write-Host "Starting Ollama Server in background..." -ForegroundColor Yellow
$process = Start-Process -FilePath "ollama" -ArgumentList "serve" -PassThru -NoNewWindow

Write-Host "Waiting 5 seconds for initialization..."
Start-Sleep -Seconds 5

if ($process.HasExited) {
    Write-Host "Ollama crashed on start! Check logs." -ForegroundColor Red
    exit
}

Write-Host "Triggering Qwen 3 VL Load..."
ollama run qwen3-vl "System GPU Check."

Write-Host "Done. Check Task Manager now!" -ForegroundColor Cyan
