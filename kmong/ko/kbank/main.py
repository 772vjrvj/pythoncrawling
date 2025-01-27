import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from datetime import datetime
import pandas as pd


def kbank_request_html():
    file_path = '케이뱅크.html'

    try:
        # 파일을 읽어서 내용을 반환
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"파일 '{file_path}'을(를) 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
        return None


def get_kbank_data(html):
    data_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find('div', class_="odk6He") if soup else None

        if not board_list:
            logging.error("Board list not found")
            return []

        divs = board_list.find_all('div', recursive=False)
        main_div = divs[1] if divs else None
        for index, RHo1pe in enumerate(main_div.find_all('div', class_="RHo1pe", recursive=False)):
            obj = {
                '작성일자': '',
                '작성자': '',
                '리뷰내용': '',
                '추천수': 0,
                '평점': 0
            }
            if RHo1pe:
                writer = RHo1pe.find('div', class_="X5PpBb")
                obj['작성자'] = writer.get_text(strip=True) if writer else ''

                date = RHo1pe.find('span', class_="bp9Aid")
                obj['작성일자'] = date.get_text(strip=True) if date else ''

                content = RHo1pe.find('div', class_="h3YV2d")
                obj['리뷰내용'] = content.get_text(strip=True) if content else ''

                rating = RHo1pe.find('div', class_='iXRFPc')
                aria_label = rating.get('aria-label') if rating else None
                if aria_label:
                    # 정규식을 사용하여 숫자 추출
                    match = re.search(r'(\d+)개를 받았습니다\.', aria_label)
                    if match:
                        obj['평점'] = match.group(1)

                # div 태그 찾기
                recom = RHo1pe.find('div', class_='AJTPZc')
                obj['추천수'] = (
                    int(re.search(r'\d+', recom.get_text(strip=True)).group()) if recom else 0
                )
                print(f'obj : {obj}')
                data_list.append(obj)

    except Exception as e:
        logging.error(f"Error during scraping: {e}")

    return data_list



def save_to_excel(results):

    # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    # 파일 이름 설정
    file_name = f"kbank_{current_time}.xlsx"

    try:
        # 파일이 없으면 새로 생성
        df = pd.DataFrame(results)

        # 엑셀 파일 저장
        df.to_excel(file_name, index=False)

    except Exception as e:
        # 예기치 않은 오류 처리
        logging.error(f"엑셀 저장 실패: {e}")


def main():

    all_data_list = []

    html = kbank_request_html()
    if html:
        all_data_list = get_kbank_data(html)

    print(f'all_data_list len : {len(all_data_list)}')

    save_to_excel(all_data_list)


if __name__ == '__main__':
    main()