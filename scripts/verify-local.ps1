param([switch]$SkipInstall, [switch]$OfflineModels)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
$previousHubOffline = $env:HF_HUB_OFFLINE
$previousTransformersOffline = $env:TRANSFORMERS_OFFLINE

function Invoke-CheckedPython {
    param([string[]]$PythonArguments)
    & $pythonPath @PythonArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python step failed (exit $LASTEXITCODE): $($PythonArguments -join ' ')"
    }
}

Push-Location $projectRoot
try {
    if ($OfflineModels) {
        $env:HF_HUB_OFFLINE = '1'
        $env:TRANSFORMERS_OFFLINE = '1'
    }
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        & py -3.12 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create Python 3.12 environment.' }
    }
    if (-not $SkipInstall) {
        Invoke-CheckedPython -PythonArguments @('-m', 'pip', 'install', '-e', '.[dev]')
    }
    Invoke-CheckedPython -PythonArguments @('-m', 'pip', 'check')
    Invoke-CheckedPython -PythonArguments @('-m', 'oxmemory', '--help')
    $smokeReport = Join-Path $projectRoot ('.venv/memory-system-smoke-' + [guid]::NewGuid().ToString('N') + '.json')
    Invoke-CheckedPython -PythonArguments @('scripts/smoke_memory_system.py', '--output', $smokeReport)
    # A fresh path avoids unrelated Windows pytest temp-directory permissions.
    $testDirectory = Join-Path $projectRoot ('.venv/pytest-' + [guid]::NewGuid().ToString('N'))
    Invoke-CheckedPython -PythonArguments @(
        '-m', 'pytest', 'tests/', '-v', '--basetemp', $testDirectory
    )
    Invoke-CheckedPython -PythonArguments @('-m', 'oxmemory.demo', '--output', 'demo-result.json')
    Invoke-CheckedPython -PythonArguments @(
        '-m', 'oxmemory.evaluation', '--semantic', '--output', 'evaluation-semantic.json'
    )
    Write-Host 'PASS: dependencies, architecture smoke, CLI, tests, real MCP client, embeddings, and semantic evaluation.'
}
finally {
    $env:HF_HUB_OFFLINE = $previousHubOffline
    $env:TRANSFORMERS_OFFLINE = $previousTransformersOffline
    Pop-Location
}
