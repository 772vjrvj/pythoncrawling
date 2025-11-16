# -*- coding: utf-8 -*-
"""
SSG 로그인(Selenium) 후 쿠키를 requests로 넘겨서
https://pay.ssg.com/myssg/orderInfo.ssg?page=1~5 를 크롤링하는 예제

- Selenium으로 로그인 (팝업 로그인)
- 로그인 완료 후 driver.get_cookies()를 requests.Session()에 이식
- 각 페이지 HTML을 BeautifulSoup으로 파싱
- name="divOrordUnit" 를 돌면서
    - 숨겨진 input[name="orordNo"] → "주문고유코드"
    - .codr_dvstate_bg .tx_state em span.notranslate → "택배사"
    - 같은 em 안의 텍스트 중 "/ 뒤 숫자" → "송장번호"
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
SSG_MAIN_URL = "https://www.ssg.com/"

LOGIN_ID = "ooos1103"
LOGIN_PW = "oktech431!@"

# pay.ssg.com 주문내역 URL (page만 바꿔서 사용)
ORDER_URL_TEMPLATE = (
    "https://pay.ssg.com/myssg/orderInfo.ssg"
    "?searchType=6&searchCheckBox=&page={page}"
    "&searchInfloSiteNo=&searchStartDt=&searchEndDt=&searchKeyword="
)

# 브라우저/requests 공통 User-Agent
COMMON_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0.0.0 Safari/537.36"
)


def selenium_login_and_get_cookies():
    """
    Selenium으로 SSG 로그인 후,
    driver.get_cookies() 리스트를 반환
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={COMMON_UA}")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        # 1. 메인 페이지 접속
        driver.get(SSG_MAIN_URL)

        # 2. GNB 로그인 버튼 클릭 (id="loginBtn")
        gnb_login_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        gnb_login_btn.click()

        # 3. 팝업창으로 전환
        main_handle = driver.current_window_handle
        wait.until(lambda d: len(d.window_handles) > 1)

        login_handle = None
        for handle in driver.window_handles:
            if handle != main_handle:
                login_handle = handle
                break

        if login_handle is None:
            raise Exception("로그인 팝업 창을 찾지 못했습니다.")

        driver.switch_to.window(login_handle)

        # 4. 로그인 폼 입력
        # <input type="text" name="mbrLoginId" id="mem_id" ...>
        # <input type="password" name="password" id="mem_pw" ...>
        id_input = wait.until(EC.presence_of_element_located((By.ID, "mem_id")))
        pw_input = wait.until(EC.presence_of_element_located((By.ID, "mem_pw")))

        id_input.clear()
        id_input.send_keys(LOGIN_ID)

        pw_input.clear()
        pw_input.send_keys(LOGIN_PW)

        # 5. 팝업 내 로그인 버튼 클릭
        # <button ... id="loginBtn"><span>로그인</span></button>
        login_btn_popup = wait.until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        login_btn_popup.click()

        # 6. 로그인 완료 기다리기
        #    - 사이트마다 다르지만, 보통 팝업이 닫히거나
        #      특정 요소가 뜨는 방식으로 확인.
        #    여기서는 "창이 1개만 남을 때"까지 대기
        WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) == 1)

        driver.switch_to.window(main_handle)

        # 혹시 세션/쿠키 전파까지 딜레이 있을 수 있어서 잠깐 대기
        time.sleep(2)

        # 7. 쿠키 가져오기
        cookies = driver.get_cookies()  # [{name, value, domain, path, ...}, ...]

        print(f"[INFO] Selenium 쿠키 개수: {len(cookies)}")
        return cookies, driver

    except Exception as e:
        # 에러 시 브라우저를 바로 닫지 않고 확인하고 싶으면 여기서 처리
        print("[ERROR] 로그인 중 오류:", str(e))
        driver.quit()
        raise


def build_requests_session_from_cookies(cookies):
    """
    Selenium 쿠키 리스트를 받아서
    requests.Session()에 주입한 후 반환
    """
    sess = requests.Session()

    # 기본 헤더
    sess.headers.update({
        "User-Agent": COMMON_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })

    # 쿠키 이식
    for c in cookies:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain", "")
        path = c.get("path", "/")

        # domain이 ".ssg.com" 형태면 "ssg.com"으로 정리
        if domain.startswith("."):
            domain = domain[1:]

        # pay.ssg.com에서만 필요한 쿠키만 필터링하고 싶으면 여기서 조건 걸어도 됨
        # if not domain.endswith("ssg.com"):
        #     continue

        sess.cookies.set(name, value, domain=domain, path=path)

    return sess


def parse_order_page(html):
    """
    주문내역 페이지 HTML을 받아서
    name="divOrordUnit" 단위로 파싱, 결과 리스트 반환

    반환 형식:
    [
        {
            "주문고유코드": "202511068C18D0",
            "택배사": "천일택배",
            "송장번호": "81469114484",
        },
        ...
    ]
    """
    soup = BeautifulSoup(html, "html.parser")

    results = []

    # name="divOrordUnit"인 요소들 (보통 <div name="divOrordUnit">일 가능성 높음)
    order_units = soup.find_all(attrs={"name": "divOrordUnit"})

    for unit in order_units:
        # === 주문고유코드 ===
        orord_no = None
        orord_input = unit.find("input", attrs={"name": "orordNo"})
        if orord_input and orord_input.has_attr("value"):
            orord_no = orord_input["value"].strip()

        # === 택배사 / 송장번호 ===
        carrier_name = None
        invoice_no = None

        dvstate = unit.find("div", class_="codr_dvstate_bg")
        if dvstate:
            tx_state = dvstate.find("div", class_="tx_state")
            if tx_state:
                em = tx_state.find("em")
                if em:
                    # 택배사: <span class="notranslate">천일택배</span>
                    span_carrier = em.find("span", class_="notranslate")
                    if span_carrier:
                        carrier_name = span_carrier.get_text(strip=True)

                    # 송장번호: em 안 텍스트 중 "/ 뒤의 숫자"
                    em_text = "".join(em.stripped_strings)  # "천일택배/81469114484" 형태 예상
                    parts = em_text.split("/")
                    if len(parts) >= 2:
                        after_slash = parts[1]
                        m = re.search(r"(\d+)", after_slash)
                        if m:
                            invoice_no = m.group(1)

        results.append({
            "주문고유코드": orord_no,
            "택배사": carrier_name,
            "송장번호": invoice_no,
        })

    return results


def main():
    # 1) Selenium으로 로그인하고 쿠키 획득
    cookies, driver = selenium_login_and_get_cookies()

    try:
        # 2) requests.Session으로 쿠키 옮기기
        sess = build_requests_session_from_cookies(cookies)

        all_data = []

        # 3) page=1~5 순회
        for page in range(1, 6):
            url = ORDER_URL_TEMPLATE.format(page=page)
            # referer는 상황에 맞게 조절 (여기선 예시로 viewType=Ssg 페이지)
            sess.headers["Referer"] = "https://pay.ssg.com/myssg/orderInfo.ssg?viewType=Ssg"

            print(f"[INFO] 요청: {url}")
            resp = sess.get(url)
            resp.raise_for_status()

            page_data = parse_order_page(resp.text)
            print(f"[INFO] page={page} 에서 {len(page_data)}건 추출")

            all_data.extend(page_data)

            # 서버 부담 줄이기 위해 약간의 딜레이
            time.sleep(1)

        # 4) 결과 확인 (여기서는 콘솔 출력)
        print("\n=== 최종 결과 ===")
        for idx, row in enumerate(all_data, start=1):
            print(f"{idx}. 주문고유코드={row['주문고유코드']}, "
                  f"택배사={row['택배사']}, 송장번호={row['송장번호']}")

        # 필요하면 여기서 CSV로 저장도 가능
        # import csv
        # with open("ssg_orders.csv", "w", newline="", encoding="utf-8-sig") as f:
        #     writer = csv.DictWriter(f, fieldnames=["주문고유코드", "택배사", "송장번호"])
        #     writer.writeheader()
        #     writer.writerows(all_data)

    finally:
        # Selenium 브라우저 종료
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
