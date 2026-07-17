$ErrorActionPreference = "SilentlyContinue"

$ServerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $ServerDir "server.pid"

$Stopped = $false

if (Test-Path $PidFile) {
  $PidValue = Get-Content $PidFile | Select-Object -First 1
  if ($PidValue) {
    $Process = Get-Process -Id ([int]$PidValue) -ErrorAction SilentlyContinue
    if ($Process) {
      Stop-Process -Id ([int]$PidValue) -Force
      Write-Host "Luoyi ESG API stopped by pid file. PID=$PidValue"
      $Stopped = $true
    }
  }
  Remove-Item $PidFile -Force
}

$Connections = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
foreach ($Connection in $Connections) {
  $PortPid = [int]$Connection.OwningProcess
  if ($PortPid -gt 0) {
    $Process = Get-Process -Id $PortPid -ErrorAction SilentlyContinue
    if ($Process) {
      Stop-Process -Id $PortPid -Force
      Write-Host "Luoyi ESG API stopped by port 8765. PID=$PortPid"
      $Stopped = $true
    }
  }
}

if (-not $Stopped) {
  Write-Host "No Luoyi ESG API process found."
}
