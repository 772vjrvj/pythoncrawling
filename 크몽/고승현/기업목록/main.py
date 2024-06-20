import requests
from bs4 import BeautifulSoup
import pandas as pd

index = 0

def fetch_page_content(page):
    base_url = "https://www.ifa-berlin.com/exhibitors?&page={page}&searchgroup=00000001-exhibitors"
    response = requests.get(base_url.format(page=page))
    if response.status_code == 200:
        return response.content
    else:
        return None

def fetch_company_details(company_id):
    url = f"https://www.ifa-berlin.com/exhibitors/{company_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        return None

def parse_exhibitors(content):
    soup = BeautifulSoup(content, 'html.parser')
    items = soup.select(".m-exhibitors-list__items__item.js-librarylink-entry")

    result = []

    for item in items:
        # 기업 ID 추출
        company_id = None
        a_tag = item.select_one(".m-exhibitors-list__items__item__header__title__link.js-librarylink-entry")
        if a_tag and 'href' in a_tag.attrs:
            company_url = a_tag['href']
            company_id = company_url.split("exhibitors/")[1]

        # 기업 이름 추출
        company_name = a_tag.text.strip() if a_tag else ''

        # 카테고리 추출
        category_tag = item.select_one(".m-exhibitors-list__items__item__header__label")
        category = category_tag.text.replace("IFA ", "").strip() if category_tag else ''

        # GLOBAL 여부 확인
        global_tag = item.select_one("div.m-exhibitors-list__items__item__logo.global-markets")
        global_status = "Y" if global_tag is not None else "N"

        # 기업 세부 정보 추출
        company_details_content = fetch_company_details(company_id)
        company_info, company_address, email, youtube, instagram, tiktok, facebook = "", "", "", "", "", "", ""

        if company_details_content:
            company_soup = BeautifulSoup(company_details_content, 'html.parser')

            # 기업정보 추출
            info_tag = company_soup.select_one(".m-exhibitor-entry__item__body__description")
            if info_tag:
                info_meta = info_tag.select_one(".m-exhibitor-entry__item__body__description__meta")
                if info_meta and "Brand info:" in info_meta.get_text():
                    company_info = info_tag.get_text().replace("Brand info:", "").strip()

                # 기업 주소 추출
                address_tag = info_tag.select_one(".m-exhibitor-entry__item__body__description__address")
                if address_tag:
                    company_address = address_tag.get_text().replace('\r', '').replace('\n', '').replace('\t', '').strip()
                else:
                    company_address = ""

                # 소셜 미디어 추출
                social_tags = company_soup.select(".m-exhibitor-entry__item__body__social__item")
                for tag in social_tags:
                    text = tag.text.strip()
                    if "youtube" in text.lower():
                        youtube = text
                    elif "instagram" in text.lower():
                        instagram = text
                    elif "facebook" in text.lower():
                        facebook = text
                    elif "tiktok" in text.lower():
                        tiktok = text
                    elif "@" in text:
                        email = text

        data = {
            "기업ID": company_id,
            "기업이름": company_name,
            "카테고리": category,
            "GLOBAL여부": global_status,
            "기업정보": company_info,
            "기업주소": company_address,
            "이메일": email,
            "유튜브": youtube,
            "인스타그램": instagram,
            "틱톡": tiktok,
            "페이스북": facebook
        }


        print(f"index : {++index},  data : {data}")
        # 결과 리스트에 추가
        result.append(data)



    return result

def main():
    all_exhibitors = []

    for page in range(1, 2):  # 테스트를 위해 페이지를 2개로 제한
        print(f"page : {page}")
        content = fetch_page_content(page)
        if content:
            exhibitors = parse_exhibitors(content)
            all_exhibitors.extend(exhibitors)

    # 결과 출력
    # 엑셀로 저장
    df = pd.DataFrame(all_exhibitors)
    df.to_excel('exhibitors.xlsx', index=False)

if __name__ == "__main__":
    main()
