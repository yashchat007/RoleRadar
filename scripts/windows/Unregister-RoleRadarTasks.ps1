Unregister-ScheduledTask -TaskName "RoleRadar-Discover" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "RoleRadar-JobAlerts" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Removed RoleRadar scheduled tasks (if they existed)."
