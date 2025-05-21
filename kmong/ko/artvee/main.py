import json
import os
import random
import re
import ssl
import sys
import time
import traceback
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from selenium import webdriver
from tqdm import tqdm

# 현재 디렉터리에 있는 다른 파일을 import하려면 sys.path.append("./")를 추가해야 해당 파일을 찾을 수 있습니다.
sys.path.append("./")

# SSL 인증서 검증을 건너뜀
ssl._create_default_https_context = ssl._create_unverified_context

class ARTVEE:
    def __init__(self) -> None:
        self.baseUrl = "https://artvee.com/"
        self.sess = requests.Session()

    def login(self)->dict:
        webdriver_options = webdriver.ChromeOptions()
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')
        webdriver_options.add_argument("--start-maximized")
        webdriver_options.add_argument("headless")
        webdriver_options.add_experimental_option('useAutomationExtension', False)
        webdriver_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        webdriver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=webdriver_options)
        self.driver.set_page_load_timeout(120)
        self.driver.get("https://artvee.com/")
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.sess.cookies.set(cookie['name'], cookie['value'])
        self.version = self.driver.capabilities["browserVersion"]
        self.headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.version}"
        }
        self.driver.quit()
        return self.headers

    def getArtistsUrlList(self) -> list[dict]:
        artistsUrlList:list[dict] = []
        totalCount = 1
        i = 1
        while 1:
            url:str = f"{self.baseUrl}artists/page/{i}/"
            res:requests.Response = self.sess.get(url,headers=self.headers)
            time.sleep(random.uniform(0.3, 0.5))
            i += 1
            if res.status_code == 200:
                soup = BeautifulSoup(res.content,"html.parser")
                allArtist = soup.find_all("div",class_="wrapp-catti")
                if len(allArtist) ==0:
                    break
                for artistInfo in allArtist:
                    artistUrl = artistInfo.find("a")["href"]
                    artistcount = artistInfo.find("mark", class_="count").text.strip()
                    artistsUrlList.append({"artistUrl":artistUrl,"artistcount":artistcount,"page":(i-1),"totalCount":totalCount})
                    totalCount+=1
        return artistsUrlList

    def getExcelArtistsUrlList(self, file_path) -> list[dict]:
        artistsUrlList: list[dict] = []

        # 엑셀 파일 읽기
        df = pd.read_excel(file_path)

        # 'artist_list' 컬럼에서 URL들을 추출하여 리스트로 변환
        url_list = df['artist_list'].tolist()
        print(f'artist_list : {url_list}')

        # URL 목록을 artistsUrlList에 추가
        totalCount = 1
        for i, artistUrl in enumerate(url_list, start=1):
            artistsUrlList.append({
                "artistUrl": artistUrl,
                "artistcount": '0',  # 엑셀 파일에 'artistcount' 정보가 없으므로 임시로 'N/A'를 설정
                "page": 0,  # 페이지 번호는 URL 순서대로 설정
                "totalCount": totalCount
            })
            totalCount += 1

        return artistsUrlList

    def extractCollectionExcelInfo(self,df:pd.DataFrame,df_data:pd.DataFrame,collectionUrl:str,category:str) -> list[pd.DataFrame]:
        i = 1
        totalCount = 1
        totalImageInfoList:list[dict] = []
        while 1:
            url = f"{collectionUrl}page/{i}?&per_page=70"
            try:
                res = requests.get(url,headers=self.headers)
            except:
                time.sleep(10)
                print(f"사이트 오류로 인한 넘김 : {url}")
                i+=1
                continue
            if res.status_code != 200:
                break
            time.sleep(random.uniform(0.45, 0.55))
            soup = BeautifulSoup(res.content,"html.parser")
            if soup.find("div",class_="entry-content") != None or str(soup).find("Sorry, we can't seem to find the page you're looking for") != -1:
                break
            i += 1
            collectionName = soup.find("h1",class_="entry-title").text.strip()
            titlwrap = soup.find('div', class_='titlwrap')
            artistDescription = ""
            if titlwrap:
                containers = titlwrap.find_all('div', class_='container')
                for container in containers:
                    p = container.find('p')
                    if p:
                        artistDescription = p.get_text(strip=True)
                        break  # 첫 번째 <p> 텍스트만 원할 경우

            infoList = soup.find_all("div",class_="pbm")

            total = soup.find("p",class_="woocommerce-result-count").text.replace("items","").strip()

            artist_count_dict = {}
            for index, infoData in enumerate(infoList, start=1):
                brand_div = infoData.find('div', class_='woodmart-product-brands-links')
                country = ""
                artistName = ""
                country_years = ""
                if brand_div:
                    match = re.search(r'\(([^)]+)\)', brand_div.text)
                    if match:
                        country_years = match.group(1)  # 'Norwegian, 1911 - 1992'
                        country = country_years.split(',')[0].strip()  # 'Norwegian'

                    a_tag = brand_div.find('a')
                    if a_tag:
                        artistName = a_tag.get_text(strip=True)

                key = artistName if artistName else "작가명 없음"
                artist_count_dict[key] = artist_count_dict.get(key, 0) + 1


                div = infoData.find("div", class_="woodmart-product-cats")
                field = div.text.strip() if div else ""
                data = infoData.find("div")
                idData = data["data-id"].strip()
                sizeData = json.loads(data["data-sk"])
                imgInfo = sizeData["sk"]
                try:
                    standard = sizeData["sdlimagesize"].split("px")[0].split("x")
                    standardX = standard[0].strip()
                    standardY = standard[1].strip()
                except:
                    standardX = "정보없음"
                    standardY = "정보없음"
                try:
                    max = sizeData["hdlimagesize"].split("px")[0].split("x")
                    maxX = max[0].strip()
                    maxY = max[1].strip()
                except:
                    maxX = "정보없음"
                    maxY = "정보없음"
                pieceUrl = str(infoData.find("a")["href"])
                pieceInfo = infoData.find("h3",class_="product-title").text.strip()
                title = pieceInfo.split("(")[0].strip()
                if len(pieceInfo.split("(")) == 1:
                    birth = "없음"
                elif len(pieceInfo.split("(")) == 2:
                    birth = pieceInfo.split("(")[1].split(")")[0].strip()
                elif len(pieceInfo.split("(")) == 3:
                    birth = pieceInfo.split("(")[2].split(")")[0].strip()
                try:
                    int(birth)
                except:
                    birth = "없음"
                if title == "":
                    title = "("+pieceInfo.split("(")[1].split("(")[0].strip()
                df_info = pd.DataFrame.from_dict([{
                    "페이지":i-1,
                    "ID":idData,
                    "작가명":key,
                    "작품명":title,
                    "작품명풀네임":pieceInfo,
                    "국가":country,
                    "국적및생몰년도":country_years,
                    "장르":category,
                    "작품년도":birth,
                    "Px-가로":standardX,
                    "Px-세로":standardY,
                    "MaxPx-가로":maxX,
                    "MaxPx-세로":maxY,
                    "url":pieceUrl,
                    "skdata":imgInfo
                }])
                print({
                    "페이지":i-1,
                    "ID":idData,
                    "작가명":key,
                    "작품명":title,
                    "작품명풀네임":pieceInfo,
                    "국가":country,
                    "국적및생몰년도":country_years,
                    "장르":category,
                    "작품년도":birth,
                    "Px-가로":standardX,
                    "Px-세로":standardY,
                    "MaxPx-가로":maxX,
                    "MaxPx-세로":maxY,
                    "url":pieceUrl,
                    "skdata":imgInfo
                })
                df = pd.concat([df,df_info])
                totalCount+=1

            # 최종 작가별 수량 DataFrame 생성
            df_data = pd.DataFrame(
                [{"작가명": name, "수량": count}
                 for name, count in artist_count_dict.items() if name != "작가명 없음"]
                + [{"작가명": "작가명 없음", "수량": artist_count_dict["작가명 없음"]}]
                if "작가명 없음" in artist_count_dict else
                [{"작가명": name, "수량": count} for name, count in artist_count_dict.items()]
            )

        return [df,df_data,totalImageInfoList]

    def extractArtistExcelInfo(self,df:pd.DataFrame,df_data:pd.DataFrame,artistUrl:str,artistcount:str,page:int,artistTotalCount:int) -> list[pd.DataFrame]:
        i = 1
        totalCount = 1
        totalImageInfoList:list[dict] = []
        while 1:
            url = f"{artistUrl}page/{i}?&per_page=70"
            try:
                res = requests.get(url,headers=self.headers)
            except:
                time.sleep(10)
                print(f"사이트 오류로 인한 넘김 : {url}")
                i+=1
                continue
            if res.status_code != 200:
                break
            time.sleep(random.uniform(0.45, 0.55))
            soup = BeautifulSoup(res.content,"html.parser")
            if soup.find("div",class_="entry-content") != None or str(soup).find("Sorry, we can't seem to find the page you're looking for") != -1:
                break
            i += 1
            artistName = soup.find("h1",class_="entry-title").text.strip()
            abdate = soup.find("div", class_="abdate").text.strip().split(",")
            country = abdate[0].strip()
            artistDescription = soup.find("div",class_="term-description").text.strip()
            infoList = soup.find_all("div",class_="pbm")

            total = soup.find("p",class_="woocommerce-result-count").text.replace("items","").strip()
            for infoData in infoList:
                field = infoData.find("div",class_="woodmart-product-cats").text.strip()
                data = infoData.find("div")
                idData = data["data-id"].strip()
                sizeData = json.loads(data["data-sk"])
                imgInfo = sizeData["sk"]
                try:
                    standard = sizeData["sdlimagesize"].split("px")[0].split("x")
                    standardX = standard[0].strip()
                    standardY = standard[1].strip()
                except:
                    standardX = "정보없음"
                    standardY = "정보없음"
                try:
                    max = sizeData["hdlimagesize"].split("px")[0].split("x")
                    maxX = max[0].strip()
                    maxY = max[1].strip()
                except:
                    maxX = "정보없음"
                    maxY = "정보없음"
                pieceUrl = str(infoData.find("a")["href"])
                pieceInfo = infoData.find("h3",class_="product-title").text.strip()
                title = pieceInfo.split("(")[0].strip()
                if len(pieceInfo.split("(")) == 1:
                    birth = "없음"
                elif len(pieceInfo.split("(")) == 2:
                    birth = pieceInfo.split("(")[1].split(")")[0].strip()
                elif len(pieceInfo.split("(")) == 3:
                    birth = pieceInfo.split("(")[2].split(")")[0].strip()
                try:
                    int(birth)
                except:
                    birth = "없음"
                if title == "":
                    title = "("+pieceInfo.split("(")[1].split("(")[0].strip()
                df_info = pd.DataFrame.from_dict([{
                    "페이지":page,
                    "작가순서":artistTotalCount,
                    "그림순서":totalCount,
                    "ID":idData,
                    "작가명":artistName,
                    "작품명":title,
                    "작품명풀네임":pieceInfo,
                    "국가":country,
                    "장르":field,
                    "작품년도":birth,
                    "수량":total,
                    "Px-가로":standardX,
                    "Px-세로":standardY,
                    "MaxPx-가로":maxX,
                    "MaxPx-세로":maxY,
                    "url":pieceUrl,
                    "skdata":imgInfo
                }])
                df = pd.concat([df,df_info])
                totalCount+=1

        df_data_info =pd.DataFrame.from_dict([{
            "페이지":page,
            "작가명":artistName,
            "국가":country,
            "수량":total,
            "작가내용":artistDescription
        }])
        df_data = pd.concat([df_data,df_data_info])
        return [df,df_data,totalImageInfoList]


def main()->None:
    currentPath = os.getcwd().replace("\\","/")
    excelCheck = input("전체 엑셀 추출 하시겠습니까? 1.예 2. 아니오 : ").strip()
    downloadCheck = input("1. 이미지 다운로드 / 2. 다운안된 이미지 재 다운로드 : ")
    if downloadCheck == "1":
        startPage = input("추출 페이지를 입력해주세요 (엔터시 처음부터): ").strip()
        selectArtistName:str = input("추출 작가명을 입력해주세요 (엔터시 처음부터): ").strip()
    firstSheetColumn = ["페이지","작가순서","그림순서","ID","작가명","작품명","작품명풀네임","국가","장르","작품년도","수량","Px-가로","Px-세로","MaxPx-가로","MaxPx-세로","url","skdata","이미지 저장여부"]
    secondSheetColumn = ["","페이지","작가명","국가","수량","작가내용"]
    totalImageInfoList:list[dict] = []
    excelIndex = 1
    artvee = ARTVEE()
    headers=artvee.login()
    if excelCheck == "1":
        print("전체 예술가 목록 확인중 ..... ")
        artistUrlList:list[dict] = artvee.getArtistsUrlList()
        print("전체 예술가 목록 확인 완료!")
        print("예술가 정보 엑셀 추출 시작!")
        df = pd.DataFrame(columns=firstSheetColumn)
        df_data = pd.DataFrame(columns=secondSheetColumn)
        beforePage = 1
        for artistInfoForExcel in tqdm(artistUrlList):
            artistUrl=artistInfoForExcel["artistUrl"]
            artistcount=artistInfoForExcel["artistcount"]
            artistPage = artistInfoForExcel["page"]
            artistTotalCount = artistInfoForExcel["totalCount"]
            ################################################
            # url = f"{artistUrl}"
            # res = requests.get(url)
            # soup = BeautifulSoup(res.content,"html.parser")
            # try:
            #     imgUrl = soup.find("img",class_="imspanc")["src"]
            # except:
            #     print(url)
            #     beforePage+=1
            #     continue
            # imgName = soup.find("h1",class_="entry-title").text.strip()
            # number = f"0000{beforePage}"
            # imgName = number[-4:]+" "+imgName
            # imageInfo = requests.get(imgUrl)
            # f = open(f"./result/image/{imgName}.jpg",'wb')
            # f.write(imageInfo.content)
            # f.close()
            # beforePage+=1
            ####################################################
            if len(df["작품명"].tolist()) > 15000 and artistPage != beforePage:
                with pd.ExcelWriter(f"{currentPath}/result/excel/artvee_{excelIndex}.xlsx",engine='openpyxl') as writer: #xlsxwriter
                    df.to_excel(writer,sheet_name="1",index=False)
                    df_data.to_excel(writer,sheet_name="2",index=False)
                excelIndex += 1
                df = pd.DataFrame(columns=firstSheetColumn)
                df_data = pd.DataFrame(columns=secondSheetColumn)
            df_info = artvee.extractArtistExcelInfo(df=df,df_data=df_data,artistUrl=artistUrl,artistcount=artistcount,page=artistPage,artistTotalCount=artistTotalCount)
            df = df_info[0].reset_index(drop=True)
            df_data = df_info[1].reset_index(drop=True)
            totalImageInfoList+=df_info[2]
            beforePage = artistPage
        if (df["작품명"].tolist()) != 0:
            with pd.ExcelWriter(f"{currentPath}/result/excel/artvee_{excelIndex}.xlsx",engine='openpyxl') as writer: #xlsxwriter
                df.to_excel(writer,sheet_name="1",index=False)
                df_data.to_excel(writer,sheet_name="2",index=False)
        print("전체 엑셀 추출 완료")
    excelPath = f"{currentPath}/result/excel"
    imagePath = f"{currentPath}/result/image"
    fileList = os.listdir(path=excelPath)

    for fileInfo in fileList:
        if fileInfo.find("~$") != -1:
            print("엑셀파일을 닫아주세요")
            continue
        try:
            df_excel = pd.read_excel(f"{excelPath}/{fileInfo}",sheet_name="1")
            df_excel_data = pd.read_excel(f"{excelPath}/{fileInfo}",sheet_name="2")
        except:
            print(f"{excelPath}/{fileInfo}는 엑셀 파일이 아닙니다.")
            continue
        print(f"{fileInfo} 이미지 추출중")
        for idx, dataInfo in enumerate(tqdm(df_excel["skdata"])):
            imageUrl = f"https://mdl.artvee.com/sdl/{dataInfo}sdl.jpg"
            pageInfo = str(df_excel.at[idx,"페이지"])
            nameInfo = df_excel.at[idx,"작가명"]
            pieceInfo = df_excel.at[idx,"작품명"]
            artistNum = "0000"+str(df_excel.at[idx,"작가순서"])
            artistNum = artistNum[-3:]
            pieceNumInfo = "0000"+str(df_excel.at[idx,"그림순서"])
            pieceNumInfo = pieceNumInfo[-4:]
            idInfo = df_excel.at[idx,"ID"]
            imageIs = df_excel.at[idx,"이미지 저장여부"]
            if downloadCheck =="2" and imageIs != "X":
                continue

            if selectArtistName != "" and selectArtistName != nameInfo:
                continue
            if startPage != "" and startPage != pageInfo:
                continue
            filename = f"{pageInfo}_{artistNum}_{pieceNumInfo}_{nameInfo}_{pieceInfo}_{idInfo}"
            try:
                imageInfo = requests.get(imageUrl,headers=headers,timeout=30)
            except: # timeout으로 인한 넘김
                print(f"{filename} 저장 실패")
                df_excel.at[idx,"이미지 저장여부"] = "X"
                time.sleep(5)
                continue
            if imageInfo.status_code == 200:
                namePath = f"{imagePath}/{pageInfo}_{nameInfo}"
                if os.path.exists(namePath) == False:
                    os.makedirs(namePath)
                try:
                    f = open(f"{namePath}/{filename}.jpg",'wb')
                    f.write(imageInfo.content)
                    f.close()
                    df_excel.at[idx,"이미지 저장여부"] = ""
                except:
                    print(f"{filename} 저장 실패")
                    df_excel.at[idx,"이미지 저장여부"] = "X"
                    time.sleep(5)
            elif imageInfo.status_code == 404:
                soup = BeautifulSoup(imageInfo.content,"xml")
                errormsg = soup.find("Code").text
                if errormsg.find("NoSuchKey") != -1:
                    df_excel.at[idx,"이미지 저장여부"] = "없음"
                    continue
            else:
                print(f"{filename} 저장 실패")
                df_excel.at[idx,"이미지 저장여부"] = "X"
                time.sleep(5)
            time.sleep(0.5)
        with pd.ExcelWriter(f"{excelPath}/{fileInfo}",engine='openpyxl') as writer: #xlsxwriter
            df_excel.to_excel(writer,sheet_name="1",index=False)
            df_excel_data.to_excel(writer,sheet_name="2",index=False)

def translatorFromExcel()->None:
    currentPath = os.getcwd().replace("\\","/")
    excelPath = f"{currentPath}/result/excel"
    fileList = os.listdir(path=excelPath)
    translator = GoogleTranslator(source='auto', target='ko')
    for fileInfo in fileList:
        if fileInfo.find("~$") != -1:
            print("엑셀파일을 닫아주세요")
            continue
        try:
            df_excel = pd.read_excel(f"{excelPath}/{fileInfo}",sheet_name="1")
            df_excel_data = pd.read_excel(f"{excelPath}/{fileInfo}",sheet_name="2")
        except:
            traceback.print_exc()
            print(f"{fileInfo} 엑셀 읽기 실패")
            continue
        for idx, data in enumerate(tqdm(df_excel["페이지"])):
            try:
                pieceInfo = df_excel.at[idx,"작품명"]
                pieceFullInfo = df_excel.at[idx,"작품명풀네임"]
                try:
                    pieceInfoTrans = translator.translate(pieceInfo)
                    pieceFullInfoTrans = translator.translate(pieceFullInfo)
                except:
                    try:
                        time.sleep(20)
                        pieceInfoTrans = translator.translate(pieceInfo)
                        pieceFullInfoTrans = translator.translate(pieceFullInfo)
                    except:
                        time.sleep(60)
                        pieceInfoTrans = translator.translate(pieceInfo)
                        pieceFullInfoTrans = translator.translate(pieceFullInfo)
                if idx !=0 and idx%1000==0:
                    with pd.ExcelWriter(f"{excelPath}/{fileInfo}",engine='openpyxl') as writer: #xlsxwriter
                        df_excel.to_excel(writer,sheet_name="1",index=False)
                        df_excel_data.to_excel(writer,sheet_name="2",index=False)
                time.sleep(0.3)
                df_excel.at[idx,"번역-1(괄호포함)"] = pieceFullInfoTrans
                df_excel.at[idx,"번역-2(괄호 미포함)"] = pieceInfoTrans
            except:
                traceback.print_exc()
                print("페이지 번역 또는 저장 실패")
                df_excel.at[idx,"번역-1(괄호포함)"] = "번역실패"
                df_excel.at[idx,"번역-2(괄호 미포함)"] = "번역실패"
                time.sleep(30)
        with pd.ExcelWriter(f"{excelPath}/{fileInfo}",engine='openpyxl') as writer: #xlsxwriter
            df_excel.to_excel(writer,sheet_name="1",index=False)
            df_excel_data.to_excel(writer,sheet_name="2",index=False)


def sub_main()->None:
    currentPath = os.getcwd()  # 현재 작업 디렉터리
    excelPath = f"{currentPath}/result"
    file_path = os.path.join(excelPath, "artvee_artist_list.xlsx")
    if not os.path.exists(file_path):
        print("artvee_artist_list.xlsx 파일이 존재하지 않습니다.")
        return None
    # 파일이 존재하면 아래 작업을 진행
    print("artvee_artist_list.xlsx 파일이 존재합니다.")
    currentPath = os.getcwd().replace("\\","/")
    excelCheck = input("전체 엑셀 추출 하시겠습니까? 1.예 2. 아니오 : ").strip()
    downloadCheck = input("1. 이미지 다운로드 / 2. 다운안된 이미지 재 다운로드 : ")
    firstSheetColumn = ["페이지","작가순서","그림순서","ID","작가명","작품명","작품명풀네임","국가","장르","작품년도","수량","Px-가로","Px-세로","MaxPx-가로","MaxPx-세로","url","skdata","이미지 저장여부"]
    secondSheetColumn = ["","페이지","작가명","국가","수량","작가내용"]
    totalImageInfoList:list[dict] = []
    excelIndex = 1
    artvee = ARTVEE()
    headers=artvee.login()
    if excelCheck == "1":
        print("추가 예술가 목록 확인중 ..... ")
        artistUrlList:list[dict] = artvee.getExcelArtistsUrlList(file_path)
        print("추가 예술가 목록 확인 완료!")
        print("예술가 정보 엑셀 추출 시작!")
        df = pd.DataFrame(columns=firstSheetColumn)
        df_data = pd.DataFrame(columns=secondSheetColumn)
        beforePage = 1
        for artistInfoForExcel in tqdm(artistUrlList):
            artistUrl=artistInfoForExcel["artistUrl"]
            artistcount=artistInfoForExcel["artistcount"]
            artistPage = artistInfoForExcel["page"]
            artistTotalCount = artistInfoForExcel["totalCount"]
            ################################################
            # url = f"{artistUrl}"
            # res = requests.get(url)
            # soup = BeautifulSoup(res.content,"html.parser")
            # try:
            #     imgUrl = soup.find("img",class_="imspanc")["src"]
            # except:
            #     print(url)
            #     beforePage+=1
            #     continue
            # imgName = soup.find("h1",class_="entry-title").text.strip()
            # number = f"0000{beforePage}"
            # imgName = number[-4:]+" "+imgName
            # imageInfo = requests.get(imgUrl)
            # f = open(f"./result/image/{imgName}.jpg",'wb')
            # f.write(imageInfo.content)
            # f.close()
            # beforePage+=1
            ####################################################
            if len(df["작품명"].tolist()) > 15000 and artistPage != beforePage:
                with pd.ExcelWriter(f"{currentPath}/result/excel/artvee_artist_{excelIndex}.xlsx",engine='openpyxl') as writer: #xlsxwriter
                    df.to_excel(writer,sheet_name="1",index=False)
                    df_data.to_excel(writer,sheet_name="2",index=False)
                excelIndex += 1
                df = pd.DataFrame(columns=firstSheetColumn)
                df_data = pd.DataFrame(columns=secondSheetColumn)
            df_info = artvee.extractArtistExcelInfo(df=df,df_data=df_data,artistUrl=artistUrl,artistcount=artistcount,page=artistPage,artistTotalCount=artistTotalCount)
            df = df_info[0].reset_index(drop=True)
            df_data = df_info[1].reset_index(drop=True)
            totalImageInfoList+=df_info[2]
            beforePage = artistPage
        if (df["작품명"].tolist()) != 0:

            with pd.ExcelWriter(f"{currentPath}/result/excel/artvee_artist_{excelIndex}.xlsx",engine='openpyxl') as writer: #xlsxwriter
                df.to_excel(writer,sheet_name="1",index=False)
                df_data.to_excel(writer,sheet_name="2",index=False)
        print("전체 엑셀 추출 완료")
    excelPath = f"{currentPath}/result/excel"
    imagePath = f"{currentPath}/result/image"
    fileList = os.listdir(path=excelPath)

    for fileInfo in fileList:
        if fileInfo.find("~$") != -1:
            print("엑셀파일을 닫아주세요")
            continue
        try:
            df_excel = pd.read_excel(f"{excelPath}/{fileInfo}",sheet_name="1")
            df_excel_data = pd.read_excel(f"{excelPath}/{fileInfo}",sheet_name="2")
        except:
            print(f"{excelPath}/{fileInfo}는 엑셀 파일이 아닙니다.")
            continue
        print(f"{fileInfo} 이미지 추출중")
        for idx, dataInfo in enumerate(tqdm(df_excel["skdata"])):
            imageUrl = f"https://mdl.artvee.com/sdl/{dataInfo}sdl.jpg"
            pageInfo = str(df_excel.at[idx,"페이지"])
            nameInfo = df_excel.at[idx,"작가명"]
            pieceInfo = df_excel.at[idx,"작품명"]
            artistNum = "0000"+str(df_excel.at[idx,"작가순서"])
            artistNum = artistNum[-3:]
            pieceNumInfo = "0000"+str(df_excel.at[idx,"그림순서"])
            pieceNumInfo = pieceNumInfo[-4:]
            idInfo = df_excel.at[idx,"ID"]
            imageIs = df_excel.at[idx,"이미지 저장여부"]
            if downloadCheck =="2" and imageIs != "X":
                continue
            filename = f"{pageInfo}_{artistNum}_{pieceNumInfo}_{nameInfo}_{pieceInfo}_{idInfo}"
            try:
                imageInfo = requests.get(imageUrl,headers=headers,timeout=30)
            except: # timeout으로 인한 넘김
                print(f"{filename} 저장 실패")
                df_excel.at[idx,"이미지 저장여부"] = "X"
                time.sleep(5)
                continue
            if imageInfo.status_code == 200:
                namePath = f"{imagePath}/{pageInfo}_{nameInfo}"
                if os.path.exists(namePath) == False:
                    os.makedirs(namePath)
                try:
                    f = open(f"{namePath}/{filename}.jpg",'wb')
                    f.write(imageInfo.content)
                    f.close()
                    df_excel.at[idx,"이미지 저장여부"] = ""
                except:
                    print(f"{filename} 저장 실패")
                    df_excel.at[idx,"이미지 저장여부"] = "X"
                    time.sleep(5)
            elif imageInfo.status_code == 404:
                soup = BeautifulSoup(imageInfo.content,"xml")
                errormsg = soup.find("Code").text
                if errormsg.find("NoSuchKey") != -1:
                    df_excel.at[idx,"이미지 저장여부"] = "없음"
                    continue
            else:
                print(f"{filename} 저장 실패")
                df_excel.at[idx,"이미지 저장여부"] = "X"
                time.sleep(5)
            time.sleep(0.5)
        with pd.ExcelWriter(f"{excelPath}/{fileInfo}",engine='openpyxl') as writer: #xlsxwriter
            df_excel.to_excel(writer,sheet_name="1",index=False)
            df_excel_data.to_excel(writer,sheet_name="2",index=False)


def collection_filter()-> tuple[str, str]:
    excelCheck = input("전체 엑셀 추출 하시겠습니까? 1.예 2. 아니오 : ").strip()
    downloadCheck = input("1. 이미지 다운로드 / 2. 다운안된 이미지 재 다운로드 : ")
    return excelCheck, downloadCheck


def collection_main(category, excelCheck, downloadCheck)->None:
    currentPath = os.getcwd()  # 현재 작업 디렉터리
    excelPath = f"{currentPath}/result/excel/collection"
    file_path = os.path.join(excelPath, f"artvee_{category}.xlsx")
    if not os.path.exists(file_path):
        print(f"artvee_{category}.xlsx 파일이 존재하지 않습니다.")
        return None
    # 파일이 존재하면 아래 작업을 진행
    print(f"artvee_{category}.xlsx 파일이 존재합니다.")
    currentPath = os.getcwd().replace("\\","/")
    firstSheetColumn = ["페이지","ID","작가명","작품명","작품명풀네임","국가","국적및생몰년도","장르","작품년도","Px-가로","Px-세로","MaxPx-가로","MaxPx-세로","url","skdata","이미지 저장여부"]
    secondSheetColumn = ["페이지","작가명","국가","수량","작가내용"]
    totalImageInfoList:list[dict] = []
    artvee = ARTVEE()
    headers=artvee.login()

    collectionUrl = f"https://artvee.com/c/{category}/"
    collectionCount = "0"

    if excelCheck == "1":
        print(f"{category} 정보 엑셀 추출 시작!")
        df = pd.DataFrame(columns=firstSheetColumn)
        df_data = pd.DataFrame(columns=secondSheetColumn)
        df_info = artvee.extractCollectionExcelInfo(df=df,df_data=df_data,collectionUrl=collectionUrl,category=category)
        df = df_info[0].reset_index(drop=True)
        df_data = df_info[1].reset_index(drop=True)
        totalImageInfoList+=df_info[2]
        if (df["작품명"].tolist()) != 0:
            with pd.ExcelWriter(f"{currentPath}/result/excel/collection/artvee_{category}.xlsx",engine='openpyxl') as writer: #xlsxwriter
                df.to_excel(writer,sheet_name="1",index=False)
                df_data.to_excel(writer,sheet_name="2",index=False)
            print("전체 엑셀 추출 완료")

    file_name = f"artvee_{category}.xlsx"
    excelPath = f"{currentPath}/result/excel/collection"
    imageCategoryPath = f"{currentPath}/result/image/collection/{category}/category"
    imageArtistPath = f"{currentPath}/result/image/collection/{category}/artist"
    file_path = os.path.join(excelPath, file_name)

    if not os.path.exists(file_path):
        print(f"{file_name} 파일이 존재하지 않습니다.")
        return

    fileInfo = file_name  # for문 없이 변수만 지정

    if fileInfo.find("~$") != -1:
        print("엑셀파일을 닫아주세요")
        return
    try:
        df_excel = pd.read_excel(f"{excelPath}/{fileInfo}",sheet_name="1")
        df_excel_data = pd.read_excel(f"{excelPath}/{fileInfo}",sheet_name="2")
    except:
        print(f"{excelPath}/{fileInfo}는 엑셀 파일이 아닙니다.")
        return
    print(f"{fileInfo} 이미지 추출중")

    for idx, dataInfo in enumerate(tqdm(df_excel["skdata"])):
        imageUrl = f"https://mdl.artvee.com/sdl/{dataInfo}sdl.jpg"
        nameInfo = df_excel.at[idx,"작가명"]
        pieceInfo = df_excel.at[idx,"작품명"]
        idInfo = df_excel.at[idx,"ID"]
        imageIs = df_excel.at[idx,"이미지 저장여부"]
        if downloadCheck =="2" and imageIs != "X":
            continue
        filename = f"{nameInfo}_{pieceInfo}_{idInfo}"
        try:
            imageInfo = requests.get(imageUrl,headers=headers,timeout=30)
        except Exception as e: # timeout으로 인한 넘김
            print(f'e :{e}')
            print(f"{filename} 저장 실패")
            df_excel.at[idx,"이미지 저장여부"] = "X"
            time.sleep(5)
            continue
        if imageInfo.status_code == 200:
            try:

                # (1) category 경로에 저장
                os.makedirs(imageCategoryPath, exist_ok=True)
                f = open(f"{imageCategoryPath}/{filename}.jpg",'wb')
                f.write(imageInfo.content)
                f.close()

                # ✅ (2) 작가별 폴더에도 저장 (추가)
                os.makedirs(imageArtistPath, exist_ok=True)
                safe_artist_name = nameInfo.replace("/", "_").replace("\\", "_").strip()
                artist_dir = Path(imageArtistPath) / safe_artist_name
                artist_dir.mkdir(parents=True, exist_ok=True)

                with open(artist_dir / f"{filename}.jpg", 'wb') as f:
                    f.write(imageInfo.content)

                df_excel.at[idx,"이미지 저장여부"] = ""
            except Exception as e: # timeout으로 인한 넘김
                print(f'e :{e}')
                print(f"{filename} 저장 실패")
                df_excel.at[idx,"이미지 저장여부"] = "X"
                time.sleep(5)
        elif imageInfo.status_code == 404:
            soup = BeautifulSoup(imageInfo.content,"xml")
            errormsg = soup.find("Code").text
            if errormsg.find("NoSuchKey") != -1:
                df_excel.at[idx,"이미지 저장여부"] = "없음"
                continue
        else:
            print(f"{filename} 저장 실패")
            df_excel.at[idx,"이미지 저장여부"] = "X"
            time.sleep(5)
        time.sleep(0.5)
    with pd.ExcelWriter(f"{excelPath}/{fileInfo}",engine='openpyxl') as writer: #xlsxwriter
        df_excel.to_excel(writer,sheet_name="1",index=False)
        df_excel_data.to_excel(writer,sheet_name="2",index=False)


if __name__ == "__main__":
    mode = input("1. artvee 다운 / 2. 엑셀 번역 : / 3. artvee artist 다운 : / 4. collection by category 선택 : ")
    if mode == "1":
        try:
            main()
        except Exception as e:
            print(f"{str(e)} 오류로 인한 종료")
            traceback.print_exc()
    elif mode == "2":
        try:
            translatorFromExcel()
        except Exception as e:
            print(f"{str(e)} 오류로 인한 종료")
            traceback.print_exc()
    elif mode == "3":
        try:
            sub_main()
        except Exception as e:
            print(f"{str(e)} 오류로 인한 종료")
            traceback.print_exc()
    elif mode == "4":
        print("\n")
        print("-------------------------------------------------------------------------------------")
        print("\n")
        print("1. Abstract / 2. Figurative / 3. Landscape / 4. Posters / 5. Illustration")
        print("6. Religion / 7. Drawings / 8. Mythology / 9. Botanical / 10. Asian Art / 11. Animals")

        selected = input("다운받을 카테고리 번호를 입력하세요 (예: 1,3,5): ")

        # 번호와 카테고리 매핑
        category_map = {
            1: "abstract",
            2: "figurative",
            3: "landscape",
            4: "posters",
            5: "illustration",
            6: "religion",
            7: "drawings",
            8: "mythology",
            9: "botanical",
            10: "asian-art",
            11: "animals"
        }

        try:
            category_numbers = [int(num.strip()) for num in selected.split(",") if num.strip().isdigit()]
            selected_categories = [category_map[num] for num in category_numbers if num in category_map]
            print(f"선택된 카테고리 이름: {selected_categories}")

            # 선택된 카테고리 이름 리스트를 collection_main에 넘김

            excelCheck, downloadCheck = collection_filter()

            for category in selected_categories:
                collection_main(category, excelCheck, downloadCheck)

        except Exception as e:
            print(f"{str(e)} 오류로 인한 종료")
            traceback.print_exc()
    input("완료")




