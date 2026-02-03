# -*- coding: utf-8 -*-
import httpx, json

URL = "https://457deep.com/community/success-story/detail/cmhtzltqb001es27w52ictj06?_rsc=qyxkw"
HEADERS = {
    "rsc": "1",
    "next-url": "/community/success-story",
    "referer": "https://457deep.com/community/success-story?page=6",
    "user-agent": "Mozilla/5.0",
}

def _extract_json_obj(text: str, key: str):
    k = text.find(f'"{key}":')
    if k < 0:
        return None
    i = text.find('{', k)
    if i < 0:
        return None

    d = 0
    for j in range(i, len(text)):
        ch = text[j]
        if ch == '{':
            d += 1
        elif ch == '}':
            d -= 1
            if d == 0:
                return json.loads(text[i:j+1])
    return None

def fetch_post():
    with httpx.Client(http2=True, headers=HEADERS, timeout=30) as c:
        r = c.get(URL)
        r.raise_for_status()
        t = r.text  # ✅ httpx가 알아서 디코딩까지 처리

    post = _extract_json_obj(t, "post")
    if post is None:
        raise RuntimeError("post not found in response")
    return post

if __name__ == "__main__":
    post = fetch_post()
    print(post)
