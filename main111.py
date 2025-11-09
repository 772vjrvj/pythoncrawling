# rate_limit_test.py
import time
import requests
from collections import Counter

BASE_URL = "https://healmecare.com"
LOCATION_URL = f"{BASE_URL}/location"
API_URL = f"{BASE_URL}/api/location/select"

# 브라우저처럼 보이는 UA (정상 테스트용)
NORMAL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

# API 기본 페이로드 (질문 주신 값 그대로)
API_PARAMS_BASE = {
    "keyword": "",
    "category": "",
    "province": "",
    "city": "",
    "town": "",
    "offset": "20",
    "size": "20"
}


def hit(url, n, interval_sec, headers=None, params=None, label=""):
    sess = requests.Session()
    stats = Counter()
    print(f"\n=== HITTING {url} ({label}) n={n}, interval={interval_sec}s ===")
    for i in range(1, n + 1):
        try:
            r = sess.get(url, headers=headers, params=params, timeout=10)
            stats[r.status_code] += 1
            text_preview = (r.text[:120].replace("\n", " ") + "...") if r.text else ""
            print(f"[{i:03d}] {r.status_code} {r.reason} {text_preview}")
        except Exception as e:
            print(f"[{i:03d}] EXC {e}")
            stats["EXC"] += 1
        time.sleep(interval_sec)
    print(f"--- RESULT {label} ---")
    for k, v in sorted(stats.items(), key=lambda x: str(x[0])):
        print(f"  {k}: {v}")
    return stats


def test_location_polite():
    # 정중: 1초 간격 15회
    return hit(LOCATION_URL, n=15, interval_sec=1.0, headers=NORMAL_HEADERS, label="LOCATION polite")


def test_location_aggressive():
    # 공격적: 0.1초 간격 30회 (빠른 연타)
    return hit(LOCATION_URL, n=30, interval_sec=0.1, headers=NORMAL_HEADERS, label="LOCATION aggressive")


def test_api_polite():
    # API 정중: 2초 간격 10회 (API는 더 엄격할 수 있음)
    return hit(API_URL, n=10, interval_sec=2.0, headers=NORMAL_HEADERS, params=API_PARAMS_BASE, label="API polite")


def test_api_aggressive():
    # API 공격적: 0.2초 간격 20회 (빨리 때려보는 시나리오)
    return hit(API_URL, n=20, interval_sec=0.2, headers=NORMAL_HEADERS, params=API_PARAMS_BASE, label="API aggressive")


if __name__ == "__main__":
    print("=== START polite tests ===")
    test_location_polite()
    test_api_polite()

    print("\n=== START aggressive tests ===")
    test_location_aggressive()

    print("cooldown wait 12s ...")
    time.sleep(12)

    test_api_aggressive()
    print("\n=== DONE ===")
