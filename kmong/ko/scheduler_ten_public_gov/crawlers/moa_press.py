import re

from bs4 import BeautifulSoup

from utils.date import convert_to_yyyymmdd
from utils.logger import logger
from utils.request_util import common_request


class MoaPress:
    def __init__(self):
        self.url = "http://www.moa.gov.cn/xw/zwdt/"
        self.src = '중국 농업농촌부 소식'


    def request(self):
        return common_request(self.url)


    def process_data(self, html):
        data_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            board_list = soup.find('div', class_='pub-media1-txt-list') if soup else None

            if not board_list:
                logger.error("Board list not found")
                return []

            list_items = board_list.find_all('li', class_='ztlb')

            if list_items and len(list_items) > 0:
                # list_items를 10개 이하로 자르기
                list_items = list_items[:10]

                for index, item in enumerate(list_items):

                    url = ''
                    ttl = ''
                    reg_ymd_text = ''
                    dmnfr_trend_no = ''

                    # 날짜
                    span_tag = item.find('span')
                    if span_tag:
                        date_str = span_tag.get_text(strip=True) if span_tag else ''
                        reg_ymd_text = convert_to_yyyymmdd(date_str, '-')

                    a_tag = item.find('a')
                    if a_tag:
                        title_value = a_tag['title'] if 'title' in a_tag.attrs else ''
                        ttl = title_value

                        url = a_tag['href'] if 'href' in a_tag.attrs else ''

                        if url:
                            if url.startswith('./'):
                                url = "http://www.moa.gov.cn/xw/zwdt" + url[1:]  # "./"를 제거하고 기본 URL을 붙임

                            # 정규 표현식을 사용하여 URL에서 숫자 추출
                            match = re.search(r'(\d+)(?=\.htm$)', url)
                            if match:
                                dmnfr_trend_no = match.group(1)  # 6468463 추출

                    data_obj = {
                        "DMNFR_TREND_NO": dmnfr_trend_no,
                        "STTS_CHG_CD": "succ",
                        "TTL": ttl,
                        "SRC": self.src,
                        "REG_YMD": reg_ymd_text,
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