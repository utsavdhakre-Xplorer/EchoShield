# EchoShield backend setup and run helper for Windows PowerShell.
# Usage: .\setup.ps1 [-SkipInstall] [-RunServer]

[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$RunServer
)

$ErrorActionPreference = "Stop"
$BackendDir = $PSScriptRoot
$VenvDir = Join-Path $BackendDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
$EnvFile = Join-Path $BackendDir ".env"
$EnvExample = Join-Path $BackendDir ".env.example"

function Assert-Python311 {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python was not found. Install Python 3.11 and add it to PATH."
    }
    $version = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
    if ($version -ne "3.11") {
        throw "EchoShield backend targets Python 3.11; found Python $version. Use the Python 3.11 launcher (py -3.11)."
    }
}

Assert-Python311

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating Python 3.11 virtual environment..."
    & python -m venv $VenvDir
}
if (-not (Test-Path $PythonExe)) {
    throw "Virtual environment creation failed: $PythonExe was not found."
}

if (-not $SkipInstall) {
    Write-Host "Installing backend dependencies from the pinned requirements file..."
    & $PipExe install --upgrade pip
    & $PipExe install -r (Join-Path $BackendDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
}

if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "Created backend/.env from .env.example. Edit it before using accounts/database features."
}

Write-Host "Setup complete. Python environment: $VenvDir"
if ($RunServer) {
    Write-Host "Starting EchoShield backend on http://127.0.0.1:8000"
    Push-Location $BackendDir
    try { & $PythonExe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload }
    finally { Pop-Location }
} else {
    Write-Host "To start the server: .\setup.ps1 -SkipInstall -RunServer"
}
