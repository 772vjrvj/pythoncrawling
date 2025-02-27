import requests
from bs4 import BeautifulSoup
import pandas as pd

# 요청 헤더 설정
HEADERS = {
    "authority": "chsjjj.shop.blogpay.co.kr",
    "method": "GET",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "priority": "u=0, i",
    "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "cookie": "ch-veil-id=84ceba26-7f6d-43b9-bae9-7dd55bec1412; PHPSESSID=di6o0nppojeln93elraldjro3b; device=pro;"
}

# 리뷰 상세 페이지 URL 템플릿
BASE_URL = "https://chsjjj.shop.blogpay.co.kr/controller/shop/board/bview"

# 엑셀 파일 읽기
def read_excel(filename="output.xlsx"):
    df = pd.read_excel(filename)
    return df.to_dict("records")  # 객체 리스트 반환

# 리뷰 상세 정보 크롤링
def crawl_review(bbsidx):
    params = {"bbsid": "BBS:GoodRate", "bbsidx": str(bbsidx)}

    # GET 요청
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"bbsidx {bbsidx} 요청 실패: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # listpage 내부 테이블 찾기
    listpage = soup.find("div", id="listpage")
    if not listpage:
        print(f"bbsidx {bbsidx}: listpage 없음")
        return None

    tables = listpage.find_all("table", class_="table table-bordered")
    if len(tables) < 1:
        print(f"bbsidx {bbsidx}: table 없음")
        return None

    table = tables[0]  # 첫 번째 테이블 선택

    # title 추출
    thead = table.find("thead")
    title = thead.find("th").text.strip() if thead else ""

    # tbody 내부 데이터 추출
    tbody = table.find("tbody")
    if not tbody:
        print(f"bbsidx {bbsidx}: tbody 없음")
        return None

    trs = tbody.find_all("tr")

    # 첫 번째 tr에서 작성일, 이메일 추출
    review_reg_date, review_email = "", ""
    if len(trs) > 0:
        td = trs[0].find("td")
        if td:
            text = td.get_text(separator="\n").strip()
            lines = text.split("\n")
            for line in lines:
                if "작성일" in line:
                    review_reg_date = line.replace("작성일 :", "").strip()
                elif "이메일" in line:
                    review_email = line.replace("이메일 :", "").strip()

    # 두 번째 tr에서 리뷰 내용 및 이미지 추출
    review_content = ""
    review_images = []

    if len(trs) > 1:
        td = trs[1].find("td", class_="textarea-box")
        if td:
            review_content = ""
            review_images = []

            # <a> 태그 뒤에 (가격) 형식 텍스트 제거
            for a_tag in td.find_all("a"):
                next_text = a_tag.find_next_sibling(string=True)
                if next_text and next_text.strip().startswith("(") and next_text.strip().endswith("원)"):
                    next_text.extract()  # "(33,000원)" 같은 가격 텍스트 삭제

            # 특정 패턴 (br, br, img, a, br, br) 찾기 및 삭제 (해당 블록 내 텍스트까지 삭제)
            br_tags = td.find_all("br")
            for i in range(len(br_tags) - 3):
                br1 = br_tags[i]
                br2 = br1.find_next_sibling()
                img_tag = br2.find_next_sibling() if br2 else None
                a_tag = img_tag.find_next_sibling() if img_tag else None
                br3 = a_tag.find_next_sibling() if a_tag else None
                br4 = br3.find_next_sibling() if br3 else None

                # 패턴이 정확히 일치하는 경우만 삭제
                if (
                        br1 and br2 and br3 and br4 and img_tag and a_tag and
                        br2.name == "br" and img_tag.name == "img" and
                        a_tag.name == "a" and br3.name == "br" and br4.name == "br"
                ):
                    # 해당 블록 내 텍스트까지 삭제
                    for element in [br1, br2, img_tag, a_tag, br3, br4]:
                        element.extract()
                    break  # 패턴은 한 번만 발생하므로 종료

            # "관리자 > 게시판 관리 > Q&A, 구매후기 이미지" 주석 삭제
            comments = td.find_all(string=lambda text: "관리자 > 게시판 관리 > Q&A, 구매후기 이미지" in text)
            for comment in comments:
                comment.extract()  # 주석 삭제

            # 불필요한 이미지 필터링 (logo.png, topbutton.png 등 특정 키워드 제거)
            images = td.find_all("img")
            for img in images:
                src = img["src"]
                if "logo.png" not in src and "topbutton.png" not in src:  # 불필요한 이미지 제거
                    review_images.append(src)

            # 남은 부분을 텍스트로 저장 (이미지 제외)
            text_parts = []
            for element in td.contents:
                if element.name == "br":
                    text_parts.append("\n")  # 줄바꿈 추가
                elif element.name is None:  # 텍스트 노드
                    text_parts.append(element.strip())

            review_content = "".join(text_parts).strip()  # 모든 텍스트 합치기


    return {
        "bbsidx": bbsidx,
        "title": title,
        "review_reg_date": review_reg_date,
        "review_email": review_email,
        "review_content": review_content,
        "review_image": review_images,
    }

# 엑셀 저장 함수
def save_to_excel(data, filename="review_output.xlsx"):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"엑셀 저장 완료: {filename}")

# 실행 메인 함수
def main():
    # 기존 데이터 읽기
    products = read_excel()
    all_reviews = []

    for product in products:
        bbsidx = product.get("product_bbsidx")
        if not bbsidx:
            continue

        print(f"bbsidx {bbsidx} 크롤링 중...")
        review_data = crawl_review(bbsidx)
        if review_data:
            all_reviews.append(review_data)

    # 엑셀 저장
    save_to_excel(all_reviews)

if __name__ == "__main__":
    main()
