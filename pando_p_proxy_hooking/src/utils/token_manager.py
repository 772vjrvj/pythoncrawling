# src/utils/token_manager.py

import threading
import time
from src.utils.api import fetch_token_from_api
from src.utils.file_storage import load_data, save_data
from src.utils.logger import ui_log


def start_token(data):
    token = fetch_token_from_api(data['store_id'])
    if not token:
        raise Exception("토큰 갱신 실패")  # === 신규 ===

    data['token'] = token
    ui_log(f"[판도] 토큰 갱신 완료 → 저장 예정: {data}")
    save_data(data)
    ui_log("[판도] 토큰 갱신 + 저장 완료")
    return True