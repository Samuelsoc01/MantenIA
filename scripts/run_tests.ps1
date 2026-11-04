param([string]$PythonExe = "")
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not $PythonExe) {
    if (Test-Path ".runtime\python311\python.exe") { $PythonExe = ".runtime\python311\python.exe" }
    else { $PythonExe = ".venv\Scripts\python.exe" }
}
New-Item -ItemType Directory -Force .runtime,results/integration | Out-Null
$env:PYTHONDONTWRITEBYTECODE = "1"
& $PythonExe -m pytest -q --basetemp=.runtime/pytest --junitxml=results/integration/pytest.xml
if ($LASTEXITCODE -ne 0) { throw "Las pruebas fallaron." }
