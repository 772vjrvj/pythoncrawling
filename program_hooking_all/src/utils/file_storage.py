# src/utils/file_storage.py

import os
import sys
import json
from src.utils.logger import ui_log

def get_base_dir():
    # 빌드된 exe에서 실행 중이면 sys.executable 기준
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

DATA_FILE = os.path.join(get_base_dir(), 'data.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        ui_log(f"[판도] data.json 없음. 새로 생성합니다: {DATA_FILE}")
        save_data({})
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        ui_log("[판도] data.json 내용 파싱 실패. 빈 딕셔너리로 대체합니다.")
        return {}

def save_data(data):
    ui_log(f"[판도] 저장 중: {DATA_FILE}")
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
