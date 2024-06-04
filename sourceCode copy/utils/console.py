import os

from .colors import *

def clear():
    # os.system("clear")
    os.system("cls")

def crwalingScreen(data):
    country, what, year, round = data
    clear()
    print(bcolors.OKCYAN + f"나라: {country}" + bcolors.ENDC)
    print(bcolors.OKCYAN + f"카테고리: {what}" + bcolors.ENDC)
    print(bcolors.OKCYAN + f"년도: {year}" + bcolors.ENDC)
    print(bcolors.OKCYAN + f"라운드: {round}" + bcolors.ENDC)
    print(bcolors.OKGREEN + "크롤링 성공!" + bcolors.ENDC)

def selectInt(menu, isClear: bool = True, itemList: list = None) -> int:
    notList = False;    notInt = False
    
    while True:
        if isClear: clear()
        if itemList != None: selectList = menu(itemList)
        else: selectList = menu()
        try:
            if(notList):
                notList = False
                select = int(input("유효하지 않은 숫자입니다. 입력: "))
            elif(notInt):
                notInt = False
                select = int(input("숫자를 입력해주세요. 입력: "))
            else: select = int(input("입력: "))
            if(not select in selectList):
                notList = True
                continue
            break
        except:
            notInt = True
    return select

# 색깔 없애기
# 단순이 아래 로그만 찍음
def menuMain() -> list[int]:
    print("전체 크롤링: 1")
    print("예약 하기(선택 하기): 2")
    print("예약 크롤링(선택한 정보로 크롤링): 3")
    print("나라 정보 보기: 4")
    print("종료 하기: -1")

    return [-1, 1, 2, 3, 4]

def menuFromYear() -> list[int]:
    print("시작년도: (1800~현재)")
    return [year for year in range(1800, 3000)] + [-1]
def menuToYear() -> list[int]:
    print("끝년도: (1800~현재)")
    return [year for year in range(1800, 3000)] + [-1]
def menuWhat(itemList: list[str]):
    print("선택할 데이터")
    listString = ", ".join([f"{item}: {index}" for index, item in enumerate(itemList)])
    print(listString)

    return [i for i in range(len(itemList))] + [-1]
def menuCountry(itemList: list[str]):
    print(bcolors.OKCYAN + "선택할 국가" + bcolors.ENDC)
    listString = ", ".join([f"{item}: {index}" for index, item in enumerate(itemList)])
    print(bcolors.OKBLUE + listString + bcolors.ENDC)

    return [i for i in range(len(itemList))] + [-1]