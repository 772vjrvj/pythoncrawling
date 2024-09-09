import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import traceback

df = pd.read_excel("프로그램.xlsx")  # 엑셀 명 수정 가능능
limit_count = 3

try:
    options = Options()
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
except: ## webdriver_manager 에서 chrome127버전 에러 있어서 일단 수동 드라이버로 작동 128버전 부터는 잘 작동될 수도 있음
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

merge_list = []

for i in range(len(df)):

    Name = df.loc[i,'상품명']
    Naver_url = df.loc[i,'네이버 URL']
    Danawa_url = df.loc[i,'다나와 URL']
    Enuri_url = df.loc[i,'에누리 URL']

    ###### 네이버 파트 #######

    driver.get(Naver_url)
    time.sleep(3)

    # 카드할인 토클 클릭 ON으로 둘다 변경 (위 아래 있음)
    driver.find_elements(By.CSS_SELECTOR,'[data-shp-contents-type="카드할인가 정렬"]')[0].click() #카드할인
    time.sleep(0.5)
    # 상품구성: 1개
    opt_name = driver.execute_script('return document.querySelector("#section_price em").closest("div");').text.split(" : ")[0].split(',')[-1] ## 옵션 이름 ex)수량, 개수, 상품구성 등등
    print(opt_name)
    #상품구성: 1개 아래 ['1개', '2개', '3개', '4개', '5개'] ...
    if len(driver.find_elements(By.CSS_SELECTOR,f'.condition_area a[data-shp-contents-type="{opt_name}"] .info')) != 0:
        Qtys = driver.find_elements(By.CSS_SELECTOR,f'.condition_area a[data-shp-contents-type="{opt_name}"] .info')

    elif len(driver.find_elements(By.CSS_SELECTOR,'.condition_area a .info')) != 0:
        Qtys = driver.find_elements(By.CSS_SELECTOR,'.condition_area a .info') ## 수량, 개수 옵션이 없다면 2번째 옵션으로 지정
    #['1개', '2개', '3개', '4개', '5개']
    Qlist = [ q.text for q in Qtys ]
    print(Qlist)

    for p in range(len(Qtys)):

        driver.find_element(By.CSS_SELECTOR,f'[data-shp-contents-id="{Qlist[p]}"]').click()
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")

        uls =  driver.find_elements(By.CSS_SELECTOR,'#section_price ul') ## ul 목록

        for e in uls: # ul안에 li class 이름 가져오기
            if 'productList_list_seller' in e.get_attribute('class'):
                ul_class = e.get_attribute('class').replace(' ','.')

        prod_list = driver.find_elements(By.CSS_SELECTOR,f'#section_price .{ul_class} li')

        action = ActionChains(driver)
        action.move_to_element(prod_list[0]).perform()
        time.sleep(1)

        for e in prod_list: #[판매처, 상품명, 판매가] [옥션, 써클, 8,320원]
            while True: ### 셀레늄 에러 발생시 재시도도
                try:
                    try:     mall_name = e.find_element(By.CSS_SELECTOR,'[data-shp-area="prc.mall"] img').get_attribute('alt')
                    except:  mall_name = e.find_element(By.CSS_SELECTOR,'[data-shp-area="prc.mall"]').text.split('\n')[0]

                    prod_name = e.find_element(By.CSS_SELECTOR,'[data-shp-area="prc.pd"]').text
                    price = e.find_element(By.CSS_SELECTOR,'[data-shp-area="prc.price"]').text.replace('최저','').strip()
                    # ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '롯데ON', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 1병 / 베타글루칸', '10,470원']
                    temp_list = [ Name, '네이버', Qlist[p], mall_name , '' , prod_name, price ]

                    merge_list.append(temp_list)
                    break
                except:
                    print(traceback.format_exc())
                    True


    ##### 다나와 파트 #######

    driver.get(Danawa_url)

    if driver.find_elements(By.XPATH,'//*[@id="bundleProductMoreOpen"]') != []:  ##구성 상품열기 #다른 구성상품5개 (아래화살표)
        driver.find_element(By.XPATH,'//*[@id="bundleProductMoreOpen"]').click()

    danawa_opt_url_list = [ e.get_attribute('href') for e in driver.find_elements(By.CSS_SELECTOR,'[class="othr_list"] li .chk a') ]
    danawa_opt_text_list = [ e.text for e in driver.find_elements(By.CSS_SELECTOR,'[class="othr_list"] li .chk a') ]
    # ['1개', '2개', '3개', '4개', '5개'] #['https://prod.danawa.com/info/?pcode=5970722', 'https://prod.danawa.com/info/?pcode=5970724', 'https://prod.danawa.com/info/?pcode=5970731', 'https://prod.danawa.com/info/?pcode=5970748', 'https://prod.danawa.com/info/?pcode=5970738']
    print(danawa_opt_url_list)
    print(danawa_opt_text_list)

    for ii in range(len(danawa_opt_url_list)):

        print(danawa_opt_url_list[ii])
        print(danawa_opt_text_list[ii])

        if danawa_opt_text_list[ii] == '1개': ## 1개는 스킵 # 복수 구성이 없는 상품은 에러처리안나게 건너 뛰기
            continue

        driver.get(danawa_opt_url_list[ii])
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")
        driver.find_elements(By.CSS_SELECTOR,'.cardSaleChkbox')[0].click()  ## 카드할인가 클릭 (최저가순 빠른배송 배송비포함 V카드할인가
        time.sleep(1)


        html = driver.page_source
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 좌측 : 무료배송, 우측 : 배송비 유/무료 (좌측)
        free_dil_prod_e_list = soup.select('.columm.left_col .diff_item') ### 다나와 무료베송
        time.sleep(1)

        for ei in range(len(free_dil_prod_e_list)):
            if ei > limit_count: break

            while True:
                try:
                    try:    mall_name = soup.select('.columm.left_col .diff_item')[ei].select('img')[0].get('alt')
                    except: mall_name = soup.select('.columm.left_col .diff_item')[ei].select('a .txt_logo')[0].text

                    prod_name = soup.select('.columm.left_col .diff_item')[ei].select('.info_line')[0].text.strip()
                    price = soup.select('.columm.left_col .diff_item')[ei].select('.prc_c')[0].text

                    temp_list = [ Name, '다나와' , danawa_opt_text_list[ii] , mall_name , '무료배송' , prod_name , price ]
                    merge_list.append(temp_list) # ['GNM자연의품격 맥주효모환 120g', '다나와', '2개', '옥션', '무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 2병', '13,230']
                    break
                except:
                    print(traceback.format_exc())
                    True



        pay_dil_prod_e_list = soup.select('.columm.rgt_col .diff_item') ### 다나와 유/무료베송
        time.sleep(1)

        for ei in range(len(pay_dil_prod_e_list)):
            if ei > limit_count: break

            while True:
                try:
                    try:    mall_name = soup.select('.columm.rgt_col .diff_item')[ei].select('img')[0].get('alt')
                    except: mall_name = soup.select('.columm.rgt_col .diff_item')[ei].select('a .txt_logo')[0].text

                    prod_name = soup.select('.columm.rgt_col .diff_item')[ei].select('.info_line')[0].text.strip()
                    price = soup.select('.columm.rgt_col .diff_item')[ei].select('.prc_c')[0].text

                    temp_list = [ Name, '다나와' , danawa_opt_text_list[ii] , mall_name , '유/무료배송' , prod_name , price ]
                    merge_list.append(temp_list)
                    break
                except:
                    print(traceback.format_exc())
                    True

    #### 에누리 파트 ###########

    print(f"merge_list : {merge_list}")

    driver.get(Enuri_url)

    time.sleep(0.5)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    driver.execute_script("window.scrollTo(0, 0);")

    time.sleep(0.5)

    if len(driver.find_elements(By.CSS_SELECTOR,'#prod_option .adv-search__btn--more')) != 0:
        driver.find_element(By.CSS_SELECTOR,'#prod_option .adv-search__btn--more').click()

    time.sleep(1)

    radio_opts = driver.find_elements(By.CSS_SELECTOR,'[name="radioOPTION"]')  ## 라디오박스 요소 추출
    xpath_list = [ '//*[@for="' + e.get_attribute('id') + '"]' for e in radio_opts] ## 라디오 박스 요소 기반으로 클릭할 요소의 XPATH를 미리 찾아놓기 (클릭할때마다 바뀌기 때문)
    time.sleep(1)

    for eei,e in enumerate(radio_opts):
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")

        try: driver.find_element(By.CSS_SELECTOR,'#prod_option .adv-search__btn--more').click()
        except: True

        elem = driver.find_element(By.XPATH,xpath_list[eei]) ## 갯수 엘리먼트

        how_many = elem.text.split()[0] ## 갯수 텍스트
        if how_many == '1개': ## 1개는 스킵
            continue

        elem.click() ## 갯수 클릭

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)

        check_box = driver.find_element(By.CSS_SELECTOR,'#cardsaleInc-3')
        if check_box.is_selected() == False:
            try: driver.find_element(By.CSS_SELECTOR,'[for="cardsaleInc-3"]').click()
            except: True

        while True:
            if driver.find_element(By.XPATH,'//*[@class="comm-loader"]').get_attribute('style') != "display: none;":
                time.sleep(0.5)
            else:
                print(traceback.format_exc())
                break

        html = driver.page_source
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        free_dil_prod_e_list = soup.select(".comparison__lt .comprod__item") ## 상품 리스트 (무료배송)
        time.sleep(0.5)

        if '해당 쇼핑몰이 없습니다.' not in soup.select(".comparison__lt .comprod__item")[0].text:

            for ei in range(len(free_dil_prod_e_list)):
                if ei > limit_count: break

                while True:

                    try:
                        try:    mall_name = soup.select(".comparison__lt .comprod__item img")[ei].get('alt')
                        except: mall_name = soup.select(".comparison__lt .comprod__item")[ei].select('a')[0].text

                        prod_name = soup.select(".comparison__lt .comprod__item")[ei].select('.tx_prodname')[0].text.strip()
                        price = soup.select(".comparison__lt .comprod__item")[ei].select('.tx_price')[0].text.strip()

                        temp_list = [ Name, '에누리' , how_many , mall_name , '무료배송' , prod_name , price ]
                        merge_list.append(temp_list)
                        break
                    except:
                        print(traceback.format_exc())
                        True


        pay_dil_prod_e_list = soup.select('.comparison__rt .comprod__item') ## 상품 리스트 (유/무료배송)
        time.sleep(0.5)

        if '해당 쇼핑몰이 없습니다.' not in soup.select(".comparison__rt .comprod__item")[0].text:

            for ei in range(len(pay_dil_prod_e_list)):
                if ei > limit_count: break

                while True:

                    try:
                        try:    mall_name = soup.select(".comparison__rt .comprod__item img")[ei].get('alt')
                        except: mall_name = soup.select(".comparison__rt .comprod__item")[ei].select('a')[0].text

                        prod_name = soup.select(".comparison__rt .comprod__item")[ei].select('.tx_prodname')[0].text.strip()
                        price = soup.select(".comparison__rt .comprod__item")[ei].select('.tx_price')[0].text.strip()

                        temp_list = [ Name, '에누리' , how_many , mall_name , '유/무료배송' , prod_name , price ]
                        merge_list.append(temp_list)
                        break
                    except:
                        print(traceback.format_exc())
                        True


whole_df = pd.DataFrame(merge_list , columns = ['상품명','사이트','갯수','쇼핑몰','배송','제품명','가격'])

##################### 가격기준 정하기 ################

for i in range(len(df)):

    except_list = df.loc[i,'수집제외몰'].split(',')

    condition = (
            (whole_df['상품명'] == df.loc[i, '상품명']) &
            (whole_df['사이트'] == '네이버') &  # 사이트 = 네이버
            (~whole_df['쇼핑몰'].isin(except_list)) # 제외 목록 판매처 제외
    )
    filtered_df = whole_df[condition].reset_index(drop = True)  ### whole_df에서 필터링 네이버 모든 상품 가격

    df.loc[i,'기준가격(네이버)'] = int(int(''.join(filter(str.isdigit, filtered_df.loc[0,'가격'])))  / int(''.join(filter(str.isdigit, filtered_df.loc[0,'갯수']))))


################### 나머지칸 채우기 ###################

for i in range(len(df)):

    condition = (
        (whole_df['상품명'] == df.loc[i, '상품명'])
    )
    filtered_df = whole_df[condition].reset_index(drop = True) ### filtered_df 는 메인 df 기준 같은 상품명 제품 모두 가져옴

    filtered_df['가격/갯수'] = 0

    for ii in range(len(filtered_df)): ### filtered_df에 모든 제품의 가격/갯수를 입력
        filtered_df.loc[ii,'가격/갯수'] = int(int(''.join(filter(str.isdigit, filtered_df.loc[ii,'가격'])))  / int(''.join(filter(str.isdigit, filtered_df.loc[ii,'갯수']))))

    filtered_df = filtered_df.sort_values(by='가격/갯수').reset_index(drop=True) ######### filtered_df 는 모든 제품의 가격/갯수 순으로 나열 필요하면 다운 가능

    df.loc[i,'판매처1'] = filtered_df.loc[0,'쇼핑몰']
    df.loc[i,'상품명1'] = filtered_df.loc[0,'제품명']
    df.loc[i,'가격1'] = filtered_df.loc[0,'가격/갯수']
    df.loc[i,'판매처2'] = filtered_df.loc[1,'쇼핑몰']
    df.loc[i,'상품명2'] = filtered_df.loc[1,'제품명']
    df.loc[i,'가격2'] = filtered_df.loc[1,'가격/갯수']
    df.loc[i,'판매처3'] = filtered_df.loc[2,'쇼핑몰']
    df.loc[i,'상품명3'] = filtered_df.loc[2,'제품명']
    df.loc[i,'가격3'] = filtered_df.loc[2,'가격/갯수']

df.to_excel("result.xlsx")

driver.quit()

# [
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '옥션', '', 'GNM자연의품격 GNM자연의품격 맥주효모환 120g / 써클', '8,320원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '옥션', '', '100% 건조 맥주효모환 베타글루칸 120g x 1병', '8,330원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '더클라우드세븐', '', 'GNM자연의품격 맥주효모환 120g x 1박스', '8,600원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '써클홀딩스', '', 'GNM자연의품격 맥주효모환 120g', '8,780원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '롯데홈쇼핑', '', '[GNM자연의품격] [GNM자연의품격] 100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,030원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '11번가', '', 'GNM자연의품격 맥주효모환 120g / 써클', '9,120원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', 'CJ온스타일', '', '100% 맥주효모 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,230원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', 'G마켓', '', 'GNM자연의품격 GNM자연의품격 100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,280원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '11번가', '', '100 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,570원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '롯데ON', '', '자연의품격 GNM 100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,600원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', 'SK스토아', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,640원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '11번가', '', 'GNM 100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,760원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', 'GNM 자연의품격', '', 'GNM 100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,800원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', 'GSSHOP', '', 'GNM 100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '9,810원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '자연의품격', '', '건조 맥주효모환 1병', '9,900원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', 'G마켓', '', 'GNM자연의품격 갤러리아 GNM 100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '10,050원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '홈앤쇼핑', '', '[GNM자연의품격] 100% 맥주효모 건조 맥주효모환 120g x 1병 / 베타글루칸', '10,140원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '하프클럽', '', '[GNM] GNM 100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '10,470원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '롯데ON', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 1병 / 베타글루칸', '10,470원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '1개', '신세계몰', '', '[9/12(목) 14시 주문마감]100% 건조 맥주효모환 120g x 1병 / 베타글루칸', '10,900원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '옥션', '', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 2병', '13,230원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '롯데홈쇼핑', '', '[GNM자연의품격] [GNM자연의품격] 100% 건조 맥주효모환 120g x 2병 / 베타글루칸', '14,820원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', 'CJ온스타일', '', '100% 맥주효모 건조 맥주효모환 120g x 2병 / 베타글루칸', '15,160원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', 'G마켓', '', 'GNM자연의품격 GNM자연의품격 100% 건조 맥주효모환 120g x 2병 / 베타글루칸', '15,310원'],
# ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '롯데ON', '', '자연의품격 GNM 100% 건조 맥주효모환 120g x 2병 / 베타글루칸', '15,760원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', 'SK스토아', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 2병 / 베타글루칸', '15,820원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '현대Hmall', '', 'GNM 100% 건조 맥주효모환 120g x 2병 / 베타글루칸', '15,980원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '써클홀딩스', '', 'GNM자연의품격 맥주효모환 120g 2개', '16,000원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '11번가', '', 'GNM자연의품격 맥주효모환 120g 2개 / 써클', '16,200원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '쿠팡', '', 'GNM자연의품격 맥주효모환 2개 120g', '16,320원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '자연의품격', '', '건조 맥주효모환 2병', '16,900원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '옥션', '', 'GNM자연의품격 9/12(목) 14시 주문마감100% 건조 맥주효모환 120g x 2병 / 베타글루칸', '17,000원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', 'SSG닷컴', '', 'GNM 건조 맥주효모환 120g x 2병 / 베타글루칸', '17,180원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '11번가', '', '[GNM자연의품격] 백프로 건조 맥주효모환 120g x 2병 / 베타글루칸', '17,190원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '롯데ON', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 2병 / 베타글루칸', '17,190원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '하프클럽', '', '[GNM] GNM 100% 건조 맥주효모환 120g x 2병 / 베타글루칸', '17,200원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '제로투원 스토어', '', 'GNM자연의품격 맥주효모환 120g 2개', '17,650원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '더클라우드세븐', '', 'GNM자연의품격 맥주효모환 120g x 2박스', '18,840원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '2개', '11번가', '', 'GNM 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '22,290원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '쿠팡', '', 'GNM자연의품격 맥주효모환 3개 120g', '19,500원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '옥션', '', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 3병', '19,520원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '신세계라이브쇼핑', '', 'GNM 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '20,800원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', 'CJ온스타일', '', '100% 맥주효모 건조 맥주효모환 120g x 3병 / 베타글루칸', '21,080원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', 'G마켓', '', 'GNM자연의품격 GNM 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '21,280원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '옥션', '', 'GNM자연의품격 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '21,410원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', 'G마켓', '', 'GNM자연의품격 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '21,420원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '11번가', '', '100 건조 맥주효모환 120g x 3병 / 베타글루칸', '21,850원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '자연의품격', '', '건조 맥주효모환 3병', '21,900원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '롯데ON', '', '자연의품격 GNM 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '21,920원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '써클홀딩스', '', 'GNM자연의품격 맥주효모환 120g 3개', '22,000원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', 'SK스토아', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 3병 / 베타글루칸', '22,010원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '현대Hmall', '', 'GNM 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '22,220원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '하프클럽', '', '[GNM] GNM 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '22,960원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '옥션', '', 'GNM자연의품격 GNM자연의품격 GNM 건조 맥주효모환 120g x 3병 / 베타글루칸', '23,140원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', 'G마켓', '', 'GNM자연의품격 GNM자연의품격 GNM 건조 맥주효모환 120g x 3병 / 베타글루칸', '23,170원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '11번가', '', '[신세계라이브쇼핑]GNM 100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '23,310원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '옥션', '', 'GNM자연의품격 9/12(목) 14시 주문마감100% 건조 맥주효모환 120g x 3병 / 베타글루칸', '23,640원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '11번가', '', '[NS홈쇼핑]100% 건조 맥주효모환 120g x 3병[25942806]', '23,790원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '3개', '롯데ON', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 3병 / 베타글루칸', '23,910원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '4개', '이마트몰', '', 'GNM 건조 맥주효모환 120g x 4병 / 베타글루칸', '32,900원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '4개', 'SSG닷컴', '', 'GNM 건조 맥주효모환 120g x 4병 / 베타글루칸', '32,900원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '4개', '신세계몰', '', 'GNM 건조 맥주효모환 120g x 4병 / 베타글루칸', '32,900원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', 'CJ온스타일', '', '100% 맥주효모 건조 맥주효모환 120g x 5병 / 베타글루칸', '30,790원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', 'SK스토아', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 5병 / 베타글루칸', '31,730원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '11번가', '', '100 맥주효모 건조 맥주효모환 120g x 5병 베타글루칸', '32,990원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '현대Hmall', '', 'GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '34,780원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '11번가', '', '100 건조 맥주효모환 120g x 5병 / 베타글루칸', '34,930원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', 'G마켓', '', 'GNM자연의품격 GNM자연의품격 GNM 건조 맥주효모환 120g x 5병 / 베타글루칸', '35,250원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '옥션', '', 'GNM자연의품격 GNM자연의품격 GNM 건조 맥주효모환 120g x 5병 / 베타글루칸', '35,250원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '11번가', '', 'GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '35,630원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '옥션', '', 'GNM자연의품격 (현대hmall)GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '36,240원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '롯데ON', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 5병 / 베타글루칸', '36,390원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '신세계라이브쇼핑', '', 'GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '36,620원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '11번가', '', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 5병 / 베타글루칸', '36,960원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '11번가', '', '갤러리아 GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '37,460원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '롯데ON', '', '자연의품격 GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '신한카드 37,810원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '하프클럽', '', '[GNM자연의품격] GNM 건조 맥주효모환 120g x 5병 / 베타글루칸', '37,900원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', 'SSG닷컴', '', 'GNM 건조 맥주효모환 120g x 5병 / 베타글루칸', '37,900원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '하프클럽', '', '[GNM] GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '38,230원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '11번가', '', '[신세계라이브쇼핑]GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '38,810원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', 'GNM 자연의품격', '', 'GNM 100% 건조 맥주효모환 120g x 5병 / 베타글루칸', '38,900원'], ['GNM자연의품격 맥주효모환 120g', '네이버', '5개', '자연의품격', '', '건조 맥주효모환 5병', '38,900원'], ['GNM자연의품격 맥주효모환 120g', '다나와', '2개', '옥션', '무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 2병', '13,230'], ['GNM자연의품격 맥주효모환 120g', '다나와', '2개', 'G마켓', '무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 2병', '14,180'], ['GNM자연의품격 맥주효모환 120g', '다나와', '2개', 'G마켓', '무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 2병', '14,180'], ['GNM자연의품격 맥주효모환 120g', '다나와', '2개', '롯데홈쇼핑', '무료배송', 'GNM자연의품격 [GNM자연의품격] 100% 건조 맥주효모환 120g x 2병 / 베타글루칸', '14,980'], ['GNM자연의품격 맥주효모환 120g', '다나와', '2개', 'G마켓', '유/무료배송', 'GNM자연의품격 GNM자연의품격 맥주효모환 120g 2개 / 써클', '14,970'], ['GNM자연의품격 맥주효모환 120g', '다나와', '2개', '롯데ON', '유/무료배송', 'GNM자연의품격 맥주효모환 120g 2개 / 써클', '15,370'], ['GNM자연의품격 맥주효모환 120g', '다나와', '2개', 'G마켓', '유/무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 2병 445973', '30,700'], ['GNM자연의품격 맥주효모환 120g', '다나와', '3개', '11번가', '무료배송', 'GNM 100% 건조 맥주효모환 120g x 2병 / 베타글루칸', '16,830'], ['GNM자연의품격 맥주효모환 120g', '다나와', '3개', '쿠팡', '무료배송', 'GNM자연의품격 맥주효모환  3개  120g', '19,500'], ['GNM자연의품격 맥주효모환 120g', '다나와', '3개', '옥션', '무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 3병', '19,520'], ['GNM자연의품격 맥주효모환 120g', '다나와', '3개', '옥션', '무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 3병', '19,520'], ['GNM자연의품격 맥주효모환 120g', '다나와', '3개', '롯데ON', '유/무료배송', 'GNM자연의품격 맥주효모환 120g 3개 / 써클', '23,240'], ['GNM자연의품격 맥주효모환 120g', '다나와', '3개', 'G마켓', '유/무료배송', 'GNM자연의품격 GNM자연의품격 맥주효모환 120g 3개 / 써클', '26,300'], ['GNM자연의품격 맥주효모환 120g', '다나와', '4개', '옥션', '무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 4병', '25,920'], ['GNM자연의품격 맥주효모환 120g', '다나와', '4개', 'G마켓', '무료배송', 'GNM자연의품격 100% 건조 맥주효모환 베타글루칸 120g x 4병', '27,670'], ['GNM자연의품격 맥주효모환 120g', '다나와', '4개', 'SK스토아', '무료배송', '[GNM자연의품격]GNM 건조 맥주효모환 120g x 4병 / 베타글루칸', '29,610'], ['GNM자연의품격 맥주효모환 120g', '다나와', '4개', 'G마켓', '무료배송', 'GNM자연의품격 GNM 건조 맥주효모환 120g x 4병 / 베타글루칸', '30,580'], ['GNM자연의품격 맥주효모환 120g', '다나와', '4개', 'G마켓', '유/무료배송', 'GNM자연의품격 GNM자연의품격 맥주효모환 120g 4개 / 써클', '30,370'], ['GNM자연의품격 맥주효모환 120g', '다나와', '4개', '롯데ON', '유/무료배송', 'GNM자연의품격 맥주효모환 120g 4개 / 써클', '31,190'], ['GNM자연의품격 맥주효모환 120g', '다나와', '4개', 'G마켓', '유/무료배송', '100% 건조 맥주효모환 베타글루칸 120g x 4병 446000 100% 건조 맥주효모환 베타글루칸 120g x 4병', '52,600'],
# ['GNM자연의품격 맥주효모환 120g', '다나와', '5개', '11번가', '무료배송', '100  맥주효모 건조 맥주효모환 120g x 5병   베타글루칸', '32,130'],
# ['GNM자연의품격 맥주효모환 120g', '다나와', '5개', 'CJ온스타일', '무료배송', '100% 맥주효모 건조 맥주효모환 120g x 5병 / 베타글루칸', '32,140'],
# ['GNM자연의품격 맥주효모환 120g', '다나와', '5개', '옥션', '무료배송', 'GNM자연의품격 100 맥주효모 건조 맥주효모환 120g x 5병  베타글루칸', '32,140'],
# ['GNM자연의품격 맥주효모환 120g', '다나와', '5개', 'G마켓', '무료배송', 'GNM자연의품격 100 맥주효모 건조 맥주효모환 120g x 5병  베타글루칸', '32,140'],
# ['GNM자연의품격 맥주효모환 120g', '다나와', '5개', 'G마켓', '유/무료배송', 'GNM자연의품격 GNM자연의품격 맥주효모환 120g 5개 / 써클', '38,450'],
# ['GNM자연의품격 맥주효모환 120g', '다나와', '5개', '롯데ON', '유/무료배송', 'GNM자연의품격 맥주효모환 120g 5개 / 써클', '39,130'], ['GNM자연의품격 맥주효모환 120g', '다나와', '5개', 'G마켓', '유/무료배송', 'GNM자연의품격 GNM자연의품격 맥주효모환 120g 5개 / win', '88,960']
# ]