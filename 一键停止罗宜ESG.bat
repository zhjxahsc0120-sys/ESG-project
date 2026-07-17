@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
title 罗宜高速 ESG 一键停止

echo ========================================
echo   罗宜高速 ESG 数字化管理平台
echo   一键停止：后端 API
echo ========================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%server\stop_backend.ps1"

echo.
echo 前端 Vite 窗口如仍在运行，请在对应窗口按 Ctrl+C 关闭。
echo.
pause
