from bs4 import BeautifulSoup
import pandas as pd

def extract_data_from_html(html_file):
    """HTML 파일에서 데이터를 추출하여 리스트로 반환."""
    try:
        with open(html_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")
    except FileNotFoundError:
        print(f"파일 '{html_file}'을(를) 찾을 수 없습니다.")
        return []

    result = []
    outer_divs = soup.find_all("div", class_="xrvj5dj xd0jker x1evr45z")

    for outer_div in outer_divs:
        try:
            obj = {"글본문": '', "좋아요": '', "url": '', "날짜": ''}

            inner_div = outer_div.find("div", class_="x1xdureb xkbb5z x13vxnyz")
            if inner_div:
                # 글본문 추출
                text_div = inner_div.find("div", class_="x1a6qonq x6ikm8r x10wlt62 xj0a0fe x126k92a x6prxxf x7r5mf7")
                if text_div:
                    obj["글본문"] = text_div.get_text(strip=True)

                # 좋아요 추출
                like_text_div = inner_div.find("span", class_="x17qophe x10l6tqk x13vifvy")
                if like_text_div:
                    obj["좋아요"] = like_text_div.get_text(strip=True)

            # URL과 날짜 추출
            url_a_tag = outer_div.find("a", class_="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1lku1pv x12rw4y6 xrkepyr x1citr7e x37wo2f")
            if url_a_tag:
                raw_url = url_a_tag.get("href")
                obj["url"] = f"https://www.threads.net{raw_url}" if raw_url else ''

                # 날짜 추출
                time_tag = url_a_tag.find("time")
                if time_tag:
                    obj["날짜"] = time_tag.get("title", '')

            result.append(obj)
        except Exception as e:
            print(f"데이터 추출 중 오류 발생: {e}")

    return result

def save_to_excel(data, output_file):
    """데이터를 엑셀 파일로 저장."""
    try:
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        print(f"데이터가 '{output_file}'에 저장되었습니다.")
    except Exception as e:
        print(f"엑셀 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    html_file = "test.html"
    output_file = "extracted_data.xlsx"

    data = extract_data_from_html(html_file)
    if data:
        save_to_excel(data, output_file)
