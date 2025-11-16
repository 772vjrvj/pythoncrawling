# -*- coding: utf-8 -*-
"""
11번가 통합 크롤러

1) Selenium으로 로그인
2) 쿠키를 requests.Session으로 이식
3) /my11st/order/BuyManager.tmall?method=getCancelRequestListAjax 호출 (page 1~5)
4) 응답 HTML에서 주문번호 / dlvNo 추출
5) dlvNo로 trace.tmall 들어가서 택배사 / 송장번호 추출
6) {주문고유코드, 택배사, 송장번호} 리스트 출력
"""

import re
import time
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# 설정
# =========================
LOGIN_ID = "ooos1103"
LOGIN_PW = "oktech431@@"
LOGIN_URL = "https://login.11st.co.kr/auth/v2/login"

# 취소요청 리스트 AJAX 엔드포인트
CANCEL_LIST_URL = "https://buy.11st.co.kr/my11st/order/BuyManager.tmall"

# 배송조회 엔드포인트
TRACE_URL_BASE = "https://buy.11st.co.kr/delivery/trace.tmall?dlvNo={dlv_no}"

# 조회 기간 (JS 코드에서 쓰던 값 그대로)
DATE_FROM = "20250915"
DATE_TO = "20251114"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0.0.0 Safari/537.36"
)


# =========================
# 1) Selenium 로그인
# =========================
def login_11st_and_get_cookies():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={UA}")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    driver.get(LOGIN_URL)

    try:
        # ID 입력
        id_input = wait.until(EC.presence_of_element_located((By.ID, "memId")))
        id_input.clear()
        id_input.send_keys(LOGIN_ID)

        # PW 입력
        pw_input = wait.until(EC.presence_of_element_located((By.ID, "memPwd")))
        pw_input.clear()
        pw_input.send_keys(LOGIN_PW)

        # 로그인 버튼
        login_btn = wait.until(EC.element_to_be_clickable((By.ID, "loginButton")))
        login_btn.click()

        # 공용 PC 팝업 → "다음에 할게요"
        try:
            close_btn = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a[modal-auto-action='close']")
                )
            )
            close_btn.click()
        except Exception:
            print("[INFO] 공용 PC 팝업 없음 또는 자동으로 넘어감")

        # 세션 안정화 약간 대기
        time.sleep(2)

        cookies = driver.get_cookies()
        print(f"[INFO] 로그인 후 쿠키 개수: {len(cookies)}")

        return cookies, driver

    except Exception as e:
        print("[ERROR] 로그인 실패:", str(e))
        driver.quit()
        raise


# =========================
# 2) Selenium 쿠키 → requests.Session
# =========================
def build_session_from_cookies(cookies):
    sess = requests.Session()

    sess.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    })

    for c in cookies:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain", "").lstrip(".")
        path = c.get("path", "/")
        sess.cookies.set(name, value, domain=domain, path=path)

    return sess


# =========================
# 3) 취소요청 리스트 AJAX 호출
# =========================
def get_cancel_request_list_html(sess, page_number,
                                 date_from=DATE_FROM, date_to=DATE_TO,
                                 shPrdNm="", pageNumberPendingFail=1, pageNumberPendingDone=1):
    params = {
        "method": "getCancelRequestListAjax",
        "type": "orderList2nd",
        "pageNumber": page_number,
        "rows": 10,
        "shDateFrom": date_from,
        "shDateTo": date_to,
        "ver": "02",
        "shPrdNm": shPrdNm,
        "shOrdprdStat": "",
        "pageNumberPendingFail": pageNumberPendingFail,
        "pageNumberPendingDone": pageNumberPendingDone
    }

    # JS에서 referer는 리스트 페이지 (대충 맞춰줌)
    sess.headers["Referer"] = (
        "https://buy.11st.co.kr/my11st/order/OrderList.tmall"
    )

    print(f"[INFO] AJAX 호출: pageNumber={page_number}")
    resp = sess.get(CANCEL_LIST_URL, params=params)
    resp.raise_for_status()
    return resp.text  # HTML 조각


# =========================
# 4) AJAX 응답 HTML → (주문번호, dlvNo) 리스트
# =========================
def parse_cancel_list_for_pairs(html):
    """
    취소요청 리스트 HTML 조각에서
    (주문고유코드, dlvNo) 튜플 목록 추출

    - 주문번호:
        td.first 안의 a.bt_detailview 의 href
        javascript:goOrderDetail('20251109012348664');
        또는 "(20251109012348664)" 텍스트

    - dlvNo:
        td.td-center 안의
        a[href^="javascript:goDeliveryTracking('2650634166', ..."]
    """
    soup = BeautifulSoup(html, "html.parser")

    pairs = []
    current_order_no = None

    # 조각이라 form/table이 없을 수도 있어서 그냥 tr 전체 순회
    for tr in soup.find_all("tr"):
        # (1) 주문번호 갱신 (td.first)
        td_first = tr.find("td", class_="first")
        if td_first:
            a = td_first.find("a", class_="bt_detailview")
            order_no = None

            if a:
                href = a.get("href", "")
                m = re.search(r"goOrderDetail\('(\d+)'\)", href)
                if m:
                    order_no = m.group(1)

            if not order_no:
                text = td_first.get_text(" ", strip=True)
                m = re.search(r"\((\d+)\)", text)
                if m:
                    order_no = m.group(1)

            if order_no:
                current_order_no = order_no

        # (2) 배송조회 버튼에서 dlvNo 추출
        a_dlv = tr.find("a", href=re.compile(r"goDeliveryTracking\("))
        if a_dlv and current_order_no:
            href = a_dlv.get("href", "")
            m = re.search(r"goDeliveryTracking\('(\d+)'", href)
            if m:
                dlv_no = m.group(1)
                pairs.append((current_order_no, dlv_no))

    return pairs


# =========================
# 5) 배송조회 페이지 파싱 (택배사 / 송장번호)
# =========================
def parse_trace_page(html):
    """
    배송조회 페이지 HTML:

    <div class="delivery_info">
        <dl>
            <div class="field">
                <dt>택배사</dt>
                <dd>천일택배 <span class="num">031-462-1001</span></dd>
            </div>
            <div class="field">
                <dt>송장번호</dt>
                <dd>87564143273</dd>
            </div>
        </dl>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    info = soup.find("div", class_="delivery_info")
    if not info:
        print("[WARN] delivery_info 블럭을 찾지 못했습니다.")
        return {"택배사": None, "송장번호": None}

    result = {"택배사": None, "송장번호": None}

    for field in info.find_all("div", class_="field"):
        dt = field.find("dt")
        dd = field.find("dd")
        if not dt or not dd:
            continue

        title = dt.get_text(strip=True)
        val_text = dd.get_text(strip=True)

        if title == "택배사":
            # dd: "천일택배 031-462-1001" → 택배사만
            if dd.contents:
                result["택배사"] = str(dd.contents[0]).strip()
            else:
                result["택배사"] = val_text

        elif title == "송장번호":
            result["송장번호"] = val_text.strip()

    return result


# =========================
# 메인 실행
# =========================
def main():
    cookies, driver = login_11st_and_get_cookies()

    try:
        sess = build_session_from_cookies(cookies)

        all_rows = []

        # pageNumber = 1 ~ 5
        for page_number in range(1, 6):
            html = get_cancel_request_list_html(sess, page_number)
            pairs = parse_cancel_list_for_pairs(html)

            print(f"[INFO] pageNumber={page_number} → (주문번호, dlvNo) {len(pairs)}건")

            for order_no, dlv_no in pairs:
                trace_url = TRACE_URL_BASE.format(dlv_no=dlv_no)
                print(f"  - 배송조회: 주문고유코드={order_no}, dlvNo={dlv_no}")

                r = sess.get(trace_url)
                r.raise_for_status()

                info = parse_trace_page(r.text)

                row = {
                    "주문고유코드": order_no,
                    "택배사": info.get("택배사"),
                    "송장번호": info.get("송장번호"),
                }
                all_rows.append(row)

                # 서버 부하 줄이기
                time.sleep(0.5)

            time.sleep(1)

        # 최종 출력
        print("\n=========== 최종 결과 ===========")
        for idx, row in enumerate(all_rows, start=1):
            print(
                f"{idx}. 주문고유코드={row['주문고유코드']}, "
                f"택배사={row['택배사']}, "
                f"송장번호={row['송장번호']}"
            )

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
