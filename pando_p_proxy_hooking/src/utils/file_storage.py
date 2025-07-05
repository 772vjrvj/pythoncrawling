#src/utils/.file_storage.py
import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"⚠️ data.json 없음. 새로 생성합니다: {DATA_FILE}")
        save_data({})
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        print("⚠️ data.json 내용 파싱 실패. 빈 딕셔너리로 대체합니다.")
        return {}

def save_data(data):
    print(data)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
