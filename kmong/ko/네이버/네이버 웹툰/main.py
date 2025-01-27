import requests
import json

# JSONP에서 콜백 함수 부분을 제거하는 함수
def parse_jsonp(response_text):
    """
    JSONP 응답에서 콜백 함수 부분을 제거하고 순수한 JSON 데이터만 반환합니다.
    """
    start = response_text.index('(') + 1
    end = response_text.rindex(')')
    return response_text[start:end]

# JSON 데이터를 예쁘게 출력하는 함수
def pretty_print_json(json_data):
    """
    JSON 데이터를 예쁘게 출력합니다.
    """
    pretty_json = json.dumps(json_data, indent=4, ensure_ascii=False)  # 들여쓰기와 함께 문자열로 변환
    print(pretty_json)

# GET 요청을 보내는 함수
def make_request(url, headers):
    """
    주어진 URL에 GET 요청을 보내고, JSONP 응답을 JSON 형식으로 변환하여 반환합니다.
    """
    response = requests.get(url, headers=headers)
    json_data = parse_jsonp(response.text)  # JSONP 형식에서 콜백 제거
    return json.loads(json_data)  # JSON 문자열을 Python 객체로 변환

def main():
    # 요청을 보낼 URL
    url = "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=comic&templateId=webtoon&pool=cbox3&_cv=20241007144116&lang=ko&country=KR&objectId=833415_1&categoryId=&pageSize=100&indexSize=10&groupId=833415&listType=OBJECT&pageType=more&page=1&currentPage=1&refresh=false&sort=NEW&current=472993216&prev=473001130&moreParam.direction=next&moreParam.prev=06duf8vz4cthi&moreParam.next=06du482nv6iyt&_="

    # 헤더 정보 설정 (쿠키는 제외)
    headers = {
        "authority": "apis.naver.com",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://comic.naver.com/webtoon/detail?titleId=833415&no=1&week=sat",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "cookie": "NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; NACT=1; nid_inf=385973303; NID_AUT=/7uxLohgIznvHie7mWffEFjkvia0qCRC1rdTmkreQDszmTYCa7j4nYXX782IL8OA; NID_SES=AAABqJkxcl+oO3+/RhAY3SL/SGcbLtnKTjr/mHtVP451MMFfvWcWOexsPQAgi8y9xYm98GWi3NAe8CSdy6wL2uaNbIOWK3p2E/dyE/djvYO8PiKrHhVyHWb96Qhg0hjWwS2PBR1sG531vloNUurHDfnLQ0uzNYITwpqMiHZK8qoX3TTiJpOrQElLYcoy7hhVk2yJ18DPbTlik1rQIjAfdXnfr+R+OB647fX5mUbaZ1uWqw7A4ofL9x83etiPAi0yPwINis56vpMo6xwosx5n/jPmbX3RN0/dPR63FePsTy/HBJ/pyqhHZ9zqtqETrbta9olqlu7CHOD0Ou8oDbSWCNnZhkFJe4KgalXYJJEqweWNCq327H539cDDYxedJS9FP3pNvq5S1XAneHoN/E3zfU4w7ic5K2gPVsPRT/9+szQbV2+hTMp90oej6Z0tXUVRM3OvUu1UoVcblMW1+dJt6Zzgd+DKgIk5lEhB1DOiVOZT/JbUqrLZeiXJUs976BoaelaVfIiKXJ7ndGBHP1RgVuHQKEL/QEMQaz3/UBgoMDkILp9P3HOAEWddlwS3hxRzBI6t9g==; NID_JKL=NFGVziyIEOAGnRJqaaUpgBVhp6uRbzhGCEOWkL/B4xw=; BUC=JHcIAozrc167DTvvawRWP7NX4MYPq4uQVsGWz30u0QE=",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }

    # GET 요청 보내고 결과를 받아서 출력
    json_data = make_request(url, headers)
    pretty_print_json(json_data)

if __name__ == "__main__":
    main()
