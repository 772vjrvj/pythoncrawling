import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import concurrent.futures

# 크롤링할 키워드 리스트
keywords = ['채권추심', '빌려준돈', '떼인돈', '지급명령신청']

# 최대 연관 키워드 수
max_keywords = 200

start_time = time.time()  # 시작 시간 기록

# 크롤링 결과를 저장할 리스트
data = []

# 각 키워드에 대해 크롤링 수행하는 함수
def crawl_keyword(keyword):
    url = f'https://www.cardveryview.com/네이버-키워드-검색량-조회-확인/?keyword={keyword}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')





    # id가 keywordTableth인 테이블 찾기
    table2 = soup.find('table', id='keywordTableth')

    if table2:
        rows = table2.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 5:  # 데이터가 있는 행인지 확인
                related_keyword = cols[0].text.strip()
                pc_search_volume = int(cols[1].text.strip().replace(',', ''))  # 콤마 제거 후 숫자로 변환
                mobile_search_volume = int(cols[2].text.strip().replace(',', ''))  # 콤마 제거 후 숫자로 변환
                total_search_volume = int(cols[3].text.strip().replace(',', ''))  # 콤마 제거 후 숫자로 변환
                competition_index = cols[4].text.strip()
                if pc_search_volume >= 20 or mobile_search_volume >= 20:
                    if related_keyword not in keywords and len(keywords) < max_keywords:  # 중복 및 최대 키워드 개수 체크
                        keywords.append(related_keyword)

def crawl_keyword_data(keyword):
    url = f'https://www.cardveryview.com/네이버-키워드-검색량-조회-확인/?keyword={keyword}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # id가 firstKeyword인 테이블 찾기
    table1 = soup.find('table', id='firstKeyword')

    if table1:
        rows = table1.find_all('tr')
        pc_search_volume = rows[0].find_all('td')[1].text.strip().replace(',', '')
        mobile_search_volume = rows[1].find_all('td')[1].text.strip().replace(',', '')
        total_search_volume = rows[2].find_all('td')[1].text.strip().replace(',', '')
        competition_index = rows[3].find_all('td')[1].text.strip()
        data.append({
            '연관키워드': keyword,
            '월간 PC 검색량': pc_search_volume,
            '월간 MOBILE 검색량': mobile_search_volume,
            '총합': total_search_volume,
            '경쟁지수': competition_index
        })


if __name__ == '__main__':

    for keyword in keywords:
        print(f"keywords len: {len(keywords)}")
        if len(keywords) >= max_keywords:
            break
        crawl_keyword(keyword)


    print(f"total keywords len : {len(keywords)}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(crawl_keyword_data, keywords)


    end_time = time.time()  # 종료 시간 기록
    total_time = end_time - start_time  # 총 걸린 시간 계산


    print(f"총 걸린 시간: {total_time} 초")
    print(f"total keywords len: {len(keywords)}")
    print(f"total keywords: {keywords}")



# pandas DataFrame으로 변환
df = pd.DataFrame(data, columns=['연관키워드', '월간 PC 검색량', '월간 MOBILE 검색량', '총합', '경쟁지수'])

# 엑셀 파일로 저장
df.to_excel('keyword_search_volume.xlsx', index=False)

print("엑셀 파일이 성공적으로 생성되었습니다.")