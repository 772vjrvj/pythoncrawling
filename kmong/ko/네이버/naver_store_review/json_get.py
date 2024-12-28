import json
import os

# json_data 폴더가 없으면 생성
folder_path = 'json_data'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# 48개의 JSON 파일 생성
for i in range(1, 49):
    # 데이터 예시 (원하는 데이터를 여기에 추가)
    data = {
        "id": i,
        "name": f"data_{i}",
        "value": i * 10
    }

    # 파일 경로
    file_path = os.path.join(folder_path, f'json_data_{i}.json')

    # JSON 파일로 저장
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

print("48개의 JSON 파일이 생성되었습니다.")
