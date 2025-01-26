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
    # 카드할인 토클 클릭
    driver.find_elements(By.CSS_SELECTOR,'[data-shp-contents-type="카드할인가 정렬"]')[0].click() #카드할인
    time.sleep(0.5)

    opt_name = driver.execute_script('return document.querySelector("#section_price em").closest("div");').text.split(" : ")[0].split(',')[-1] ## 옵션 이름 ex)수량, 개수, 상품구성 등등
    print(opt_name)
    
    if len(driver.find_elements(By.CSS_SELECTOR,f'.condition_area a[data-shp-contents-type="{opt_name}"] .info')) != 0:
        Qtys = driver.find_elements(By.CSS_SELECTOR,f'.condition_area a[data-shp-contents-type="{opt_name}"] .info')
    
    elif len(driver.find_elements(By.CSS_SELECTOR,'.condition_area a .info')) != 0:
         Qtys = driver.find_elements(By.CSS_SELECTOR,'.condition_area a .info') ## 수량, 개수 옵션이 없다면 2번째 옵션으로 지정 
 
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
        
        for e in prod_list:
            while True: ### 셀레늄 에러 발생시 재시도도
                try:
                    try:     mall_name = e.find_element(By.CSS_SELECTOR,'[data-shp-area="prc.mall"] img').get_attribute('alt')
                    except:  mall_name = e.find_element(By.CSS_SELECTOR,'[data-shp-area="prc.mall"]').text.split('\n')[0]
                        
                    prod_name = e.find_element(By.CSS_SELECTOR,'[data-shp-area="prc.pd"]').text
                    price = e.find_element(By.CSS_SELECTOR,'[data-shp-area="prc.price"]').text.replace('최저','').strip()
            
                    temp_list = [ Name, '네이버', Qlist[p], mall_name , '' , prod_name, price ]
                    merge_list.append(temp_list)
                    break
                except:
                    print(traceback.format_exc())
                    True


    ##### 다나와 파트 #######
    
    driver.get(Danawa_url)

    if driver.find_elements(By.XPATH,'//*[@id="bundleProductMoreOpen"]') != []:  ##구성 상품열기
        driver.find_element(By.XPATH,'//*[@id="bundleProductMoreOpen"]').click()

    danawa_opt_url_list = [ e.get_attribute('href') for e in driver.find_elements(By.CSS_SELECTOR,'[class="othr_list"] li .chk a') ]
    danawa_opt_text_list = [ e.text for e in driver.find_elements(By.CSS_SELECTOR,'[class="othr_list"] li .chk a') ]

    print(danawa_opt_url_list)
    print(danawa_opt_text_list)

    for ii in range(len(danawa_opt_url_list)):
        
        print(danawa_opt_url_list[ii])
        print(danawa_opt_text_list[ii])
        
        if danawa_opt_text_list[ii] == '1개': ## 1개는 스킵
            continue
            
        driver.get(danawa_opt_url_list[ii])
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")
        driver.find_elements(By.CSS_SELECTOR,'.cardSaleChkbox')[0].click()  ## 카드할인가 클릭
        time.sleep(1)


        html = driver.page_source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        

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
                    merge_list.append(temp_list)
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
