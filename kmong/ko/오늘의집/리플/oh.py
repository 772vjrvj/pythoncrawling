import requests
import time
import random
import pandas as pd


def fetch_reviews(production_id):

    """
    특정 production_id에 대한 모든 리뷰를 가져오는 함수
    """
    page = 1
    reviews = []

    while True:

        headers = {
            "authority": "ohou.se",
            "method": "GET",
            "path": f"/production_reviews.json?production_id={production_id}&page={page}&order=best&photo_review_only=",
            "scheme": "https",
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "cookie": "",
            "priority": "u=1, i",
            "referer": f"https://ohou.se/productions/{production_id}/selling",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        # URL 생성
        url = f"https://ohou.se/production_reviews.json?production_id={production_id}&page={page}&order=best&photo_review_only="

        print(f"production_id={production_id}, page={page}.")
        # GET 요청
        response = requests.get(url, headers=headers)

        # 응답 확인
        if response.status_code != 200:
            print(f"Error: Unable to fetch data for production_id={production_id}, page={page}.")
            break

        # JSON 파싱
        data = response.json()

        # 리뷰가 없으면 반복 종료
        if not data.get("reviews"):
            break

        # 리뷰 추가
        reviews.extend(data["reviews"])

        # 다음 페이지로 이동
        page += 1

        # time.sleep(random.uniform(0.5, 1))  # Wait for the page to load
        time.sleep(0.5)  # Wait for the page to load

    return reviews


def export_to_excel(result, file_name="oh_reviews.xlsx"):
    # pandas DataFrame으로 변환
    df = pd.DataFrame(result)

    # DataFrame을 엑셀로 저장
    df.to_excel(file_name, index=False)

    print(f"Data has been successfully exported to {file_name}")


def main():

    url_list = [
        "https://ohou.se/productions/2224217/selling",
        "https://ohou.se/productions/2239988/selling",
        "https://ohou.se/productions/1399521/selling",
        "https://ohou.se/productions/1880477/selling",
        "https://ohou.se/productions/1964051/selling",
        "https://ohou.se/productions/1921924/selling",
        "https://ohou.se/productions/2051088/selling",
        "https://ohou.se/productions/741886/selling",
        "https://ohou.se/productions/807450/selling",
        "https://ohou.se/productions/756325/selling",
        "https://ohou.se/productions/807442/selling",
        "https://ohou.se/productions/838729/selling",
        "https://ohou.se/productions/838735/selling",
        "https://ohou.se/productions/782486/selling",
        "https://ohou.se/productions/739561/selling",
        "https://ohou.se/productions/735319/selling",
        "https://ohou.se/productions/1457816/selling",
        "https://ohou.se/productions/1925331/selling",
        "https://ohou.se/productions/1925371/selling",
        "https://ohou.se/productions/1925385/selling",
        "https://ohou.se/productions/1020566/selling",
        "https://ohou.se/productions/2596106/selling",
        "https://ohou.se/productions/1202947/selling",
        "https://ohou.se/productions/1202824/selling",
        "https://ohou.se/productions/1422428/selling",
        "https://ohou.se/productions/1502444/selling"
    ]

    result = []

    for url in url_list:
        # URL에서 production_id 추출
        production_id = url.split('/')[-2]

        print(f"Fetching reviews for production_id={production_id}...")

        # 리뷰 가져오기
        reviews = fetch_reviews(production_id)
        print(f'production_id {production_id}, reviws len : {len(reviews)}')
        # reviews를 순회하며 객체 생성
        for review in reviews:
            # 필요한 정보를 추출하여 객체 생성
            review_data = {
                "등록일자": review.get("created_at"),
                "닉네임": review.get("writer_nickname"),
                "상품명": review.get("production_information", {}).get("name"),
                "내용": review.get("review", {}).get("comment"),
                "후기점수": review.get("review", {}).get("star_avg"),
                "포토URL": review.get("card", {}).get("image_url"),
            }
            print(f'production_id {production_id}, review_data : {review_data}')
            # 결과 리스트에 추가
            result.append(review_data)

    export_to_excel(result)

if __name__ == "__main__":
    main()
