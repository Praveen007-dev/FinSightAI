$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot ".venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"
$UvicornPath = Join-Path $VenvPath "Scripts\uvicorn.exe"
$EnvPath = Join-Path $ProjectRoot ".env"
$Port = 8000
$Url = "http://127.0.0.1:$Port"

Write-Host "FinSight AI launcher" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python 3.11+ and ensure it is available on PATH."
}

if (-not (Test-Path $PythonPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the virtual environment."
    }
}

if (-not (Test-Path $EnvPath)) {
    if (Test-Path (Join-Path $ProjectRoot ".env.example")) {
        Copy-Item (Join-Path $ProjectRoot ".env.example") $EnvPath
        Write-Host "Created .env from .env.example. Add your API keys before live research." -ForegroundColor Yellow
    }
    else {
        throw "Missing .env and .env.example."
    }
}

Write-Host "Installing or updating Python dependencies..." -ForegroundColor Yellow
& $PythonPath -m pip install --upgrade pip --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    throw "Could not update pip."
}

& $PythonPath -m pip install -r (Join-Path $ProjectRoot "requirements.txt") --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    throw "Could not install project dependencies."
}

Write-Host "Checking application import..." -ForegroundColor Yellow
& $PythonPath -c "import app; print('Application import: OK')"
if ($LASTEXITCODE -ne 0) {
    throw "The application could not be imported. Review the error above."
}

$ExistingListener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($ExistingListener) {
    $ExistingProcess = Get-Process -Id $ExistingListener[0].OwningProcess -ErrorAction SilentlyContinue
    if ($ExistingProcess) {
        Write-Host "Port $Port is already in use by $($ExistingProcess.ProcessName) (PID $($ExistingProcess.Id))." -ForegroundColor Yellow
        Write-Host "Open $Url if this is the FinSight server." -ForegroundColor Yellow
        Start-Process $Url
        exit 0
    }
}

Write-Host "Starting FastAPI backend and browser frontend on $Url..." -ForegroundColor Green
$Server = Start-Process `
    -FilePath $PythonPath `
    -ArgumentList "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "$Port" `
    -WorkingDirectory $ProjectRoot `
    -PassThru

$Ready = $false
for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    Start-Sleep -Seconds 1
    try {
        $Health = Invoke-WebRequest -Uri "$Url/health" -UseBasicParsing -TimeoutSec 2
        if ($Health.StatusCode -eq 200) {
            $Ready = $true
            break
        }
    }
    catch {
        if ($Server.HasExited) {
            throw "The FastAPI server stopped during startup."
        }
    }
}

if (-not $Ready) {
    if (-not $Server.HasExited) {
        Stop-Process -Id $Server.Id
    }
    throw "The FastAPI server did not become ready within 30 seconds."
}

Write-Host "FinSight AI is ready at $Url" -ForegroundColor Green
Start-Process $Url
Write-Host "Press Ctrl+C to stop this launcher. The server process will remain available until stopped." -ForegroundColor DarkGray

try {
    Wait-Process -Id $Server.Id
}
catch {
    # The server may be stopped externally while the launcher is open.
}
