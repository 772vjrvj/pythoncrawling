import time
import random
import requests
from bs4 import BeautifulSoup
import re
import json

def get_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def process_author_info(url):
    soup = get_soup(url)
    author_span = soup.find("span", itemprop="author", itemscope=True, itemtype="http://schema.org/Person")
    if author_span:
        author_url = author_span.find("link", itemprop="url")["href"]
        return f"{author_url}/videos"
    return None

def extract_published_time(url):
    soup = get_soup(url)
    scripts = soup.find_all("script")

    for script in scripts:
        if script.string and "ytInitialData" in script.string:
            json_text = re.search(r"var ytInitialData = ({.*?});", script.string, re.DOTALL)
            if json_text:
                try:
                    yt_data = json.loads(json_text.group(1))
                    tabs = yt_data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
                    for tab in tabs:
                        rich_grid_renderer = tab.get("tabRenderer", {}).get("content", {}).get("richGridRenderer", {})
                        for item in rich_grid_renderer.get("contents", []):
                            video_renderer = item.get("richItemRenderer", {}).get("content", {}).get("videoRenderer", {})
                            if video_renderer.get("publishedTimeText"):
                                return video_renderer["publishedTimeText"]["simpleText"]
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    return None
    return None

def main():
    urls = [
        "https://www.youtube.com/watch?v=QFHpl362P5U&t=47s",
        "https://www.youtube.com/watch?v=6i-bHf3OiIg",
        "https://www.youtube.com/watch?v=uUWdYkAIGtU",
        "https://www.youtube.com/c/danbiii/videos",
        "https://www.youtube.com/watch?v=PMhkuv3xLTA&t=120s",
        "https://www.youtube.com/channel/UCfAmK0K_H6e2xQSz_uIJMJg/videos",
        "https://www.youtube.com/watch?v=OSLXQOEsYDc&t=9s",
        "https://www.youtube.com/watch?v=a-H-SMInU18&t=123s",
        "https://www.youtube.com/watch?v=7-HCVk-9jFY",
        "https://www.youtube.com/watch?v=yqVYEQW089E&t=46s",
        "https://www.youtube.com/watch?v=tDmrMCBgELk&t=23s"
    ]

    for idx, url in enumerate(urls, start=1):
        print(f"Processing URL {idx}: {url}")

        video_url = None
        if "/watch" in url:
            video_url = process_author_info(url)
        if not video_url:
            video_url = url

        result = extract_published_time(video_url)
        print(f"Result for URL {idx}: {result or 'Not found'}")

        # 요청 사이에 랜덤한 대기 시간 추가
        time.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    main()
