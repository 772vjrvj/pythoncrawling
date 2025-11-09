# ua_block_test.py
import requests

BASE_URL = "https://healmecare.com"
LOCATION_URL = f"{BASE_URL}/location"

def test_default_requests_ua():
    # requests 기본 User-Agent (python-requests/...)로 바로 호출
    print("== default requests UA test ==")
    try:
        r = requests.get(LOCATION_URL, timeout=10)
        print("status:", r.status_code, r.reason)
        print("body preview:", r.text[:200].replace("\n", " "))
    except Exception as e:
        print("EXC:", e)

def test_custom_python_ua():
    # 일부러 'python' 문자열 포함 UA
    headers = {"User-Agent": "my-crawler python/3.10 (+https://example.com)"}
    print("== custom python UA test ==")
    try:
        r = requests.get(LOCATION_URL, headers=headers, timeout=10)
        print("status:", r.status_code, r.reason)
        print("body preview:", r.text[:200].replace("\n", " "))
    except Exception as e:
        print("EXC:", e)

if __name__ == "__main__":
    test_default_requests_ua()
    print("\n--- wait 2s ---\n")
    import time; time.sleep(2)
    test_custom_python_ua()
