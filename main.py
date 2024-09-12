import requests
from bs4 import BeautifulSoup

def create_payload(entpName, itemNoFullname, query2, pageNum, nowPageNum):
    """POST 요청에 사용할 페이로드를 생성하는 함수"""
    return {
        'chkList': '1',
        'toggleBtnState': '',
        'nowPageNum': nowPageNum,  # nowPageNum 설정
        'tabGubun': '1',
        'tcsbizRsmptSeCdNm': '',
        'indtyCdNm': '',
        'itemStateNm': '',
        'mnftrNtnCdNm': '',
        'query2': query2,  # 사용자 입력 명칭
        'udidiCode': '',
        'grade': '0',
        'itemState': '',
        'itemNoFullname': itemNoFullname,  # 사용자 입력 품목허가번호
        'entpName': entpName,  # 사용자 입력 업체명
        'indtyCd': '1|2|21|22',
        'tcsbizRsmptSeCd': '',
        'mdentpPrmno': '',
        'mnfacrNm': '',
        'typeName': '',
        'brandName': '',
        'itemName': '',
        'query': '',
        'rcprslryCdInptvl': '',
        'mdClsfNo': '',
        'prdlPrmDtFrom': '',
        'prdlPrmDtTo': '',
        'validDateFrom': '',
        'validDateTo': '',
        'rcprslryTrgtYn': '',
        'traceManageTargetYn': '',
        'xprtppYn': '',
        'hmnbdTspnttyMdYn': '',
        'chkGroup': 'GROUP_BY_FIELD_01',
        'pageNum': pageNum,  # pageNum 설정
        'searchYn': 'true',
        'searchAfKey': '',
        'sort': '',
        'sortOrder': '',
        'searchOn': 'Y',
        'ean13': '',
        'searchUdiCode': ''
    }

def create_headers():
    """요청에 사용할 헤더 생성 함수"""
    return {
        'accept': 'text/html, */*; q=0.01',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'connection': 'keep-alive',
        'host': 'emedi.mfds.go.kr',
        'referer': 'https://emedi.mfds.go.kr/search/data/MNU20237',
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

def parse_table(soup):
    """HTML의 tr 태그에서 데이터를 추출하는 함수"""
    result_list = []
    for i in range(10):
        tr = soup.find('tr', id=f'itemTr_{i}')
        if tr:
            tds = tr.find_all('td')
            if len(tds) >= 7:
                item = {
                    '순번': tds[0].get_text(strip=True),
                    '업체명': tds[1].get_text(strip=True),
                    '품목명': tds[2].get_text(strip=True),
                    '품목허가번호': tds[3].get_text(strip=True),
                    '품목등급': tds[4].get_text(strip=True),
                    '품목상태': tds[5].get_text(strip=True),
                    '취소/취하일시': tds[6].get_text(strip=True)
                }
                result_list.append(item)
    return result_list

def scrape_data(entpName, itemNoFullname, query2):
    """페이징 처리 및 데이터를 크롤링하는 함수"""
    pageNum = 1
    nowPageNum = 1

    # 헤더 생성
    headers = create_headers()

    while True:
        # 페이로드 생성
        payload = create_payload(entpName, itemNoFullname, query2, pageNum, nowPageNum)
        url = "https://emedi.mfds.go.kr/search/data/list"

        # POST 요청 (헤더 추가)
        response = requests.post(url, data=payload, headers=headers)

        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # tr 태그 데이터 파싱
        result_list = parse_table(soup)

        # 결과 출력
        for item in result_list:
            print(item)

        # 페이지 넘버와 nowPageNum 증가
        pageNum += 1
        nowPageNum = (pageNum - 1) * 10

        print(f"pageNum : {pageNum}")
        print(f"nowPageNum : {nowPageNum}")

        # 데이터가 없거나 10개 미만이면 마지막 페이지로 간주하고 종료
        if not result_list or len(result_list) < 10:
            print(f"페이징 완료: pageNum {pageNum - 1}")
            break

def main():
    """메인 함수"""
    entpName = ""
    itemNoFullname = ""
    query2 = "팁"

    scrape_data(entpName, itemNoFullname, query2)  # 데이터 스크래핑

if __name__ == "__main__":
    main()
