import re
import time
from urllib.parse import urlparse
import json

import requests

director = ""

# 쿠팡 api 호출 테스트

def _extract_id_from_url(url):
    # URL을 파싱
    parsed_url = urlparse(url)

    # path에서 play/ 또는 titles/ 다음에 오는 값을 정규식으로 추출
    match = re.search(r'/(play|titles)/([^/]+)', parsed_url.path)

    # 값 반환 (없으면 None)
    return match.group(2) if match else None

def _fetch_place_info(main_url, result):
    base_url = "https://discover.coupangstreaming.com/v1/discover/titles/"
    uuid = _extract_id_from_url(main_url)
    url = f"{base_url}{uuid}"
    headers = {}

    max_retries = 3  # 최대 재시도 횟수

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                result['error'] = 'Y'
                result['message'] = f"{data['error'].get('status', '')} {data['error'].get('name', '')}"
                break

            if not director:
                _fetch_director(data, base_url, headers)

            _extract_data(data, result, main_url)
            break

        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                result['error'] = 'Y'
                result['message'] = f"서버 호출 에러, 최대 재시도 횟수를 초과했습니다.: {e}"
                break
            time.sleep(1)

def _fetch_director(data, base_url, headers):
    global director
    parent_id = data["data"].get("parent_id")
    if parent_id:
        parent_url = f"{base_url}{parent_id}"
        parent_res = requests.get(parent_url, headers=headers)
        parent_res.raise_for_status()
        parent_data = parent_res.json()
        director = ", ".join(
            person["name"] for person in parent_data["data"].get("people", []) if person["role"] == "DIRECTOR"
        )

def _extract_data(data, result, main_url):
    result.update({
        "url": main_url,
        "title": data["data"].get("title", ""),
        "episode_synopsis": data["data"].get("description", ""),
        "episode_title": data["data"].get("short_description", ""),
        "episode_seq": str(data["data"].get("episode", "")),
        "episode_season": str(data["data"].get("season", "")),
        "year": str(data["data"].get("meta", {}).get("releaseYear", "")),
        "season": str(data["data"].get("season", "")),
        "rating": data["data"].get("rating", {}).get("age", ""),
        "genre": ", ".join(
            tag["label"] for tag in data["data"].get("tags", []) if tag.get("meta", {}).get("genre")
        ),
        "summary": data["data"].get("description", ""),
        "cast": ", ".join(
            person["name"] for person in data["data"].get("people", []) if person["role"] == "CAST"
        ),
        "director": director or ", ".join(
            person["name"] for person in data["data"].get("people", []) if person["role"] == "DIRECTOR"
        ),
        "success": "O",
        "message": "데이터 추출 성공",
        "error": "X"
    })

if __name__ == "__main__":
    ## https://discover.coupangstreaming.com/v1/discover/titles/fb2bb8b0-a544-4be1-8489-83cb38adad05
    url = "https://www.coupangplay.com/play/00e36596-f0b5-4082-80a4-1d8e5f759dcd"

    result = {}

    _fetch_place_info(url, result)

    print(json.dumps(result, ensure_ascii=False, indent=4))