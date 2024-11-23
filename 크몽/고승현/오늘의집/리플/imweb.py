import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def fetch_reviews(prod_idx, review_page):
    """
    특정 페이지의 리뷰 HTML을 가져오는 함수
    """
    url = "https://www.deelisa.com/shop/prod_review_pc_html.cm"
    headers = {
        "authority": "www.deelisa.com",
        "method": "POST",
        "scheme": "https",
        "accept": "text/html, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-length": "59",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.deelisa.com",
        "cookie": "al=KR; _fbp=fb.1.1732113378120.29031472111411586; _fwb=236DE0CaNOpGdea2LEzSC5y.1732113378344; IMWEBVSSID=u5mq7udsud8u91ssgdegktrgolpi3r54jt36ktae4uhuo718cabnjdrt8qo708219120dmengarn5ob4fdc5h0tdipr8p35dn94e3v3; FB_EXTERNAL_ID=u2022020561fe51af4b527202411234bd7be0590839; __bs_imweb=%7B%22utmSource%22%3Anull%2C%22utmMedium%22%3Anull%2C%22utmCampaign%22%3Anull%2C%22utmTerm%22%3Anull%2C%22utmContent%22%3Anull%2C%22deviceId%22%3A%22c34eca41099b751e32651a706313be31%22%2C%22sessionId%22%3A%22ssdeab73bf885b437481feb5314f94930a%22%2C%22memberCode%22%3Anull%2C%22initialReferrer%22%3A%22%40direct%22%2C%22initialReferrerDomain%22%3A%22%40direct%22%2C%22siteCode%22%3A%22S20220205677982edb62a5%22%2C%22unitCode%22%3A%22u2022020561fe51af4b527%22%2C%22platform%22%3A%22DESKTOP%22%2C%22os%22%3A%22WINDOWS%22%2C%22language%22%3A%22ko-KR%22%2C%22browserName%22%3A%22Chrome%22%2C%22browserVersion%22%3A%22131.0.0.0%22%2C%22userAgent%22%3A%22Mozilla%2F5.0%20(Windows%20NT%2010.0%3B%20Win64%3B%20x64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F131.0.0.0%20Safari%2F537.36%22%2C%22path%22%3A%22%2F1858462307%2F%22%7D; SITE_STAT_SID=202411246741ef5d1e4182.69974622; wcs_bt=s_2487a7b963ae:1732375294",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "referer": "https://www.deelisa.com/1858462307/?idx=314",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    payload = {
        "prod_idx": prod_idx,
        "review_page": review_page,
        "qna_page": 1,
        "only_photo": "N",
        "rating": 0
    }

    response = requests.post(url, headers=headers, data=payload, verify=False)

    if response.status_code != 200:
        print(f"Error: Failed to fetch page {review_page}")
        return None
    return response.text


def parse_review_data(html, prod_name):
    """
    HTML을 파싱하여 리뷰 데이터를 추출하는 함수
    """
    soup = BeautifulSoup(html, "html.parser")
    review_list = []
    reviews = soup.select("ul.list_review_wrap > li")

    for review in reviews:
        # 후기 점수
        score = len(review.select(".star_point_wrap .bt-star.active"))

        # 내용
        content = review.select_one(".txt._txt._review_body")
        content_text = content.get_text(strip=True) if content else ""

        # 포토 URL
        photo_elements = review.select(".thumb_detail_img_wrap img")
        photo_urls = [img["src"] for img in photo_elements]

        # 닉네임
        nickname = review.select_one(".table-cell.vertical-top.width-5.text-13.use_summary > div:nth-of-type(1)")
        nickname_text = nickname.get_text(strip=True) if nickname else ""

        # 등록일자
        date = review.select_one(".table-cell.vertical-top.width-5.text-13.use_summary > div:nth-of-type(2)")
        date_text = date.get_text(strip=True) if date else ""

        # 리뷰 데이터 추가
        review_data = {
            "상품명": prod_name,
            "후기점수": score,
            "내용": content_text,
            "닉네임": nickname_text,
            "등록일자": date_text
        }

        # 포토 URL 동적 추가
        for idx, url in enumerate(photo_urls, start=1):
            review_data[f"포토URL{idx}"] = url

        review_list.append(review_data)

    return review_list


def export_to_excel(result, file_name="oh_reviews.xlsx"):
    # pandas DataFrame으로 변환
    df = pd.DataFrame(result)

    # DataFrame을 엑셀로 저장
    df.to_excel(file_name, index=False)

    print(f"Data has been successfully exported to {file_name}")

def extract_idx(url):
    """
    URL에서 idx 값을 추출하는 함수
    """
    match = re.search(r"idx=(\d+)", url)
    if match:
        return match.group(1)
    return None

def main():

    prod_list = [
        {"name": "모듈리 플로어램프 라운드", "url": "https://www.deelisa.com/1858462307/?idx=389"},
        {"name": "시즈 플로어 램프", "url": "https://www.deelisa.com/1858462307/?idx=87"},
        {"name": "시그니쳐 골드림 플로어 램프", "url": "https://www.deelisa.com/1858462307/?idx=282"},
        {"name": "아토 테이블 램프", "url": "https://www.deelisa.com/1858462307/?idx=314"},
        {"name": "아리아 우드 원형 테이블 램프", "url": "https://www.deelisa.com/1858462307/?idx=42"},
        {"name": "바네사 우드 월 램프", "url": "https://www.deelisa.com/1858462307/?idx=54"},
        {"name": "에이시메트리컬 월넛 우드 램프", "url": "http://www.deelisa.com/all-bedding/?idx=56"},
        {"name": "와이드 홀리데이 쉐이드 조명갓", "url": "https://www.deelisa.com/1858462307/?idx=131"},
        {"name": "워셔블 소프트 스테이 사계절 러그", "url": "https://www.deelisa.com/201/?idx=450"},
        {"name": "사계절 루프 카페트 러그 SQUARE", "url": "https://www.deelisa.com/201/?idx=50"},
        {"name": "사계절 루프 카페트 러그 CIRCLE", "url": "https://www.deelisa.com/201/?idx=49"},
        {"name": "사계절 루프 카페트 러그 BRICK", "url": "https://www.deelisa.com/201/?idx=48"},
        {"name": "네추럴 오벌 셰이커 우드박스 정리함", "url": "https://www.deelisa.com/living/?idx=80"},
        {"name": "이태리 직수입 메모리폼 매트리스", "url": "https://www.deelisa.com/120/?idx=346"},
        {"name": "이태리 직수입 메모리폼 매트리스", "url": "https://www.deelisa.com/120/?idx=347"},
        {"name": "이태리 직수입 메모리폼 매트리스", "url": "https://www.deelisa.com/120/?idx=348"},
        {"name": "C2 페브릭 모듈소파", "url": "https://www.deelisa.com/120/?idx=77"},
        {"name": "C2 페브릭 모듈소파 암쿠션", "url": "https://www.deelisa.com/120/?idx=293"},
        {"name": "펫소파", "url": "https://www.deelisa.com/120/?idx=417"},
        {"name": "몽구르 1인용 소파", "url": "https://www.deelisa.com/120/?idx=264"},
        {"name": "스탠딩 우드미러 탁상형 거울", "url": "https://www.deelisa.com/120/?idx=126"}
    ]

    all_reviews = []


    for index, prod in enumerate(prod_list, start=1):

        print(f'제품 : {prod['name']}, ({index}/{len(prod_list)})')
        prod_idx = extract_idx(prod['url'])

        review_page = 1
        while True:
            print(f"Fetching reviews from page {review_page}...")
            html = fetch_reviews(prod_idx, review_page)
            if not html:
                break

            reviews = parse_review_data(html, prod['name'])
            print(f'reviews : {reviews}')

            if not reviews:
                break

            if all_reviews and reviews and all_reviews[-1] == reviews[-1]:
                break

            all_reviews.extend(reviews)
            review_page += 1


    export_to_excel(all_reviews)


if __name__ == "__main__":
    main()
