import os
import requests
import pandas as pd
import threading
from queue import Queue

# CSV 파일 경로
csv_file = "Women_20250224230007.csv"
output_dir = "images"  # 이미지 저장 디렉토리

# 저장 폴더가 없으면 생성
os.makedirs(output_dir, exist_ok=True)

# CSV 파일 읽기
df = pd.read_csv(csv_file)

# 이미지 다운로드 함수
def download_image(q):
    while not q.empty():
        index, row = q.get()
        image_url = row["image_url"]
        image_name = row["image_name"]  # image_name 컬럼 값 사용
        image_path = os.path.join(output_dir, f"{image_name}.jpg")

        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
                df.at[index, "image_yn"] = "Y"
                print(f"✅ {image_path} 다운로드 완료")
            else:
                print(f"❌ {image_url} 다운로드 실패 (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ {image_url} 오류: {e}")

        q.task_done()

# 멀티스레드 실행 함수
def multi_thread_download(df, num_threads=6):
    q = Queue()

    # image_yn이 "Y"가 아닌 데이터만 큐에 추가
    for index, row in df.iterrows():
        if row.get("image_yn", "N") != "Y":
            q.put((index, row))

    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=download_image, args=(q,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

# 멀티스레드 이미지 다운로드 실행
multi_thread_download(df)

# CSV 파일 업데이트
df.to_csv(csv_file, index=False)
print("✅ CSV 파일 업데이트 완료!")
