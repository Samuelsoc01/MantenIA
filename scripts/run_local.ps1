param([string]$PythonExe = "")
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if ($PythonExe) { $pythonCommand = $PythonExe }
elseif (Test-Path ".runtime\python311\python.exe") { $pythonCommand = Join-Path $projectRoot ".runtime\python311\python.exe" }
elseif (Test-Path ".venv\Scripts\python.exe") { $pythonCommand = Join-Path $projectRoot ".venv\Scripts\python.exe" }
else {
    & py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Instale Python 3.11 o indique -PythonExe." }
    $pythonCommand = Join-Path $projectRoot ".venv\Scripts\python.exe"
    & $pythonCommand -m pip install --no-cache-dir -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar dependencias." }
}
$env:PYTHONDONTWRITEBYTECODE = "1"
& $pythonCommand -m scripts.local_stack
if ($LASTEXITCODE -ne 0) { throw "Revise .runtime/local.log." }
