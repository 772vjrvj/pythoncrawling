import requests
from bs4 import BeautifulSoup

# 요청 URL
url = "https://abcmart.a-rt.com/display/search-word/result/list"

# 쿼리 파라미터 (페이로드)
payload = {
    "searchPageType": "brand",
    "channel": "10001",
    "page": "2",
    "pageColumn": "4",
    "deviceCode": "10000",
    "firstSearchYn": "Y",
    "tabGubun": "total",
    "searchPageGubun": "brsearch",
    "searchRcmdYn": "Y",
    "brandNo": "000003",
    "searchBrandNo": "000003",
    "brandPrdtArtDispYn": "Y",
    "sort": "latest",
    "perPage": "30",
    "rdoProdGridModule": "col3",
    # "_": "1736952631519"
}

# GET 요청에 사용할 헤더
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "connection": "keep-alive",
    "cookie": "_fbp=fb.1.1736697584355.75386422653127915; _gcl_au=1.1.2065324078.1736697584; _kmpid=km|a-rt.com|1736697584816|2ecedbf9-3b38-4a65-9092-c1e38cdce0c4; _ga=GA1.1.810624497.1736697585; WMONID=swq5-8thFww; _fwb=123o5m8EOPZceie5hxSQODg.1736699414936; JSESSIONID=eaaHpVSbNFN7ye3G1TjrzA44n0ZBd3Zc89idVVgKOv8yWK-NVGN_o85hlwO6; cDomain=abcmart.a-rt.com; _TBS_NAUIDA_1085=235ef9de99bfb74a00409ad4e85ceda1#1736697584#1736952484#4; _TBS_AUIDA_1085=definedvalue:4; _TBS_ASID_1085=704070624179fa7406b42e0fe1eb1db0; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22unknown%22%2C%22expiryDate%22%3A%222026-01-15T14%3A50%3A32.233Z%22%7D; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22AVjny1VROcrOxJnGlZkj%22%2C%22expiryDate%22%3A%222026-01-15T14%3A50%3A32.234Z%22%7D; _ga_1TNDXE1VZN=GS1.1.1736952484.6.1.1736952632.59.0.0; _ga_LCF0H8N8VP=GS1.1.1736952484.6.1.1736952632.0.0.0; wcs_bt=s_1a84e8fc3413:1736952632; cto_bundle=_1oWD19NJTJCJTJGRGU5R2pVT05zUlQ2SlEwNnl0VVhNJTJCOEpoZDc1d2xuMHg3OUtpQSUyQmVaV3dYcWl5ZjBuZTFWWEV3YmFTRE1vamgzMWxJQjBqcXolMkJDVXBRRlJuM1ZxSHhud251b2ZycE96eVBwdnFNSFZzVmw5eiUyQktlSVF1RHlYSmdPYjhTOFdmS1Y1ZGZZS042Q2ViJTJGWVpRTWw1dyUzRCUzRA",
    "host": "abcmart.a-rt.com",
    "referer": "https://abcmart.a-rt.com/product/brand/page/main?brandNo=000003&page=1",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

# GET 요청
response = requests.get(url, headers=headers, params=payload)

# 요청 성공 여부 확인
if response.status_code == 200:
    # HTML 파싱
    soup = BeautifulSoup(response.text, 'html.parser')

    # a 태그(class="prod-link") 찾기
    links = soup.find_all('a', class_='prod-link')

    # href 속성만 추출
    href_list = [link.get('href') for link in links if link.get('href')]

    # 결과 출력
    print(len(href_list))
    print(href_list)
else:
    print(f"요청 실패: {response.status_code}")
