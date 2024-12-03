import requests
from bs4 import BeautifulSoup

def parse_table(soup):
    """HTML의 tr 태그에서 데이터를 추출하는 함수"""
    result_list = []
    try:
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
    except Exception as e:
        print(f"Error parsing table: {e}")
    return result_list

def total_cnt(soup):
    """전체 품목 수를 가져오는 함수"""
    try:
        count = soup.find('b', id='countExcel').get_text(strip=True)
        return count
    except AttributeError:
        return "0"
    except Exception as e:
        print(f"Error getting total count: {e}")
        return "0"

def fetch_data(payload):
    """GET 요청을 보내고 HTML을 파싱하는 함수"""
    url = "https://emedi.mfds.go.kr/search/data/list"

    try:
        response = requests.get(url, params=payload)
        response.raise_for_status()  # HTTP 에러가 있을 시 예외 발생
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def main(page_num, now_page_num, query2, itemNoFullname, entpName):
    """주요 실행 함수"""
    # 요청에 필요한 파라미터 설정 (payload)
    payload = {
        'chkList': '1',
        'toggleBtnState': '',
        'nowPageNum': str(now_page_num),
        'tabGubun': '1',
        'query2': query2,
        'itemNoFullname': itemNoFullname,
        'entpName': entpName,
        'indtyCd': '1|2|21|22',
        'chkGroup': 'GROUP_BY_FIELD_01',
        'pageNum': str(page_num),
        'searchOn': 'Y',
        'tcsbizRsmptSeCdNm': '',
        'indtyCdNm': '',
        'itemStateNm': '',
        'mnftrNtnCdNm': '',
        'udidiCode': '',
        'grade': '0',
        'itemState': '',
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
        'searchAfKey': '',
        'sort': '',
        'sortOrder': '',
        'ean13': '',
        'searchUdiCode': '',
        'searchYn': ''
    }


    # 데이터 가져오기
    soup = fetch_data(payload)

    if soup:
        # 테이블 데이터 파싱
        result_list = parse_table(soup)
        result_total = total_cnt(soup)

        # 결과 출력
        if result_list:
            for item in result_list:
                print(item)

        # 전체 품목 수 출력
        print(f"전체 품목 수: {result_total}")
    else:
        print("Error: 데이터 수집에 실패했습니다.")

if __name__ == "__main__":
    # 사용자 입력값
    query2 = '팁'  # 사용자 입력 명칭
    itemNoFullname = ''  # 사용자 입력 품목허가번호
    entpName = ''  # 사용자 입력 업체명

    # 페이지 정보
    page_num = 1
    now_page_num = 1

    # main 함수 실행
    main(page_num, now_page_num, query2, itemNoFullname, entpName)
