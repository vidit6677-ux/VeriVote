param(
    [switch]$InstallPyInstaller
)

$ErrorActionPreference = "Stop"

if ($InstallPyInstaller) {
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller installation failed."
    }
}

$running = Get-Process -Name "VeriVote" -ErrorAction SilentlyContinue
if ($running) {
    throw "VeriVote.exe is still running. Close it before rebuilding."
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name VeriVote `
    --add-data "models;models" `
    --add-data "face_data;face_data" `
    --add-data "demo_qr_codes;demo_qr_codes" `
    main.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed. Close any old executable and retry."
}

if (-not (Test-Path "dist\VeriVote\VeriVote.exe")) {
    throw "Build finished without creating dist\VeriVote\VeriVote.exe."
}

Write-Host "Build complete: dist\VeriVote\VeriVote.exe"
