import requests
from bs4 import BeautifulSoup
import json
import re

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
    'cookie': 'NNB=2HHDT25LLBYWO; NAC=qpjLBcAU3Vpv; NACT=1; nid_inf=190225495; NID_AUT=6CoPRSVhcz6OajU0mURj/aea82NyBXmRHaDxEX+lNnHjHwfVzA7waGw3ufKAWTCl; NID_JKL=6Ulm4aqG+Y0oe7KfukzXZ/F/CFu4FG1ZuuA2T2D41m8=; 066c80626d06ffa5b32035f35cabe88d=%AD3%23%88%FC%DB%3Ey%FFx%A0j%AA%14f%0CT%E4%B9C%E9i%E963%3F%B4%21%E3%BD%3C%0D%FCFc9n%2A%D6%9B0%3A.%DE%D9%1E1%CF%82%5E%A0%D2R%D8%13%03%D4%09%12tp%D7%F5%F9%23w%B8qq%91l%80%21%F6d%9F%2A%8D%3A%9Bd%02%BF%17%0B4%A1%2F%27%21%C4%8B%3B%D2KV%E8dL%CD%F42%A8%7B%8C%1A4%05XA%E1%E2%C8Yq%0AN-T%B7%C6%F3%90%18H%DD0%FBUin%EC%16%91%B6%0BY%B0%3D%E8%03%A2%8E%B8; 1a5b69166387515780349607c54875af=k%7Dh%BA%12%80%81%D2; NID_SES=AAABqyXIIhTcBfIGtqKDJG4Y2kymVo3FRCDaawzuccnpnwekwUG9m6y8q7MrzFySkp2zSM2diNdjPzuS7AtgfUb2iuDVKC6hNA3l1ghgVV6qY9AryovCEnVXmIavehotsW9CwV14ThRB9xcDYlQ2srdoNPHm8tTurL65YOCLbaTst5Fxg7cCbXxcGHI8eAxePzz2QWkCO6XUbL6CrQkFHUoQld/e02hJwGZH29IxK9INjFKy3xJWFJlxz4qimo3AlwWVnOU6g9UuYoz4gKlqMZYd3uhjq3suJH1m+mDBFpKl76z6lUQz5bLv7qJsZ84u3+ogZWpjuvOhY08zUDl9Nf1wBXR2rJc3gZ88+uMDH1IsrLZ41OM2ncBXcYSyUy77Aeb6EEFXunTg/gcO4qvHIUu68F2cCnXnLO27p8jXwCAj0KPffaGan5jBK2kxt9ml+AKqCk/0Am4LwVzS2JCg0Q3KACGz3LyhZVWrlc+E59zzoYX74BN2uT2e21qAIdOvVAJUJqBEKGBMZq8bf20fNkp75CVyCuO2XMjFCJuOOUVa/5HpcupnbSR4yWHv+u4yaN4mcA==; SRT30=1735663507; SRT5=1735663507; BUC=cP-IC5g6uFQELg2csds4X4LOM4miB1fPiQXgp6eRitk=',
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
                            # print(f"Key: {key}, Value: {apollo_state_obj[key]}")

                            print(f'id : {apollo_state_obj[key]['id']}')
                            print(f'blogCafeReviewCount : {apollo_state_obj[key]['blogCafeReviewCount']}')
                            print(f'visitorReviewCount : {apollo_state_obj[key]['visitorReviewCount']}')
                            a += 1
                    print(a)

                except json.JSONDecodeError:
                    print("JSON 파싱 오류 발생")
except requests.exceptions.RequestException as e:
    print(f"요청 오류: {e}")
