$projectDir = "C:\Users\TB\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a53a1b3d0f497e311ecc95f"
$releaseDir = Join-Path $projectDir "release-pack"
$eDriveDir = "E:\luoyi-esg-dashboard"
$zipName = "luoyi-esg-dashboard.zip"
$zipPath = Join-Path $eDriveDir $zipName

if (Test-Path $releaseDir) {
    Remove-Item -Recurse -Force $releaseDir
}

New-Item -ItemType Directory -Path $releaseDir | Out-Null

Copy-Item -Recurse (Join-Path $projectDir "dist") -Destination (Join-Path $releaseDir "dist")
Copy-Item (Join-Path $projectDir "启动本地服务器.bat") -Destination (Join-Path $releaseDir "双击启动.bat")

$readmeContent = @"
# 罗宜高速 ESG 领导层看板 - 本地预览说明

## 使用方法

1. 双击 `双击启动.bat`
2. 自动打开浏览器访问 http://localhost:8080
3. 看完后在命令行窗口按 Ctrl+C 停止服务器

## 为什么不能直接双击 index.html?

本项目使用 Vue 3 + Vite 构建，采用 ES Module 格式。
浏览器安全策略不允许 file:// 协议直接加载模块脚本，需要通过 HTTP 服务器访问。

## 系统要求

- Windows 10/11（自带 Python）
- 或者安装 Node.js
"@

$readmePath = Join-Path $releaseDir "README.txt"
$readmeContent | Out-File -FilePath $readmePath -Encoding UTF8

Write-Host "Release directory created: $releaseDir"

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

Compress-Archive -Path (Join-Path $releaseDir "*") -DestinationPath $zipPath -Force

Write-Host "ZIP created: $zipPath"
Write-Host "Done!"
