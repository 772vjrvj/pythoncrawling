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

def load_data():
    data_file = os.path.join(get_base_dir(), 'data.json')
    if not os.path.exists(data_file):
        ui_log(f"data.json 없음. 새로 생성합니다: {data_file}")
        save_data({})
        return {}
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        ui_log("data.json 내용 파싱 실패. 빈 딕셔너리로 대체합니다.")
        return {}

def save_data(data):
    data_file = os.path.join(get_base_dir(), 'data.json')
    ui_log(f"저장 중: {data_file}")
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
