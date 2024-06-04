from .colors import *

def printCountryInfo(countryInfo: list[tuple[str, str]]):
    index = 0; length = len(countryInfo)
    while True:
        if index >= length: break
        elif index + 2 < length:
            print(bcolors.BOLD + f"{countryInfo[index][0]} -> {index}\t{countryInfo[index+1][0]} -> {index+1}\t{countryInfo[index+2][0]} -> {index+2}" + bcolors.ENDC)
            index += 3
        elif index + 1 < length:
            print(bcolors.BOLD + f"{countryInfo[index][0]} -> {index}\t{countryInfo[index+1][0]} -> {index+1}" + bcolors.ENDC)
            index += 2
        else:
            print(bcolors.BOLD + f"{countryInfo[index][0]} -> {index}" + bcolors.ENDC)
            index += 1
    input(bcolors.HEADER + "Enter키를 쳐서 돌아가기" + bcolors.ENDC)