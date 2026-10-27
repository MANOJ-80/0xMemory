[CmdletBinding()]
param(
    [string]$Project,
    [ValidateSet('vscode','codex','cursor','antigravity')]
    [string[]]$Clients = @('vscode','codex'),
    [string]$PythonBin,
    [switch]$SkipInstall,
    [switch]$OfflineModels,
    [switch]$FullVerify,
    [ValidateSet('native','anonymous')][string]$McpTransport = 'native'
)
$ErrorActionPreference = 'Stop'
$engineRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $engineRoot '.venv/Scripts/python.exe'
$bootstrapArgs = @()
if ($PythonBin) { $bootstrap = $PythonBin }
elseif (Test-Path -LiteralPath $venvPython) { $bootstrap = $venvPython }
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $bootstrap = 'py'
    try { & py -3.12 -c 'import sys' 2>$null; $has312 = ($LASTEXITCODE -eq 0) }
    catch { $has312 = $false }
    if ($has312) { $bootstrapArgs = @('-3.12') }
    else {
        try { & py -3.11 -c 'import sys' 2>$null; $has311 = ($LASTEXITCODE -eq 0) }
        catch { $has311 = $false }
        if (-not $has311) { throw 'Install Python 3.12 or provide -PythonBin with a Python 3.11/3.12 executable.' }
        $bootstrapArgs = @('-3.11')
    }
}
elseif (Get-Command python -ErrorAction SilentlyContinue) { $bootstrap = 'python' }
else { throw 'Install Python 3.12 and Git, reopen PowerShell, then rerun setup.' }
$setupArgs = @((Join-Path $PSScriptRoot 'demo_setup.py'), '--clients') + $Clients
if ($Project) { $setupArgs += @('--project', $Project) }
if ($SkipInstall) { $setupArgs += '--skip-install' }
if ($OfflineModels) { $setupArgs += '--offline-models' }
if ($FullVerify) { $setupArgs += '--full-verify' }
$setupArgs += @('--mcp-transport', $McpTransport)
& $bootstrap @bootstrapArgs @setupArgs
if ($LASTEXITCODE -ne 0) { throw "Demo setup failed (exit $LASTEXITCODE). See the output/log for the failed step." }
