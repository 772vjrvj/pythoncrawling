import requests
import json
import math
import time

# 전역 변수 설정
totalPages = 0
result_index = None

def get_naver_blog_search(count_per_page, current_page, keyword):
    # URL과 파라미터 설정
    url = "https://section.blog.naver.com/ajax/SearchList.naver"
    params = {
        "countPerPage": count_per_page,
        "currentPage": current_page,
        "endDate": "",
        "keyword": keyword,
        "orderBy": "sim",
        "startDate": "",
        "type": "post"
    }

    # 헤더 설정 (쿠키 제외)
    headers = {
        "authority": "section.blog.naver.com",
        "method": "GET",
        "path": "/ajax/SearchList.naver",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=1, i",
        "referer": f"https://section.blog.naver.com/BlogHome.naver?directoryNo=0&currentPage={current_page}&groupId=0",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    # GET 요청 보내기
    response = requests.get(url, headers=headers, params=params)

    # 응답 상태 코드 확인
    if response.status_code == 200:
        try:
            # 응답을 텍스트로 읽고, 앞의 불필요한 문자열을 제거
            text_data = response.text
            if text_data.startswith(")]}',"):
                text_data = text_data[5:]  # 불필요한 문자열 제거

            # JSON 파싱
            data = json.loads(text_data)

            return {
                "pagePerCount": data.get("result", {}).get("pagePerCount"),
                "totalCount": data.get("result", {}).get("totalCount"),
                "searchList": data.get("result", {}).get("searchList")
            }
        except json.JSONDecodeError:
            print("JSON 디코딩 오류가 발생했습니다. 응답 내용:", response.text)
    else:
        print("요청 실패, 상태 코드:", response.status_code)
        print("응답 내용:", response.text)

    return None

def find_target_log(keyword, target_log_no):
    count_per_page = 7
    current_page = 1

    # 첫 페이지 조회
    result = get_naver_blog_search(count_per_page, current_page, keyword)
    print("진행중 페이지:", 1)
    if result:
        total_count = result["totalCount"]
        totalPages = math.ceil(total_count / count_per_page)  # 전체 페이지 수 계산

        # 첫 페이지에서 target_log_no 찾기
        for index, item in enumerate(result["searchList"]):
            if item.get("logNo") == int(target_log_no):
                result_index = index + 1
                print("찾은 페이지:", current_page)
                print("찾은 위치:", result_index)
                return result_index

        # 첫 페이지에 없다면 다음 페이지부터 탐색
        for page in range(2, totalPages + 1):
            print("진행중 페이지:", page)
            time.sleep(1)
            result = get_naver_blog_search(count_per_page, page, keyword)

            if result:
                for index, item in enumerate(result["searchList"]):
                    if item.get("logNo") == int(target_log_no):
                        # 해당 페이지에서 찾은 경우
                        result_index = count_per_page * (page - 1) + (index + 1)
                        print("찾은 페이지:", page)
                        print("찾은 위치:", result_index)
                        return result_index

    print("logNo를 찾을 수 없습니다.")
    return None


def main():
    # 파라미터 설정
    keyword = "광명시호프집"
    target_log_no = "223616675523"

    # keyword = "3루점"
    # target_log_no = "223616683550"

    keyword = "봉구통닭"
    target_log_no = "223616674787"

    # logNo 찾기
    result_number = find_target_log(keyword, target_log_no)
    print(f'result_number : {result_number}')

if __name__ == "__main__":
    main()
