import requests


# 검색수 가져오기
def search_keyword_cnt(keyword):
    # 기본 URL과 동적 키워드 설정
    base_url = "https://manage.searchad.naver.com/keywordstool"
    params = {
        "format": "json",
        "hintKeywords": keyword,
        "siteId": "",
        "month": "",
        "biztpId": "",
        "event": "",
        "includeHintKeywords": "0",
        "showDetail": "1",
        "keyword": "",
    }

    # 헤더 설정
    headers = {
        "method": "GET",
        "accept": "application/json, text/plain, */*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpbklkIjoiNzcydmpydmo6bmF2ZXIiLCJyb2xlIjowLCJjbGllbnRJZCI6Im5hdmVyLWNvb2tpZSIsImlzQXBpIjpmYWxzZSwidXNlcklkIjozNTAzNTM3LCJ1c2VyS2V5IjoiOGQ4NTkzZWYtY2U2YS00MjQ3LTg1NzktM2NmMTg3MDE5NTlmIiwiY2xpZW50Q3VzdG9tZXJJZCI6MzIxNjY2MSwiaXNzdWVUeXBlIjoidXNlciIsIm5iZiI6MTczODUyMDQwNCwiaWRwIjoidXNlci1leHQtYXV0aCIsImN1c3RvbWVySWQiOjMyMTY2NjEsImV4cCI6MTczODUyMTA2NCwiaWF0IjoxNzM4NTIwNDY0LCJqdGkiOiIxMGZmNzg4Yy0yNWJhLTRlODItYjQxZC0zMzU5NTExYzQzZTEifQ.W57fpVMJm3xg9FGsvI7EdDR706ChGjDpzuCQ0w3nXGY",
        "priority": "u=1, i",
        "referer": "https://manage.searchad.naver.com/customers/3216661/tool/keyword-planner",
        "cookie": "NAC=QxawBcQ0b8SY; NNB=C4PCULYBJGJGO; nid_inf=108076668; NID_AUT=siaRT2oIzgxgaoHS87DFyK8MO0LRua/3I5YEJcqHVLkV2C1HdhAwz8fiKFhoa9Hx; NID_JKL=ANWQMDarLa7TEKbHC/8yQnrPxebOJcZDGl1mtDbCyW8=; _fwb=183oRB4JpEeireCK5QvEMvc.1738428443162; _fwb=183oRB4JpEeireCK5QvEMvc.1738428443162; NACT=1; NID_SES=AAABsY7uUy8XSIwQgmopbPXUi0tlAyXRUGGpT7yr3sC4JF9VNacXjjEnppNlpLor6fz6Yagl+3pcW0ervUX5tMNb6cV8qu8XaCDnuoZtJ1yhLLWsWTGZOFZGDlHZs20Y889YdxvpDiWwohZDRGg9KfXMXBsweFJnrqOsQMhVQiRnn9TYU5LFZrZKycvLV0A7kYN2lpOFQk1e7r99GDzgEn/DkAVSJ6lDfeSM8LJOz2tlLyB4Tr51NRV8vC/hjQBBbn7bC3A8QO92+EuveTn9q5mdpiFBTAi5cH9sLgSflOwxpfSJWOZDAwzxcvhQxXV/RX4RJMMNjSrMUWaDcTpOIm+GYRY0Lz074bA6EoGszyslHZ+OvdzS+UM0TEGvxH6qIQSI2wei11zwBAGirfwrPvHkeEIs3o/qkpGwILYQaqndCKkZEUBlk59UJ8lyd7lf8fAIMkm/7SNd1QzOM3zQ12tQ/ykJnYJ2gZjHLRAIdyYvOmXUr4Bxbqmktr1RNZy64y81sKKh0FMb3ygd56Uz5tLuce1Mn9CNatQZfDcYxdf8QrUpd9boFiaKbA2VAMGl+RxmkhGjwBiQof2yvsme9swtTIg=; SRT30=1738518434; 066c80626d06ffa5b32035f35cabe88d=%AD3%23%88%FC%DB%3Ey%FFx%A0j%AA%14f%0CR%05%C7%00%DF+%E6%08h%E0f%8F%5B%97VLr%FD%3A%DA%28IG%E6%DC9eI%E4%E8%1F%CF%00%A2%1C%0A%FB%24%CE%CB%A6%29%06%E0%3Es%05%89%23w%B8qq%91l%80%21%F6d%9F%2A%8D%3A%9Bd%02%BF%17%0B4%A1%2F%13%BF%1AW%FA%E6k6%E4%7D%90s%A2%05%CFmu%28%BCa%B4%AF%90%3E%C8Yq%0AN-T%B7%C6%F3%90%18H%DD0%FB%B0+%8E%E7%0C%18%DAA0%1D%E9%A7%A8%F8%99_; 1a5b69166387515780349607c54875af=k%7Dh%BA%12%80%81%D2; 1b25d439ceac51f5d414df7689017f6c=%AE%E2%BFK%3D%9B%07K%FD%15%0B%15%DC%97%95%C4%A3%B8%DD%E9%D6%3F%12a%3B%D6%CDj%DA%11%DCB%BB%2B%19%3B%C37%C1%CA%14%7D%7C%11%B9%15%25%83%13%EF%83%24%C1%CB%5C%3Ev%21%16V%BF%9Eq%8E%00%BBc%FBU%ECF%F2%1C-%E3%FFx%91%8F%CCz%0C%F2%7B%0A%03%BEP%DA%D5%C5p%60%96%F8%F0%02%97%C0%BC%D48%84%CE%FB%AB%F3%2B%C6Y6%DA%9D%831%D9%A6%AF%22%01%F7%94%CF_r%BBz%E0%04L%90%A8%FF3P%D7%CD%99A%1Ap%C7K%CD%14%D5%5C%110qp%FA%AD%E2%A5%2B%14%BE%AD%0FQO%0F%80%BB3%14a%2A%83%0F%C7%93%A6n%88%0B%22%AE%E4%F9%B76%A9%1B%B9%8E%ECkT%5C%96%5B%D5%EDB.%D1%CE%3B%A5%E66x%D8%C4%F1F6%AE%EB%C2%EB%E0%B1i%C3_Ev%EA%C3%AD%E3%0A%B8%91Q%95%3C%89%40%2FT%A5%05%92%EC%AE%0DF%E40%87%EF-%AA%9D%BE%E4%83%26%179%EA%10%D1%DA%AF%B6h%FBCF%BF%7F%83b%03%F6sN%96%85%03%F3%27%FF%DF%CC%00%B9%E4%8350%18%C4%9A%D0%CF%02%0D-%80%04%2B%A0%E0%5DL%8A%1B%ED%AEe%97%40Bn%F4%17%1A%E0%87%DB%F9I%E4%DAmt%1B%E2%D9%E0i%7F%9A%D0%CF%02%0D-%80%04u%EDs%AD%03%AF%EBl%3Ex%F9%7FH%89%AFP%BE%A9%EE%C8%E7%3B%12h%9D%C1%9A%FA%85%3E%FE%B7%1B%F6%92%7D%9E%AD%D2%7C%267%F3%E1%FC%A5%2B%24t0%A3H%F7%B2%D6%EB%2FJ%E0%F7%97%24%2A%85%8E%B9Q%C4k%BBz%90%FC%A2%D5%EF%98%2B%29%2F%3A%8E%14%94%EA%DE%FE9z%9A%D4%A0f%E3%3E%CC%DC%C0.LA%83%CB%14X%DB%F8%83%A4%AA%8B%08%E1%23%10D%0B%E8%F4%E8%D8%FF%14Z%90%0D%8Ci%0F%B2B%9Bwk%F0%B8%0D%BE%F2%5C%0B2Ix%F8C%FFA%B8%94ey%AC+%DE%94%F7%0A4%ED%05g%87j%B3Y%7C%09%A4%409%DC%C0u%F3%DC8.%F1%FD%8Cl3%9E%EA%90%C9I%C9%A6%E3X%E9F%95%CD%BFF%92+%D9%3F%A2%F1%F3U0V%EE%40%10d_%DD%B8%16%A6Y%E66%FB%DD%9B%AF4%0D%7Bz%0E%8A%CD%D3%97%E9%8A%15%ED%97V%8A%7C%CF1%FD%3C%85%7F%A9%60%28%15%C2+I72; hxq1clp=shown; nsac_show_autologin_popup=0; page_uid=iH+ykwqo1aVssk6SWXossssstM8-302381; BUC=I_zPdT6at1AK9wzL7LEIBRQPahReC7cwiFi75w09p8Y=; wcs_bt=2413704dbffb64:1738519863",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "x-accept-language": "ko"
    }



    # GET 요청 보내기
    response = requests.get(base_url, headers=headers, params=params)


    # 응답 처리
    if response.status_code == 200:
        try:
            data = response.json()
            keyword_list = data.get("keywordList", [])
            for kw in keyword_list:
                if kw['relKeyword'] == keyword:
                    return kw
        except ValueError:
            print("응답이 JSON 형식이 아닙니다.")
    else:
        print(f"요청 실패: 상태 코드 {response.status_code}")
    return None



# region
# ══════════════════════════════════════════════════════
# 메인 초기화
# ══════════════════════════════════════════════════════


# 최초 시작 메인
if __name__ == "__main__":
    kw = search_keyword_cnt('평택맛집')
    print('kw : ', kw)

# ══════════════════════════════════════════════════════
# endregion