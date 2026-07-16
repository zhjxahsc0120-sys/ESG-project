@echo off
chcp 65001 >nul
echo ========================================
echo   罗宜高速 ESG 领导层看板
echo   本地预览启动器
echo ========================================
echo.
cd /d "%~dp0dist"
echo 正在启动本地服务器...
echo 启动后请在浏览器中打开: http://localhost:8080
echo 按 Ctrl+C 可停止服务器
echo.
where python >nul 2>&1
if %errorlevel%==0 (
    echo 使用 Python 启动服务器...
    start "" "http://localhost:8080"
    python -m http.server 8080
    goto :eof
)
where npx >nul 2>&1
if %errorlevel%==0 (
    echo 使用 Node.js 启动服务器...
    start "" "http://localhost:8080"
    npx --yes serve -l 8080 .
    goto :eof
)
echo.
echo [错误] 未检测到 Python 或 Node.js，请安装其中之一后重试。
echo 下载地址:
echo   Python: https://www.python.org/downloads/
echo   Node.js: https://nodejs.org/
echo.
pause
