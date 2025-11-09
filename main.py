import time
import random
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

BASE_URL = "https://healmecare.com/api/location/select"

# (선택) 쿠키가 필요하면 여기에 그대로 붙여넣으세요.
COOKIE = "_ga=GA1.1.202799101.1762270001; _ga_MYT663CEQJ=GS2.1.s1762270001$o1$g1$t1762271215$j57$l0$h0"

def build_session():
    s = requests.Session()
    # 기본 헤더: pseudo-header(:authority 등)는 제거. requests가 Host를 자동으로 넣습니다.
    s.headers.update({
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://healmecare.com/location",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/142.0.0.0 Safari/537.36",
        "origin": "https://healmecare.com",
    })

    # 429/5xx 자동 재시도 + 지수 백오프(1,2,4,8,16초; Retry-After도 존중)
    retry = Retry(
        total=5,
        connect=3,
        read=3,
        status=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

def main():
    session = build_session()

    offset = 0
    size = 20

    while True:
        params = {
            "keyword": "",
            "category": "",
            "province": "",
            "city": "",
            "town": "",
            "offset": offset,
            "size": size,
        }

        try:
            # 타임아웃은 (연결 5초, 응답 20초)
            resp = session.get(BASE_URL, params=params, timeout=(5, 20))
        except requests.RequestException as e:
            print(f"offset={offset} 요청 실패: {e}")
            # 네트워크 오류면 잠깐 쉬고 다음 루프
            time.sleep(2.5)
            continue

        # 재시도 후에도 200이 아닐 수 있음 (예: 계속 429)
        if resp.status_code == 429:
            # 서버가 Retry-After 주면 urllib3가 이미 대기했을 수 있음.
            # 여기서는 추가로 랜덤 지터를 넣고 계속 시도.
            sleep_sec = 3 + random.uniform(0, 2)
            print(f"offset={offset} 429 Too Many Requests → {sleep_sec:.1f}s 대기 후 재시도")
            time.sleep(sleep_sec)
            # 다음 while 반복에서 동일 offset 재시도
            continue

        if not resp.ok:
            print(f"offset={offset} HTTP {resp.status_code} → 건너뜀")
            # 상태가 안 좋을 땐 느리게 한 박자 쉬고 재시도(같은 offset)
            time.sleep(2.0)
            continue

        try:
            payload = resp.json()
        except ValueError:
            print(f"offset={offset} JSON 파싱 실패")
            # 다음 페이지로 넘어가면 누락될 수 있으니 같은 offset 재시도
            time.sleep(1.0)
            continue

        data = payload.get("data", [])
        count = len(data) if isinstance(data, list) else 0
        print(f"offset={offset}, count={count}")

        if count == 0:
            print("데이터 끝.")
            break

        # 페이지 사이에 약간의 지터 딜레이(봇 속도 완화)
        time.sleep(0.4 + random.uniform(0, 0.4))

        offset += size

if __name__ == "__main__":
    main()
