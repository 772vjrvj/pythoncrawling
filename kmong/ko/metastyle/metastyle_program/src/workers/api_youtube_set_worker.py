from PyQt5.QtCore import QThread, pyqtSignal
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
import pandas as pd
from datetime import datetime
import random

blog_ing = 0

# API
class ApiNetflixSetLoadWorker(QThread):
    api_data_received = pyqtSignal(object)  # API 호출 결과를 전달하는 시그널

    def __init__(self, url_list, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.cookie = None
        self.driver = None


    def run(self):
        result_list = []
        for idx, url in enumerate(self.url_list, start=1):

            result = {
                "url": url,
                "title": "",
                "year": "",
                "season": "",
                "rating": "",
                "genre": "",
                "summary": "",
                "cast": "",
                "director": "",
                "success": "X",
                "message": "",
            }

            self.parent.add_log(f'번호 : {idx}, 시작')
            soup = self.fetch_place_info(url,result)

            if soup:
                self.extract_netflix_data(soup, result)

            self.parent.add_log(f'번호 : {idx}, 데이터 : {result}')
            result_list.append(result)
            pro_value = (idx / len(self.url_list)) * 1000000
            self.parent.set_progress(pro_value)

            time.sleep(random.uniform(2, 3))

        self.save_to_excel(result_list)


    def save_to_excel(self, results):
        self.parent.add_log("엑셀 저장 시작")

        # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")

        # 파일 이름 설정
        file_name = f"넷플릭스_{current_time}.xlsx"

        try:
            # 파일이 없으면 새로 생성
            df = pd.DataFrame(results)

            # 엑셀 파일 저장
            df.to_excel(file_name, index=False)
            self.parent.add_log(f"엑셀 저장 완료: {file_name}")

        except Exception as e:
            # 예기치 않은 오류 처리
            self.parent.add_log(f"엑셀 저장 실패: {e}")



    def fetch_place_info(self, url, result):
        match = re.search(r'\/(\d+)$', url)
        if match:
            last_number = match.group(1)
        else:
            result['message'] = '잘못된 URL 입니다.'
            self.parent.add_log("잘못된 URL 입니다.")
            return None

        headers = {
            "authority": "www.netflix.com",
            "method": "GET",
            "path": f"/kr/title/{last_number}",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": "\"\"",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"10.0.0\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        max_retries = 3  # 최대 재시도 횟수
        attempts = 0

        while attempts <= max_retries:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

                # 만약 404 오류가 발생하면 result에 메시지를 설정하고 종료
                if response.status_code == 404:
                    self.parent.add_log("404 죄송합니다. 해당 페이지를 찾을 수 없습니다. 홈페이지로 이동해 다양한 콘텐츠를 만나보세요.")
                    result['message'] = '404 죄송합니다. 해당 페이지를 찾을 수 없습니다. 홈페이지로 이동해 다양한 콘텐츠를 만나보세요.'
                    return None

                soup = BeautifulSoup(response.text, "html.parser")

                # main_container 찾기
                try:
                    main_container = soup.find("div", class_="default-ltr-cache-kiz1b3 em9qa8x3")
                    if not main_container:
                        raise Exception("페이지 로드 실패.")
                except Exception as e:
                    self.parent.add_log(f"오류 발생: {e}, 재시도 {attempts + 1}/{max_retries}")
                    attempts += 1
                    if attempts > max_retries:
                        self.parent.add_log("최대 재시도 횟수를 초과했습니다.")
                        result['message'] = "서버 호출 에러, 최대 재시도 횟수를 초과했습니다."
                        return None
                    time.sleep(2)  # 2초 대기 후 재시도
                    continue  # 재시도하려면 continue로 반복문을 다시 실행

                return soup

            except requests.exceptions.RequestException as e:
                # 404을 제외한 다른 오류가 발생하면 처리
                if response.status_code == 404:
                    # 404 오류 처리 - 메시지 출력하고 종료
                    self.parent.add_log("404 죄송합니다. 해당 페이지를 찾을 수 없습니다. 홈페이지로 이동해 다양한 콘텐츠를 만나보세요.")
                    result['message'] = '404 죄송합니다. 해당 페이지를 찾을 수 없습니다. 홈페이지로 이동해 다양한 콘텐츠를 만나보세요.'
                    return None
                else:
                    attempts += 1
                    self.parent.add_log(f"페이지 요청 중 오류 발생: {e}, 재시도 {attempts}/{max_retries}")
                    if attempts > max_retries:
                        self.parent.add_log("최대 재시도 횟수를 초과했습니다.")
                        return None
                    time.sleep(2)  # 2초 대기 후 재시도


    def extract_netflix_data(self, soup, result):
        """
        Netflix 페이지에서 필요한 정보를 추출하여 객체로 반환.

        Args:
            soup (BeautifulSoup): HTML 파싱된 BeautifulSoup 객체.

        Returns:
            dict: 추출된 정보를 담은 객체.
        """
        try:
            # 메인 컨테이너
            main_container = soup.find("div", class_="default-ltr-cache-kiz1b3 em9qa8x3")

            # Title (h2 태그)
            title_tag = main_container.find("h2", class_="default-ltr-cache-11jsu7c euy28770")
            result["title"] = title_tag.text.strip() if title_tag else ""

            # Year, Season, Rating, Genre
            details_container = main_container.find("div", class_="default-ltr-cache-56ff39 em9qa8x2")
            details_list = details_container.find("ul", class_="default-ltr-cache-1xty6x8 e32lqeb1") if details_container else None

            if details_list:

                li_tags = details_list.find_all("li", class_="default-ltr-cache-1payn3k e32lqeb0")

                if len(li_tags) == 4:

                    result["year"] = li_tags[0].text.strip() if len(li_tags) > 0 else ""

                    season_text = li_tags[1].text.strip() if len(li_tags) > 1 else ""
                    season_text = season_text.replace('\u2068', '').replace('\u2069', '')
                    result["season"] = season_text

                    rating_text = li_tags[2].text.strip() if len(li_tags) > 2 else ""
                    rating_text = rating_text.replace('\u2068', '').replace('\u2069', '')
                    result["rating"] = rating_text

                    genre_text = li_tags[3].text.strip() if len(li_tags) > 3 else ""
                    genre_text = genre_text.replace('\u2068', '').replace('\u2069', '')
                    result["genre"] = genre_text

                if len(li_tags) == 3:

                    result["year"] = li_tags[0].text.strip() if len(li_tags) > 0 else ""

                    rating_text = li_tags[1].text.strip() if len(li_tags) > 1 else ""
                    rating_text = rating_text.replace('\u2068', '').replace('\u2069', '')
                    result["rating"] = rating_text

                    genre_text = li_tags[2].text.strip() if len(li_tags) > 2 else ""
                    genre_text = genre_text.replace('\u2068', '').replace('\u2069', '')
                    result["genre"] = genre_text

            else:
                result.update({"year": "", "season": "", "rating": "", "genre": ""})


            # Summary (줄거리)
            summary_container = main_container.find("div", class_="default-ltr-cache-18fxwnx em9qa8x0")
            summary_tag = summary_container.find("div", class_="default-ltr-cache-1y7pnva em9qa8x1") if summary_container else None
            summary_span = summary_tag.find("span", class_="default-ltr-cache-v92n84 euy28770") if summary_tag else None
            result["summary"] = summary_span.text.strip() if summary_span else ""

            # Cast and Director
            cast_director_container = summary_container.find("div", class_="default-ltr-cache-1wmy9hl ehsrwgm0") if summary_container else None
            cast_divs = cast_director_container.find_all("div", class_="default-ltr-cache-eywhmi ehsrwgm1") if cast_director_container else []

            # Cast (출연진)
            if len(cast_divs) > 0:
                cast_span = cast_divs[0].find_all("span", class_="default-ltr-cache-3z6sz6 euy28770")
                result["cast"] = cast_span[0].text.strip()
            else:
                result["cast"] = ""

            # Director (감독)
            if len(cast_divs) > 1:
                director_span = cast_divs[1].find_all("span", class_="default-ltr-cache-3z6sz6 euy28770")
                result["director"] = director_span[0].text.strip()
            else:
                result["director"] = ""
            result['success'] = 'O'
        except AttributeError as e:
            self.parent.add_log(f"데이터 추출 중 오류 발생: {e}")
