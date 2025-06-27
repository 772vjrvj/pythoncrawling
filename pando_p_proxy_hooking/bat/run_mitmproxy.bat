@echo off
title mitmproxy 후킹 실행기

netsh winhttp set proxy 127.0.0.1:8080

rem 현재 bat 위치는 src/bat 이므로 src/server 로 상대경로 지정
mitmdump -s ..\server\proxy_server.py

pause