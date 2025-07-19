import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import json
from urllib.parse import urlparse
import shutil
import os

# 공통 헤더
common_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

category_urls = {
    "홈케어/방문": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=24&ctg=1",
    "왁싱": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=3",
    "1인샵": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=2",
    "24시간": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=11",
    "사우나/스파": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=8",
    "수면가능": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=5",
    "여성환영": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=12",
    "타이마사지": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=14",
    "감성마사지": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=19",
    "슈얼마사지": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=18",
    "로미로미": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=17",
    "스웨디시": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=16",
    "딥티슈": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=26",
    "스크럽": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=27",
    "두리코스": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=28",
    "호텔식마사지": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=31",
    "아로마마사지": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=32",
    "림프관리": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&idx=&ctg=3&sfl=wr_7&sfl2=&sca3=&sca2=33"
}

def fetch_wr_id_list_from_html(html, category_name):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".listRow")
    tab_items = []

    for row in rows:
        a_tag = row.select_one(".subject a[href*='wr_id']")
        span = row.select_one(".subject span")
        if a_tag and span:
            match = re.search(r"wr_id=(\d+)", a_tag['href'])
            if match:
                wr_id = match.group(1)
                title = span.get_text(strip=True)
                tab_items.append({
                    "SHOP_ID": wr_id,
                    "TITLE": title,
                    "MAIN_CATEGORY": category_name
                })

    return tab_items


def fetch_all_wr_id_items():
    print("🔍 카테고리별 wr_id 수집 시작...")
    result_list = []

    for category, base_url in category_urls.items():
        tab = 1
        prev_count = -1
        final_items = []

        while True:
            if "tab=" in base_url:
                url = re.sub(r'tab=\d+', f'tab={tab}', base_url)
            else:
                url = base_url + f"&tab={tab}"

            print(f'url : {url}')

            try:
                headers = {
                    **common_headers,
                    "Referer": url
                }
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"[{category}][tab={tab}] 상태코드 오류: {response.status_code}")
                    break

                html = response.text
                items = fetch_wr_id_list_from_html(html, category)
                current_count = len(items)

                if current_count == 0:
                    print(f"[{category}][tab={tab}] 데이터 없음, 종료")
                    break

                print(f"[{category}][tab={tab}] 수집된 항목 수: {current_count}")

                # 이전과 같으면 최종 데이터로 판단하고 종료
                if current_count == prev_count:
                    final_items = items
                    print(f"[{category}][tab={tab}] 이전과 항목 수 같음 → 종료")
                    break

                prev_count = current_count
                tab += 1
                time.sleep(0.5)

            except Exception as e:
                print(f"[{category}][tab={tab}] 에러 발생: {e}")
                break

        result_list.extend(final_items)
        print(f"[{category}] ✅ 최종 저장 항목 수: {len(final_items)}, 전체 항목수 : {len(result_list)}")

    print(f"\n✅ 전체 최종 수집 개수: {len(result_list)}\n")
    return result_list

def fetch_review_count(wr_id: str) -> int:
    url = "https://vipgunma.com/bbs/rev.php"
    headers = {
        **common_headers,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://vipgunma.com",
        "Referer": f"https://vipgunma.com/bbs/board.php?bo_table=gm_1&wr_id={wr_id}"
    }
    data = {
        "request": "requestRev",
        "page": 1,
        "wr_id": wr_id
    }

    try:
        res = requests.post(url, headers=headers, data=data)
        if res.status_code == 200:
            json_data = res.json()
            if json_data.get("result_code") == "success":
                return json_data.get("result_data", {}).get("total", 0)
    except Exception as e:
        print(f"[{wr_id}] 리뷰 수 요청 실패: {e}")

    return 0

def fetch_detail(shop_id: str, program_title: str, category: str) -> dict:
    url = f"https://vipgunma.com/bbs/board.php?bo_table=gm_1&wr_id={shop_id}"
    res = requests.get(url, headers=common_headers)

    if res.status_code != 200:
        print(f"[{shop_id}] 요청 실패: {res.status_code}")
        return {}

    item = {
        "SHOP_ID": shop_id,
        "TITLE": program_title,
        "MAIN_CATEGORY": category,
    }

    soup = BeautifulSoup(res.text, "html.parser")

    # 상호명
    store = soup.select_one(".storeName")
    item["SHOP_NAME"] = store.text.strip() if store else ""

    # 조회수
    views = soup.select_one(".extra > div > span")
    item["VIEW_COUNT"] = views.text.strip().replace(",", "") if views else ""

    # 리뷰수
    item["REVIEW_COUNT"] = fetch_review_count(shop_id)

    # 샵특징
    shop_type = soup.select_one(".shopType")
    item["FEATURES"] = shop_type.text.strip() if shop_type else ""

    # 상세정보
    detail_rows = soup.select(".content .detailRow")
    for row in detail_rows:
        head = row.select_one(".detailHead")
        con = row.select_one(".detailCon")
        if not head or not con:
            continue
        key = head.text.strip()
        if key == "오시는길":
            address_divs = con.select("div")
            item["지번주소"] = address_divs[0].text.strip() if len(address_divs) > 0 else ""
            item["도로명주소"] = address_divs[1].text.strip() if len(address_divs) > 1 else ""
        else:
            item[key] = con.text.strip()

        # 프로그램 정보

    course_info_tag = soup.select_one(".detailCon.programCon > div")
    course_info = course_info_tag.get_text(strip=True).replace('\xa0', ' ') if course_info_tag else ""
    item["COURSE_INFO"] = course_info


    programs = []

    heads = soup.select(".programWrap .programHead")
    for head in heads:
        idx = head.get("idx")
        title = re.sub(r'\ufeff', '', head.get_text(strip=True))

        content = soup.select_one(f".programContents[idx='{idx}']")
        if not content:
            continue

        rows = content.select(".itemRow")
        for row in rows:
            duration_tag = row.select_one(".line1 .infoTxt")
            org_price_tag = row.select(".line1 .diP")[-1] if row.select(".line1 .diP") else None
            dis_price_tag = row.select(".line2 .prc")[-1] if row.select(".line2 .prc") else None
            category_tag = row.select_one(".line2 .subTxt")

            # 값 추출
            duration = duration_tag.get_text(strip=True) if duration_tag else ""
            category_text = category_tag.get_text(strip=True) if category_tag else ""

            try:
                original_price = int(org_price_tag.get_text(strip=True).replace(",", "")) if org_price_tag else None
            except ValueError:
                original_price = ''

            try:
                discount_price = int(dis_price_tag.get_text(strip=True).replace(",", "")) if dis_price_tag else None
            except ValueError:
                discount_price = ''

            # JSON 객체 구성
            program = {
                "title": title,
                "duration": duration,
                "categories": category_text,
                "original_price": original_price,
                "discount_price": discount_price
            }

            programs.append(program)

    # 문자열로 저장 (엑셀에도 들어갈 수 있게 문자열 처리)
    item["PROGRAMS"] = json.dumps(programs, ensure_ascii=False)

    hash_tag_spans = soup.select(".hashTag span")
    hash_tags = ", ".join([span.get_text(strip=True) for span in hash_tag_spans]) if hash_tag_spans else ""
    item["HASHTAG"] = hash_tags

    event_tag = soup.select_one(".detailRow.eventRow .detailCon")
    event_text = event_tag.get_text("\n", strip=True).replace('\xa0', ' ') if event_tag else ""
    item["event"] = event_text

    image_data = []

    # sliderGal.slider-for 안에 .si > img 추출
    slider_imgs = soup.select(".sliderGal.slider-for .si img")

    for idx, img in enumerate(slider_imgs, 1):
        src = img.get("src")
        alt = img.get("alt", "")
        if not src:
            continue

        try:
            parsed_url = urlparse(src)
            ext = os.path.splitext(parsed_url.path)[-1] or ".jpg"
        except Exception as e:
            print(f"[{shop_id}] 이미지 URL 파싱 실패: {e}")
            continue

        save_dir = os.path.join("images", "vip", shop_id)
        os.makedirs(save_dir, exist_ok=True)

        filename = f"{shop_id}_{idx}{ext}"
        filepath = os.path.join(save_dir, filename)

        try:
            response = requests.get(src, timeout=10)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
            else:
                print(f"[{shop_id}] 이미지 다운로드 실패 ({src})")
        except Exception as e:
            print(f"[{shop_id}] 다운로드 오류: {e}")
            continue

        image_data.append({
            "src": src,
            "alt": alt,
            "filename": filename
        })

    item["images"] = image_data

    return item

def main():
    wr_items = fetch_all_wr_id_items()
    results = []

    for i, shop in enumerate(wr_items, 1):
        shop_id = shop["SHOP_ID"]
        title = shop["TITLE"]
        category = shop["MAIN_CATEGORY"]
        item = fetch_detail(shop_id, title, category)
        if item:
            results.append(item)
            print(f"[{i}/{len(wr_items)}] {shop_id} 수집 완료: {item.get('SHOP_NAME', '')}")
        else:
            print(f"[{i}/{len(wr_items)}] {shop_id} 수집 실패")
        time.sleep(0.5)

    df = pd.DataFrame(results)
    df.to_excel("vipgunma_detail_2025-07-17.xlsx", index=False)
    print("\n✅ 모든 데이터 수집 및 저장 완료: vipgunma_detail_2025-07-17.xlsx")

if __name__ == "__main__":
    main()
