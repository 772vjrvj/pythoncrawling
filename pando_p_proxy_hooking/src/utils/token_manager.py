# src/utils/token_manager.py

import threading
import time
from src.utils.api import fetch_token_from_api
from src.utils.file_storage import load_data, save_data
from src.utils.logger import log_info, log_error

def start_token(data):
    token = fetch_token_from_api(data['store_id'])
    if token:
        data['token'] = token
        log_info(f"[판도] 토큰 갱신 완료 → 저장 예정: {data}")
        save_data(data)
        log_info("[판도] 토큰 갱신 + 저장 완료")
    else:
        log_error("[판도] 토큰 갱신 실패")
