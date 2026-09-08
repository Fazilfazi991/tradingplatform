[CmdletBinding()]
param(
    [string]$Workspace = (Split-Path -Parent $PSScriptRoot),
    [string]$State = "data/local/intelligence-operations.sqlite3",
    [string]$OutputRoot = "data/local/intelligence"
)

$ErrorActionPreference = "Stop"
$workspacePath = (Resolve-Path -LiteralPath $Workspace).Path
Set-Location -LiteralPath $workspacePath

$envPath = Join-Path $workspacePath ".env"
if (-not (Test-Path -LiteralPath $envPath)) {
    throw "Required local environment file is absent."
}

foreach ($line in Get-Content -LiteralPath $envPath) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
        $name = $Matches[1]
        $value = $Matches[2].Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}

if (-not $env:OPENAI_API_KEY) { throw "OPENAI_API_KEY is absent." }
if ($env:OPENAI_MODEL -ne "gpt-5.6-luna") { throw "Approved OPENAI_MODEL is not configured." }
$env:LLM_RUNTIME_ENABLED = "true"
$env:VE_INTELLIGENCE_SUPERVISOR = "WINDOWS_TASK_SCHEDULER"

$python = Join-Path $workspacePath ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Project Python runtime is absent." }

$logRoot = Join-Path $workspacePath "data/local/intelligence-worker"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$logPath = Join-Path $logRoot "worker.log"

& $python "scripts/run_intelligence_worker.py" --state $State --output-root $OutputRoot *>> $logPath
exit $LASTEXITCODE
