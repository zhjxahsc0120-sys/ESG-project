@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
title 罗宜高速 ESG 一键启动

echo ========================================
echo   罗宜高速 ESG 数字化管理平台
echo   一键启动：后端 API + 前端页面 + GIS
echo ========================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\start-luoyi-esg.ps1"

echo.
echo 如窗口中提示启动完成，请访问：
echo   http://localhost:5173/#/
echo.
pause
