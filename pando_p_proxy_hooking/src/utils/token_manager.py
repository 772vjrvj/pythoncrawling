import threading
import time
from src.utils.api import fetch_token_from_api
from src.utils.file_storage import load_data, save_data

_cached_token = None
_refresh_thread = None
_store_id = None

def refresh_token_loop():
    global _cached_token
    while True:
        token = fetch_token_from_api(_store_id)
        if token:
            _cached_token = token

            config = load_data()
            config['token'] = token
            save_data(config)

            print("토큰 갱신 + 저장 완료")
        else:
            print("토큰 갱신 실패")
        time.sleep(60 * 60)  # 1시간 간격

def start_token_refresh(store_id):
    global _refresh_thread, _store_id
    _store_id = store_id
    if _refresh_thread is None or not _refresh_thread.is_alive():
        _refresh_thread = threading.Thread(target=refresh_token_loop, daemon=True)
        _refresh_thread.start()

def get_token():
    return _cached_token

def get_store_id():
    return _store_id
