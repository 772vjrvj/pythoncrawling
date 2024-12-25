import re

from bs4 import BeautifulSoup

from utils.date import convert_to_yyyymmdd
from utils.logger import logger
from utils.request_util import common_request


class KatiReport:
    def __init__(self):
        self.url = "https://www.kati.net/board"
        self.url_main_path = 'reportORpubilcationList.do'
        self.url_main = f'{self.url}/{self.url_main_path}'
        self.src = '농식품수출정보-보고서'


    def request(self):
        return common_request(self.url_main)


    def process_data(self, html):
        data_list = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            board_list = soup.find('div', class_='report-list-area mt10')
            if not board_list:
                logger.error("Board list not found")
                return []

            report_items = board_list.find_all('div', class_='report-item')
            if not report_items:
                logger.error("report_items not found")
                return []

            for index, report_item in enumerate(report_items):
                url = ''
                ttl = ''
                reg_ymd = ''
                dmnfr_trend_no = ''

                em_tag = report_item.find('em', class_='report-tit')
                span_tag = report_item.find('span', class_='report-date')

                if em_tag:
                    a_tag = em_tag.find('a')
                    if a_tag:
                        href_text = a_tag['href'] if 'href' in a_tag.attrs else ''
                        if href_text:
                            before_url = f'{self.url}{href_text.lstrip('.')}'
                            url = before_url.replace('\r\n\t\t\t\t\t\t\t\t\t\t', '')
                        ttl = a_tag.get_text(strip=True)

                        match = re.search(r'board_seq=(\d+)', href_text)
                        if match:
                            dmnfr_trend_no = match.group(1)

                if span_tag:
                    date_str = span_tag.get_text(strip=True).replace("등록일", "").strip()
                    reg_ymd = convert_to_yyyymmdd(date_str, "-")


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