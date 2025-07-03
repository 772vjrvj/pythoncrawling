#src/utils/.file_storage.py
import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        # 파일 내용이 유효하지 않을 때 빈 dict 반환
        return {}

def save_data(data):
    print(data)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
