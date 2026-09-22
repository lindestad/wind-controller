param([string]$Workspace = (Join-Path (Split-Path $PSScriptRoot -Parent) '../wind-zephyr'))
$ErrorActionPreference = 'Stop'
if (Test-Path (Join-Path $Workspace '.west')) { throw 'Workspace already initialized; refusing to replace it.' }
New-Item -ItemType Directory -Path $Workspace -Force | Out-Null
& py -3.12 -m venv (Join-Path $Workspace '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 and its py launcher first.' }
$python = Join-Path $Workspace '.venv/Scripts/python.exe'
& $python -m pip install west==1.5.0
if ($LASTEXITCODE -ne 0) { throw 'west installation failed' }
& $python -m west init -m https://github.com/zephyrproject-rtos/zephyr --mr dccb09599635bdff17633fa7e9dab014b91dce90 $Workspace
if ($LASTEXITCODE -ne 0) { throw 'west init failed' }
Push-Location $Workspace
try {
    & $python -m west update
    if ($LASTEXITCODE -ne 0) { throw 'west update failed' }
    & $python -m pip install -r zephyr/scripts/requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Zephyr requirements failed' }
    & $python -m west packages pip --install
    if ($LASTEXITCODE -ne 0) { throw 'Module requirements failed' }
    & $python -m west blobs fetch hal_espressif
    if ($LASTEXITCODE -ne 0) { throw 'Espressif blobs failed' }
    & $python -m pip install esptool==5.4.0
    if ($LASTEXITCODE -ne 0) { throw 'esptool installation failed' }
} finally { Pop-Location }
Write-Output 'Dependencies ready. Install Zephyr SDK 1.0.1 and run scripts/build.ps1.'
