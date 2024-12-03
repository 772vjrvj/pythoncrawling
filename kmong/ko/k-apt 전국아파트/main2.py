import requests
from bs4 import BeautifulSoup

def first_post_request():
    url = 'http://www.k-apt.go.kr/kaptinfo/openkaptinfo.do'
    payload = {
        'go_url': '/kaptinfo/openkaptinfo.do',
        'bjd_code': '2817710400',
        'kapt_code': 'A10026406',
        'search_date': '202403',
        'kapt_usedate': '',
        'kapt_name': ''
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'www.k-apt.go.kr',
        'Origin': 'http://www.k-apt.go.kr',
        'Referer': 'http://www.k-apt.go.kr/cmmn/knewMapView.do',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

def second_post_request(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    print(f"soup {soup}")
    # 필요한 데이터 추출 예시 (변경 필요)
    # 추출할 데이터가 특정한 형식이라면 그에 맞게 코드를 작성하세요.
    # 예를 들어, 특정 값 추출:
    # value = soup.find('input', {'name': 'some_name'}).get('value', '')

    url = 'http://www.k-apt.go.kr/kaptinfo/openkaptinfo.do'
    payload = {
        'go_url': '/kaptinfo/openkaptinfo.do',
        'bjd_code': '2817710400',
        'kapt_code': 'A10026406',
        'search_date': '202403',
        'kapt_usedate': '',
        'kapt_name': ''
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'www.k-apt.go.kr',
        'Origin': 'http://www.k-apt.go.kr',
        'Referer': 'http://www.k-apt.go.kr/cmmn/knewMapView.do',
        'Upgrade-Insecure-Requests': '1',
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

def main():
    response_text = first_post_request()
    if response_text:
        second_post_request(response_text)

if __name__ == "__main__":
    main()
