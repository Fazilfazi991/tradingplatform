[CmdletBinding()]
param(
    [string]$TaskName = "VerifiedEdge-IntelligenceWorker"
)

$ErrorActionPreference = "Stop"
$workspacePath = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$runner = Join-Path $workspacePath "scripts/run_intelligence_worker_supervised.ps1"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$runner`" -Workspace `"$workspacePath`"" `
    -WorkingDirectory $workspacePath
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal `
    -Description "Platform-owned supervised RBI/SEBI intelligence scheduler" -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName

$monitorName = "$TaskName-HealthMonitor"
$python = Join-Path $workspacePath ".venv/Scripts/python.exe"
$monitorAction = New-ScheduledTaskAction `
    -Execute $python `
    -Argument "scripts/build_current_intelligence_health.py" `
    -WorkingDirectory $workspacePath
$monitorTrigger = New-ScheduledTaskTrigger `
    -Once `
    -At ((Get-Date).AddMinutes(1)) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName $monitorName -Action $monitorAction -Trigger $monitorTrigger `
    -Settings $settings -Principal $principal `
    -Description "Independent current-health monitor for the intelligence worker" -Force | Out-Null
Start-ScheduledTask -TaskName $monitorName

Write-Output "TASK_REGISTERED_AND_STARTED"
