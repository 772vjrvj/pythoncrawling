import requests
import json
from bs4 import BeautifulSoup

def fetch_data():
    # 첫 번째 요청할 URL 및 페이로드 설정
    url = 'https://www.d2b.go.kr/mainBidAnnounceList.json'
    payload = {
        'anmt_name': '실시설계',
        'mnuf_code': '',
        'date_from': '20231221',
        'date_to': '20240621',
        'search_divs': '',
        'gubun': '1',
        'anmt_divs': '',
        'numb_divs': '',
        'dprt_name': '',
        'dprt_code': '',
        'edix_gtag': '',
        'chgDate': '-6m',
        'sch_typeA': 'true',
        'sch_typeB': 'true',
        'sch_typeC': 'true',
        'sch_typeD': 'true',
        'currentPageNo': 1
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4, ensure_ascii=False))
        return data['list']
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        print(response.text)
        return []


# 사용가능
def post_data(item):
    url = 'https://www.d2b.go.kr/peb/bid/announceView.do'
    payload = {
        'dprt_code': item.get('dprtCode', ''),
        'anmt_divs': item.get('anmtDivs', ''),
        'anmt_numb': item.get('anmtNumb', ''),
        'rqst_degr': item.get('rqstDegr', ''),
        'dcsn_numb': item.get('dcsnNumb', ''),
        'rqst_year': item.get('rqstYear', ''),
        'bsic_stat': item.get('bsicStat', ''),
        'dmst_itnb': item.get('dmstItnb', ''),
        'anmt_date': item.get('anmtDate', ''),
        'csrt_numb': item.get('dcsnNumb', ''),
        'lv2Divs': item.get('lv2Divs', ''),
        'cont_mthd': item.get('contMthd', ''),
        'pageDivs': 'E1',
        'searchData': json.dumps({
            "anmt_name": "",
            "mnuf_code": "",
            "date_from": "20231221",
            "date_to": "20240621",
            "search_divs": "",
            "gubun": "1",
            "anmt_divs": "",
            "numb_divs": "",
            "dprt_name": "",
            "dprt_code": "",
            "edix_gtag": "",
            "chgDate": "-6m",
            "sch_typeA": True,
            "sch_typeB": True,
            "sch_typeC": True,
            "sch_typeD": True
        })
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        post_tit_elements = soup.find_all(class_='post_tit')
        for element in post_tit_elements:
            print(element.get_text(strip=True))
    else:
        print(f"Failed to post data: {response.status_code}")
        print(response.text)

def main():
    items = fetch_data()
    print(f"items : {items}")



    # for item in items:
    #     post_data(item)

if __name__ == "__main__":
    main()
