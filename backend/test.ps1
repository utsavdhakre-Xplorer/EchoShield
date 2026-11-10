# Run EchoShield backend unit tests using the project virtual environment.
# Usage: .\test.ps1 [-InstallDependencies]

[CmdletBinding()]
param(
    [switch]$InstallDependencies
)

$ErrorActionPreference = "Stop"
$BackendDir = $PSScriptRoot
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
$PipExe = Join-Path $BackendDir ".venv\Scripts\pip.exe"

if (-not (Test-Path $PythonExe)) {
    throw "Backend virtual environment not found. Run .\setup.ps1 first."
}

if ($InstallDependencies) {
    Write-Host "Installing backend requirements before tests..."
    & $PipExe install -r (Join-Path $BackendDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
}

Write-Host "Running backend unit tests..."
Push-Location $BackendDir
try {
    & $PythonExe -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }
}
finally {
    Pop-Location
}
