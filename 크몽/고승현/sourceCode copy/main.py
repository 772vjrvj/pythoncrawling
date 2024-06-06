import os
import json
import sys
import platform
from utils import *

# current_system = platform.system()
#
# if not current_system == 'Darwin':
#     os.chdir(sys._MEIPASS)

def yeyak(countryInfo) -> str:
    base_url = "https://www.worldfootball.net"
    clear()
    print(bcolors.FAIL + "예약을 종료하려면 아무 선택지에서나 -1을 입력" + bcolors.ENDC)
    country = selectInt(menuCountry, False, [countryData[0] for countryData in countryInfo])
    if(country == - 1): return "exit"
    what = selectInt(menuWhat, False, [whatData[0] for whatData in getWhatURL(base_url + countryInfo[country][1])])
    if(what == - 1): return "exit"
    fromYear = selectInt(menuFromYear, False)
    if(fromYear == - 1): return "exit"
    toYear = selectInt(menuToYear, False)
    if(toYear == - 1): return "exit"

    data = {
        "1": country,
        "2": what,
        "3": fromYear,
        "4": toYear
    }
    if not os.path.exists("./yeyak.json"):
        with open("yeyak.json", "w") as file:
            json.dump([data], file)
    else:
        with open("yeyak.json", "r") as file:
            existing_data = json.load(file)
        existing_data.append(data)
        with open("yeyak.json", "w") as file:
            json.dump(existing_data, file)

    return "success"

def yeyakCrawling():
    if not os.path.exists("./yeyak.json"):
        return
    
    with open("yeyak.json", "r") as file:
        datas = json.load(file)

    crawling([tuple(data.values()) for data in datas])

    os.remove("./yeyak.json")

def allCrawling(countryInfo):
    index = 0; length = len(countryInfo)
    base_url = "https://www.worldfootball.net"
    while True:
        if index >= length: break
        what_num = len(getWhatURL(base_url + countryInfo[index][1]))

        country_crawling = []

        for w in range(what_num): country_crawling.append((index, w, 1800, 2200))

        crawling(country_crawling)

        index += 1

if __name__ == "__main__":
    countryInfo = getCountryURL()

    ############################################
    # NOTE: template.xlsx와 crawling.py 건네줘야함 #
    ############################################

    while True:
        mainSelect = selectInt(menuMain)
        if mainSelect == -1: exit(0)
        elif mainSelect == 1:
            fromYear = selectInt(menuFromYear, True)
            if(fromYear == - 1): continue
            toYear = selectInt(menuToYear, True)
            if(toYear == - 1): continue

            allCrawling(countryInfo)
            # allCrawling(countryInfo, fromYear, toYear)
        elif mainSelect == 2:
            while True:
                url = yeyak(countryInfo)
                if url == "exit": break
        elif mainSelect == 3: yeyakCrawling()
        elif mainSelect == 4: printCountryInfo(countryInfo)