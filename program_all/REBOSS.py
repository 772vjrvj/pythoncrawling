import time
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
LOGIN_URL = "https://dome2.oxox.co.kr/"
BASE_URL  = "https://dome2.oxox.co.kr/product/"
HEADERS   = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/114.0.0.0 Safari/537.36")
}

# 주석 처리된 항목은 제외하고, 아래 리스트만 순회합니다.
CATEGORY_LIST = [
    {
        "url": "https://dome2.oxox.co.kr/product/p_list_reboss.php?g=1&page={}",
        "name": "[리보스] 신상품"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list_reboss.php?g=3&page={}",
        "name": "[리보스] 재입고"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list_reboss.php?g=5&page={}",
        "name": "[리보스] 전용상품"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list_reboss.php?g=6&page={}",
        "name": "[리보스] 사은품관"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list_detail.php?g=2&page={}",
        "name": "[리보스] 상세수정"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list_reboss.php?g=8&page={}",
        "name": "[리보스] 권장 소비자 품목"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list_reboss.php?g=4&page={}",
        "name": "전파미인증 판매금지"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list_reboss.php?g=7&page={}",
        "name": "품절상품관 (확인해주세요)"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=37&page={}",
        "name": "할인특가(한정수량)"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/13&page={}",
        "name": "남성명품관 > 남성명품관"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/11&page={}",
        "name": "남성명품관 > 리얼돌"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/02&page={}",
        "name": "남성명품관 > 남성홀컵"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/12&page={}",
        "name": "남성명품관 > 자동핸드잡(홀)"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/03&page={}",
        "name": "남성명품관 > 대형 바디 자동"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/04&page={}",
        "name": "남성명품관 > 대형 바디 수동"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/05&page={}",
        "name": "남성명품관 > 중형 바디"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/06&page={}",
        "name": "남성명품관 > 핸드잡 소형"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/07&page={}",
        "name": "남성명품관 > 특수 점보 실리콘"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/08&page={}",
        "name": "남성명품관 > 진동 강화링"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/09&page={}",
        "name": "남성명품관 > 일반 보조링"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=01/10&page={}",
        "name": "남성명품관 > 확장기"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=02/01&page={}",
        "name": "여성용품 코너 > 여성명품관"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=02/02&page={}",
        "name": "여성용품 코너 > 페어리 진동기"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=02/03&page={}",
        "name": "여성용품 코너 > 회전형 진동기"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=02/04&page={}",
        "name": "여성용품 코너 > 일체형 진동기"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=02/05&page={}",
        "name": "여성용품 코너 > 분리형 진동기"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=02/06&page={}",
        "name": "여성용품 코너 > 리얼 진동먹쇠"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=02/07&page={}",
        "name": "여성용품 코너 > 리얼 수동먹쇠"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=02/08&page={}",
        "name": "여성용품 코너 > 대물먹쇠/전시물"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=03/01&page={}",
        "name": "애널용품 코너 > 진동애널"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=03/02&page={}",
        "name": "여성용품 코너 > 수동애널"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=04/01&page={}",
        "name": "국산콘돔 > 국산콘돔"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=04/02&page={}",
        "name": "국산콘돔 > 수입/초박형 콘돔"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=05/01&page={}",
        "name": "맛사지젤 / 향수 코너 > 기능 마사지젤"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=05/02&page={}",
        "name": "맛사지젤 / 향수 코너 > 고급 마사지젤"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=05/03&page={}",
        "name": "맛사지젤 / 향수 코너 > 페로몬 향수"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=05/04&page={}",
        "name": "맛사지젤 / 향수 코너 > 세정제/기타"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=06/01&page={}",
        "name": "섹시속옷 / 란제리 코너 > JSP 섹시란제리"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=06/02&page={}",
        "name": "섹시속옷 / 란제리 코너 > 여성섹시팬티"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=06/03&page={}",
        "name": "섹시속옷 / 란제리 코너 > 남성섹시팬티"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=06/04&page={}",
        "name": "섹시속옷 / 란제리 코너 > 섹시 망사/스타킹"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=06/05&page={}",
        "name": "섹시속옷 / 란제리 코너 > 섹시란제리"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=06/06&page={}",
        "name": "섹시속옷 / 란제리 코너 >  섹시코스프레"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=06/07&page={}",
        "name": "섹시속옷 / 란제리 코너 > 섹시가터벨트"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=07/01&page={}",
        "name": "SM용품 코너 > 목줄/수갑/족갑"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=07/02&page={}",
        "name": "SM용품 코너 > 자갈/바디구속"
    },
    {
        "url": "https://dome2.oxox.co.kr/product/p_list.php?c=07/03&page={}",
        "name": "SM용품 코너 > 채직/가면/안대"
    }
]

# ──────────────────────────────────────────────
# 1) 셀레니움 로그인 → 쿠키 추출
# ──────────────────────────────────────────────
def login_and_get_cookies(user_id: str, password: str) -> dict:
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    # opts.add_argument("--headless")

    driver = webdriver.Chrome(options=opts)
    driver.get(LOGIN_URL)

    driver.find_element(By.NAME, "id").send_keys(user_id)
    driver.find_element(By.NAME, "passwd").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='image']").click()
    time.sleep(3)  # 로그인 완료 대기

    cookies = driver.get_cookies()
    driver.quit()
    return {c["name"]: c["value"] for c in cookies}

# ──────────────────────────────────────────────
# 2) 리스트 페이지 → 상품 상세 링크 수집 (페이지: 데이터 없을 때까지 while)
# ──────────────────────────────────────────────
def collect_product_links(list_url_tmpl: str, cookies: dict) -> list:
    collected = set()
    page = 1
    while True:
        url = list_url_tmpl.format(page)
        print(f"📄 리스트 요청: {url}")
        r = requests.get(url, headers=HEADERS, cookies=cookies, timeout=30)
        if r.status_code != 200:
            print(f"❌ 리스트 요청 실패: {r.status_code} (page={page}) → 종료")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        page_added = 0

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "p_view.php" in href:
                full = href if href.startswith("http") else BASE_URL + href.lstrip("/")
                if full not in collected:
                    collected.add(full)
                    page_added += 1

        if page_added == 0:
            print(f"⚠️ 페이지 {page}에서 상품 없음 → 리스트 수집 종료")
            break

        print(f"✅ 페이지 {page}: {page_added}개 추가 (누적 {len(collected)})")
        page += 1
        time.sleep(0.4)  # 과도한 호출 방지 (선택)
    return sorted(collected)

# ──────────────────────────────────────────────
# 3) 상세 페이지 파싱
#    - 썸네일: style="border:1px solid #C2C2C2" 의 img src
#    - 상세이미지: src가 http://rebossshop.cafe24.com/web/ 로 시작
#    - 상품명: <font style="font: bold 18px ...">
#    - 가격: 첫 번째 <font color="#008bcc">의 텍스트 숫자만
#            없으면 "입고예정"이 들어간 td의 텍스트 전체
# ──────────────────────────────────────────────
def parse_product_detail(detail_url: str, cookies: dict) -> dict:
    r = requests.get(detail_url, headers=HEADERS, cookies=cookies, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"상세 요청 실패({r.status_code})")

    soup = BeautifulSoup(r.text, "html.parser")

    # 썸네일
    thumb_tag = soup.find("img", style=lambda v: v and "border:1px solid #C2C2C2" in v)
    thumbnail = thumb_tag["src"] if thumb_tag else ""

    # 상세 이미지 (web/ 로 시작)
    detail_imgs = [
        img["src"] for img in soup.find_all("img", src=True)
        if img["src"].startswith("http://rebossshop.cafe24.com/web/")
    ]

    # 상품명
    name_tag = soup.find("font", style=lambda v: v and "bold 18px" in v)
    product_name = name_tag.get_text(strip=True) if name_tag else ""

    # 가격
    price = ""
    price_tag = soup.find("font", attrs={"color": "#008bcc"})
    if price_tag:
        price_text = price_tag.get_text(strip=True)
        price = re.sub(r"[^0-9]", "", price_text)  # 숫자만
    else:
        incoming_td = soup.find("td", string=lambda text: text and "입고예정" in text)
        if incoming_td:
            price = incoming_td.get_text(strip=True)

    return {
        "url": detail_url,
        "상품명": product_name,
        "가격": price,
        "썸네일": thumbnail,
        "상세이미지": ", ".join(detail_imgs)
    }

# ──────────────────────────────────────────────
# 4) 메인: 카테고리 순회 → 엑셀 저장(시트별)
# ──────────────────────────────────────────────
def main():
    # 1) 로그인
    cookies = login_and_get_cookies("gokioka", "q1w2e3r4")
    print("🔐 로그인/쿠키 세팅 완료")

    # 2) 카테고리별 수집 및 파싱
    excel_path = "dome_products.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for cat in CATEGORY_LIST:
            list_url = cat["url"]
            cat_name = cat["name"]
            print(f"\n====== 🚩 카테고리 시작: {cat_name} ======")

            links = collect_product_links(list_url, cookies)
            print(f"🔗 {cat_name}: 총 {len(links)}개 상세 링크 수집")

            results = []
            total = len(links)
            for idx, link in enumerate(links, start=1):
                try:
                    item = parse_product_detail(link, cookies)
                    # 진행 로그
                    print(f"[{idx}/{total}] ✅ {item.get('상품명','')} (URL: {link})")
                    # 카테고리 이름 컬럼 추가
                    item["카테고리"] = cat_name
                    results.append(item)
                    time.sleep(0.3)  # 과한 호출 방지
                except Exception as e:
                    print(f"[{idx}/{total}] ❌ 에러 ({link}): {e}")

            # 3) 엑셀 시트 저장 (시트명 31자 제한 및 특수문자 제거)
            df = pd.DataFrame(results)
            sheet_name = re.sub(r'[\\/*?:\[\]]', '', cat_name)[:31]
            if df.empty:
                # 비어 있어도 시트는 만들어 둠 (필요 시 제거 가능)
                pd.DataFrame(columns=["url","상품명","가격","썸네일","상세이미지","카테고리"]).to_excel(
                    writer, index=False, sheet_name=sheet_name
                )
            else:
                df.to_excel(writer, index=False, sheet_name=sheet_name)

            print(f"📁 [{cat_name}] 시트 저장 완료 (행: {len(df)})")

    print(f"\n✅ 모든 카테고리 저장 완료 → {excel_path}")

if __name__ == "__main__":
    main()