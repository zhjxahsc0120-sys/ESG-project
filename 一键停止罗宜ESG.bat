@echo off
set "ROOT=%~dp0"
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
title Luoyi ESG One Click Stop

echo ========================================
echo   Luoyi ESG Platform
echo   Stop backend API
echo ========================================
echo.

"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%ROOT%server\stop_backend.ps1"

echo.
echo If the frontend Vite window is still running, press Ctrl+C in that window.
echo.
pause
