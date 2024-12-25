import re

from bs4 import BeautifulSoup

from utils.date import convert_to_yyyymmdd
from utils.logger import logger
from utils.request_util import common_request


class KreiList:
    def __init__(self):
        self.url = "https://www.krei.re.kr/krei"
        self.url_main_path = 'selectBbsNttList.do'
        self.url_main = f'{self.url}/{self.url_main_path}'
        self.payload = {
            'bbsNo': '76',
            'key': '271'
        }
        self.src = 'KREI 주간브리프'


    def request(self):
        return common_request(self.url_main, self.payload)


    def process_data(self, html):
        data_list = []
        try:

            soup = BeautifulSoup(html, 'html.parser')

            # 'tbl default' 클래스의 table 요소 찾기
            board_list = soup.find('table', class_='tbl default')
            if not board_list:
                logger.error("Board list not found")
                return []

            tbody = board_list.find('tbody')
            if not tbody:
                logger.error("tbody not found")
                return []

            # tr 요소 순회
            for index, tr in enumerate(tbody.find_all('tr', recursive=False)):

                url = ''
                ttl = ''
                reg_ymd = ''
                dmnfr_trend_no = ''

                tds = tr.find_all('td', recursive=False)

                # td 요소가 부족하면 skip
                if len(tds) >= 3:

                    a_tag = tds[1].find('a')

                    if a_tag:
                        ttl = a_tag.get_text(strip=True)
                        href_text = a_tag['href'] if 'href' in a_tag.attrs else ''
                        if href_text:
                            url = f'{self.url}{href_text.lstrip('.')}'
                            # 정규 표현식 패턴: nttNo= 뒤에 숫자만 추출
                            match = re.search(r'nttNo=(\d+)', href_text)

                            if match:
                                dmnfr_trend_no = match.group(1)  # 숫자 부분만 반환

                    # '일자' 제거하고 앞뒤 공백 제거
                    reg_ymd = tds[2].get_text(strip=True).replace("일자", "").strip()
                    reg_ymd = convert_to_yyyymmdd(reg_ymd, '.')

                    # 데이터 객체 구성
                    data_obj = {
                        "DMNFR_TREND_NO": dmnfr_trend_no,
                        "STTS_CHG_CD": "succ",
                        "TTL": ttl,
                        "SRC": self.src,
                        "REG_YMD": reg_ymd,
                        "URL": url
                    }
                    data_list.append(data_obj)

        except Exception as e:
            logger.error(f"An error occurred while processing the data: {e}")

        finally:
            return data_list


    def run(self):
        """크롤러 실행"""
        html = self.request()
        if html:
            return self.process_data(html)
        else:
            return None