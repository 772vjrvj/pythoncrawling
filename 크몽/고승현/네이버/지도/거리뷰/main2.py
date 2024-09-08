import requests
import os

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
            print("No panorama data found.")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

# Panorama 이미지를 다운로드하는 함수
def download_panorama_images(panorama_id):
    if panorama_id is None:
        return

    # 이미지 URL 템플릿
    image_urls = [
        f"https://panorama.pstatic.net/image/{panorama_id}/512/P",
        f"https://panorama.map.naver.com/api/v2/overlays/floor/{panorama_id}",
        f"https://panorama.pstatic.net/image/{panorama_id}/512/T/l",
        f"https://panorama.pstatic.net/image/{panorama_id}/512/T/f",
        f"https://panorama.pstatic.net/image/{panorama_id}/512/T/r",
        f"https://panorama.pstatic.net/image/{panorama_id}/512/T/b",
        f"https://panorama.pstatic.net/image/{panorama_id}/512/T/d",
        f"https://panorama.pstatic.net/image/{panorama_id}/512/T/u"
    ]

    # 이미지 저장 폴더
    save_folder = "panorama_images"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # 각 이미지 다운로드
    for idx, img_url in enumerate(image_urls):
        img_response = requests.get(img_url)
        if img_response.status_code == 200:
            # 이미지 파일 저장
            img_file_path = os.path.join(save_folder, f"image_{idx}.jpg")
            with open(img_file_path, 'wb') as img_file:
                img_file.write(img_response.content)
            print(f"Downloaded: {img_file_path}")
        else:
            print(f"Failed to download: {img_url}")

# 메인 함수
def main():
    # 사용자로부터 위도와 경도 입력 받기

    # longitude = input("Enter the longitude: ")
    # latitude = input("Enter the latitude: ")
    longitude = '127.05382990000169'
    latitude = '37.239594600001126'

    # 강원강릉시
    longitude = '128.8784972'
    latitude = '37.74913611'

    latitude = '37.4482284564'
    longitude = '126.6496530682'

    # Panorama 데이터 가져오기
    panorama_id = get_panorama_data(longitude, latitude)

    # Panorama 이미지 다운로드
    download_panorama_images(panorama_id)

if __name__ == "__main__":
    main()
