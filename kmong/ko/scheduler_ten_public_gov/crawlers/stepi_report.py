import re

from bs4 import BeautifulSoup

from utils.date import convert_to_yyyymmdd
from utils.logger import logger
from utils.request_util import common_request


class StepiReport:
    def __init__(self):
        self.url = "https://www.stepi.re.kr/site/stepiko"
        self.url_main_path = 'ex/bbs/reportList.do'
        self.url_main = f'{self.url}/{self.url_main_path}'
        self.src = '과학기술정책연구원	STEPI'

        self.payload = {
            'cbIdx': '1292'
        }


    def request(self):
        return common_request(self.url_main, self.payload)


    def process_data(self, html):
        data_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            board_list = soup.find('ul', class_='boardList')
            if not board_list:
                logger.error("Board list not found")
                return []

            cbIdx = 1292
            pageIndex = 1
            tgtTypeCd = 'ALL'

            for index, li in enumerate(board_list.find_all('li', recursive=False)):

                url = ''
                dmnfr_trend_no = ''
                ttl = ''
                reg_ymd = ''

                title_tag = li.find('div', class_='title')
                info_tag = li.find('div', class_='info')
                if title_tag:
                    tit_tag = title_tag.find('a', class_='tit')
                    if tit_tag:
                        report_view = tit_tag['href'] if 'href' in tit_tag.attrs else ''

                        if report_view:

                            if "reportView2" in report_view:
                                # 정규 표현식을 사용하여 reIdx와 cateCont 추출
                                match = re.search(r"reportView2\('([^']+)',\s*'([^']+)'\)", report_view)
                                if match:
                                    reIdx = match.group(1)
                                    dmnfr_trend_no = reIdx
                                    cateCont = match.group(2)
                                    url = f"{self.url}/report/View.do?pageIndex={pageIndex}&cateTypeCd=&tgtTypeCd={tgtTypeCd}&searchType=&reIdx={reIdx}&cateCont={cateCont}&cbIdx={cbIdx}&searchKey="
                            else:
                                # 정규 표현식을 사용하여 reIdx와 cateCont 추출
                                match = re.search(r"reportView\((\d+),\s*'([^']+)'\)", report_view)

                                if match:
                                    reIdx = match.group(1)
                                    dmnfr_trend_no = reIdx
                                    cateCont = match.group(2)
                                    url = f"{self.url}/report/View.do?pageIndex={pageIndex}&cateTypeCd=&tgtTypeCd={tgtTypeCd}&searchType=&reIdx={reIdx}&cateCont={cateCont}&cbIdx={cbIdx}&searchKey="
                        ttl = tit_tag.get_text(strip=True)

                if info_tag:
                    span_tags = info_tag.find_all('span')
                    if span_tags and len(span_tags) > 1:
                        reg_ymd = span_tags[1].get_text(strip=True)
                        reg_ymd = convert_to_yyyymmdd(reg_ymd, "-")


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
            logger.error(f"Error : {e}")
        finally:
            return data_list


    def run(self):
        """크롤러 실행"""
        html = self.request()
        if html:
            return self.process_data(html)
        else:
            return None