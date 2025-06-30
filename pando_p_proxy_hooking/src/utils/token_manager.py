# src/utils/token_manager.py
import threading
import time
from src.utils.api import fetch_token_from_api
from src.utils.file_storage import load_data, save_data

def start_token(data):
    token = fetch_token_from_api(data['store_id'])
    if token:
        data['token'] = token
        print(f"data : {data}")
        print("토큰 갱신 + 저장 완료")
    else:
        print("토큰 갱신 실패")
