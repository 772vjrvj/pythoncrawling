from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


baseUrl = 'https://www.google.com/search?q='
plusUrl = input('무엇을 검색할까요? :')
url = baseUrl + quote_plus(plusUrl)

options = Options()

# 화면이 제일 크게 열림
options.add_argument("--start-maximized")
# 헤드리스 모드 (브라우저 창을 띄우지 않음)
# options.add_argument('--headless')

# 화면이 안꺼짐
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=options)
driver.get(url)

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

r = soup.select('.g')
for i in r:
    print(i.select_one('.LC20lb').text)
    print(i.select_one('.tjvcx.GvPZzd.cHaqb').text)
    print(i.a.attrs['href'])
    print()

driver.close()