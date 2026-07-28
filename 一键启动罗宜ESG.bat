@echo off
set "ROOT=%~dp0"
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
title Luoyi ESG One Click Start

echo ========================================
echo   Luoyi ESG Platform
echo   Start backend API + frontend + GIS
echo ========================================
echo.

"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\start-luoyi-esg.ps1"

echo.
echo If startup is complete, open:
echo   http://localhost:5173/#/
echo.
pause
