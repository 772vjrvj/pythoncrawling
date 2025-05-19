from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver

from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import traceback
import requests
import random
import json
import time
import ssl
import sys
import os

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



if __name__ == "__main__":
    mode = input("1. artvee 다운 / 2. 엑셀 번역 : / 3. artvee artist 다운 : ")
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
    input("완료")