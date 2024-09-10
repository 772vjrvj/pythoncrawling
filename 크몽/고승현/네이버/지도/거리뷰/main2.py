import requests
import os
import pandas as pd
import time
import random

# Panorama 데이터를 가져오는 함수
def get_panorama_data(longitude, latitude):
    # URL 동적 생성
    url = f'https://map.naver.com/p/api/panorama/nearby/{longitude}/{latitude}/3'

    # 헤더 설정
    headers = {
        'referer': 'https://map.naver.com/',
    }

    # GET 요청 보내기
    response = requests.get(url, headers=headers)

    # 요청이 성공했는지 확인
    if response.status_code == 200:
        # JSON 데이터를 파싱
        data = response.json()
        features = data.get('features', [])

        if len(features) > 0:
            # 첫 번째 feature에서 id 추출
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
def download_panorama_images(panorama_id, save_folder):
    if panorama_id is None:
        return

    # 이미지 URL 템플릿
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

    # 이미지 저장 폴더가 없으면 생성
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # 각 이미지 다운로드
    for img_url in image_urls:
        img_response = requests.get(img_url['url'])
        if img_response.status_code == 200:
            # 이미지 파일 저장
            img_file_path = os.path.join(save_folder, f"image_{img_url['loc']}.jpg")
            with open(img_file_path, 'wb') as img_file:
                img_file.write(img_response.content)
            print(f"다운로드 완료: {img_file_path}")
        else:
            print(f"다운로드 실패: {img_url}")

# 엑셀 파일에서 데이터를 읽고 처리하는 함수
def process_excel_and_download_images(file_path):
    # 엑셀 파일 읽기
    df = pd.read_excel(file_path)

    # 각 행에 대해 처리
    for index, row in df.iterrows():
        fid = row['FID']
        x_code = row['X_Code'] # 위도
        y_code = row['Y_Code'] # 경도

        print(f"처리 중: FID={fid}, X_Code={x_code}, Y_Code={y_code}")

        # 크롤링 감지 방지를 위한 지연시간
        time.sleep(2)

        # Panorama 데이터 가져오기
        panorama_id = get_panorama_data(x_code, y_code)

        # 크롤링 감지 방지를 위한 지연시간
        time.sleep(2)

        # 이미지를 FID 이름의 폴더에 저장
        save_folder = os.path.join("panorama_images", f"FID_{fid}")
        download_panorama_images(panorama_id, save_folder)

# 메인 함수
def main():
    # 엑셀 파일 경로 설정 (프로그램이 실행되는 경로 에 파일을 둔다)
    excel_file_path = '네이버지도_X-Y_좌표_샘플.xlsx'

    # 엑셀 파일에서 데이터 처리 및 이미지 다운로드
    process_excel_and_download_images(excel_file_path)

if __name__ == "__main__":
    main()
