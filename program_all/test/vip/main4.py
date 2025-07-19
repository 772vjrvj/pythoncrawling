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

def fetch_wr_id_list():
    print("🔍 wr_id 수집 시작...")
    result_list = []
    tab = 1
    base_url = "https://vipgunma.com/bbs/loadStore.php?bo_table=gm_1&ctg=3&tab={}"

    headers = {
        **common_headers,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://vipgunma.com/bbs/board.php?bo_table=gm_1&ctg=3&tab=1"
    }

    while True:
        url = base_url.format(tab)
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"[{tab}] 상태코드 오류: {response.status_code}")
            break

        try:
            data = response.json()
        except Exception as e:
            print(f"[{tab}] JSON 파싱 오류: {e}")
            break

        if data.get("result_code") != "success":
            print(f"[{tab}] result_code != success, 종료")
            break

        html = data.get("result_data", {}).get("html", "")
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select(".listRow")

        if not rows:
            print(f"[{tab}] listRow 없음, 종료")
            break

        tab_items = []
        for row in rows:
            a_tag = row.select_one(".subject a[href*='wr_id']")
            span = row.select_one(".subject span")
            if a_tag and span:
                match = re.search(r"wr_id=(\d+)", a_tag['href'])
                if match:
                    wr_id = match.group(1)
                    title = span.get_text(strip=True)
                    tab_items.append({"SHOP_ID": wr_id, "TITLE": title})

        result_list.extend(tab_items)
        print(f"[{tab}] 수집된 항목 수: {len(tab_items)}")
        tab += 1
        time.sleep(0.5)

    print(f"\n✅ 총 수집 개수: {len(result_list)}\n")
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

def fetch_detail(shop_id: str) -> dict:
    url = f"https://vipgunma.com/bbs/board.php?bo_table=gm_1&wr_id={shop_id}"
    res = requests.get(url, headers=common_headers)

    if res.status_code != 200:
        print(f"[{shop_id}] 요청 실패: {res.status_code}")
        return {}

    soup = BeautifulSoup(res.text, "html.parser")
    item = {"SHOP_ID": shop_id}

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
    wr_items = fetch_wr_id_list()
    results = []

    for i, shop in enumerate(wr_items, 1):
        shop_id = shop["SHOP_ID"]
        item = fetch_detail(shop_id)
        if item:
            item["TITLE"] = shop["TITLE"]
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
