from selenium import webdriver
from bs4 import BeautifulSoup
import csv
import os
import time

def setup_driver():
    """
    Set up Selenium WebDriver.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 브라우저 창을 표시하지 않음
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    return driver

def fetch_html_with_selenium(driver, url):
    """
    Use Selenium to fetch HTML content from the given URL.
    """
    driver.get(url)
    time.sleep(5)  # JavaScript 로딩 대기
    return driver.page_source

def parse_table(html):
    """
    Parse the HTML to extract tables within the specified class.
    Returns a list of parsed tables as 2D lists (header + rows).
    """
    soup = BeautifulSoup(html, 'html.parser')
    divs = soup.select('.table_type01.transverse_scroll.cbox')  # Select the div
    combined_data = []

    for div_index, div in enumerate(divs):
        tables = div.find_all('table')  # Find tables within the div
        for table_index, table in enumerate(tables):
            headers = []
            rows = []

            # Extract headers from thead
            thead = table.find('thead')
            if thead:
                for tr in thead.find_all('tr'):
                    headers.append([th.text.strip() for th in tr.find_all('th')])

            # Extract rows from tbody
            tbody = table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    rows.append([td.text.strip() for td in tr.find_all('td')])

            # Add headers and rows to combined_data
            if headers:
                combined_data.append(headers[0])  # 첫 번째 줄만 추가 (공통 헤더로 가정)
            combined_data.extend(rows)

    return combined_data

def save_to_csv(combined_data, filename):
    """
    Save the combined table data to a single CSV file.
    """
    output_dir = "output_files"
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
    filepath = os.path.join(output_dir, filename)
    with open(filepath, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerows(combined_data)

def process_url(driver, url, output_filename):
    """
    Process a single URL: fetch, parse, and save the table data.
    """
    print(f"Processing URL: {url}")
    html = fetch_html_with_selenium(driver, url)
    combined_data = parse_table(html)
    print(f"Found {len(combined_data)} rows of data in {url}")
    save_to_csv(combined_data, output_filename)
    print(f"Saved data to {output_filename}")

def main():
    urls = [
        "https://statiz.sporki.com/stats/?m=team&m2=pitching&m3=value&so=&ob=&year=2020&sy=2020&ey=2020&te=&po=&lt=10100&reg=&pe=&ds=&de=&we=&hr=&ha=&ct=&st=&vp=&bo=&pt=&pp=&ii=&vc=&um=&oo=&rr=&sc=&bc=&ba=&li=&as=&ae=&pl=&gc=&lr=&pr=50&ph=&hs=&us=&na=&ls=&sf1=&sk1=&sv1=&sf2=&sk2=&sv2=",
        "https://statiz.sporki.com/stats/?m=team&m2=fielding&m3=default&so=&ob=&year=2020&sy=2020&ey=2020&te=&po=&lt=&reg=&pe=&ds=&de=&we=&hr=&ha=&ct=&st=&vp=&bo=&pt=&pp=&ii=&vc=&um=&oo=&rr=&sc=&bc=&ba=&li=&as=&ae=&pl=&gc=&lr=&pr=50&ph=&hs=&us=&na=&ls=&sf1=&sk1=&sv1=&sf2=&sk2=&sv2="
    ]

    driver = setup_driver()

    try:
        for idx, url in enumerate(urls, start=1):
            output_filename = f"output_table_{idx}.csv"
            process_url(driver, url, output_filename)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
