# Wrapper for Task Scheduler: ensures backend cwd, PYTHONPATH, and propagates exit code.
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("discover_jobs", "send_job_alerts")]
    [string]$Task
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Backend = Join-Path $RepoRoot "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$Logs = Join-Path $Backend "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

if (-not (Test-Path $Python)) {
    Write-Error "Python not found at $Python"
    exit 4
}

Set-Location $Backend
$env:PYTHONPATH = "."

$module = switch ($Task) {
    "discover_jobs" { "app.scripts.discover_jobs" }
    "send_job_alerts" { "app.scripts.send_job_alerts" }
}

& $Python -m $module
exit $LASTEXITCODE
