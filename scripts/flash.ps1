param(
    [Parameter(Mandatory=$true)][string]$Port,
    [string]$Workspace = (Join-Path (Split-Path $PSScriptRoot -Parent) '../wind-zephyr')
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$Workspace = (Resolve-Path -LiteralPath $Workspace).Path
$python = Join-Path $Workspace '.venv/Scripts/python.exe'
$env:PATH = (Join-Path $Workspace '.venv/Scripts') + ';' + $env:PATH
if (!(Test-Path -LiteralPath (Join-Path $projectRoot 'build/zephyr/zephyr.bin'))) {
    throw 'Build the firmware with scripts/build.ps1 first.'
}
& $python (Join-Path $PSScriptRoot 'stop_for_flash.py') --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Controller did not confirm stopped; flash cancelled.' }
Push-Location (Join-Path $Workspace 'zephyr')
try {
    & $python -m west flash -d (Join-Path $projectRoot 'build') --no-rebuild --esp-device $Port
    if ($LASTEXITCODE -ne 0) { throw 'Flashing failed; keep fans clear and use USB-only recovery.' }
} finally { Pop-Location }
