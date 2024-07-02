import urllib.request
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import pyperclip, time

hrd = { 'User-Agent' : 'Mozilla/5.0'}
baseUrl = 'https://www.google.com/search?q='
plusUrl = input('검색어를 입력하세요 : ')
url = baseUrl + quote_plus(plusUrl)

req = urllib.request.Request(url, headers=hrd)
html = urllib.request.urlopen(req).read()
soup = BeautifulSoup(html, 'html.parser')

pyperclip.copy(soup.prettify())