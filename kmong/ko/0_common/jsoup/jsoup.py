from bs4 import BeautifulSoup

from utils.date import convert_to_yyyymmdd
from utils.logger import logger
from utils.request_util import common_request


class UsdaPress:
    def __init__(self):
        self.url_main = "https://www.usda.gov/about-usda/news/press-releases"
        self.src = '미국 USDA 보도자료'

        self.payload = {
            'page': 0
        }


    def request(self):
        return common_request(self.url_main, self.payload)


    def process_data(self, html):
        data_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            board_list = soup.find('div', class_='views-element-container') if soup else None

            if not board_list:
                logger.error("Board list not found")
                return []

            views = board_list.find_all('div', class_='views-row')

            if views and len(views) > 0:

                for index, view in enumerate(views):

                    url = ''
                    dmnfr_trend_no = ''
                    ttl = ''
                    reg_ymd = ''

                    h2_tag = view.find('h2')
                    a_tag = h2_tag.find('a') if h2_tag else None

                    if a_tag:
                        ttl = a_tag.get_text(strip=True)

                        href_text = a_tag['href'] if 'href' in a_tag.attrs else ''

                        if href_text:
                            url = f'https://www.usda.gov{href_text}'
                            html = common_request(url)
                            if html:
                                press_no_soup = BeautifulSoup(html, 'html.parser') if soup else None
                                article_release_no_value = press_no_soup.find('div', class_='article-release-no-value') if press_no_soup else None
                                field_item = article_release_no_value.find('div', class_='field__item') if article_release_no_value else None
                                field_item_text = field_item.get_text(strip=True) if field_item else ''
                                # 숫자에서 소수점(.)을 제거하고, 문자열을 정수로 변환
                                dmnfr_trend_no = int(field_item_text.replace('.', '')) if field_item_text else 0


                    # 'time' 태그에서 datetime 속성 가져오기
                    time_tag = view.find('time')

                    # datetime 속성에서 날짜만 추출하고, YYYYMMDD 형식으로 변환
                    if time_tag:
                        reg_ymd = time_tag['datetime'][:10]  # '2024-12-23T16:55:00Z'에서 '2024-12-23'만 추출
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