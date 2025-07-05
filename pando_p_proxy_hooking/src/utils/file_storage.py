#src/utils/.file_storage.py
import os
import json
import os
import sys

def get_base_dir():
    # 빌드된 exe에서 실행 중이면 sys.executable 기준
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # 평소 개발 환경에선 이 파일 기준
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

DATA_FILE = os.path.join(get_base_dir(), 'data.json')

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
    print(f"💾 저장 중: {DATA_FILE}")
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
