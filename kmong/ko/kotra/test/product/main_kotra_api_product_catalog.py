import requests
import os

def download_product_data(goodsSn, goodsInfoCd, goodsInfoSn, save_path="downloads"):
    """
    상품 데이터를 다운로드하는 함수
    """
    url = f"https://buykorea.org/ec/prd/goodsFileDownload.do?goodsSn={goodsSn}&goodsInfoCd={goodsInfoCd}&goodsInfoSn={goodsInfoSn}"
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        os.makedirs(save_path, exist_ok=True)
        filename = os.path.join(save_path, f"{goodsSn}_{goodsInfoCd}_{goodsInfoSn}.pdf")  # 파일 확장자 필요시 수정

        with open(filename, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        print(f"파일 다운로드 완료: {filename}")
    else:
        print(f"다운로드 실패: {response.status_code}")

# 사용 예시
if __name__ == "__main__":
    download_product_data("3732079", "04", "1")
