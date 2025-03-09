import csv
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# 입력 및 출력 CSV 경로
input_csv_path = "DB/KOHLS_Men_Mess Bottoms_Shorts.csv"
output_csv_path = "DB/KOHLS_Men_Mess Bottoms_Shorts_Processed.csv"

# Selenium WebDriver 설정
chrome_options = Options()
# chrome_options.add_argument("--headless")  # GUI 없이 실행
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0")

service = Service(executable_path="chromedriver")  # ChromeDriver 경로 설정
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
# 객체 리스트
product_list = []

# CSV 파일 읽기
with open(input_csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for index, row in enumerate(reader):
        time.sleep(2)
        product_url = row.get("product_url", "").strip()
        product_fabric_care = row.get("product_fabric_care", "").strip()
        product_id = row.get("product_id", "").strip()

        print(f"==============================")
        if not product_fabric_care == "[]":
            print(f"생략X index: {index}")
            product_list.append(row)
            continue  # URL이 없으면 스킵
        else:
            print(f"진행O index: {index}")
            print(f"product_id: {product_id}")
            print(f"크롤링 중: {product_url}")
            # Selenium으로 페이지 열기
            driver.get(product_url)
            time.sleep(2)  # 페이지 로딩 대기

            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # FABRIC & CARE 섹션 찾기
            fabric_section = soup.find("p", string="FABRIC & CARE")
            product_fabric_care = []
            if fabric_section:
                ul_tag = fabric_section.find_next_sibling("ul")
                if ul_tag:
                    product_fabric_care = [li.get_text(strip=True) for li in ul_tag.find_all("li")]

            print(f"product_fabric_care: {product_fabric_care}")

            # 기존 데이터 유지 + product_fabric_care 추가
            row["product_fabric_care"] = product_fabric_care  # 배열 그대로 유지
            product_list.append(row)

# WebDriver 종료
driver.quit()

# 결과 CSV 파일로 저장 (JSON 문자열로 저장)
with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = list(product_list[0].keys())  # 기존 필드 + product_features
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for product in product_list:
        product["product_fabric_care"] = json.dumps(product["product_fabric_care"], ensure_ascii=False)  # JSON 문자열 변환
        writer.writerow(product)

print(f"처리 완료: {output_csv_path}")
