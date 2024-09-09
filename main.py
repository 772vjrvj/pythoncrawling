import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import traceback

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

def parse_naver(driver, Name, Naver_url, limit_count):
    merge_list = []
    try:
        driver.get(Naver_url)
        time.sleep(3)

        driver.find_elements(By.CSS_SELECTOR, '[data-shp-contents-type="카드할인가 정렬"]')[0].click()  # 카드할인
        time.sleep(0.5)

        opt_name = driver.execute_script('return document.querySelector("#section_price em").closest("div");').text.split(" : ")[0].split(',')[-1]
        print(f"Naver 옵션 이름: {opt_name}")

        if len(driver.find_elements(By.CSS_SELECTOR, f'.condition_area a[data-shp-contents-type="{opt_name}"] .info')) != 0:
            Qtys = driver.find_elements(By.CSS_SELECTOR, f'.condition_area a[data-shp-contents-type="{opt_name}"] .info')
        elif len(driver.find_elements(By.CSS_SELECTOR, '.condition_area a .info')) != 0:
            Qtys = driver.find_elements(By.CSS_SELECTOR, '.condition_area a .info')

        Qlist = [q.text for q in Qtys]
        print(f"Naver 옵션 리스트: {Qlist}")

        for p in range(len(Qtys)):
            driver.find_element(By.CSS_SELECTOR, f'[data-shp-contents-id="{Qlist[p]}"]').click()
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, 0);")

            uls = driver.find_elements(By.CSS_SELECTOR, '#section_price ul')
            for e in uls:
                if 'productList_list_seller' in e.get_attribute('class'):
                    ul_class = e.get_attribute('class').replace(' ', '.')

            prod_list = driver.find_elements(By.CSS_SELECTOR, f'#section_price .{ul_class} li')

            action = ActionChains(driver)
            action.move_to_element(prod_list[0]).perform()
            time.sleep(1)

            for e in prod_list:
                try:
                    mall_name = e.find_element(By.CSS_SELECTOR, '[data-shp-area="prc.mall"] img').get_attribute('alt')
                    prod_name = e.find_element(By.CSS_SELECTOR, '[data-shp-area="prc.pd"]').text
                    price = e.find_element(By.CSS_SELECTOR, '[data-shp-area="prc.price"]').text.replace('최저', '').strip()

                    temp_list = [Name, '네이버', Qlist[p], mall_name, '', prod_name, price]
                    merge_list.append(temp_list)
                except Exception as err:
                    print(f"Error parsing Naver: {traceback.format_exc()}")
    except Exception as e:
        print(f"Error during Naver parsing: {traceback.format_exc()}")

    return merge_list

def parse_danawa(driver, Name, Danawa_url, limit_count):
    merge_list = []
    try:
        driver.get(Danawa_url)
        time.sleep(2)

        if driver.find_elements(By.XPATH, '//*[@id="bundleProductMoreOpen"]') != []:
            driver.find_element(By.XPATH, '//*[@id="bundleProductMoreOpen"]').click()

        danawa_opt_url_list = [e.get_attribute('href') for e in driver.find_elements(By.CSS_SELECTOR, '[class="othr_list"] li .chk a')]
        danawa_opt_text_list = [e.text for e in driver.find_elements(By.CSS_SELECTOR, '[class="othr_list"] li .chk a')]

        for ii in range(len(danawa_opt_url_list)):
            if danawa_opt_text_list[ii] == '1개':
                continue

            driver.get(danawa_opt_url_list[ii])
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, 0);")
            driver.find_elements(By.CSS_SELECTOR, '.cardSaleChkbox')[0].click()
            time.sleep(1)

            html = driver.page_source
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            free_dil_prod_e_list = soup.select('.columm.left_col .diff_item')
            for ei in range(len(free_dil_prod_e_list)):
                if ei > limit_count: break
                try:
                    mall_name = soup.select('.columm.left_col .diff_item')[ei].select('img')[0].get('alt')
                    prod_name = soup.select('.columm.left_col .diff_item')[ei].select('.info_line')[0].text.strip()
                    price = soup.select('.columm.left_col .diff_item')[ei].select('.prc_c')[0].text
                    temp_list = [Name, '다나와', danawa_opt_text_list[ii], mall_name, '무료배송', prod_name, price]
                    merge_list.append(temp_list)
                except Exception as err:
                    print(f"Error parsing Danawa: {traceback.format_exc()}")
    except Exception as e:
        print(f"Error during Danawa parsing: {traceback.format_exc()}")

    return merge_list

def parse_enuri(driver, Name, Enuri_url, limit_count):
    merge_list = []
    try:
        driver.get(Enuri_url)
        time.sleep(0.5)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")

        time.sleep(0.5)

        if len(driver.find_elements(By.CSS_SELECTOR, '#prod_option .adv-search__btn--more')) != 0:
            driver.find_element(By.CSS_SELECTOR, '#prod_option .adv-search__btn--more').click()

        time.sleep(1)

        radio_opts = driver.find_elements(By.CSS_SELECTOR, '[name="radioOPTION"]')
        xpath_list = [ '//*[@for="' + e.get_attribute('id') + '"]' for e in radio_opts]

        for eei, e in enumerate(radio_opts):
            time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 0);")

            elem = driver.find_element(By.XPATH, xpath_list[eei])

            how_many = elem.text.split()[0]
            if how_many == '1개':
                continue

            elem.click()
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)

            check_box = driver.find_element(By.CSS_SELECTOR, '#cardsaleInc-3')
            if not check_box.is_selected():
                try:
                    driver.execute_script("arguments[0].click();", check_box)  # 자바스크립트로 클릭 강제 실행
                except Exception as e:
                    print(f"Error clicking the checkbox: {e}")

            html = driver.page_source
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 'tb-compare__list' 클래스 내부의 tbody 태그에서 모든 tr 태그를 찾음
            free_dil_prod_e_list = soup.select('.tb-compare__list tbody tr')

            for ei in range(len(free_dil_prod_e_list)):
                if ei > limit_count: break
                try:
                    mall_name = soup.select(".comparison__lt .comprod__item img")[ei].get('alt')
                    prod_name = soup.select(".comparison__lt .comprod__item")[ei].select('.tx_prodname')[0].text.strip()
                    price = soup.select(".comparison__lt .comprod__item")[ei].select('.tx_price')[0].text.strip()

                    temp_list = [Name, '에누리', how_many, mall_name, '무료배송', prod_name, price]
                    merge_list.append(temp_list)
                except Exception as err:
                    print(f"Error parsing Enuri: {traceback.format_exc()}")

            pay_dil_prod_e_list = soup.select('.comparison__rt .comprod__item')
            for ei in range(len(pay_dil_prod_e_list)):
                if ei > limit_count: break
                try:
                    mall_name = soup.select(".comparison__rt .comprod__item img")[ei].get('alt')
                    prod_name = soup.select(".comparison__rt .comprod__item")[ei].select('.tx_prodname')[0].text.strip()
                    price = soup.select(".comparison__rt .comprod__item")[ei].select('.tx_price')[0].text.strip()

                    temp_list = [Name, '에누리', how_many, mall_name, '유/무료배송', prod_name, price]
                    merge_list.append(temp_list)
                except Exception as err:
                    print(f"Error parsing Enuri: {traceback.format_exc()}")
    except Exception as e:
        print(f"Error during Enuri parsing: {traceback.format_exc()}")

    return merge_list

# 가격 기준 정하기 함수
def set_price_reference(df, whole_df, idx):
    except_list = df.loc[idx, '수집제외몰'].split(',')

    condition = (
            (whole_df['상품명'] == df.loc[idx, '상품명']) &
            (whole_df['사이트'] == '네이버') &  # 사이트 = 네이버
            (~whole_df['쇼핑몰'].isin(except_list))  # 제외 목록 판매처 제외
    )
    filtered_df = whole_df[condition].reset_index(drop=True)

    # 기준가격(네이버) 계산
    if not filtered_df.empty:
        df.loc[idx, '기준가격(네이버)'] = int(
            int(''.join(filter(str.isdigit, filtered_df.loc[0, '가격']))) /
            int(''.join(filter(str.isdigit, filtered_df.loc[0, '갯수'])))
        )
    else:
        df.loc[idx, '기준가격(네이버)'] = None  # 필터링 결과 없을 때 처리

# 나머지 칸 채우기 함수
def fill_remaining_columns(df, whole_df, idx):
    condition = (
        (whole_df['상품명'] == df.loc[idx, '상품명'])
    )
    filtered_df = whole_df[condition].reset_index(drop=True)

    if not filtered_df.empty:
        # 가격/갯수 계산
        filtered_df['가격/갯수'] = 0
        for ii in range(len(filtered_df)):
            filtered_df.loc[ii, '가격/갯수'] = int(
                int(''.join(filter(str.isdigit, filtered_df.loc[ii, '가격']))) /
                int(''.join(filter(str.isdigit, filtered_df.loc[ii, '갯수'])))
            )

        # 가격/갯수 순으로 정렬
        filtered_df = filtered_df.sort_values(by='가격/갯수').reset_index(drop=True)

        # 상위 3개 정보를 df에 저장
        df.loc[idx, '판매처1'] = filtered_df.loc[0, '쇼핑몰']
        df.loc[idx, '상품명1'] = filtered_df.loc[0, '제품명']
        df.loc[idx, '가격1'] = filtered_df.loc[0, '가격/갯수']
        df.loc[idx, '판매처2'] = filtered_df.loc[1, '쇼핑몰']
        df.loc[idx, '상품명2'] = filtered_df.loc[1, '제품명']
        df.loc[idx, '가격2'] = filtered_df.loc[1, '가격/갯수']
        df.loc[idx, '판매처3'] = filtered_df.loc[2, '쇼핑몰']
        df.loc[idx, '상품명3'] = filtered_df.loc[2, '제품명']
        df.loc[idx, '가격3'] = filtered_df.loc[2, '가격/갯수']

def main():
    # 엑셀 데이터 불러오기
    df = pd.read_excel("프로그램.xlsx")
    limit_count = 3
    driver = setup_driver()

    for i in range(len(df)):
        Name = df.loc[i, '상품명']
        Naver_url = df.loc[i, '네이버 URL']
        Danawa_url = df.loc[i, '다나와 URL']
        Enuri_url = df.loc[i, '에누리 URL']

        # 각 상품마다 merge_list 초기화
        merge_list = []

        # 네이버, 다나와, 에누리 각각 함수 호출
        merge_list.extend(parse_naver(driver, Name, Naver_url, limit_count))
        merge_list.extend(parse_danawa(driver, Name, Danawa_url, limit_count))
        merge_list.extend(parse_enuri(driver, Name, Enuri_url, limit_count))

        # DataFrame 생성
        whole_df = pd.DataFrame(merge_list, columns=['상품명', '사이트', '갯수', '쇼핑몰', '배송', '제품명', '가격'])

        # 가격 기준 정하기
        set_price_reference(df, whole_df, i)

        # 나머지 칸 채우기
        fill_remaining_columns(df, whole_df, i)

        # 엑셀 파일에 즉시 업데이트
        with pd.ExcelWriter("프로그램.xlsx", engine='openpyxl', mode='a', if_sheet_exists="replace") as writer:
            df.to_excel(writer, index=False, sheet_name='Updated')

    driver.quit()

if __name__ == "__main__":
    main()