# -*- coding: utf-8 -*-
import requests

def main():
    """
    KIPRIS /kpat/resulta.do JSON 요청 (POST)
    """
    url = "https://www.kipris.or.kr/kpat/resulta.do"

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "cookie": (
            "JSESSIONID=MOw4bqzTtHo3I6rA3z5UIZHbsx1MEUN8fxh4KRaUVLlZOPkwlp9yFdZ13UEiD1bi.amV1c19kb21haW4va3BhdDE=; "
            "_ga=GA1.1.1858042139.1761006044; "
            "_ga_6RVR9V6306=GS2.1.s1761216402$o7$g1$t1761216823$j60$l0$h0; "
            "_ga_XYF3QRKKDC=GS2.1.s1761216823$o14$g0$t1761216823$j60$l0$h0; "
            "_ga_4R5CJZBQXD=GS2.1.s1761216823$o14$g0$t1761216823$j60$l0$h0"
        ),
        "origin": "https://www.kipris.or.kr",
        "referer": "https://www.kipris.or.kr/khome/search/searchResult.do",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36"
        ),
        "x-requested-with": "XMLHttpRequest",
    }

    # === 신규 === 검색 파라미터
    payload = {
        "queryText": "AN=[2002]*IPC=[G06F]*AP=[삼성전자주식회사]*TRH=[삼성전자주식회사]",
        "expression": "AN=[2002]*IPC=[G06F]*AP=[삼성전자주식회사]*TRH=[삼성전자주식회사]",
        "historyQuery": "AN=[2002]*IPC=[G06F]*AP=[삼성전자주식회사]*TRH=[삼성전자주식회사]",
        "numPerPage": "90",
        "numPageLinks": "10",
        "currentPage": "5",
        "piSearchYN": "N",
        "beforeExpression": "",
        "prefixExpression": "",
        "downYn": "N",
        "downStart": "",
        "downEnd": "",
        "viewField": "",
        "fileType": "",
        "inclDraw": "",
        "inclJudg": "",
        "inclReg": "",
        "inclAdmin": "",
        "sortField": "RANK",
        "sortState": "Desc",
        "viewMode": "",
        "searchInTrans": "N",
        "pageLanguage": "",
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        print(response.text)  # JSON 문자열 그대로 출력
    except Exception as e:
        print(f"[ERROR] 요청 실패: {str(e)}")

if __name__ == "__main__":
    main()
