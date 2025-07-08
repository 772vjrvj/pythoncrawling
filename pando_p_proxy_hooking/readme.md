■ 매장정보

    ceo 정보
    id:fogjin94
    pw:cns0753!

    매장 아이디 : 6823189ccaf95dcb25d42273
    매장 : 골프존파크 죽전골프앤
    경영주id : bancj1
    비번 : qwer1234

    매장 아이디 : 68636f9e1b554bb5c193ad06
    매장 : 당산 골프존파크
    경영주id : fogjin94
    비번 : cns0753!

    운영 매장 아이디
    ● 매장 아이디 : 6768ee8213b5aa99057cdec1
    ● 매장명 : 시흥 대야소래산점 3층
    ● 지점 : 골프존파크_투비전NX


    운영 매장 아이디
    ● 매장 아이디 : 66bc390a667cb9fc7e12481f
    ● 매장명 : 평택 용이 쪽스크린
    ● 지점 : 골프존파크_투비전NX



■ 2025-06-24
    안녕하세요.
    매장 운영하면서 확인된 이슈가 있는데요.
    PandoK에서 띄운 브라우저를 닫은 다음에 ,
    PandoK에서 [시작]버튼만을 눌러 브라우저를 띄운 후에는 예약이 수집되지 않는 현상이 있습니다.
    예약정보 파싱 부분 점검시 가능하시면 같이 점검해봐주시면 좋겠습니다.
    쉽지 않다면, 파싱 부분 먼저 부탁 드리겠습니다.
    --> 파싱 부분 수정

    1.로그인 후>크롬만 닫음>시작 눌러 크롬 실행되면 예약>예약 수집안됨
    2.1번 이후 크롬을 다시 닫으면 아래와같은 팝업 발생
    --> 프로세스 강제 종료
    -- 0.9.4 ver
    
    https://docs.google.com/spreadsheets/d/1ll0t1y2RmXiCY_pfXszL6gv8D8KQFQSRrcWISwkjB9c/edit?gid=0#gid=0
    
    502에러
    www.passuneb.com
    www.ceo.dev.anytimegolf24.com


■ 2025-07-08
    3. 모바일 : 선결제 금액 그대로 표기해야된다. - 모바일 결재금액 매핑안되는 이슈
    4. 모바일 : 예약변경이 이루어지면 안된다. - 1. 모바일예약 -> 2. 모바일예약 변경창만 띄워둠 (변경은 안한상태) -> 3. 모바일취소 -> 4. 2에서 띄워둔 변경창으로 변경 
    3,4 수정 완료


✅ HTTP/2 끄기
bash
mitmdump --no-http2 -s proxy_server.py
일부 서버는 HTTP/2가 아닌 경우에만 정상 동작합니다.

mitmproxy는 HTTP/2를 100% 완벽하게 지원하지 않음
- .\mitmdump.exe -s src/server/proxy_server.py > logs\stdout.log 2> logs\stderr.log
+ .\mitmdump.
+ exe --no-http2 --ssl-insecure -s src/server/proxy_server.py > logs\stdout.log 2> logs\stderr.log



✅ 빌드
pyinstaller main.py `
  --onefile `
  --name main `
  --uac-admin `
  --noconfirm `
  --distpath dist `
  --workpath build `
  --paths . `
  --windowed 콘솔창 없이(선택사항)
