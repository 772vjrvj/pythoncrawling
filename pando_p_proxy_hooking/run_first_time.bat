@echo off
title 🔐 mitmproxy 인증서 등록 (최초 1회 실행용)

:: 🔐 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔐 관리자 권한으로 재실행 중...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

:: 📁 경로 이동 및 콘솔 설정
cd /d "%~dp0"
chcp 65001 >nul

:: 🔍 mitmdump.exe 존재 확인
if not exist mitmdump.exe (
    echo ❌ mitmdump.exe가 현재 경로에 없습니다!
    pause
    exit /b
)

:: 🧹 기존 인증서 제거
echo 🧹 기존 mitmproxy 루트 인증서 제거
certutil -delstore "Root" "mitmproxy" >nul 2>&1

echo 🧨 .mitmproxy 폴더 삭제
rd /s /q "%USERPROFILE%\.mitmproxy" >nul 2>&1

:: ⚙️ 인증서 생성용 mitmdump 실행 (백그라운드 실행 후 잠시 대기)
echo ⚙️ mitmdump 실행하여 인증서 생성...
start "" mitmdump.exe --listen-port 9999 --no-http2 --ssl-insecure --set console_eventlog_verbosity=error

:: ⏳ 인증서 생성 대기
timeout /t 3 /nobreak >nul

:: 🔪 mitmdump 강제 종료
taskkill /F /IM mitmdump.exe /T >nul 2>&1

:: 🔐 루트 인증서 등록
echo 🔐 루트 인증서 등록 중...
certutil -addstore "Root" "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer"
if errorlevel 1 (
    echo ❌ 등록 실패: 관리자 권한 확인 필요!
    pause
    exit /b
)

echo ✅ 인증서 등록 완료! 이제 프로그램을 실행하셔도 됩니다.
pause
