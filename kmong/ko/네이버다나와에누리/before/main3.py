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


# 드라이버 설정 함수
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

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            '''
        })
    except Exception as e:
        print(f"Error setting up the driver: {e}")
        driver = None
    return driver


# 네이버 크롤링 함수
def scrape_naver(driver, name, naver_url, merge_list, limit_count):
    try:
        driver.get(naver_url)
        time.sleep(3)

        # 카드할인 토클 클릭 ON으로 둘다 변경 (위 아래 있음)
        driver.find_elements(By.CSS_SELECTOR, '[data-shp-contents-type="카드할인가 정렬"]')[0].click()  # 카드할인
        time.sleep(0.5)

        # 옵션 이름 ex)수량, 개수, 상품구성 등등
        opt_name = driver.execute_script('return document.querySelector("#section_price em").closest("div");').text.split(" : ")[0].split(',')[-1]
        print(opt_name)

        #상품구성: 1개 아래 ['1개', '2개', '3개', '4개', '5개'] ...
        if len(driver.find_elements(By.CSS_SELECTOR, f'.condition_area a[data-shp-contents-type="{opt_name}"] .info')) != 0:
            qtys = driver.find_elements(By.CSS_SELECTOR, f'.condition_area a[data-shp-contents-type="{opt_name}"] .info')
        elif len(driver.find_elements(By.CSS_SELECTOR, '.condition_area a .info')) != 0:
            qtys = driver.find_elements(By.CSS_SELECTOR, '.condition_area a .info')  # 수량, 개수 옵션이 없다면 2번째 옵션으로 지정

        #['1개', '2개', '3개', '4개', '5개']
        qlist = [q.text for q in qtys]
        print(qlist)

        for p in range(len(qtys)):
            driver.find_element(By.CSS_SELECTOR, f'[data-shp-contents-id="{qlist[p]}"]').click()
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, 0);")

            uls = driver.find_elements(By.CSS_SELECTOR, '#section_price ul')  # ul 목록
            ul_class = ""

            for e in uls:  # ul 안에 li class 이름 가져오기
                if 'productList_list_seller' in e.get_attribute('class'):
                    ul_class = e.get_attribute('class').replace(' ', '.')

            prod_list = driver.find_elements(By.CSS_SELECTOR, f'#section_price .{ul_class} li')

            action = ActionChains(driver)
            action.move_to_element(prod_list[0]).perform()
            time.sleep(1)

            for e in prod_list:
                retry_count = 0
                max_retries = 3  # 최대 3번 재시도

                while retry_count < max_retries:  # 셀레늄 에러 발생 시 최대 3번 재시도
                    try:
                        try:
                            mall_name = e.find_element(By.CSS_SELECTOR, '[data-shp-area="prc.mall"] img').get_attribute('alt')
                        except:
                            mall_name = e.find_element(By.CSS_SELECTOR, '[data-shp-area="prc.mall"]').text.split('\n')[0]

                        prod_name = e.find_element(By.CSS_SELECTOR, '[data-shp-area="prc.pd"]').text
                        price = e.find_element(By.CSS_SELECTOR, '[data-shp-area="prc.price"]').text.replace('최저', '').strip()

                        temp_list = [name, '네이버', qlist[p], mall_name, '', prod_name, price]
                        merge_list.append(temp_list)
                        break  # 성공 시 루프 탈출
                    except Exception as error:
                        retry_count += 1  # 재시도 횟수 증가
                        print(f"Error in scraping Naver product list (Attempt {retry_count}/{max_retries}): {error}")
                        time.sleep(1)  # 재시도 전에 잠시 대기
                        if retry_count == max_retries:
                            print(f"Skipping this product after {max_retries} failed attempts.")
                            break  # 재시도 한도를 넘으면 루프 탈출


    except Exception as e:
        print(f"Error in Naver scraping: {e}")


# 다나와 크롤링 함수
def scrape_danawa(driver, name, danawa_url, merge_list, limit_count):
    try:
        driver.get(danawa_url)

        if driver.find_elements(By.XPATH, '//*[@id="bundleProductMoreOpen"]') != []:   #구성 상품열기 #다른 구성상품5개 (아래화살표)
            driver.find_element(By.XPATH, '//*[@id="bundleProductMoreOpen"]').click()

        danawa_opt_url_list = [e.get_attribute('href') for e in driver.find_elements(By.CSS_SELECTOR, '[class="othr_list"] li .chk a')]
        danawa_opt_text_list = [e.text for e in driver.find_elements(By.CSS_SELECTOR, '[class="othr_list"] li .chk a')]
        # ['1개', '2개', '3개', '4개', '5개'] #['https://prod.danawa.com/info/?pcode=5970722', 'https://prod.danawa.com/info/?pcode=5970724', 'https://prod.danawa.com/info/?pcode=5970731', 'https://prod.danawa.com/info/?pcode=5970748', 'https://prod.danawa.com/info/?pcode=5970738']

        print(danawa_opt_url_list)
        print(danawa_opt_text_list)

        for ii in range(len(danawa_opt_url_list)):
            print(danawa_opt_url_list[ii])
            print(danawa_opt_text_list[ii])

            if danawa_opt_text_list[ii] == '1개':  # 1개는 스킵 # 복수 구성이 없는 상품은 에러처리안나게 건너 뛰기
                continue

            driver.get(danawa_opt_url_list[ii])
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, 0);")
            driver.find_elements(By.CSS_SELECTOR, '.cardSaleChkbox')[0].click()  # 카드할인가 클릭
            time.sleep(1)

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # 좌측: 무료배송
            free_dil_prod_e_list = soup.select('.columm.left_col .diff_item')
            time.sleep(1)

            for ei in range(min(len(free_dil_prod_e_list), limit_count)):
                try:
                    try:
                        mall_name = soup.select('.columm.left_col .diff_item')[ei].select('img')[0].get('alt')
                    except:
                        mall_name = soup.select('.columm.left_col .diff_item')[ei].select('a .txt_logo')[0].text

                    prod_name = soup.select('.columm.left_col .diff_item')[ei].select('.info_line')[0].text.strip()
                    price = soup.select('.columm.left_col .diff_item')[ei].select('.prc_c')[0].text

                    temp_list = [name, '다나와', danawa_opt_text_list[ii], mall_name, '무료배송', prod_name, price]
                    merge_list.append(temp_list)
                except Exception as e:
                    print(f"Error in scraping Danawa (free shipping): {e}")
                    continue  # 에러 발생 시 다음 루프 항목으로 이동

            # 우측: 유/무료 배송
            pay_dil_prod_e_list = soup.select('.columm.rgt_col .diff_item')
            time.sleep(1)

            for ei in range(min(len(pay_dil_prod_e_list), limit_count)):
                try:
                    try:
                        mall_name = soup.select('.columm.rgt_col .diff_item')[ei].select('img')[0].get('alt')
                    except:
                        mall_name = soup.select('.columm.rgt_col .diff_item')[ei].select('a .txt_logo')[0].text

                    prod_name = soup.select('.columm.rgt_col .diff_item')[ei].select('.info_line')[0].text.strip()
                    price = soup.select('.columm.rgt_col .diff_item')[ei].select('.prc_c')[0].text

                    temp_list = [name, '다나와', danawa_opt_text_list[ii], mall_name, '유/무료배송', prod_name, price]
                    merge_list.append(temp_list)
                except Exception as e:
                    print(f"Error in scraping Danawa (paid shipping): {e}")
                    continue  # 에러 발생 시 다음 루프 항목으로 이동

    except Exception as e:
        print(f"Error in Danawa scraping: {e}")


# 에누리 크롤링 함수
def scrape_enuri(driver, name, enuri_url, merge_list, limit_count):
    try:
        driver.get(enuri_url)
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)

        # 1개 2개 3개 4개 5개 라디오 아래 더보기 버튼
        if len(driver.find_elements(By.CSS_SELECTOR, '#prod_option .adv-search__btn--more')) != 0:
            driver.find_element(By.CSS_SELECTOR, '#prod_option .adv-search__btn--more').click()

        time.sleep(1)

        radio_opts = driver.find_elements(By.CSS_SELECTOR, '[name="radioOPTION"]')
        xpath_list = ['//*[@for="' + e.get_attribute('id') + '"]' for e in radio_opts]
        time.sleep(1)

        for eei, e in enumerate(radio_opts):
            time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 0);")
            elem = driver.find_element(By.XPATH, xpath_list[eei])  # 갯수 엘리먼트

            how_many = elem.text.split()[0]  # 갯수 텍스트
            if how_many == '1개':  # 1개는 스킵
                continue

            elem.click()  # 갯수 클릭
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)

            # 카드 할인 토글 클릭
            check_box = driver.find_element(By.CSS_SELECTOR, '#cardsaleInc-3')
            if not check_box.is_selected():
                try:
                    driver.find_element(By.CSS_SELECTOR, '[for="cardsaleInc-3"]').click()
                except Exception as e:
                    print(f"Error clicking the checkbox: {e}")

            max_wait_time = 10  # 최대 대기 시간 (초)
            start_time = time.time()

            while True:
                try:
                    # 로딩 상태가 아직 보이는지 확인
                    if driver.find_element(By.XPATH, '//*[@class="comm-loader"]').get_attribute('style') != "display: none;":
                        time.sleep(0.5)

                        # 최대 대기 시간이 넘으면 루프 탈출
                        if time.time() - start_time > max_wait_time:
                            print("Loader is taking too long. Skipping this step.")
                            break
                    else:
                        # 로딩이 끝났으면 루프 탈출
                        break
                except Exception as e:
                    # 에러가 발생했을 경우 에러 메시지 출력 후 루프 탈출
                    print(f"Error while waiting for loader: {e}")
                    print(traceback.format_exc())
                    break

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # 'tb-compare__list' 클래스 내부의 tbody 태그에서 모든 tr 태그를 찾음
            free_dil_prod_e_list = soup.select('.tb-compare__list tbody tr')


            for ei in range(min(len(free_dil_prod_e_list), limit_count)):
                try:
                    # 판매처 추출
                    mall_name = ""
                    shop_td = free_dil_prod_e_list[ei].find('td', class_='tb-col--shop')
                    if shop_td:
                        img_tag = shop_td.find('img')
                        mall_name = img_tag['alt'] if img_tag and 'alt' in img_tag.attrs else shop_td.get_text(strip=True)

                    # 제품명 추출
                    prod_name = ""
                    name_td = free_dil_prod_e_list[ei].find('td', class_='tb-col--name')
                    if name_td:
                        name_div = name_td.find('div', class_='tb-col__tx--name')
                        if name_div:
                            # <i> 태그 제거 후 텍스트만 추출
                            [i_tag.extract() for i_tag in name_div.find_all('i')]
                            prod_name = name_div.get_text(strip=True)

                    # 가격 추출
                    price = ""
                    price_div = free_dil_prod_e_list[ei].find('div', class_='tx-price')
                    if price_div:
                        em_tag = price_div.find('em')
                        price = em_tag.get_text(strip=True) if em_tag else ""

                    # 리스트에 데이터 추가
                    temp_list = [name, '에누리', how_many, mall_name, '무료배송', prod_name, price]
                    merge_list.append(temp_list)
                    print(temp_list)

                except Exception as e:
                    print(f"Error in scraping Enuri free shipping list (index {ei}): {e}")
                    continue

    except Exception as e:
        print(f"Error in Enuri scraping: {e}")


# 엑셀로 저장하는 함수
def save_to_excel(df, merge_list, excel_path="result.xlsx"):
    try:
        # 엑셀 파일 읽기 (기존 데이터 유지)
        existing_df = pd.read_excel(excel_path)

        # merge_list 데이터를 데이터프레임으로 변환
        whole_df = pd.DataFrame(merge_list, columns=['상품명', '사이트', '갯수', '쇼핑몰', '배송', '제품명', '가격'])

        # 기준가격 및 각 판매처와 상품명 업데이트
        for i in range(len(existing_df)):
            except_list = existing_df.loc[i, '수집제외몰'].split(',')
            condition = (
                    (whole_df['상품명'] == existing_df.loc[i, '상품명']) &
                    (whole_df['사이트'] == '네이버') &
                    (~whole_df['쇼핑몰'].isin(except_list))
            )
            filtered_df = whole_df[condition].reset_index(drop=True)
            if not filtered_df.empty:
                existing_df.loc[i, '기준가격(네이버)'] = int(int(''.join(filter(str.isdigit, filtered_df.loc[0, '가격']))) /
                                                      int(''.join(filter(str.isdigit, filtered_df.loc[0, '갯수']))))

        # 나머지 판매처 및 상품 업데이트
        for i in range(len(existing_df)):
            condition = (whole_df['상품명'] == existing_df.loc[i, '상품명'])
            filtered_df = whole_df[condition].reset_index(drop=True)

            filtered_df['가격/갯수'] = 0
            for ii in range(len(filtered_df)):
                filtered_df.loc[ii, '가격/갯수'] = int(int(''.join(filter(str.isdigit, filtered_df.loc[ii, '가격']))) /
                                                   int(''.join(filter(str.isdigit, filtered_df.loc[ii, '갯수']))))

            filtered_df = filtered_df.sort_values(by='가격/갯수').reset_index(drop=True)

            # 판매처 1, 2, 3과 상품명, 가격 업데이트
            if len(filtered_df) > 0:
                existing_df.loc[i, '판매처1'] = filtered_df.loc[0, '쇼핑몰']
                existing_df.loc[i, '상품명1'] = filtered_df.loc[0, '제품명']
                existing_df.loc[i, '가격1'] = filtered_df.loc[0, '가격/갯수']
            if len(filtered_df) > 1:
                existing_df.loc[i, '판매처2'] = filtered_df.loc[1, '쇼핑몰']
                existing_df.loc[i, '상품명2'] = filtered_df.loc[1, '제품명']
                existing_df.loc[i, '가격2'] = filtered_df.loc[1, '가격/갯수']
            if len(filtered_df) > 2:
                existing_df.loc[i, '판매처3'] = filtered_df.loc[2, '쇼핑몰']
                existing_df.loc[i, '상품명3'] = filtered_df.loc[2, '제품명']
                existing_df.loc[i, '가격3'] = filtered_df.loc[2, '가격/갯수']

        # 기존 엑셀 파일에 업데이트된 데이터 저장
        existing_df.to_excel(excel_path, index=False)
        print("엑셀 파일이 성공적으로 업데이트되었습니다.")

    except Exception as e:
        print(f"Error saving to Excel: {e}")


# 메인 함수
def main():
    try:
        df = pd.read_excel("프로그램.xlsx")
        limit_count = 3
        driver = setup_driver()

        if not driver:
            print("Failed to initialize the web driver.")
            return

        merge_list = []

        for i in range(len(df)):
            name = df.loc[i, '상품명']
            naver_url = df.loc[i, '네이버 URL']
            danawa_url = df.loc[i, '다나와 URL']
            enuri_url = df.loc[i, '에누리 URL']

            # 네이버 크롤링
            scrape_naver(driver, name, naver_url, merge_list, limit_count)

            # 다나와 크롤링
            scrape_danawa(driver, name, danawa_url, merge_list, limit_count)

            # 에누리 크롤링
            scrape_enuri(driver, name, enuri_url, merge_list, limit_count)

        # 엑셀로 저장
        save_to_excel(df, merge_list)

        driver.quit()

    except Exception as e:
        print(f"Error in main function: {e}")


if __name__ == "__main__":
    main()
