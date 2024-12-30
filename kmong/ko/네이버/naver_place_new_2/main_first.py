import requests
from bs4 import BeautifulSoup
import json
import re
import urllib.parse

# 요청 URL
url = "https://pcmap.place.naver.com/place/list"

keyword = '강남 네일'

# 요청 파라미터 설정
params = {
    "query": keyword,  # 한글 인코딩
    "display": "100",
    "locale": "ko",
}

# 요청 헤더 설정
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'cookie': 'NNB=2HHDT25LLBYWO; SRT30=1735481515; NAC=qpjLBcAU3Vpv; NACT=1; nid_inf=192615909; NID_AUT=6aZ2xXToKW+4coczi2XBP47AbmOvpRo1TYrhdD1eZdFgUFp9uIVMXsrWNyDANqza; NID_SES=AAABt7MMvdvWfUwXfVG52fWOs+NBhHADovpbfNY44kCEkNJKpOpWc8puWrLADDfTxewq1UeqOLgYXnoeTISkGn2nG8h+LKISprrkT/j22rBHHM53C04SGqZKtd2NfDUJKM36wnSEbQ0FZG34ellRJueYDQT5ZszX8+PnIpnJ5GBJnt+D2E25oQrrw7CwmLwMuoNXcI6spYcoPCHiB1kGxxJOD2CcZLEYZG2Dpr3dokBSqYJiwMjTcudZBElX+ECJFV2fZlmXZ/FlU7/rmyhtnYNg/u0l2joHz7Aa90ISi2/Q3YGd9VUcRuvJCOAMrU8J1WvglMRVyBylF60PUNQiU+i9Pd+ec28snwlcylgDcmwTz9Ia0KZZS7t+EWAqg9iCZNGZKEh1h+p0Fdn2d0UqzPAGGrusrqWQqJfNCA/Ex+qrIbVFc6LyqLt3HwQx3yIam90KYO46CLXI/KaciPmeO9P00gzU/mvbBiaofR7lJDXYk00d6GSlpKjbrd5jxGwZaNrIQ2XWeY/pFkNUcI2JE76jRBzMNjMGMDhex+B9mwnl6h5pYhBLnzRc/hpzpMRuif7+Qauh3gF9qmGUUnbEtsGyZsw=; NID_JKL=hRzYPOifPeJNbgLh090MsDWzFvCVdKscficTVEhs7D4=; SRT5=1735483799; BUC=NiI6vYpoP9KO_Wzms62Z8B46pdwzSUtKT4exGmV6hQs=',
    'referer': f'https://map.naver.com/p/search',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}

# GET 요청 보내기
try:
    response = requests.get(url, headers=headers, params=params)
    response.encoding = 'utf-8'  # 응답을 UTF-8로 처리
    response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킴
    # 응답 처리
    soup = BeautifulSoup(response.text, 'html.parser')

    # 모든 <script> 태그 찾기
    script_tags = soup.find_all('script')

    # window.__APOLLO_STATE__ 객체를 찾고 키들을 출력하기
    for script in script_tags:
        # script.string이 None이 아닐 때만 정규식을 실행
        if script.string:
            # window.__APOLLO_STATE__ 객체를 찾기 위한 정규식 (키에 ':' 포함 가능)
            match = re.search(r'window\.__APOLLO_STATE__ = ({.*?});', script.string, re.DOTALL)
            if match:
                apollo_state = match.group(1)  # 객체 부분만 추출
                try:
                    # JSON 형태로 파싱
                    apollo_state_obj = json.loads(apollo_state)

                    # 객체의 모든 키를 출력 (BeautySummary:1941401558와 같은 키도 처리 가능)
                    a = 0
                    for key in apollo_state_obj.keys():
                        if 'Summary' in key and 'AdSummary' not in key:
                            # 한글이 깨지지 않도록 출력
                            print(f"Key: {key}, Value: {apollo_state_obj[key]}")
                            a += 1
                    print(a)

                except json.JSONDecodeError:
                    print("JSON 파싱 오류 발생")
except requests.exceptions.RequestException as e:
    print(f"요청 오류: {e}")
