@echo off
title mitmproxy 재시작 + 캐시 초기화

REM 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

REM 현재 경로로 이동
cd /d "%~dp0"

REM UTF-8 환경 설정
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM 기존 mitmdump 프로세스 종료
taskkill /IM mitmdump.exe /F >nul 2>&1

REM __pycache__ 강제 삭제 (전체 하위 경로 포함)
for /r %%i in (.) do (
    if exist "%%i\__pycache__" (
        rd /s /q "%%i\__pycache__"
    )
)

REM 로그 디렉토리 생성
if not exist logs (
    mkdir logs
)

REM 프록시 서버 실행
.\mitmdump.exe -s test_server.py > logs\stdout.log 2> logs\stderr.log
