import os
import pandas as pd

# 설정
EXCEL_PATH = "YUPOO_20250711012843.xlsx"  # 입력 파일
OUTPUT_PATH = "YUPOO_20250711012843_완성본.xlsx"  # 출력 파일
IMAGE_FOLDER = "images/yupoo"  # 이미지 경로
BASE_URL = "https://trendell.store/data/editor/yupoo"  # 이미지 주소 prefix

# 엑셀 불러오기
df = pd.read_excel(EXCEL_PATH, dtype=str)
df.fillna("", inplace=True)

def process_row(row):
    product_id = str(row["상품ID"]).strip()
    image_dir = os.path.join(IMAGE_FOLDER, product_id)

    if not os.path.isdir(image_dir):
        return "", ""  # 폴더 없으면 빈 값 반환

    image_files = sorted([
        f for f in os.listdir(image_dir)
        if f.startswith(f"{product_id}_") and f.endswith(".jpg")
    ])

    # 이미지1 설정
    image1_filename = f"{product_id}_0.jpg"
    image1 = f"{product_id}/{image1_filename}" if image1_filename in image_files else ""

    # 상품설명 HTML 구성
    html_blocks = []
    for f in image_files:
        if f == image1_filename:
            continue  # 이미지1 제외
        full_url = f"{BASE_URL}/{product_id}/{f}"
        block = (
            f'<p><img src="{full_url}" title="{f}" alt="{f}">'
            f'<br style="clear:both;"></p>'
        )
        html_blocks.append(block)

    description_html = "\n".join(html_blocks)
    return description_html, image1

# 상품설명과 이미지1 컬럼 채우기
df[["상품설명", "이미지1"]] = df.apply(process_row, axis=1, result_type="expand")

# 엑셀로 저장
df.to_excel(OUTPUT_PATH, index=False)
print(f"✅ 저장 완료: {OUTPUT_PATH}")
