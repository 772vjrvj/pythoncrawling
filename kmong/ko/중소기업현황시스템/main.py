import requests
from bs4 import BeautifulSoup

def make_request():
    # URL 및 Payload 설정
    url = "https://sminfo.mss.go.kr/si/ei/IEI001R0.do?cmd=com&kcd=0007189422"
    payload = {
        "detailYn": "Y",
        "cmMenuId": "421010100",
        "returnCmMenuId": "",
        "searchUrl": "/gc/sf/GSF002R0.print",
        "returnUrl": "",
        "cmQueryEncoding": "",
        "sidoNmEncoding": "",
        "gugunNmEncoding": "",
        "dongNmEncoding": "",
        "ksic11BzcCdNmEncoding": "",
        "pdNmEncoding": "",
        "clickcontrol": "disable",
        "iInd_cd": "",
        "chkindex": "",
        "iGB": "1",
        "locSrchCd": "0",
        "sidoCd": "",
        "gugunCd": "",
        "dongCd": "",
        "sidoNm": "",
        "gugunNm": "",
        "dongNm": "",
        "estbDt": "",
        "enpTypCoYn": "",
        "enpTypIndvYn": "",
        "enpScdNormalYn": "Y",
        "enpScdCloseYn": "",
        "enpScdQuitYn": "",
        "vetureCd": "",
        "vetureCd02": "",
        "enobiz": "",
        "newCom": "",
        "licenseSeq": "",
        "iqFlag": "S",
        "gubun": "",
        "cmQueryOption": "08",
        "cmTotalRowCount": "",
        "cmPageNo": "1",
        "cmSortField": "",
        "cmSortOption": "0",
        "tITLESortOption": "2",
        "bZNOSortOption": "2",
        "nAMESortOption": "2",
        "kedcd": "0007532321",
        "mode": "",
        "htmlvalue": "<dl class='selected_group'><dt>업종명</dt><dd>가방 및 기타 보호용 케이스 제조업</dd></dl>",
        "cmQueryOptionCombo": "00",
        "cmQuery": "",
        "ksic11BzcCdNm": "가방 및 기타 보호용 케이스 제조업",
        "ksic11BzcCd": "C15129",
        "iSido": "",
        "iGugun": "",
        "iDong": "",
        "ipoCd": "",
        "enpFcd": "",
        "userOk": "",
        "pdNm": "",
        "hpageUrl": "",
        "estbDtCd": ""
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "connection": "keep-alive",
        "content-length": "1121",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": "SCOUTER=z3942kb362sv52; acopendivids=nada; acgroupswithpersist=nada; JSESSIONID=HjgPcq67O3nzV4WzxS5tlrrTFwe6ZqdAOZ21jEkFWv2PaeXvvR4SWeyRgcpvWLLB.amV1c19kb21haW4vcG9ydGFsNA==",
        "host": "sminfo.mss.go.kr",
        "origin": "https://sminfo.mss.go.kr",
        "referer": "https://sminfo.mss.go.kr/gc/sf/GSF002R0.print",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    # POST 요청 보내기
    response = requests.post(url, data=payload, headers=headers)
    return response.text

def parse_html(html_content):
    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(html_content, 'html.parser')

    # 원하는 테이블 찾기
    table = soup.find('table', class_='col_table col_table_mob')
    if table:
        # tbody 안에서 th 요소만 추출하여 출력
        th_elements = table.find('tbody').find_all('td')
        for th in th_elements:
            print(th.text.strip())

def main():
    # 요청 보내고 HTML 가져오기
    html_content = make_request()

    # HTML 내용 파싱하여 th 요소 출력
    parse_html(html_content)

if __name__ == "__main__":
    main()
