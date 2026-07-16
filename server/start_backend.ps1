$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = "C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$ServerDir = Join-Path $Root "server"
$PidFile = Join-Path $ServerDir "server.pid"
$LogFile = Join-Path $ServerDir "server.log"
$ErrFile = Join-Path $ServerDir "server.err.log"

if (-not (Test-Path $Python)) {
  $Python = "python"
}

if (Test-Path $PidFile) {
  $OldPid = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($OldPid) {
    $Running = Get-Process -Id ([int]$OldPid) -ErrorAction SilentlyContinue
    if ($Running) {
      Write-Host "Luoyi ESG API already running. PID=$OldPid"
      Write-Host "Health: http://127.0.0.1:8765/health"
      exit 0
    }
  }
}

& $Python (Join-Path $ServerDir "init_db.py")

$Proc = Start-Process `
  -FilePath $Python `
  -ArgumentList "server\app.py" `
  -WorkingDirectory $Root `
  -RedirectStandardOutput $LogFile `
  -RedirectStandardError $ErrFile `
  -PassThru `
  -WindowStyle Hidden

$Proc.Id | Set-Content -Path $PidFile -Encoding ASCII
Start-Sleep -Seconds 1

try {
  $Health = Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing -TimeoutSec 5
  Write-Host "Luoyi ESG API started. PID=$($Proc.Id)"
  Write-Host $Health.Content
} catch {
  Write-Host "Backend process started but health check failed. PID=$($Proc.Id)"
  Write-Host "Check logs:"
  Write-Host $LogFile
  Write-Host $ErrFile
  exit 1
}
