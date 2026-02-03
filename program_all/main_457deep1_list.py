# -*- coding: utf-8 -*-
import httpx
import json


# 필기 후기
URL = "https://457deep.com/community/resume-review?page=200"
HEADERS = {
    "rsc": "1",
    "next-url": "/community/resume-review",
    "referer": "https://457deep.com/community/resume-review",
    "user-agent": "Mozilla/5.0"
}



def fetch_posts():
    text = httpx.get(URL, headers=HEADERS, timeout=30).text

    i = text.find('"posts":')
    i = text.find('[', i)

    depth = 0
    for j in range(i, len(text)):
        if text[j] == '[':
            depth += 1
        elif text[j] == ']':
            depth -= 1
            if depth == 0:
                return json.loads(text[i:j + 1])
    return []

if __name__ == "__main__":
    posts = fetch_posts()
    print(posts)

