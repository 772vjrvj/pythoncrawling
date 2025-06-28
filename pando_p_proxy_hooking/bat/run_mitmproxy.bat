@echo off
chcp 65001 >nul
title mitmproxy 후킹 실행기

:: 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 관리자 권한으로 재실행 중...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

:: 현재 bat 경로로 이동
cd /d "%~dp0"

:: 로그 폴더 없으면 생성
if not exist logs (
    mkdir logs
)

:: 환경 변수 설정
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

:: 프록시 설정
netsh winhttp set proxy 127.0.0.1:8080

:: mitmdump 실행
.\mitmdump.exe -s src\server\proxy_server.py
