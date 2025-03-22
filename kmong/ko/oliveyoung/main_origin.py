import requests
import json

def get_reviews(goods_no, page_idx):
    """Olive Young 상품 리뷰를 가져오는 함수"""
    url = "https://www.oliveyoung.co.kr/store/goods/getGdasNewListJson.do"
    headers = {
        "authority": "www.oliveyoung.co.kr",
        "method": "GET",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={goods_no}",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    params = {
        "goodsNo": goods_no,
        "gdasSort": "05",
        "itemNo": "all_search",
        "pageIdx": str(page_idx),
        "colData": "",
        "keywordGdasSeqs": "",
        "type": "",
        "point": "",
        "hashTag": "",
        "optionValue": "",
        "cTypeLength": "0"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: 요청 실패")
        return None

def print_reviews(reviews):
    """리뷰 리스트를 출력하는 함수"""
    if not reviews or "gdasList" not in reviews:
        print("리뷰 데이터가 없습니다.")
        return

    for review in reviews["gdasList"]:
        # 'addInfoNm'이 있고, 리스트 형태이면 'mrkNm' 값 최대 4개 추출
        add_info_list = [info["mrkNm"] for info in review.get("addInfoNm", []) if "mrkNm" in info][:4]

        # gdasSeq 값 (짝수) -> 평점 변환 (0~5 범위)
        score = min(5, max(0, review["gdasSeq"] // 2))

        obj = {
            '리뷰 ID': review['gdasSeq'],
            '상품 번호': review['goodsNo'],
            '회원 닉네임': review['mbrNickNm'],
            '평점': score,  # 정수값 (0~5 범위)
            '리뷰 내용': review['gdasCont'],
            '리뷰 등록 날짜': review['dispRegDate'],
            '추가정보': add_info_list  # 최대 4개 리스트
        }

        print(obj)  # 리뷰 객체 출력 (테스트용)

def main():
    """메인 실행 함수"""
    goods_no = "A000000182989"
    page_idx = 2

    reviews = get_reviews(goods_no, page_idx)
    print_reviews(reviews)

if __name__ == "__main__":
    main()
