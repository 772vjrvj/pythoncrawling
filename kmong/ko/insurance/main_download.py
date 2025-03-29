import requests
import os
import urllib.parse

def download_pdf_file(url: str, save_path: str):
    # URL 디코딩 (한글 포함된 파일명 처리)
    decoded_url = urllib.parse.unquote(url)

    # 실제 요청
    response = requests.get(decoded_url, stream=True)

    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"✅ 다운로드 완료: {save_path}")
    else:
        print(f"❌ 다운로드 실패 (status code: {response.status_code})")

def main():
    url = "https://www.hanalife.co.kr//home/download2.do?fileName=PROD/(%EB%AC%B4)%ED%95%98%EB%82%98%EC%9B%90%ED%81%90%EC%97%B0%EA%B8%88%EC%A0%80%EC%B6%95%EB%B3%B4%ED%97%98_%EC%83%81%ED%92%88%EC%9A%94%EC%95%BD%EC%84%9C_20240401.pdf&downFileName=(%EB%AC%B4)%ED%95%98%EB%82%98%EC%9B%90%ED%81%90%EC%97%B0%EA%B8%88%EC%A0%80%EC%B6%95%EB%B3%B4%ED%97%98_%EC%83%81%ED%92%88%EC%9A%94%EC%95%BD%EC%84%9C.pdf"

    # 저장할 파일명 (원하는 경로로 수정 가능)
    save_file_path = "하나원큐연금저축보험_상품요약서.pdf"

    download_pdf_file(url, save_file_path)

if __name__ == "__main__":
    main()
