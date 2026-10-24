# Registers RoleRadar discovery + alert tasks. Edit $RepoRoot if your path differs.
# Requires backend/.env (DATABASE_URL, SMTP_*, optional ALERT_RECIPIENT_EMAIL).
# Logs: written by Python to backend/logs/ (see docs/INDEPENDENT_OPERATION.md).
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Backend = Join-Path $RepoRoot "backend"
$Wrapper = Join-Path $RepoRoot "scripts\windows\Run-RoleRadarTask.ps1"
$Logs = Join-Path $Backend "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

if (-not (Test-Path $Wrapper)) {
    Write-Error "Missing wrapper script: $Wrapper"
    exit 1
}

$DiscoverAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Wrapper`" -Task discover_jobs" `
    -WorkingDirectory $Backend
$DiscoverTrigger = New-ScheduledTaskTrigger -Daily -At "06:00"
# IgnoreNew: skips a new trigger if the previous run is still executing. Not a cross-process mutex.
$DiscoverSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "RoleRadar-Discover" -Action $DiscoverAction -Trigger $DiscoverTrigger -Settings $DiscoverSettings -Force

$AlertAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Wrapper`" -Task send_job_alerts" `
    -WorkingDirectory $Backend
$AlertTrigger = New-ScheduledTaskTrigger -Daily -At "06:30"
Register-ScheduledTask -TaskName "RoleRadar-JobAlerts" -Action $AlertAction -Trigger $AlertTrigger -Settings $DiscoverSettings -Force

Write-Host "Registered RoleRadar-Discover (06:00) and RoleRadar-JobAlerts (06:30)."
Write-Host "Unregister with scripts\windows\Unregister-RoleRadarTasks.ps1"
Write-Host "Ensure backend\.env exists before the first scheduled run."
