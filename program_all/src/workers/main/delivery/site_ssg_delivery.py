# src/workers/main/delivery/site_ssg_delivery.py
# -*- coding: utf-8 -*-

import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By


class SsgDeliveryCrawler:

    def __init__(self, driver, log_func, api_client, selenium_driver):
        self.driver = driver
        self.log = log_func
        self.api = api_client
        self.selenium = selenium_driver

        self.SSG_MAIN_URL = "https://www.ssg.com/"
        # 11번가처럼 base URL만 두고, 쿼리는 params로 보냄
        self.ORDER_URL = "https://pay.ssg.com/myssg/orderInfo.ssg"
        self.UA = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        )

    # ====================================================
    # 내부 유틸: 날짜 포맷 변환 (yyyymmdd -> yyyy-mm-dd)
    # ====================================================
    def _to_yyyy_mm_dd(self, s):
        s = (s or "").strip()
        if len(s) != 8 or not s.isdigit():
            return ""
        return s[:4] + "-" + s[4:6] + "-" + s[6:8]

    # ====================================================
    # 팝업 전환 유틸 (현재 로그인에서는 사용 안 함)
    # ====================================================
    def _switch_to_new_window(self):
        base = self.driver.current_window_handle

        for _ in range(40):
            handles = self.driver.window_handles
            if len(handles) > 1:
                for h in handles:
                    if h != base:
                        self.driver.switch_to.window(h)
                        return
            time.sleep(0.2)

        raise Exception("[SSG] 로그인 팝업창 전환 실패")

    def _wait_window_count(self, count, timeout=15):
        start = time.time()
        while time.time() - start < timeout:
            if len(self.driver.window_handles) == count:
                return
            time.sleep(0.2)
        raise Exception("[SSG] window_handles count 대기 실패")

    # ====================================================
    # 로그인 (popupLogin URL 직접 진입, 창 전환 사용 안 함)
    # ====================================================
    def _login_and_prepare_api_session(self, login_id, login_pw):
        self.log("[SSG] 로그인 시도")

        # popupLogin URL로 바로 이동 (하드코딩)
        login_url = (
            "https://member.ssg.com/member/popup/popupLogin.ssg"
            "?originSite=https%3A//www.ssg.com"
            "&t="
            "&gnb=login"
            "&retURL=https%3A%2F%2Fwww.ssg.com%2F"
        )

        self.driver.get(login_url)
        time.sleep(2)

        # 로그인 폼 요소 찾기
        id_input = self.selenium.wait_element(By.ID, "mem_id", timeout=15)
        pw_input = self.selenium.wait_element(By.ID, "mem_pw", timeout=15)

        if not id_input or not pw_input:
            raise Exception("[SSG] 로그인 입력창(mem_id/mem_pw) 로딩 실패")

        id_input.clear()
        id_input.send_keys(login_id)
        pw_input.clear()
        pw_input.send_keys(login_pw)

        # 로그인 버튼 클릭
        login_btn = self.selenium.wait_element(By.ID, "loginBtn", timeout=15)
        if not login_btn:
            raise Exception("[SSG] 로그인 버튼(loginBtn) 로딩 실패")

        try:
            login_btn.click()
        except Exception as e:
            # element not interactable 대비 JS 클릭
            self.log(f"[SSG] loginBtn.click() 오류, JS 클릭으로 재시도: {e}")
            self.driver.execute_script("arguments[0].click();", login_btn)

        self.log("[SSG] 로그인 버튼 클릭 완료")
        time.sleep(3)  # 로그인 처리 대기

        # 로그인 후 주문내역 페이지로 직접 진입
        try:
            self.driver.get(self.ORDER_URL)
            time.sleep(1.5)
        except Exception as e:
            self.log(f"[SSG] ORDER_URL 진입 중 오류(무시 가능): {e}")

        # Selenium 쿠키를 requests.Session으로 복사
        cookies = self.driver.get_cookies()
        sess = self.api.session

        for c in cookies:
            name = c.get("name")
            value = c.get("value")
            if not name or value is None:
                continue

            domain = c.get("domain", "").lstrip(".")
            path = c.get("path", "/")
            sess.cookies.set(name, value, domain=domain, path=path)

        self.log(f"[SSG] 쿠키 {len(cookies)}개 적용 완료")

    # ====================================================
    # 로그아웃
    # ====================================================
    def _logout(self):
        try:
            self.driver.get(self.SSG_MAIN_URL)
            time.sleep(1)

            logout_btn = self.selenium.wait_element(
                By.CSS_SELECTOR,
                "a[data-react-tarea='공통|GNB|로그아웃_클릭']",
                timeout=10
            )
            if logout_btn:
                logout_btn.click()
                time.sleep(1)

            self.log("[SSG] 로그아웃 완료")
        except Exception as e:
            self.log(f"[SSG] 로그아웃 오류: {e}")

    # ====================================================
    # 주문내역 한 페이지 호출 (url + headers + params + api.get)
    # ====================================================
    def _get_order_page_html(self, page_number, date_from, date_to):
        """
        date_from / date_to : 'YYYY-MM-DD' (없으면 빈 문자열)
        """
        params = {
            "searchType": "5",
            "searchCheckBox": "",
            "page": page_number,
            "searchInfloSiteNo": "",
            "searchStartDt": date_from or "",
            "searchEndDt": date_to or "",
            "searchKeyword": "",
        }

        self.log(
            f"[SSG] 주문내역 요청 page={page_number} "
            f"(searchStartDt={params['searchStartDt']}, "
            f"searchEndDt={params['searchEndDt']})"
        )

        headers = {
            "User-Agent": self.UA,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.7"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": self.ORDER_URL,
        }

        try:
            html = self.api.get(self.ORDER_URL, headers=headers, params=params)
        except Exception as e:
            self.log(f"[SSG] 주문내역 요청 실패(page={page_number}): {e}")
            return None

        if not html:
            self.log(f"[SSG] page={page_number} 응답 없음")
            return None

        return html

    # ====================================================
    # 주문내역 파싱
    # ====================================================
    def _parse_order_page(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []

        units = soup.find_all(attrs={"name": "divOrordUnit"})
        for unit in units:
            orord_no = None
            inp = unit.find("input", attrs={"name": "orordNo"})
            if inp:
                orord_no = inp.get("value", "").strip()

            carrier = None
            invoice = None

            dv = unit.find("div", class_="codr_dvstate_bg")
            if dv:
                tx = dv.find("div", class_="tx_state")
                if tx:
                    em = tx.find("em")
                    if em:
                        span = em.find("span", class_="notranslate")
                        if span:
                            carrier = span.get_text(strip=True)

                        merged = "".join(em.stripped_strings)
                        parts = merged.split("/")
                        if len(parts) >= 2:
                            m = re.search(r"(\d+)", parts[1])
                            if m:
                                invoice = m.group(1)

            results.append({
                "주문고유코드": orord_no,
                "택배사": carrier,
                "송장번호": invoice,
            })

        return results

    def _all_delivery_filled(self, excel_rows):
        for r in excel_rows:
            if not str(r.get("송장번호") or "").strip():
                return False
            if not str(r.get("택배사") or "").strip():
                return False
        return True

    # ====================================================
    # 메인
    # ====================================================
    def fetch_delivery_rows(self, excel_rows):
        if not excel_rows:
            return []

        login_id = excel_rows[0].get("id")
        login_pw = excel_rows[0].get("password")

        if not login_id or not login_pw:
            self.log("[SSG] id/password 누락")
            return []

        # 엑셀에서 날짜 범위 가져오기 (_parsed_dt: yyyymmdd 가정)
        # 11번가처럼: 가장 오래된 날짜 = 마지막 row, 가장 최근 날짜 = 첫 row
        date_from_raw = excel_rows[-1].get("_parsed_dt", "")
        date_to_raw = excel_rows[0].get("_parsed_dt", "")

        date_from = self._to_yyyy_mm_dd(date_from_raw)
        date_to = self._to_yyyy_mm_dd(date_to_raw)

        try:
            self._login_and_prepare_api_session(login_id, login_pw)

            page_number = 1

            while True:
                html = self._get_order_page_html(page_number, date_from, date_to)
                if not html:
                    self.log(f"[SSG] page={page_number} 에서 더 이상 진행 불가 → 종료")
                    break

                parsed = self._parse_order_page(html)

                if not parsed:
                    self.log(f"[SSG] page={page_number} 주문 없음 → 종료")
                    break

                # === 매핑 ===
                for item in parsed:
                    order_no_str = str(item.get("주문고유코드") or "").strip()
                    for row in excel_rows:
                        excel_order_no = str(row.get("주문고유코드") or "").strip()
                        if excel_order_no == order_no_str:
                            row["송장번호"] = item.get("송장번호")
                            row["택배사"] = item.get("택배사")

                # === 모든 배송정보 채워졌으면 조기 종료 ===
                if self._all_delivery_filled(excel_rows):
                    self.log("[SSG] 모든 주문 배송정보 매핑 완료 → 조기 종료")
                    break

                page_number += 1
                time.sleep(0.4)

            return excel_rows

        except Exception as e:
            self.log(f"[SSG] 처리 오류: {e}")
            return []

        finally:
            self._logout()
