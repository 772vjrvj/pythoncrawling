@echo off
title mitmproxy 인증서 설치기

set script_dir=%~dp0
echo [정보] 현재 실행 경로: %script_dir%

if exist "%script_dir%cert\mitmproxy-ca-cert.cer" (
    echo ✅ 인증서 파일 확인됨
) else (
    echo ❌ 인증서 파일을 찾을 수 없습니다!
    pause
    exit /b
)

certutil -addstore -f "Root" "%script_dir%cert\mitmproxy-ca-cert.cer"
echo [✔] 인증서 설치 완료
pause
