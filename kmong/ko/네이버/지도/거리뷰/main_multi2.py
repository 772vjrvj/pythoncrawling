import requests
import os
import pandas as pd
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

# Panorama 데이터를 가져오는 함수
def get_panorama_data(longitude, latitude):
    url = f'https://map.naver.com/p/api/panorama/nearby/{longitude}/{latitude}/3'
    headers = {
        'referer': 'https://map.naver.com/',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        features = data.get('features', [])

        if len(features) > 0:
            panorama_id = features[0]['properties']['id']
            print(f"Panorama ID: {panorama_id}")
            return panorama_id
        else:
            print("Panorama 데이터를 찾을 수 없습니다.")
            return None
    else:
        print(f"에러: {response.status_code}")
        return None

# Panorama 이미지를 다운로드하는 함수
def download_panorama_images(panorama_id, save_folder, fid):
    if panorama_id is None:
        return

    image_urls = [
        {"url": f"https://panorama.pstatic.net/image/{panorama_id}/512/P", "loc": "P"},
        {"url": f"https://panorama.map.naver.com/api/v2/overlays/floor/{panorama_id}", "loc": "floor"},
        {"url": f"https://panorama.pstatic.net/image/{panorama_id}/512/T/l", "loc": "l"},
        {"url": f"https://panorama.pstatic.net/image/{panorama_id}/512/T/f", "loc": "f"},
        {"url": f"https://panorama.pstatic.net/image/{panorama_id}/512/T/r", "loc": "r"},
        {"url": f"https://panorama.pstatic.net/image/{panorama_id}/512/T/b", "loc": "b"},
        {"url": f"https://panorama.pstatic.net/image/{panorama_id}/512/T/d", "loc": "d"},
        {"url": f"https://panorama.pstatic.net/image/{panorama_id}/512/T/u", "loc": "u"},
    ]

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    for img_url in image_urls:
        img_response = requests.get(img_url['url'])
        if img_response.status_code == 200:
            img_file_path = os.path.join(save_folder, f"image_{fid}_{img_url['loc']}.jpg")
            with open(img_file_path, 'wb') as img_file:
                img_file.write(img_response.content)
            print(f"다운로드 완료: {img_file_path}")
        else:
            print(f"다운로드 실패: {img_url['url']}")

# 스레드에서 실행할 작업 함수
def process_row(fid, x_code, y_code):
    print(f"처리 중: FID={fid}, X_Code={x_code}, Y_Code={y_code}")

    # 크롤링 방지용 랜덤 지연 시간 추가
    time.sleep(random.uniform(0.5, 2.0))

    # Panorama 데이터 가져오기
    panorama_id = get_panorama_data(x_code, y_code)

    # 크롤링 방지용 랜덤 지연 시간 추가
    time.sleep(random.uniform(0.5, 2.0))

    # 이미지를 FID 이름의 폴더에 저장
    save_folder = "panorama_images"
    download_panorama_images(panorama_id, save_folder, fid)

# 엑셀 파일에서 데이터를 읽고 스레드를 통해 처리하는 함수
def process_excel_and_download_images(file_path):
    df = pd.read_excel(file_path)

    # ThreadPoolExecutor 사용
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(process_row, row['FID'], row['X_Code'], row['Y_Code'])
            for _, row in df.iterrows()
        ]

        for future in as_completed(futures):
            try:
                future.result()  # 결과 처리 (에러 발생 시 여기서 예외를 잡을 수 있음)
            except Exception as exc:
                print(f"작업 중 에러 발생: {exc}")

# 메인 함수
def main():
    # 시작 시간 기록
    start_time = time.time()
    print(f"작업 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    excel_file_path = '네이버지도_X-Y_좌표_샘플.xlsx'

    # 엑셀 파일에서 데이터 처리 및 이미지 다운로드
    process_excel_and_download_images(excel_file_path)

    # 끝 시간 기록
    end_time = time.time()
    print(f"작업 종료 시간: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

    # 총 걸린 시간 계산
    elapsed_time = end_time - start_time
    formatted_time = str(timedelta(seconds=elapsed_time))
    print(f"총 걸린 시간: {formatted_time}")

if __name__ == "__main__":
    main()
