param(
    [string]$Workspace = (Join-Path (Split-Path $PSScriptRoot -Parent) '../wind-zephyr'),
    [string]$Sdk = (Join-Path $env:USERPROFILE 'zephyr-sdk-1.0.1'),
    [switch]$Pristine
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$Workspace = (Resolve-Path -LiteralPath $Workspace).Path
$python = Join-Path $Workspace '.venv/Scripts/python.exe'
$env:PATH = (Join-Path $Workspace '.venv/Scripts') + ';C:\Strawberry\c\bin;' + $env:PATH
$env:ZEPHYR_BASE = Join-Path $Workspace 'zephyr'
$env:ZEPHYR_SDK_INSTALL_DIR = $Sdk
$env:ZEPHYR_TOOLCHAIN_VARIANT = 'zephyr'
$env:CCACHE_DIR = Join-Path $projectRoot '.cache/ccache'
$buildArgs = @('-m','west','build','-b','wind_controller/esp32c3','-d',(Join-Path $projectRoot 'build'),$projectRoot)
if ($Pristine) { $buildArgs += @('-p','always') }
$buildArgs += @('--',('-DUSER_CACHE_DIR=' + (Join-Path $projectRoot '.cache/zephyr')))
Push-Location $env:ZEPHYR_BASE
try {
    & $python @buildArgs
    if ($LASTEXITCODE -ne 0) { throw 'Zephyr build failed' }
} finally { Pop-Location }
& $python (Join-Path $projectRoot 'scripts/audit_build.py') --workspace $Workspace
if ($LASTEXITCODE -ne 0) { throw 'Build configuration audit failed' }
