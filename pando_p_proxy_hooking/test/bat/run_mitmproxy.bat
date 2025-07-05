@echo off
title 🛡️ mitmproxy 재시작 (인증서 초기화 포함)


:: 📁 현재 경로로 이동 및 환경 설정
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: 🧹 __pycache__ 제거
echo 🧹 __pycache__ 제거 중...
for /r %%i in (.) do (
    if exist "%%i\__pycache__" (
        rd /s /q "%%i\__pycache__"
    )
)

:: 🚀 mitmdump 프록시 서버 실행
echo 🚀 프록시 서버 실행 중...
start "" cmd /k ".\mitmdump.exe --no-http2 --ssl-insecure -s src\server\proxy_server.py"
