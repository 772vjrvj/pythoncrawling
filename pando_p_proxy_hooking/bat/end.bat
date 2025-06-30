@echo off
:: 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔐 관리자 권한으로 재실행 중...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

title 🔪 mitmdump 강제 종료

echo 🛑 mitmdump 프로세스를 강제 종료합니다...

:: 프로세스 및 자식 프로세스 강제 종료
taskkill /F /IM mitmdump.exe /T

echo ✅ 종료 완료!
pause
