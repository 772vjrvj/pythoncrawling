# src/workers/main/delivery/site_11st_delivery.py
# -*- coding: utf-8 -*-

import re
import time
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from src.utils.api_utils import APIClient
from src.utils.selenium_utils import SeleniumUtils


class ElevenstDeliveryCrawler:
    """
    11번가 배송정보 크롤러 (계정 1개 기준)
    - Selenium driver + log 함수 + APIClient + SeleniumUtils 주입
    - fetch_delivery_rows(excel_rows) 호출 시:
        1) 로그인
        2) 최근 6개월 취소요청 리스트에서 (주문고유코드 → dlvNo) 매핑
        3) 배송조회 페이지에서 택배사/송장번호 파싱
        4) 결과 row 리스트 반환
        5) finally 에서 로그아웃
    """

    def __init__(self, driver, log_func, api_client: APIClient, selenium_driver):
        """
        :param driver: Selenium WebDriver (외부에서 생성)
        :param log_func: 로그 함수 (예: self.log_signal_func)
        :param api_client: APIClient 인스턴스
        :param selenium_driver: SeleniumUtils 인스턴스
        """
        self.driver = driver
        self.log = log_func
        self.api = api_client
        self.selenium = selenium_driver

        # === 인스턴스 상수들 ===
        self.LOGIN_URL = "https://login.11st.co.kr/auth/v2/login"
        self.LOGOUT_URL = "https://login.11st.co.kr/auth/logout.tmall"
        self.ORDER_URL = "https://buy.11st.co.kr/my11st/order/BuyManager.tmall"
        self.TRACE_URL_BASE = "https://buy.11st.co.kr/delivery/trace.tmall?dlvNo={dlv_no}"

        self.UA = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        )

    # =========================
    # 내부 유틸
    # =========================
    def _login_and_prepare_api_session(self, login_id, login_pw):
        """
        SeleniumUtils를 이용해서 11번가 로그인 후
        해당 쿠키들을 APIClient.session 으로 옮긴다.
        (이 함수 내부에는 try/except 없음 → 상위 fetch_delivery_rows 에서 한 번만 처리)
        """
        self.log(f"[11번가] 로그인 시도: id={login_id}")

        # 로그인 페이지 이동
        self.driver.get(self.LOGIN_URL)
        time.sleep(3)

        # ID 입력
        id_input = self.selenium.wait_element(By.ID, "memId", timeout=20)
        if not id_input:
            raise Exception("memId 요소를 찾지 못했습니다.")
        id_input.clear()
        id_input.send_keys(login_id)

        # PW 입력
        pw_input = self.selenium.wait_element(By.ID, "memPwd", timeout=20)
        if not pw_input:
            raise Exception("memPwd 요소를 찾지 못했습니다.")
        pw_input.clear()
        pw_input.send_keys(login_pw)

        # 로그인 버튼 클릭
        login_btn = self.selenium.wait_element(By.ID, "loginButton", timeout=20)
        if not login_btn:
            raise Exception("loginButton 요소를 찾지 못했습니다.")

        # === 신규: element not interactable 대비 JS 클릭 보강 ===
        try:
            login_btn.click()
        except Exception as e:
            self.log(f"[11번가] loginButton.click() 오류, JS 클릭으로 재시도: {e}")
            self.driver.execute_script("arguments[0].click();", login_btn)

        time.sleep(3)

        # 공용 PC 팝업 → "다음에 할게요" 닫기 (있으면 닫고, 없으면 로그만)
        close_btn = self.selenium.wait_element(
            By.CSS_SELECTOR,
            "a[modal-auto-action='close']",
            timeout=8,
        )
        if close_btn:
            close_btn.click()
            self.log("[11번가] 공용 PC 팝업 닫음")
        else:
            self.log("[11번가] 공용 PC 팝업 없음 또는 자동으로 넘어감")

        time.sleep(2)

        # 로그인 이후 쿠키 수집
        cookies = self.driver.get_cookies()
        self.log(f"[11번가] 로그인 후 쿠키 개수: {len(cookies)}")

        # Selenium 쿠키를 APIClient.session 으로 복사
        for c in cookies:
            name = c.get("name")
            value = c.get("value")
            domain = c.get("domain", "").lstrip(".")
            path = c.get("path", "/")

            if not name or value is None:
                continue

            self.api.session.cookies.set(name, value, domain=domain, path=path)

    def _logout(self):
        """
        11번가 로그아웃
        - 로그아웃 URL로 GET 호출
        (여기서만 별도 try/except 허용: 종료 단계라 실패해도 치명적이지 않음)
        """
        try:
            self.log("[11번가] 로그아웃 시도")
            self.driver.get(self.LOGOUT_URL)
            time.sleep(1)
            self.log("[11번가] 로그아웃 완료(또는 이미 로그아웃 상태)")
        except Exception as e:
            self.log(f"[11번가] 로그아웃 중 오류: {e}")

    def _get_request_list_html(self, page_number, date_from, date_to):
        params = {
            "method": "getCancelRequestListAjax",
            "type": "orderList2nd",
            "pageNumber": page_number,
            "rows": 10,
            "shDateFrom": date_from,
            "shDateTo": date_to,
            "ver": "02",
            "shPrdNm": "",
            "shOrdprdStat": "",
            "pageNumberPendingFail": 1,
            "pageNumberPendingDone": 1
        }

        headers = {
            "User-Agent": self.UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Referer": "https://buy.11st.co.kr/my11st/order/OrderList.tmall",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }

        html = self.api.get(self.ORDER_URL, headers=headers, params=params)
        if html is None:
            self.log(f"[11번가] 취소요청 리스트 응답 None (page={page_number})")
            return None
        return html


    def parse_list_for_pairs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        pairs = []

        # 배송조회 버튼만 골라서 파싱
        for a in soup.find_all("a", href=True, attrs={"ord-no": True}):
            href = a["href"]

            # 배송번호 추출
            m = re.search(r"goDeliveryTracking\('(\d+)'", href)
            if not m:
                continue

            dlv_no = m.group(1)
            order_no = a["ord-no"]

            pairs.append((order_no, dlv_no))
            self.log(f"[pair] {order_no} - {dlv_no}")

        return pairs


    def _parse_trace_page(self, html):
        """
        배송조회 페이지에서 택배사 / 송장번호 파싱
        """
        soup = BeautifulSoup(html, "html.parser")

        info = soup.find("div", class_="delivery_info")
        if not info:
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
                if dd.contents:
                    result["택배사"] = str(dd.contents[0]).strip()
                else:
                    result["택배사"] = val_text
            elif title == "송장번호":
                result["송장번호"] = val_text.strip()

        self.log(f"result={result})")

        return result

    def _all_delivery_filled(self, excel_rows):
        for row in excel_rows:
            if not str(row.get("delivery_no") or "").strip():
                return False
        return True

    def _fetch_trace_info(self, dlv_no):
        """
        배송조회 페이지 호출 + 파싱해서 dict 반환
        """
        trace_url = self.TRACE_URL_BASE.format(dlv_no=dlv_no)

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
            "Cache-Control": "max-age=0",
            "Referer": trace_url,
        }

        html = self.api.get(trace_url, headers=headers)
        if html is None:
            self.log(f"[11번가] 배송조회 응답 None (dlvNo={dlv_no})")
            return None

        return self._parse_trace_page(html)

    # =========================
    # 외부에서 사용하는 메인 메서드
    # =========================
    def fetch_delivery_rows(self, excel_rows):

        if not excel_rows:
            return []

        login_id = excel_rows[0].get("id")
        login_pw = excel_rows[0].get("password")

        if not login_id or not login_pw:
            self.log("[11번가] id 또는 password 가 없어 로그인 불가")
            return []

        # 오늘 기준 6개월 범위
        date_from = excel_rows[-1].get("_parsed_dt", "")
        date_to   = excel_rows[0].get("_parsed_dt", "")

        try:
            # 1) 로그인 + APIClient 세션 준비
            self._login_and_prepare_api_session(login_id, login_pw)

            # 2) while 루프로 페이지 증가시키면서 delivery_no 매핑
            page_number = 1

            while True:
                self.log(
                    f"[11번가] 리스트 호출 "
                    f"login_id={login_id} page={page_number} ({date_from}~{date_to})"
                )
                html = self._get_request_list_html(
                    page_number, date_from, date_to
                )
                if not html:
                    self.log(f"[11번가] page={page_number} HTML 없음 → 중단")
                    break

                list_for_pairs = self.parse_list_for_pairs(html)
                if not list_for_pairs:
                    self.log(f"[11번가] list_for_pairs page={page_number} 더 이상 주문 없음 → 중단")
                    break

                self.log(f"[11번가] page={page_number} 더 이상 주문 없음 → 중단")

                # 페이지에서 가져온 (order_no, dlv_no)를 excel_rows 에 즉시 매핑
                for order_no, dlv_no in list_for_pairs:
                    if not order_no or not dlv_no:
                        continue
                    order_no_str = str(order_no).strip()
                    dlv_no_str = str(dlv_no).strip()

                    for row in excel_rows:
                        excel_order_no = str(row.get("주문고유코드") or "").strip()
                        if excel_order_no == order_no_str:
                            row["delivery_no"] = dlv_no_str

                # 모든 주문에 delivery_no 가 채워졌으면 조기 종료
                if self._all_delivery_filled(excel_rows):
                    self.log("[11번가] 모든 주문에 delivery_no 매핑 완료, 조기 종료")
                    break

                page_number += 1
                time.sleep(0.5)

            # 매핑된 개수 로그
            filled_cnt = sum(
                1 for r in excel_rows
                if str(r.get("주문고유코드") or "").strip()
                and str(r.get("delivery_no") or "").strip()
            )
            self.log(
                f"[11번가] 엑셀 주문 {len(excel_rows)}건 중 "
                f"delivery_no 채워진 건수: {filled_cnt}건"
            )

            for r in excel_rows:
                order_no = str(r.get("주문고유코드") or "").strip()
                dlv_no = str(r.get("delivery_no") or "").strip()

                if not order_no:
                    self.log("[11번가] 주문고유코드가 비어 있어 delivery_no 조회 대상 아님 → 결제완료 처리")
                    r["송장번호"] = "결제완료"
                    r["택배사"] = "결제완료"
                    continue

                if not dlv_no:
                    self.log(f"[11번가] 주문고유코드 {order_no} : delivery_no 미존재 → 결제완료 처리")
                    r["송장번호"] = "결제완료"
                    r["택배사"] = "결제완료"
                    continue

                self.log(f"[11번가] 배송조회 호출: 주문고유코드={order_no}, dlvNo={dlv_no}")

                info = self._fetch_trace_info(dlv_no)

                if not info:
                    self.log(f"[11번가] 배송조회 실패: 주문고유코드={order_no}, dlvNo={dlv_no} → 결제완료 처리")
                    r["송장번호"] = "결제완료"
                    r["택배사"] = "결제완료"
                    continue

                # === 배송정보 성공 ===
                r["송장번호"] = info.get("송장번호")
                r["택배사"] = info.get("택배사")

                time.sleep(0.3)

            return excel_rows

        except Exception as e:
            self.log(f"[11번가] 전체 처리 중 오류: {e}")
            return []

        finally:
            # 계정별로 반드시 로그아웃
            self._logout()
