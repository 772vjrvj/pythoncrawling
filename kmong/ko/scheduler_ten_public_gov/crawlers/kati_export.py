import re

from bs4 import BeautifulSoup

from utils.date import convert_to_yyyymmdd
from utils.logger import logger
from utils.request_util import common_request

# 농식품수출정보-해외시장동향
# https://www.kati.net/board/exportNewsList.do
class KatiExport:
    def __init__(self):
        self.url = "https://www.kati.net/board"
        self.url_main_path = 'exportNewsList.do'
        self.url_main = f'{self.url}/{self.url_main_path}'
        self.payload = {
            'page': '1',
            'menu_dept3': '',
            'srchGubun': '',
            'dateSearch': 'year',
            'srchFr': '',
            'srchTo': '',
            'srchTp': '2',
            'srchWord': ''
        }

        self.src = '농식품수출정보-해외시장동향'


    def request(self):
        return common_request(self.url_main, self.payload)


    def process_data(self, html):
        data_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            board_list = soup.find('div', class_='board-list-area mt10')
            if not board_list:
                logger.error("Board list not found")
                return []

            ul = board_list.find('ul')
            if not ul:
                logger.error("ul not found")
                return []

            for index, li in enumerate(ul.find_all('li', recursive=False)):
                url = ''
                ttl = ''
                reg_ymd = ''
                dmnfr_trend_no = ''

                a_tag = li.find('a', recursive=False)

                if a_tag:
                    href_text = a_tag['href'] if 'href' in a_tag.attrs else ''
                    if href_text:
                        before_url = f'{self.url}{href_text.lstrip('.')}'
                        url = before_url.replace('\r\n\t\t\t\t\t\t', '')

                        match = re.search(r'board_seq=(\d+)', href_text)
                        if match:
                            dmnfr_trend_no = match.group(1)

                    ttl_tag = a_tag.find('span', class_='fs-15 ff-ngb')
                    ttl = ttl_tag.get_text(strip=True) if ttl_tag else ''

                    date_tag = a_tag.find('span', class_='option-area')
                    if date_tag:
                        span_tags = date_tag.find_all('span')
                        if span_tags and len(span_tags) > 0:
                            date_str = span_tags[0].get_text(strip=True).replace("등록일", "").strip()
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