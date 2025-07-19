import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 요청 대상 URL
album_url = "https://tbstore.x.yupoo.com/albums/133511037?uid=1&isSubCate=true&referrercate=185689"

# 헤더 (쿠키는 사용자가 직접 삽입)
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "ko-KR,ko;q=0.9",
    "referer": "https://tbstore.x.yupoo.com/categories/185689?isSubCate=true&page=2",
    "cookie": "여기에_쿠키_붙여주세요"
}

# 요청
res = requests.get(album_url, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

# 상품 ID
product_id = urlparse(album_url).path.split("/")[2]

# 제목 + 가격 추출
title_tag = soup.select_one(".showalbumheader__gallerydec h2")
price = name = ""
if title_tag:
    text = title_tag.get_text(strip=True)
    if '/' in text:
        parts = text.split('/', 1)
        price = parts[0].strip()
        name = parts[1].strip()
    else:
        name = text.strip()

# 사이즈 추출
size_text = soup.select_one(".showalbumheader__gallerysubtitle.htmlwrap__main")
size = ""
if size_text:
    for token in size_text.get_text(strip=True).split():
        if "-" in token and any(c.isdigit() for c in token):
            size = token
            break

# 이미지 저장 경로
save_dir = os.path.join("images", "yupoo", product_id)
os.makedirs(save_dir, exist_ok=True)

# 대표 이미지 저장
cover_img = soup.select_one(".showalbumheader__gallerycover img")
if cover_img and cover_img.get("src"):
    img_url = "https:" + cover_img["src"]
    img_data = requests.get(img_url, headers=headers).content
    with open(os.path.join(save_dir, f"{product_id}_0.jpg"), "wb") as f:
        f.write(img_data)

# 서브 이미지 저장
sub_imgs = soup.select(".showalbum__children.image__main img")
for idx, img in enumerate(sub_imgs, 1):
    img_url = "https:" + img["src"]
    img_data = requests.get(img_url, headers=headers).content
    with open(os.path.join(save_dir, f"{product_id}_{idx}.jpg"), "wb") as f:
        f.write(img_data)

# 출력 확인
print(f"상품ID: {product_id}")
print(f"상품명: {name}")
print(f"가격: {price}")
print(f"사이즈: {size}")
print(f"저장 완료: {len(sub_imgs) + 1}장 → {save_dir}")
