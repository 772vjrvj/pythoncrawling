# src/services/token_manager.py
import threading
import time
from src.utils.api import fetch_token_from_api

TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2OTBkN2VhNzUwZmY5YTY2ODllOWFmMyIsInJvbGUiOiJzaW5nbGVDcmF3bGVyIiwiZXhwIjo0ODk4ODQ0MDc3fQ.aEUYvIzMhqW6O2h6hQTG8IfzJNhpvll4fOdN7udz1yc"

_cached_token = None
_store_id = None
_refresh_thread = None
_stop_event = threading.Event()

def _log(msg):
    print(msg)  # 필요시 로거 대체

def _refresh_token():
    global _cached_token, _store_id

    while not _stop_event.is_set():
        if not _store_id:
            _log("⚠️ store_id 미설정, 토큰 갱신 중단")
            break

        try:
            token = fetch_token_from_api(_store_id)
            if not token:
                raise ValueError("null token")
            _cached_token = token
            _log("✅ 토큰 갱신 완료")
        except Exception as e:
            _log(f"❌ 토큰 갱신 실패, fallback 사용: {e}")
            # 프로덕션 환경 체크 예시 (원하는대로 수정)
            _cached_token = TEST_TOKEN

        # 1시간마다 갱신 (3600초)
        for _ in range(60*60):
            if _stop_event.is_set():
                break
            time.sleep(1)


def start(store_id_param):
    global _store_id, _refresh_thread, _stop_event, _cached_token

    if _store_id == store_id_param and _refresh_thread and _refresh_thread.is_alive() and _cached_token:
        return

    stop()
    _store_id = store_id_param
    _stop_event.clear()

    # 즉시 토큰 갱신 한 번 수행
    try:
        token = fetch_token_from_api(_store_id)
        if not token:
            raise ValueError("null token")
        global _cached_token
        _cached_token = token
        _log("✅ 토큰 초기 갱신 완료")
    except Exception as e:
        _log(f"❌ 토큰 초기 갱신 실패, fallback 사용: {e}")
        _cached_token = TEST_TOKEN

    _refresh_thread = threading.Thread(target=_refresh_token, daemon=True)
    _refresh_thread.start()

def stop():
    global _stop_event
    if _refresh_thread and _refresh_thread.is_alive():
        _stop_event.set()
        _refresh_thread.join()
        _log("🛑 자동 갱신 종료됨")

def get_store_id():
    return _store_id

def get_token():
    return _cached_token

def get_token_async(retries=10, interval=0.5):
    global _cached_token
    for _ in range(retries):
        if _cached_token:
            return _cached_token
        time.sleep(interval)
    _log("⚠️ get_token_async: 토큰 획득 실패")
    return TEST_TOKEN
