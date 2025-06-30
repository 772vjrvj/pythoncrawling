@echo off
title mitmproxy 재시작 + 캐시 초기화

REM 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo 🔫 mitmdump 종료 중...
taskkill /F /IM mitmdump.exe /T

echo 🧹 __pycache__ 정리 중...
for /r %%i in (.) do (
    if exist "%%i\__pycache__" (
        rd /s /q "%%i\__pycache__"
    )
)

if not exist logs (
    mkdir logs
)

echo 🚀 mitmdump 실행
.\mitmdump.exe -s src/server/proxy_server.py > logs\stdout.log 2> logs\stderr.log
