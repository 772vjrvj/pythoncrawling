import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 주요 키워드 리스트
main_keywords = [
    '빌려준 돈', '양육비', '임대료', '공사대금', '물품대금',
    '계약금반환', '퇴직금', '임금', '보증금',
    '상간녀 상간남 위자료', '판결 후 못 받은 돈', '소송비용', '대여금'
]

max_keywords = 50  # 키워드당 최대 연관 키워드 수

# 공통 headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def crawl_related_keywords(keyword):
    """
    단일 키워드로 연관 키워드 테이블 크롤링
    """
    related = []
    try:
        url = f'https://www.cardveryview.com/네이버-키워드-검색량-조회-확인/?keyword={keyword}'
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', id='keywordTableth')

        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 5:
                    kw = cols[0].text.strip()
                    if kw:
                        related.append(kw)
    except Exception as e:
        print(f"❌ [{keyword}] 요청 실패: {e}")
    return related


def get_full_related_keywords(seed_keyword, max_count):
    """
    하나의 메인 키워드에서 연관 키워드를 최대 max_count까지 수집
    """
    collected = []
    visited = set()
    queue = [seed_keyword]

    while queue and len(collected) < max_count:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        print(f"🔍 '{seed_keyword}' 관련 → '{current}' 연관 키워드 수집 중... ({len(collected)}/{max_count})")
        new_keywords = crawl_related_keywords(current)

        for kw in new_keywords:
            if kw not in collected and len(collected) < max_count:
                collected.append(kw)
                queue.append(kw)  # 수집한 키워드도 다음 탐색 대상으로 추가

        time.sleep(1)  # 너무 빠른 요청 방지

    return collected


if __name__ == '__main__':
    start_time = time.time()
    result_dict = {}

    for main_kw in main_keywords:
        result = get_full_related_keywords(main_kw, max_keywords)
        # 부족한 경우 빈칸 채우기
        result += [''] * (max_keywords - len(result))
        result_dict[main_kw] = result

    # 데이터프레임으로 변환
    df = pd.DataFrame(result_dict)
    df.to_excel('keyword_search_volume.xlsx', index=False)

    end_time = time.time()
    print(f"✅ 모든 키워드 수집 완료. 엑셀 저장됨. 총 소요시간: {end_time - start_time:.2f}초")
