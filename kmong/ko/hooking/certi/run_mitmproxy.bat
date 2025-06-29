@echo off
title mitmproxy 후킹 실행기

echo [🛠️] Windows 프록시 설정 중...
netsh winhttp set proxy 127.0.0.1:8080
echo [✔] 프록시 설정 완료

echo [🚀] mitmdump 실행 중...
mitmdump -s hook.py
pause
