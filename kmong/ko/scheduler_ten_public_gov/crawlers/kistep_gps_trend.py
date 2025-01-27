import re

from bs4 import BeautifulSoup

from utils.date import convert_to_yyyymmdd
from utils.logger import logger
from utils.request_util import common_request


class KistepGpsTrend:
    def __init__(self):
        self.url = "https://www.kistep.re.kr"
        self.url_main_path = 'gpsTrendList.es'
        self.url_main = f'{self.url}/{self.url_main_path}'
        self.payload = {
            'mid': 'a30200000000',
            'list_no': '',
            'nPage': 1,
            'b_list': 10,
            'data02': '',
            'data01': '',
            'dt01_sdate': '',
            'dt01_edate': '',
            'keyField': '',
            'keyWord': ''
        }
        self.src = '한국과학기술기획평가원 S&T GPS(글로벌 과학기술정책정보서비스)'

    def request(self):
        """kistep_gpsTrendList 요청"""
        return common_request(self.url_main, self.payload)

    def process_data(self, html):
        data_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # 'tstyle_list' 클래스의 테이블을 찾기
            table = soup.find('table', class_='tstyle_list')

            if not table:
                logger.info("Table not found")
                return []

            # tbody 내의 tr 요소들을 가져오기
            tbody = table.find('tbody')
            rows = tbody.find_all('tr') if tbody else None


            if rows:
                for row in rows:
                    url = ''
                    ttl = ''
                    reg_ymd = ''
                    dmnfr_trend_no = ''

                    # 각 td 요소들을 추출
                    tds = row.find_all('td')

                    if tds and len(tds) >= 5:

                        a_tag = tds[2].find('a')
                        if a_tag:
                            href = a_tag.get('href', '')  # 안전하게 href 추출

                            # list_no 파라미터 추출
                            match = re.search(r'list_no=(\d+)', href)

                            if match:
                                dmnfr_trend_no = match.group(1)

                            ttl = a_tag.get_text(strip=True)  # TTL
                            ttl = ttl.replace('새글', '').strip() if ttl else ''  # "새글" 제거하고 앞뒤 공백도 제거

                        reg_ymd = tds[4].get_text(strip=True)  # REG_YMD
                        reg_ymd = convert_to_yyyymmdd(reg_ymd, '-')

                        # URL 생성
                        if a_tag and 'href' in a_tag.attrs:
                            url = f'{self.url}{a_tag["href"]}'  # URL

                        # SRC와 STTS_CHG_CD는 고정값
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