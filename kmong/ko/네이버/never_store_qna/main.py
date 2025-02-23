import requests
import pandas as pd
from datetime import datetime
import time

# 날짜 변환 함수 (ISO -> 한국시간 yyyy-MM-dd HH:mm)
def convert_datetime(iso_date):
    if iso_date:
        dt = datetime.strptime(iso_date[:16], "%Y-%m-%dT%H:%M")
        return dt.strftime("%Y-%m-%d %H:%M")
    return ""

# 📌 1. 댓글 가져오기
def fetch_comments():
    url = "https://sell.smartstore.naver.com/api/v3/contents/comments/pages"
    params = {
        "commentType": "",
        "endDate": "2024-04-24T23:59:59.999+09:00",
        "keyword": "",
        "page": 0,
        "range": 5,
        "searchKeywordType": "PRODUCT_NAME",
        "sellerAnswer": "",
        "size": 1000,
        "startDate": "2024-01-01T00:00:00.000+09:00",
        "totalCount": 0
    }
    cookie = 'NAC=QxawBcQ0b8SY; NNB=C4PCULYBJGJGO; _fwb=145RCfYw8FcC6joPueguwLj.1737783298431; NACT=1; SRT30=1740296863; nid_inf=1971242080; NID_AUT=oVwTFncMIo5QBJrJWK8XOdOI3H436FDKjbbk4yVXRZzBQ1T3euXQB2s19rX/duZj; NID_JKL=Z+MVVtZOgkIpikhr4k1PxFQCsjQpV9VGDduSfHRSC3k=; NID_SES=AAABizc7d7dsYikUW35uQXFIriACVOkFchvXzeT7IXluvcJwatjcYv39JnMt/gxtCkmxzgl8mynCk38SADGMkfGgv8GwuA0Mqv+56pyTlgaxo5D5T0iSD7SzVKSqsFUhQi0LTUtExqb6BbwqZTNZ2AAS10Q1Julh/19PsBIhho6qimzVCud+TWMkg1pQRQ1XEQ6FP5tc4yl6bikHwkN/Tgi3lfRBvBpKSCRs91Sim7yaWTgeR1kRzCOtyEziIQlOUPEslTbSWNrxx9prT+4IIEIrIpfZc5vLuESyr13proKhAN1N1rjIBW6qlfjuAjvhIRb5NWaJfEeltJf3KPfI0Pg17dljoNDaCodyTWA6Rz2Lh9esXbkw9OC+GmYU5Y7d55yNh2vziRmHjYVr9AFCvBzYmSnl3vI99uESZfUDvurNiPy3FAbPdrCCXovWI/F43PdWJMOJedtqcfhGraVob2gLgg/vSAK8m7PXDTlD5NZWgqXE5RuAQ9lEJXBOwqKH7bJs/WG9Vsb7s8OBW3qg24Xwgso=; CBI_SES=unUCYL18E3acwozN4Bt2fxVGTQbg9yhQqK9k9R68E7OBMJVzMBLlcC4L1Dh+iCs8PTZoUf3OGgpa08DALd+JEZ8SuqBjWf1FBjjX9RYVUmHwlL77y/hFPzoa+qIpTr8kiIfB9i9Bi9NiDMJy/7zkI5oQoRTr5fJmllzX8q3c+sjqhwjjbrfp+0YD1Wo0WuaxVvFVWzQx6ia/8moY3ZwXaYsZ5LEjzwYA3vR429bO/fKgePRQJ77+EMJoS/bdE/V2kImr5OgPEkCcvkP08/52IwJfWpf3qfu+69TkWglIoHl3SRx6Z5pVSSE5hA511ZOMnZi/3jcVW5p3TrMdMWM/76H2aXmDgzakJ+R0KHIAcwFXqyT/Olpoi8tJ3VaPCkuxXujegilB3JzYQh4+awiHjVymGTc18ho2WJSmBkRpYGoEfJy9bAIj0aZKOQVrDk55QjjWvCK7OFvGI8+AnIN1IA6YswGZ/KWU+z6g93Y8oJI=; CBI_CHK="r5V0mf9uRUZHZ/vmLGy3ez7f4/k4aqWXL5o03eN68fqYjukDBGvrehvgTUH/BWMsLN0VXYEOb6dWZHFDyZXSkHVHlbv5K7Pc5VFFWdqrLALXmtRlPyl9JA6I2hnJLrm3VyBScRJCVeqIHkWK1I/BS8touN3QL8Nw9ODIvAfHAZ0="; SRT5=1740302328; NSI=sWDihU5UEgMJ18ujDf9TSff6ZqbMkchpGagSRpNr; BUC=nd6Gwue-_fwy0yP3fryecSx2fREcVBUJdJCy04VBjnQ='

    headers = {  # 주어진 헤더 그대로 사용
        "authority": "sell.smartstore.naver.com",
        "method": "GET",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://sell.smartstore.naver.com/",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-current-state": "https://sell.smartstore.naver.com/#/comment/",
        "x-current-statename": "main.contents.comment",
        "x-to-statename": "main.contents.comment",
        "cookie": f'{cookie}'  # 쿠키는 비워둠
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return []

    data = response.json()
    comments = []

    if "contents" in data:
        for item in data["contents"]:
            comment = {
                "상품 이름": item.get("productName"),
                "상품 번호": item.get("contentsObjectId"),
                "상품 등록일": convert_datetime(item.get("modDate")),
                "문의 KEY": item.get("id"),
                "문의 작성자": item.get("maskedWriterId"),
                "문의 내용": item.get("commentContent"),
            }
            comments.append(comment)

    return comments

# 📌 2. 답변 가져오기
def fetch_replies(comment_id):
    url = f"https://sell.smartstore.naver.com/api/v3/contents/comments/{comment_id}/replies"

    cookie = 'NAC=QxawBcQ0b8SY; NNB=C4PCULYBJGJGO; _fwb=145RCfYw8FcC6joPueguwLj.1737783298431; NACT=1; SRT30=1740296863; nid_inf=1971242080; NID_AUT=oVwTFncMIo5QBJrJWK8XOdOI3H436FDKjbbk4yVXRZzBQ1T3euXQB2s19rX/duZj; NID_JKL=Z+MVVtZOgkIpikhr4k1PxFQCsjQpV9VGDduSfHRSC3k=; NID_SES=AAABizc7d7dsYikUW35uQXFIriACVOkFchvXzeT7IXluvcJwatjcYv39JnMt/gxtCkmxzgl8mynCk38SADGMkfGgv8GwuA0Mqv+56pyTlgaxo5D5T0iSD7SzVKSqsFUhQi0LTUtExqb6BbwqZTNZ2AAS10Q1Julh/19PsBIhho6qimzVCud+TWMkg1pQRQ1XEQ6FP5tc4yl6bikHwkN/Tgi3lfRBvBpKSCRs91Sim7yaWTgeR1kRzCOtyEziIQlOUPEslTbSWNrxx9prT+4IIEIrIpfZc5vLuESyr13proKhAN1N1rjIBW6qlfjuAjvhIRb5NWaJfEeltJf3KPfI0Pg17dljoNDaCodyTWA6Rz2Lh9esXbkw9OC+GmYU5Y7d55yNh2vziRmHjYVr9AFCvBzYmSnl3vI99uESZfUDvurNiPy3FAbPdrCCXovWI/F43PdWJMOJedtqcfhGraVob2gLgg/vSAK8m7PXDTlD5NZWgqXE5RuAQ9lEJXBOwqKH7bJs/WG9Vsb7s8OBW3qg24Xwgso=; CBI_SES=unUCYL18E3acwozN4Bt2fxVGTQbg9yhQqK9k9R68E7OBMJVzMBLlcC4L1Dh+iCs8PTZoUf3OGgpa08DALd+JEZ8SuqBjWf1FBjjX9RYVUmHwlL77y/hFPzoa+qIpTr8kiIfB9i9Bi9NiDMJy/7zkI5oQoRTr5fJmllzX8q3c+sjqhwjjbrfp+0YD1Wo0WuaxVvFVWzQx6ia/8moY3ZwXaYsZ5LEjzwYA3vR429bO/fKgePRQJ77+EMJoS/bdE/V2kImr5OgPEkCcvkP08/52IwJfWpf3qfu+69TkWglIoHl3SRx6Z5pVSSE5hA511ZOMnZi/3jcVW5p3TrMdMWM/76H2aXmDgzakJ+R0KHIAcwFXqyT/Olpoi8tJ3VaPCkuxXujegilB3JzYQh4+awiHjVymGTc18ho2WJSmBkRpYGoEfJy9bAIj0aZKOQVrDk55QjjWvCK7OFvGI8+AnIN1IA6YswGZ/KWU+z6g93Y8oJI=; CBI_CHK="r5V0mf9uRUZHZ/vmLGy3ez7f4/k4aqWXL5o03eN68fqYjukDBGvrehvgTUH/BWMsLN0VXYEOb6dWZHFDyZXSkHVHlbv5K7Pc5VFFWdqrLALXmtRlPyl9JA6I2hnJLrm3VyBScRJCVeqIHkWK1I/BS8touN3QL8Nw9ODIvAfHAZ0="; SRT5=1740302328; NSI=sWDihU5UEgMJ18ujDf9TSff6ZqbMkchpGagSRpNr; BUC=nd6Gwue-_fwy0yP3fryecSx2fREcVBUJdJCy04VBjnQ='

    headers = {  # 주어진 답변 헤더 그대로 사용
        "authority": "sell.smartstore.naver.com",
        "method": "GET",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://sell.smartstore.naver.com/",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-current-state": "https://sell.smartstore.naver.com/#/comment/",
        "x-current-statename": "main.contents.comment",
        "x-to-statename": "main.contents.comment",
        "cookie": f"{cookie}"  # 쿠키는 비워둠
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return []

    data = response.json()
    replies = []

    for item in data:
        reply = {
            "답변 KEY": item.get("id"),
            "답변 내용": item.get("commentContent"),
            "답변 등록일": convert_datetime(item.get("modDate"))
        }
        replies.append(reply)

    return replies

# 📌 3. Excel 저장
def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Excel 파일 저장 완료: {filename}")

# 📌 4. 메인 실행
def main():
    comments = fetch_comments()

    # 댓글의 답변 가져오기
    all_data = []
    for comment in comments:
        print(comment)
        time.sleep(0.5)
        replies = fetch_replies(comment["문의 KEY"])

        if replies:
            for reply in replies:
                new_comment = comment.copy()  # 원 댓글 복사
                new_comment["답변 KEY"] = reply["답변 KEY"]
                new_comment["답변 내용"] = reply["답변 내용"]
                new_comment["답변 등록일"] = reply["답변 등록일"]
                all_data.append(new_comment)
        else:
            comment["답변 KEY"] = ""
            comment["답변 내용"] = ""
            comment["답변 등록일"] = ""
            all_data.append(comment)

    # Excel로 저장
    save_to_excel(all_data, "comments_data.xlsx")

if __name__ == "__main__":
    main()
