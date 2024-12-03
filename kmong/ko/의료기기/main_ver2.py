from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json  # 추가 필요


app = Flask(__name__)

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
        return int(count)
    except AttributeError:
        return 0
    except Exception as e:
        print(f"Error getting total count: {e}")
        return 0


def fetch_data(payload):
    """GET 요청을 보내고 HTML을 파싱하는 함수"""
    url = "https://emedi.mfds.go.kr/search/data/list"
    try:
        response = requests.get(url, params=payload)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

@app.route('/api/data', methods=['POST'])
def get_data():
    """엑셀에서 전송된 파라미터를 받아서 처리하는 엔드포인트"""
    # POST로 받은 데이터를 처리
    query2 = request.form.get('query2')
    item_no_fullname = request.form.get('item_no_fullname')
    entp_Name = request.form.get('entp_Name')
    page_num = request.form.get('page_num')
    now_page_num = request.form.get('now_page_num')

    print(f"query2: {query2}")
    print(f"item_no_fullname: {item_no_fullname}")
    print(f"entp_Name: {entp_Name}")
    print(f"page_num: {page_num}")
    print(f"now_page_num: {now_page_num}")

    payload = {
        'chkList': '1',
        'toggleBtnState': '',
        'nowPageNum': str(now_page_num),
        'tabGubun': '1',
        'query2': query2,
        'itemNoFullname': item_no_fullname,
        'entpName': entp_Name,
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
    soup = fetch_data(payload)
    if soup:
        result_list = parse_table(soup)
        result_total = total_cnt(soup)
        # 예쁘게 출력할 파이썬 딕셔너리 데이터를 출력
        result = {"result_list": result_list, "result_total": result_total}
        print(json.dumps(result, indent=4, ensure_ascii=False))  # JSON 형식으로 예쁘게 출력

        # Flask의 Response로 반환
        return jsonify(result), 200
    else:
        return jsonify({'error': '데이터 수집에 실패했습니다.'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # 포트를 8080으로 변경
    # app.run(host="0.0.0.0", port=8080, debug=True)  # 포트를 8080으로 변경

