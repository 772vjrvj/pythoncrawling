@echo off
title Windows 프록시 초기화
echo [🔄] Windows 프록시 설정 초기화 중...
netsh winhttp reset proxy
echo [✔] 프록시가 기본값으로 초기화되었습니다.
pause
