$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BackendUrl = "http://127.0.0.1:8765"
$FrontendUrl = "http://localhost:5173/#/"
$GisPreviewUrl = "http://localhost:5173/#/gis-preview"
$GaodeTileUrl = "https://webst01.is.autonavi.com/appmaptile?style=6&x=205&y=110&z=8"

function Write-Step($Text) {
  Write-Host ""
  Write-Host "==> $Text" -ForegroundColor Cyan
}

function Test-TcpPort($HostName, $Port) {
  try {
    $Client = [System.Net.Sockets.TcpClient]::new()
    $Async = $Client.BeginConnect($HostName, $Port, $null, $null)
    $Ok = $Async.AsyncWaitHandle.WaitOne(800)
    if (-not $Ok) {
      $Client.Close()
      return $false
    }
    $Client.EndConnect($Async)
    $Client.Close()
    return $true
  } catch {
    return $false
  }
}

function Test-HttpOk($Url, $TimeoutSec = 3) {
  try {
    $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
    return [int]$Response.StatusCode -ge 200 -and [int]$Response.StatusCode -lt 400
  } catch {
    return $false
  }
}

Set-Location $Root

Write-Host "项目目录：$Root"

Write-Step "检查 MySQL 端口 3307"
if (Test-TcpPort "127.0.0.1" 3307) {
  Write-Host "MySQL 端口 3307 可连接。" -ForegroundColor Green
} else {
  Write-Host "未检测到 MySQL 3307。后端可能无法读取数据库。" -ForegroundColor Yellow
  Write-Host "如首页/GIS 无数据，请先启动 MySQL，再重新运行本脚本。" -ForegroundColor Yellow
}

Write-Step "启动后端 API"
if (Test-HttpOk "$BackendUrl/health") {
  Write-Host "后端 API 已在运行：$BackendUrl" -ForegroundColor Green
} else {
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "server\start_backend.ps1")
  Start-Sleep -Seconds 2
}

if (Test-HttpOk "$BackendUrl/health") {
  Write-Host "后端 API 启动成功：$BackendUrl" -ForegroundColor Green
} else {
  Write-Host "后端 API 健康检查失败，请查看 server\server.log 和 server\server.err.log。" -ForegroundColor Red
}

Write-Step "检查 GIS API"
if (Test-HttpOk "$BackendUrl/api/esg/gis/layers") {
  Write-Host "GIS 图层接口正常：$BackendUrl/api/esg/gis/layers" -ForegroundColor Green
} else {
  Write-Host "GIS 图层接口暂不可用。请确认后端和数据库状态。" -ForegroundColor Yellow
}

Write-Step "检查在线卫星底图瓦片"
if (Test-HttpOk $GaodeTileUrl 8) {
  Write-Host "高德卫星瓦片可访问。" -ForegroundColor Green
} else {
  Write-Host "高德卫星瓦片访问失败。GIS 可能只能显示底色或业务线位。" -ForegroundColor Yellow
}

Write-Step "启动前端 Vite"
if (Test-TcpPort "127.0.0.1" 5173) {
  Write-Host "前端 5173 端口已在运行：$FrontendUrl" -ForegroundColor Green
} else {
  $Command = "Set-Location '$Root'; npm.cmd run dev -- --host 127.0.0.1 --port 5173"
  Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $Command `
    -WorkingDirectory $Root `
    -WindowStyle Minimized
  Write-Host "已启动前端 Vite 窗口，等待端口 5173 就绪..." -ForegroundColor Green

  for ($i = 0; $i -lt 20; $i++) {
    if (Test-TcpPort "127.0.0.1" 5173) { break }
    Start-Sleep -Seconds 1
  }
}

Write-Step "打开浏览器"
Start-Process $FrontendUrl

Write-Host ""
Write-Host "启动完成。" -ForegroundColor Green
Write-Host "领导首页：$FrontendUrl"
Write-Host "GIS 预览：$GisPreviewUrl"
Write-Host "数据工作台：http://localhost:5173/#/workspace"
Write-Host ""
Write-Host "如果 GIS 不显示，请按 Ctrl+F5 强制刷新页面。" -ForegroundColor Yellow
