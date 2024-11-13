import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

countries = [
    {
        "id": 288,
        "masterId": 2005,
        "codeNm": "가나 (Ghana)",
        "etc3": "map_cdo_ghana, 가나",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 266,
        "masterId": 2005,
        "codeNm": "가봉 (Gabon)",
        "etc3": "map_cdo_gabon, 가봉",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 328,
        "masterId": 2003,
        "codeNm": "가이아나 (Guyana)",
        "etc3": "map_sa_guyana, 가이아나",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 270,
        "masterId": 2005,
        "codeNm": "감비아 (Gambia)",
        "etc3": "map_cdo_rtg, 감비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41554,
        "masterId": 2003,
        "codeNm": "과델로프",
        "etc3": "map_sa_guadeloupe, 과델로프",
        "createDt": 1603417727000,
        "updateDt": 1603417727000
    },
    {
        "id": 320,
        "masterId": 2003,
        "codeNm": "과테말라 (Guatemala)",
        "etc3": "map_sa_guatemala, 과테말라",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 316,
        "masterId": 2001,
        "codeNm": "괌 (Guam)",
        "etc3": "map_ana_guam, 괌",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 308,
        "masterId": 2003,
        "codeNm": "그레나다 (Grenada)",
        "etc3": "map_sa_grenada, 그레나다",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 300,
        "masterId": 2004,
        "codeNm": "그리스 (Greece)",
        "etc3": "map_eu_greece, 그리스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 304,
        "masterId": 2002,
        "codeNm": "그린란드 (Greenland)",
        "etc3": "map_na_gi, 그린란드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41582,
        "masterId": 2001,
        "codeNm": "극남군도",
        "etc3": "map_ana_gn, 극남군도",
        "createDt": 1603439322000,
        "updateDt": 1603439322000
    },
    {
        "id": 324,
        "masterId": 2005,
        "codeNm": "기니 (Guinea)",
        "etc3": "map_cdo_guinea, 기니",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 624,
        "masterId": 2005,
        "codeNm": "기니비사우 (Guinea Bissau)",
        "etc3": "map_cdo_gb, 기니바사우",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 516,
        "masterId": 2005,
        "codeNm": "나미비아 (Namibia)",
        "etc3": "map_cdo_namibia, 나미비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 520,
        "masterId": 2001,
        "codeNm": "나우루 (Nauru)",
        "etc3": "map_ana_nauru, 나우루",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 566,
        "masterId": 2005,
        "codeNm": "나이지리아 (Nigeria)",
        "etc3": "map_cdo_nigeria, 나이지리아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 531,
        "masterId": 2005,
        "codeNm": "남수단 (Republic of South Sudan)",
        "etc3": "map_cdo_rss, 남수단",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 710,
        "masterId": 2005,
        "codeNm": "남아프리카 (South Africa)",
        "etc3": "map_cdo_rsa, 남아프리카",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41556,
        "masterId": 2003,
        "codeNm": "남조지아 남샌드위치군도",
        "etc3": "map_sa_ss, 남조지아 남샌드위치군도",
        "createDt": 1603417800000,
        "updateDt": 1603417800000
    },
    {
        "id": 528,
        "masterId": 2004,
        "codeNm": "네덜란드 (Nederlands)",
        "etc3": "map_eu_nl, 네덜란드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 524,
        "masterId": 2001,
        "codeNm": "네팔 (Nepal)",
        "etc3": "map_ana_nepal, 네팔",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 578,
        "masterId": 2004,
        "codeNm": "노르웨이 (Norway)",
        "etc3": "map_eu_norway, 노르웨이",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41580,
        "masterId": 2001,
        "codeNm": "노퍽섬",
        "etc3": "map_ana_norfolk, 노퍽섬",
        "createDt": 1603439274000,
        "updateDt": 1603439274000
    },
    {
        "id": 554,
        "masterId": 2001,
        "codeNm": "뉴질랜드 (New Zealand)",
        "etc3": "map_ana_nz, 뉴질랜드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41579,
        "masterId": 2001,
        "codeNm": "뉴칼레도니아",
        "etc3": "map_ana_nc, 뉴칼레도니아",
        "createDt": 1603439242000,
        "updateDt": 1603439242000
    },
    {
        "id": 41577,
        "masterId": 2001,
        "codeNm": "니우에",
        "etc3": "map_ana_ni, 니우에",
        "createDt": 1603439163000,
        "updateDt": 1603439163000
    },
    {
        "id": 562,
        "masterId": 2005,
        "codeNm": "니제르 (Niger)",
        "etc3": "map_cdo_niger, 니제르",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 558,
        "masterId": 2003,
        "codeNm": "니카라과 (Nicaragua)",
        "etc3": "map_sa_nicaragua, 니카라과",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 158,
        "masterId": 2001,
        "codeNm": "대만 (Taiwan)",
        "etc3": "map_ana_taiwan, 대만",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 410,
        "masterId": 2001,
        "codeNm": "대한민국 (Republic of Korea)",
        "etc3": "map_ana_rk, 대한민국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 208,
        "masterId": 2004,
        "codeNm": "덴마크 (Danmark)",
        "etc3": "map_eu_denmark, 덴마크",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 212,
        "masterId": 2003,
        "codeNm": "도미니카 (Dominica)",
        "etc3": "map_sa_dr, 도미니카",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 214,
        "masterId": 2003,
        "codeNm": "도미니카 공화국 (Dominicana Rep.)",
        "etc3": "map_sa_de_dr, 도미니카 공화국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 276,
        "masterId": 2004,
        "codeNm": "독일 (Germany)",
        "etc3": "map_eu_germany, 독일",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 626,
        "masterId": 2001,
        "codeNm": "동티모르 (Timor-Leste)",
        "etc3": "map_ana_et, 동티모르",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 886,
        "masterId": 2001,
        "codeNm": "디에고 가르시아 (Diego Garcia)",
        "etc3": "map_ana_diego, 디에고 가르시아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 418,
        "masterId": 2001,
        "codeNm": "라오스 (Laos)",
        "etc3": "map_ana_laos, 라오스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 430,
        "masterId": 2005,
        "codeNm": "라이베리아 (Liberia)",
        "etc3": "map_cdo_liberia, 라이베리아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 428,
        "masterId": 2004,
        "codeNm": "라트비아 (Latvia)",
        "etc3": "map_eu_latvia, 라트비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41501,
        "masterId": 2006,
        "codeNm": "러시아 (Russia)",
        "etc3": "map_cis_russia, 러시아",
        "createDt": 1563869514000,
        "updateDt": 1563869514000
    },
    {
        "id": 422,
        "masterId": 2005,
        "codeNm": "레바논 (Lebanon)",
        "etc3": "map_cdo_lebanon, 레바논",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 426,
        "masterId": 2005,
        "codeNm": "레소토 (Lesotho)",
        "etc3": "map_cdo_lesotho, 레소토",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 642,
        "masterId": 2004,
        "codeNm": "루마니아 (Romania)",
        "etc3": "map_eu_romania, 루마니아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 442,
        "masterId": 2004,
        "codeNm": "룩셈부르크 (Luxembourg)",
        "etc3": "map_eu_lb, 룩셈부르크",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 646,
        "masterId": 2005,
        "codeNm": "르완다 (Rwanda)",
        "etc3": "map_cdo_rwanda, 르완다",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 434,
        "masterId": 2005,
        "codeNm": "리비아 (Libya)",
        "etc3": "map_cdo_libya, 리비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41569,
        "masterId": 2005,
        "codeNm": "리유니온",
        "etc3": "map_cdo_reunion, 리유니온",
        "createDt": 1603434527000,
        "updateDt": 1603434527000
    },
    {
        "id": 440,
        "masterId": 2004,
        "codeNm": "리투아니아 (Lithuania)",
        "etc3": "map_eu_lithuania, 리투아니아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 438,
        "masterId": 2004,
        "codeNm": "리히텐슈타인 (Liechtenstein)",
        "etc3": "map_eu_pol, 리히텐슈타인",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 450,
        "masterId": 2005,
        "codeNm": "마다가스카르 (Madagascar)",
        "etc3": "map_cdo_madagascar, 마다가스카르",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 474,
        "masterId": 2003,
        "codeNm": "마르티니크 (Martinique)",
        "etc3": "map_sa_martinique, 마르티니크",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 584,
        "masterId": 2001,
        "codeNm": "마샬 군도 (Marshall Islands)",
        "etc3": "map_ana_mi, 마샬 군도",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 175,
        "masterId": 2005,
        "codeNm": "마요트 (Mayotte)",
        "etc3": "map_cdo_myt, 마요티",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 446,
        "masterId": 2001,
        "codeNm": "마카오 (Macau)",
        "etc3": "map_ana_macau, 마카오",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 807,
        "masterId": 2004,
        "codeNm": "마케도니아 (Маcedoniа)",
        "etc3": "map_eu_macedonia, 마케도니아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 454,
        "masterId": 2005,
        "codeNm": "말라위 (Malawi)",
        "etc3": "map_cdo_malawi, 말라위",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 458,
        "masterId": 2001,
        "codeNm": "말레이시아 (Malaysia)",
        "etc3": "map_ana_malaysia, 말레이시아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 466,
        "masterId": 2005,
        "codeNm": "말리 (Mali)",
        "etc3": "map_cdo_mali, 말리",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 484,
        "masterId": 2003,
        "codeNm": "멕시코 (Mexico)",
        "etc3": "map_na_mexico, 멕시코",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 492,
        "masterId": 2004,
        "codeNm": "모나코 (Monaco)",
        "etc3": "map_eu_monaco, 모나코",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 504,
        "masterId": 2005,
        "codeNm": "모로코 (Morocco)",
        "etc3": "map_cdo_morocco, 모르코",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 480,
        "masterId": 2005,
        "codeNm": "모리셔스 (Mouritius)",
        "etc3": "map_cdo_mauritius, 모리셔스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 478,
        "masterId": 2005,
        "codeNm": "모리타니 (Mauritania)",
        "etc3": "map_cdo_mauritania, 모리타니",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 508,
        "masterId": 2005,
        "codeNm": "모잠비크 (Mozambique)",
        "etc3": "map_cdo_mozambique, 모잠비크",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 499,
        "masterId": 2004,
        "codeNm": "몬테네그로 (Montenegro)",
        "etc3": "map_eu_montenegro, 몬테네그로",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41545,
        "masterId": 2003,
        "codeNm": "몬트세라트",
        "etc3": "map_sa_ms, 몬트세라트",
        "createDt": 1603417096000,
        "updateDt": 1603417096000
    },
    {
        "id": 498,
        "masterId": 2006,
        "codeNm": "몰도바 (Moldova)",
        "etc3": "map_cis_moldova, 몰도바",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 462,
        "masterId": 2001,
        "codeNm": "몰디브 (Maldives)",
        "etc3": "map_ana_maldives, 몰디브",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 470,
        "masterId": 2004,
        "codeNm": "몰타 (Malta)",
        "etc3": "map_eu_malta, 몰타",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 496,
        "masterId": 2001,
        "codeNm": "몽골 (Mongolia)",
        "etc3": "map_ana_mongolia, 몽골",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 840,
        "masterId": 2002,
        "codeNm": "미국 (United States)",
        "etc3": "map_na_usa, 미국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 35,
        "masterId": 2001,
        "codeNm": "미국령 해외 제도 (U.S. Outlying Islands)",
        "etc3": "map_ana_us, 미국령 해외 제도",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 104,
        "masterId": 2001,
        "codeNm": "미얀마 (Republic of the Union of Myanmar)",
        "etc3": "map_ana_rum, 미얀마",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 890,
        "masterId": 2001,
        "codeNm": "미크로네시아 (Micronesia)",
        "etc3": "map_ana_micronesia, 미크로네시아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 548,
        "masterId": 2001,
        "codeNm": "바누아투 (Vanuatu)",
        "etc3": "map_ana_vanuatu, 바누아투",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 48,
        "masterId": 2005,
        "codeNm": "바레인 (Bahrain)",
        "etc3": "map_cdo_bahrain, 바레인",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 52,
        "masterId": 2003,
        "codeNm": "바베이도스 (Barbados)",
        "etc3": "map_sa_barbados, 바베이도스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 336,
        "masterId": 2004,
        "codeNm": "바티칸시국 (Stato della Citta del Vaticano)",
        "etc3": "map_eu_sdcdv, 바티칸",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 44,
        "masterId": 2003,
        "codeNm": "바하마 (Bahamas)",
        "etc3": "map_sa_bahamas, 바하마",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 50,
        "masterId": 2001,
        "codeNm": "방글라데시 (Bangladesh)",
        "etc3": "map_ana_bangladesh, 방글라데시",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 60,
        "masterId": 2002,
        "codeNm": "버뮤다 (Bermuda)",
        "etc3": "map_na_bermuda, 버뮤다",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 204,
        "masterId": 2005,
        "codeNm": "베냉 (Benin)",
        "etc3": "map_cdo_benin, 베냉",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 862,
        "masterId": 2003,
        "codeNm": "베네수엘라 (Venezuela)",
        "etc3": "map_sa_brv, 베네수엘라",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 704,
        "masterId": 2001,
        "codeNm": "베트남 (Vietnam)",
        "etc3": "map_ana_vietnam, 베트남",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 56,
        "masterId": 2004,
        "codeNm": "벨기에 (Belgium)",
        "etc3": "map_eu_belgium, 벨기에",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 112,
        "masterId": 2006,
        "codeNm": "벨라루스 (Belarus)",
        "etc3": "map_cis_belarus, 벨라루스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 84,
        "masterId": 2003,
        "codeNm": "벨리즈 (Belize)",
        "etc3": "map_sa_belize, 벨리즈",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 70,
        "masterId": 2004,
        "codeNm": "보스니아 헤르체고비나 (Bosna and Herzegovina)",
        "etc3": "map_eu_bah, 보스니아 헤르체고비나",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 72,
        "masterId": 2005,
        "codeNm": "보츠와나 (Botswana)",
        "etc3": "map_cdo_botswana, 보츠와나",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 68,
        "masterId": 2003,
        "codeNm": "볼리비아 (Bolivia)",
        "etc3": "map_sa_bolivia, 볼리비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 108,
        "masterId": 2005,
        "codeNm": "부룬디 (Burundi)",
        "etc3": "map_cdo_burundi, 부룬디",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 854,
        "masterId": 2005,
        "codeNm": "부르키나파소 (Burkina Faso)",
        "etc3": "map_cdo_bf, 부르키나파소",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41557,
        "masterId": 2003,
        "codeNm": "부베",
        "etc3": "map_sa_bbd, 부베",
        "createDt": 1603417882000,
        "updateDt": 1603417882000
    },
    {
        "id": 64,
        "masterId": 2001,
        "codeNm": "부탄 (Bhutan)",
        "etc3": "map_ana_bhutan, 부탄",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41572,
        "masterId": 2001,
        "codeNm": "북마리아나군도",
        "etc3": "map_ana_nm, 북마리아나군도",
        "createDt": 1603438020000,
        "updateDt": 1603438020000
    },
    {
        "id": 100,
        "masterId": 2004,
        "codeNm": "불가리아 (Bulgaria)",
        "etc3": "map_eu_bulgaria, 불가리아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 76,
        "masterId": 2003,
        "codeNm": "브라질 (Brazil)",
        "etc3": "map_sa_brazil, 브라질",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 96,
        "masterId": 2001,
        "codeNm": "브루나이 (Brunei)",
        "etc3": "map_ana_brunei, 브루나이",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 882,
        "masterId": 2001,
        "codeNm": "사모아 (Samoa)",
        "etc3": "map_ana_samoa, 사모아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 682,
        "masterId": 2005,
        "codeNm": "사우디아라비아 (Saudi Arabia)",
        "etc3": "map_cdo_sa, 사우디아라비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 893,
        "masterId": 2004,
        "codeNm": "사우스조지아 (South Georgia ...)",
        "etc3": "map_eu_sg, 사우스조지아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41523,
        "masterId": 2001,
        "codeNm": "사이판",
        "etc3": "map_ana_saipan, 사이판",
        "createDt": 1602738700000,
        "updateDt": 1602738700000
    },
    {
        "id": 196,
        "masterId": 2004,
        "codeNm": "사이프러스 (Cyprus)",
        "etc3": "map_eu_roc, 사이프러스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 674,
        "masterId": 2004,
        "codeNm": "산마리노 (San Marino)",
        "etc3": "map_eu_sm, 산마리노",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 678,
        "masterId": 2005,
        "codeNm": "상투메 프린시페 (Sao Tome and Principe)",
        "etc3": "map_cdo_stp, 상투메프린시페",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 844,
        "masterId": 2002,
        "codeNm": "생 마르탱 (Saint-Martin )",
        "etc3": "map_na_martin, 생 마르탱",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 895,
        "masterId": 2004,
        "codeNm": "생 바르텔르미 (Saint-Barthelemy)",
        "etc3": "map_eu_, ",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41576,
        "masterId": 2001,
        "codeNm": "서사모아",
        "etc3": "map_ana_ws, 서사모아",
        "createDt": 1603439123000,
        "updateDt": 1603439123000
    },
    {
        "id": 41565,
        "masterId": 2005,
        "codeNm": "서사하라",
        "etc3": "map_cdo_ws, 서사하라",
        "createDt": 1603431272000,
        "updateDt": 1603431272000
    },
    {
        "id": 686,
        "masterId": 2005,
        "codeNm": "세네갈 (Senegal)",
        "etc3": "map_cdo_senegal, 세네갈",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 688,
        "masterId": 2004,
        "codeNm": "세르비아-몬테네그로 (Serbia and Montenegro)",
        "etc3": "map_eu_serbia, 세르비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 897,
        "masterId": 2004,
        "codeNm": "세우타 및 멜리야 (Ceuta y Melilla)",
        "etc3": "map_eu_cm, 세우타 및 멜리야",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 690,
        "masterId": 2005,
        "codeNm": "세이셸(Seychelles)",
        "etc3": "map_cdo_seychelles, 세이셀",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41542,
        "masterId": 2003,
        "codeNm": "세인트 키츠 네비스",
        "createDt": 1603332813000,
        "updateDt": 1603332813000
    },
    {
        "id": 41552,
        "masterId": 2003,
        "codeNm": "세인트 키츠 네비스",
        "etc3": "map_sa_skn, 세인트 키츠 네비스",
        "createDt": 1603417544000,
        "updateDt": 1603417544000
    },
    {
        "id": 41568,
        "masterId": 2005,
        "codeNm": "세인트 헬레나",
        "etc3": "map_cdo_sh, 세인트 헬레나",
        "createDt": 1603434501000,
        "updateDt": 1603434501000
    },
    {
        "id": 41551,
        "masterId": 2003,
        "codeNm": "세인트루시아",
        "etc3": "map_sa_sl, 세인트루시아",
        "createDt": 1603417507000,
        "updateDt": 1603417507000
    },
    {
        "id": 41550,
        "masterId": 2003,
        "codeNm": "세인트마틴",
        "etc3": "map_sa_sm, 세인트마틴",
        "createDt": 1603417475000,
        "updateDt": 1603417475000
    },
    {
        "id": 41544,
        "masterId": 2003,
        "codeNm": "세인트바돌로메",
        "etc3": "map_sa_sb, 세인트바돌로메",
        "createDt": 1603417015000,
        "updateDt": 1603417015000
    },
    {
        "id": 41549,
        "masterId": 2003,
        "codeNm": "세인트빈센트그레나딘",
        "etc3": "map_sa_svg,  세인트빈센트그레나딘",
        "createDt": 1603417410000,
        "updateDt": 1603417410000
    },
    {
        "id": 848,
        "masterId": 2002,
        "codeNm": "세인트피에르-미케롱 (Saint-Pierre-et-Miquelon)",
        "etc3": "map_na_spm, 생피에르<br/>미클롱",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 706,
        "masterId": 2005,
        "codeNm": "소말리아 (Somalia)",
        "etc3": "map_cdo_somalia, 소말리아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 90,
        "masterId": 2001,
        "codeNm": "솔로몬 제도 (Solomon Islands)",
        "etc3": "map_ana_solomon, 솔로몬 제도",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 736,
        "masterId": 2005,
        "codeNm": "수단 (Sudan)",
        "etc3": "map_cdo_sudan, 수단",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 740,
        "masterId": 2003,
        "codeNm": "수리남 (Republic of Suriname)",
        "etc3": "map_sa_suriname, 수리남",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 144,
        "masterId": 2001,
        "codeNm": "스리랑카 (Sri Lanka)",
        "etc3": "map_ana_sl, 스리랑카",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41562,
        "masterId": 2004,
        "codeNm": "스발바르",
        "etc3": "map_eu_si, 스발바르",
        "createDt": 1603418974000,
        "updateDt": 1603418974000
    },
    {
        "id": 748,
        "masterId": 2005,
        "codeNm": "스와질랜드 (Swaziland)",
        "etc3": "map_cdo_swaziland, 스와질랜드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 752,
        "masterId": 2004,
        "codeNm": "스웨덴 (Sweden)",
        "etc3": "map_eu_sweden, 스웨덴",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 756,
        "masterId": 2004,
        "codeNm": "스위스 (Switzerland)",
        "etc3": "map_eu_sl, 스위스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 724,
        "masterId": 2004,
        "codeNm": "스페인 (Spain) / 에스파냐 (Espana)",
        "etc3": "map_eu_spain, 스페인",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 703,
        "masterId": 2004,
        "codeNm": "슬로바키아 (Slovakia)",
        "etc3": "map_eu_slovakia, 슬로바키아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 705,
        "masterId": 2004,
        "codeNm": "슬로베니아 (Slovenia)",
        "etc3": "map_eu_slovenia, 슬로베니아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 760,
        "masterId": 2005,
        "codeNm": "시리아 (Syria)",
        "etc3": "map_cdo_syria, 시리아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 694,
        "masterId": 2005,
        "codeNm": "시에라리온 (Sierra Leone)",
        "etc3": "map_cdo_sl, 시에라리온",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 852,
        "masterId": 2002,
        "codeNm": "신트마르턴 (Sint Maarten)",
        "etc3": "map_na_, 신트마르턴",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 702,
        "masterId": 2001,
        "codeNm": "싱가포르 (Singapore)",
        "etc3": "map_ana_singapore, 싱가포르",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 784,
        "masterId": 2005,
        "codeNm": "아랍에미리트 연합 (United Arab Emirates)",
        "etc3": "map_cdo_uae, 아랍에미레이트",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41547,
        "masterId": 2003,
        "codeNm": "아루바",
        "etc3": "map_sa_aruba, 아루바",
        "createDt": 1603417197000,
        "updateDt": 1603417197000
    },
    {
        "id": 51,
        "masterId": 2006,
        "codeNm": "아르메니아 (Armenia)",
        "etc3": "map_cis_armenia, 아르메니아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 33,
        "masterId": 2003,
        "codeNm": "아르헨티나 (Argentina)",
        "etc3": "map_sa_argentina, 아르헨티나",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 896,
        "masterId": 2001,
        "codeNm": "아메리칸 사모아 (American Samoa)",
        "etc3": "map_ana_am_samoa, 아메리칸 사모아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 352,
        "masterId": 2004,
        "codeNm": "아이슬란드 (Republic of Iceland)",
        "etc3": "map_eu_iceland, 아이슬란드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 332,
        "masterId": 2003,
        "codeNm": "아이티 (Haiti)",
        "etc3": "map_sa_haiti, 아이티",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 372,
        "masterId": 2004,
        "codeNm": "아일랜드 (Ireland)",
        "etc3": "map_eu_ireland, 아일랜드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41,
        "masterId": 2006,
        "codeNm": "아제르바이잔 (Azerbaijan)",
        "etc3": "map_cis_azerbaijan, 아제르바이잔",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 37,
        "masterId": 2001,
        "codeNm": "아프가니스탄 (Afghanistan)",
        "etc3": "map_ana_afghanistan, 아프카니스탄",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 38,
        "masterId": 2004,
        "codeNm": "안도라 (Andorra)",
        "etc3": "map_eu_andorra, 안도라",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41548,
        "masterId": 2003,
        "codeNm": "안틸레스",
        "etc3": "map_sa_antilles, 안틸레스",
        "createDt": 1603417232000,
        "updateDt": 1603417232000
    },
    {
        "id": 42,
        "masterId": 2004,
        "codeNm": "알바니아 (Albania)",
        "etc3": "map_eu_albania, 알바니아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 43,
        "masterId": 2005,
        "codeNm": "알제리 (Algeria)",
        "etc2": " ",
        "etc3": "map_cdo_algeria, 알제리",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 39,
        "masterId": 2005,
        "codeNm": "앙골라 (Angola)",
        "etc3": "map_cdo_angola, 앙골라",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 34,
        "masterId": 2003,
        "codeNm": "앤티가 바부다 (Antigua and Barbuda)",
        "etc3": "map_sa_ab, 앤티가 바부다",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41546,
        "masterId": 2003,
        "codeNm": "앵길라",
        "etc3": "map_sa_ai, 앵길라",
        "createDt": 1603417129000,
        "updateDt": 1603417129000
    },
    {
        "id": 41564,
        "masterId": 2004,
        "codeNm": "얀바웬",
        "etc3": "map_eu_jm, 얀마웬",
        "createDt": 1603431165000,
        "updateDt": 1603431165000
    },
    {
        "id": 538,
        "masterId": 2005,
        "codeNm": "어센션 섬 (Ascension Island)",
        "etc3": "map_cdo_ascension, 어센션",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 232,
        "masterId": 2005,
        "codeNm": "에리트리아 (Eritrea)",
        "etc3": "map_cdo_eritrea, 에리트레아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 233,
        "masterId": 2004,
        "codeNm": "에스토니아 (Estonia)",
        "etc3": "map_eu_estonia, 에스토니아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 218,
        "masterId": 2003,
        "codeNm": "에콰도르 (Ecuador)",
        "etc3": "map_sa_ecuador, 에콰도르",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 231,
        "masterId": 2005,
        "codeNm": "에티오피아 (Ethiopia)",
        "etc3": "map_cdo_ethiopia, 에티오피아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 222,
        "masterId": 2003,
        "codeNm": "엘살바도르 (El Salvador)",
        "etc3": "map_sa_es, 엘살바도르",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 826,
        "masterId": 2004,
        "codeNm": "영국 (United Kingdom)",
        "etc3": "map_eu_uk, 영국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 887,
        "masterId": 2005,
        "codeNm": "예멘 (Yemen)",
        "etc3": "map_cdo_yemen, 예멘",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 512,
        "masterId": 2005,
        "codeNm": "오만 (Oman)",
        "etc3": "map_cdo_oman, 오만",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 40,
        "masterId": 2004,
        "codeNm": "오스트리아 (Austria)",
        "etc3": "map_eu_austria, 오스트리아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 340,
        "masterId": 2003,
        "codeNm": "온두라스 (Honduras)",
        "etc3": "map_sa_honduras, 온두라스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41563,
        "masterId": 2004,
        "codeNm": "올란드제도",
        "etc3": "map_eu_ai, 올란드 제도",
        "createDt": 1603419007000,
        "updateDt": 1603419007000
    },
    {
        "id": 400,
        "masterId": 2005,
        "codeNm": "요르단 (Jordan)",
        "etc3": "map_cdo_jordan, 요르단",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 800,
        "masterId": 2005,
        "codeNm": "우간다 (Uganda)",
        "etc3": "map_cdo_uganda, 우간다",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 858,
        "masterId": 2003,
        "codeNm": "우루과이 (Uruguay)",
        "etc3": "map_sa_uruguay, 우루과이",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 860,
        "masterId": 2006,
        "codeNm": "우즈베키스탄 (Uzbekistan)",
        "etc3": "map_cis_uzbekistan, 우즈베키스탄",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 804,
        "masterId": 2006,
        "codeNm": "우크라이나 (Ukraine)",
        "etc3": "map_cis_ukraine, 우크라이나",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41575,
        "masterId": 2001,
        "codeNm": "윌리스푸투나제도",
        "etc3": "map_ana_wf, 윌리스푸투나제도",
        "createDt": 1603439085000,
        "updateDt": 1603439085000
    },
    {
        "id": 368,
        "masterId": 2005,
        "codeNm": "이라크 (Iraq)",
        "etc3": "map_cdo_iraq, 이라크",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 364,
        "masterId": 2005,
        "codeNm": "이란 (Iran)",
        "etc3": "map_cdo_iran, 이란",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 376,
        "masterId": 2005,
        "codeNm": "이스라엘 (Israel)",
        "etc3": "map_cdo_israel, 이스라엘",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 818,
        "masterId": 2005,
        "codeNm": "이집트 (Egypt)",
        "etc3": "map_cdo_egypt, 이집트",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 380,
        "masterId": 2004,
        "codeNm": "이탈리아 (Italia)",
        "etc3": "map_eu_italy, 이탈리아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 356,
        "masterId": 2001,
        "codeNm": "인도(India)",
        "etc3": "map_ana_india, 인도",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 360,
        "masterId": 2001,
        "codeNm": "인도네시아 (Indonesia)",
        "etc3": "map_ana_indonesia, 인도네시아 ",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41570,
        "masterId": 2005,
        "codeNm": "인도령인도양지역",
        "etc3": "map_cdo_iot, 인도령인도양지역",
        "createDt": 1603434578000,
        "updateDt": 1603434578000
    },
    {
        "id": 392,
        "masterId": 2001,
        "codeNm": "일본 (Japan)",
        "etc3": "map_ana_japan, 일본",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 388,
        "masterId": 2003,
        "codeNm": "자메이카 (Jamaica)",
        "etc3": "map_sa_jamaica, 자메이카",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41567,
        "masterId": 2005,
        "codeNm": "자이르",
        "etc3": "map_cdo_zaire, 자이르",
        "createDt": 1603433546000,
        "updateDt": 1603433546000
    },
    {
        "id": 894,
        "masterId": 2005,
        "codeNm": "잠비아 (Zambia)",
        "etc3": "map_cdo_zambia, 잠비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 226,
        "masterId": 2005,
        "codeNm": "적도 기니 (Ecuatorial Guinea)",
        "etc3": "map_cdo_eg, 적도기니",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 268,
        "masterId": 2006,
        "codeNm": "조지아 (Georgia)",
        "etc3": "map_cis_gruziya, 조지아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 156,
        "masterId": 2001,
        "codeNm": "중국 (China)",
        "etc3": "map_ana_china, 중국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 140,
        "masterId": 2005,
        "codeNm": "중앙 아프리카 공화국 (Central African Republic)",
        "etc3": "map_cdo_car, 중앙아프리카공화국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 262,
        "masterId": 2005,
        "codeNm": "지부티 (Djibouti)",
        "etc3": "map_cdo_djibouti, 지부티",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41522,
        "masterId": 2004,
        "codeNm": "지브롤터",
        "etc3": "map_eu_gibraltar, 지브롤터",
        "createDt": 1602738208000,
        "updateDt": 1602738208000
    },
    {
        "id": 716,
        "masterId": 2005,
        "codeNm": "짐바브웨 (Zimbabwe)",
        "etc3": "map_cdo_zimbabwe, 짐바브웨",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 148,
        "masterId": 2005,
        "codeNm": "차드 (Chad)",
        "etc3": "map_cdo_chad, 차드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 203,
        "masterId": 2004,
        "codeNm": "체코 (Czech)",
        "etc3": "map_eu_czech, 체코",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 152,
        "masterId": 2003,
        "codeNm": "칠레 (Chile)",
        "etc3": "map_sa_chile, 칠레",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 542,
        "masterId": 2005,
        "codeNm": "카나리아 제도 (Islas Canarias)",
        "etc3": "map_cdo_canarias, 카나리아 제도",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41574,
        "masterId": 2001,
        "codeNm": "카라바시",
        "etc3": "map_ana_karabash, 카라바시",
        "createDt": 1603439049000,
        "updateDt": 1603439049000
    },
    {
        "id": 120,
        "masterId": 2005,
        "codeNm": "카메룬 (Cameroon)",
        "etc3": "map_cdo_cameroon, 카메룬",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 132,
        "masterId": 2005,
        "codeNm": "카보베르데(Cape Verde)",
        "etc3": "map_cdo_cv, 카보베라테",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 398,
        "masterId": 2006,
        "codeNm": "카자흐스탄 (Kazakhstan)",
        "etc3": "map_cis_kazakhstan, 카자흐스탄",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 634,
        "masterId": 2005,
        "codeNm": "카타르 (Qatar)",
        "etc3": "map_cdo_qatar, 카타르",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 116,
        "masterId": 2001,
        "codeNm": "캄보디아 (Cambodia)",
        "etc3": "map_ana_cambodia, 캄보디아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 124,
        "masterId": 2002,
        "codeNm": "캐나다 (Canada)",
        "etc3": "map_na_canada, 캐나다",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 404,
        "masterId": 2005,
        "codeNm": "케냐 (Kenya)",
        "etc3": "map_cdo_kenya, 케냐",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41559,
        "masterId": 2002,
        "codeNm": "케이만군도",
        "etc3": "map_na_ci, 케이만군도",
        "createDt": 1603418077000,
        "updateDt": 1603418077000
    },
    {
        "id": 174,
        "masterId": 2005,
        "codeNm": "코모로스 (Comoros)",
        "etc3": "map_cdo_comoros, 코모로",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 188,
        "masterId": 2003,
        "codeNm": "코스타리카 (Costa Rica)",
        "etc3": "map_sa_cr, 코스타리카",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41584,
        "masterId": 2001,
        "codeNm": "코코스제도",
        "etc3": "map_ana_cocos, 코코스제도",
        "createDt": 1603439467000,
        "updateDt": 1603439467000
    },
    {
        "id": 384,
        "masterId": 2005,
        "codeNm": "코트디부아르 (Republic of Cote d'ivoire)",
        "etc3": "map_cdo_rcd, 코트디부아르",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 170,
        "masterId": 2003,
        "codeNm": "콜롬비아 (Colombia)",
        "etc3": "map_sa_colombia, 콜롬비아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41566,
        "masterId": 2005,
        "codeNm": "콩고",
        "etc3": "map_cdo_rtc, 콩고",
        "createDt": 1603433510000,
        "updateDt": 1603433510000
    },
    {
        "id": 999,
        "masterId": 2005,
        "codeNm": "콩고공화국(REPUBLIC OF THE CONGO)",
        "etc3": "map_cdo_congo,  콩고공화국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 178,
        "masterId": 2005,
        "codeNm": "콩고민주공화국(DEMOCRATIC REPUBLIC OF CONGO)",
        "etc3": "map_cdo_de_congo,콩고민주공화국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 192,
        "masterId": 2003,
        "codeNm": "쿠바 (Cuba)",
        "etc3": "map_sa_cuba, 쿠바",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 414,
        "masterId": 2005,
        "codeNm": "쿠웨이트 (Kuwait)",
        "etc3": "map_cdo_kuwait, 쿠웨이트",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41578,
        "masterId": 2001,
        "codeNm": "쿡군도",
        "etc3": "map_ana_cook, 쿡군도",
        "createDt": 1603439202000,
        "updateDt": 1603439202000
    },
    {
        "id": 856,
        "masterId": 2002,
        "codeNm": "퀴라소 (Curacao)",
        "etc3": "map_na_curacao, 퀴라소",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 191,
        "masterId": 2004,
        "codeNm": "크로아티아 (Croatia)",
        "etc3": "map_eu_croatia, 크로아티아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41583,
        "masterId": 2001,
        "codeNm": "크리스마스제도",
        "etc3": "map_ana_cl, 크리스마스제도",
        "createDt": 1603439380000,
        "updateDt": 1603439380000
    },
    {
        "id": 861,
        "masterId": 2002,
        "codeNm": "클립퍼튼 섬 (Clipperton I.)",
        "etc3": "map_na_clipper, 클립퍼튼 섬",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 417,
        "masterId": 2006,
        "codeNm": "키르기스스탄 (Kyrgizstan)",
        "etc3": "map_cis_kirgystan, 키르기스스탄",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 296,
        "masterId": 2001,
        "codeNm": "키리바시 (Kiribati)",
        "etc3": "map_ana_kiribati, 키리바시",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 762,
        "masterId": 2006,
        "codeNm": "타지키스탄 (Tajikistan)",
        "etc3": "map_cis_tadzhikistan, 타지키스탄",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 834,
        "masterId": 2005,
        "codeNm": "탄자니아 (Tanzania)",
        "etc3": "map_cdo_tanzania, 탄자니아",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 764,
        "masterId": 2001,
        "codeNm": "태국 (Thailand)",
        "etc3": "map_ana_tl, 태국",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41558,
        "masterId": 2003,
        "codeNm": "터크스",
        "etc3": "map_sa_turks, 터크스",
        "createDt": 1603417914000,
        "updateDt": 1603417914000
    },
    {
        "id": 768,
        "masterId": 2005,
        "codeNm": "토고 (Togo)",
        "etc3": "map_cdo_togo, 토고",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41525,
        "masterId": 2001,
        "codeNm": "토켈라우",
        "etc3": "map_ana_tokelau, 토켈라우",
        "createDt": 1602741398000,
        "updateDt": 1602741398000
    },
    {
        "id": 776,
        "masterId": 2001,
        "codeNm": "통가 (Tonga)",
        "etc3": "map_ana_tonga, 통가",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 795,
        "masterId": 2006,
        "codeNm": "투르크메니스탄 (Turkmenistan)",
        "etc3": "map_cis_turkmenistan, 투르키메니스탄",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 798,
        "masterId": 2001,
        "codeNm": "투발루 (Tuvalu)",
        "etc3": "map_ana_tuvalu, 투발루",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 788,
        "masterId": 2005,
        "codeNm": "튀니지 (Tunisia)",
        "etc3": "map_cdo_tunisia, 튀니지",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 792,
        "masterId": 2004,
        "codeNm": "튀르키예 (Türkiye)",
        "etc3": "map_eu_turkey, 터키",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 780,
        "masterId": 2003,
        "codeNm": "트리니다드 토바고 (Trinidad and Tobago)",
        "etc3": "map_sa_tt, 트리니다드, 토바고 수리남",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41553,
        "masterId": 2003,
        "codeNm": "트리니다드토바고 수리남",
        "etc3": "map_sa_tt, 트리니다드 토바고 수리남",
        "createDt": 1603417601000,
        "updateDt": 1603417601000
    },
    {
        "id": 899,
        "masterId": 2004,
        "codeNm": "트리스탄다쿠냐 (Tristan da Cunha I.)",
        "etc3": "map_eu_tdc, 트리스탄다쿠냐",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 591,
        "masterId": 2003,
        "codeNm": "파나마 (Panama)",
        "etc3": "map_sa_panama, 파나마",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 600,
        "masterId": 2003,
        "codeNm": "파라과이 (Paraguay)",
        "etc3": "map_sa_paraguay, 파라과이",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 586,
        "masterId": 2001,
        "codeNm": "파키스탄 (Pakistan)",
        "etc3": "map_ana_pakistan, 파키스탄",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 598,
        "masterId": 2001,
        "codeNm": "파푸아뉴기니 (Papua New Guinea)",
        "etc3": "map_ana_png, 파푸아뉴기니",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 585,
        "masterId": 2001,
        "codeNm": "팔라우 (Palau)",
        "etc3": "map_ana_palau, 팔라우",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 275,
        "masterId": 2005,
        "codeNm": "팔레스타인 지구(Palestine)",
        "etc3": "map_cdo_palestine, 팔레스타인",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41561,
        "masterId": 2004,
        "codeNm": "페로제도",
        "etc3": "map_eu_fi, 페로제도",
        "createDt": 1603418228000,
        "updateDt": 1603418228000
    },
    {
        "id": 864,
        "masterId": 2002,
        "codeNm": "페로제도 (Faroe Islands)",
        "etc3": "map_eu_fi, 페로제도",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 604,
        "masterId": 2003,
        "codeNm": "페루 (Peru)",
        "etc3": "map_sa_peru, 페루",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 620,
        "masterId": 2004,
        "codeNm": "포르투갈 (Portugal)",
        "etc3": "map_eu_portugal, 포르투갈",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41555,
        "masterId": 2003,
        "codeNm": "포클랜드 제도",
        "etc3": "map_sa_fi, 포클랜드 제도",
        "createDt": 1603417763000,
        "updateDt": 1603417763000
    },
    {
        "id": 616,
        "masterId": 2004,
        "codeNm": "폴란드 (Poland)",
        "etc3": "map_eu_pl, 폴란드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41524,
        "masterId": 2001,
        "codeNm": "폴리네시아",
        "etc3": "map_ana_polynesia, 폴리네시아",
        "createDt": 1602741094000,
        "updateDt": 1602741094000
    },
    {
        "id": 630,
        "masterId": 2003,
        "codeNm": "푸에르토리코 (Puerto Rico)",
        "etc3": "map_sa_pr, 푸에르토리코",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 250,
        "masterId": 2004,
        "codeNm": "프랑스 (France)",
        "etc3": "map_eu_france, 프랑스",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 242,
        "masterId": 2001,
        "codeNm": "피지 (Fiji)",
        "etc3": "map_ana_fiji, 피지",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 246,
        "masterId": 2004,
        "codeNm": "핀란드 (Suomi)",
        "etc3": "map_eu_fl, 핀란드",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 608,
        "masterId": 2001,
        "codeNm": "필리핀 (Philippines)",
        "etc3": "map_ana_philippines, 필리핀",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41581,
        "masterId": 2001,
        "codeNm": "핏케인제도",
        "etc3": "map_ana_pi, 핏케인제도",
        "createDt": 1603439299000,
        "updateDt": 1603439299000
    },
    {
        "id": 41573,
        "masterId": 2001,
        "codeNm": "허드맥도날드제도",
        "etc3": "map_ana_hlml, 허드맥도날드제도",
        "createDt": 1603439013000,
        "updateDt": 1603439013000
    },
    {
        "id": 348,
        "masterId": 2004,
        "codeNm": "헝가리 (Hungary)",
        "etc3": "map_eu_hungary, 헝가리",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 36,
        "masterId": 2001,
        "codeNm": "호주 (Australia)",
        "etc3": "map_ana_australia, 호주",
        "createDt": 1491962887000,
        "updateDt": 1491962887000
    },
    {
        "id": 41571,
        "masterId": 2001,
        "codeNm": "홍콩",
        "etc3": "map_ana_hk, 홍콩",
        "createDt": 1603437978000,
        "updateDt": 1603437978000
    }
]



# 공통 헤더
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "cookie": "ACEUCI=1; ACEUCI=1; portal_visited=20241109041401813001; org.springframework.web.servlet.i18n.CookieLocaleResolver.LOCALE=ko; JSESSIONID=5vDqEB7pY39ZkpcG7yNJ9Bs34ZSyD39zw2oJZ8uBxvp4f2L1vrIDPm8UrAHQcAjj.blue1_servlet_engine1; ACEFCID=UID-672E62F7CF671048EACE546D; _ga=GA1.1.859242966.1731093240; AUFAH1A45931692707=1731093240136334028|2|1731093240136334028|1|1731093239905234028; ACEUACS=1731093239905234028; AUAH1A45931692707=1731097002678702851%7C3%7C1731093240136334028%7C1%7C1731093239905234028%7C1; _ga_C8W44QRLHV=GS1.1.1731097002.2.1.1731097275.4.0.0; ASAH1A45931692707=1731097002678702851%7C1731097275423701211%7C1731097002678702851%7C0%7Cbookmark; ARAH1A45931692707=httpswwwkoreannetportalglobalpgnewslocaldomodelistarticleLimit10articleoffset10bookmark; RT=\"z=1&dm=www.korean.net&si=2e6c3380-5413-4448-a9ad-49c7a645d1a5&ss=m394cosf&sl=0&tt=0&bcn=%2F%2F684d0d46.akstat.io%2F\"",
    "priority": "u=0, i",
    "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}

# 페이지 요청 함수
def fetch_page_content(url, offset):
    full_url = f"{url}?mode=list&&articleLimit=10&article.offset={offset}"
    response = requests.get(full_url, headers=headers)
    response.raise_for_status()
    return response.text

# 이미지 URL 가져오는 함수
def fetch_image_url(content_url):
    response = requests.get(content_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    img_tag = soup.select_one(".contents_wrap .contents img")
    if img_tag and 'src' in img_tag.attrs:
        return "https://www.korean.net" + img_tag["src"]
    return ""

# 데이터 파싱 함수
def parse_content(html, base_url, category):
    global countries
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".tbl_type1 tbody tr")
    data_list = []

    for index, row in enumerate(rows):
        content = {
            "콘텐츠 명": "",
            "콘텐츠 분류": "글",
            "공개일자": "",
            "노출매체": "코리안넷 웹사이트",
            "퀄리티": "",
            "콘텐츠 대상지역": "",
            "콘텐츠 내용": "",
            "콘텐츠 저작권 소유처": "코리안넷",
            "라이선스": "제작 저작권 소유",
            "콘텐츠 시청 방법": "코리안넷 웹사이트",
            "이미지 url": "",
            "콘텐츠 주소": "",
            "카테고리": category
        }


        # td 태그 안에 있는 경우라면, row 대신 부모 요소로 접근하여 확인합니다.

        article_country = row.find("input", class_="articleCountry")
        if article_country:
            value = int(article_country['value'])  # '724'을 int로 변환하여 사용

            target_country = next((country for country in countries if country['id'] == value), None)
            if target_country:
                # 한글 부분만 추출
                content["콘텐츠 대상지역"] = target_country['codeNm'].split('(')[0].strip()

        # 콘텐츠 명
        title_tag = row.select_one(".inputTitle")
        if title_tag:
            content["콘텐츠 명"] = title_tag.get_text(strip=True)


        content["콘텐츠 내용"] = (
            "재외동포 인터뷰"
            if "인터뷰" in content["콘텐츠 명"]
            else f"({content['콘텐츠 대상지역']}) 재외동포 일상"
        )

        content["콘텐츠 분류"] = "인터뷰" if "인터뷰" in content["콘텐츠 명"] else "글"

        # 콘텐츠 공개 연도
        date_tag = row.select_one(".t1_date.date")
        if date_tag:
            content["공개일자"] = date_tag.get_text(strip=True)

        # 콘텐츠 주소
        link_tag = row.select_one(".viewLink")
        if link_tag and 'href' in link_tag.attrs:
            href = link_tag["href"]
            content["콘텐츠 주소"] = f"{base_url}{href}"

            # 콘텐츠 이미지 URL
            article_no = href.split("articleNo=")[1]
            content_url = f"{base_url}?mode=view&articleNo={article_no}"  # '.do' 없이 구성
        content["이미지 url"] = fetch_image_url(content_url)
        print(f'index : {index}, content : {content}')
        data_list.append(content)
        time.sleep(0.1)  # 요청 간 딜레이 추가

    return data_list

# 엑셀 저장 함수
def save_to_excel(data_list, filename="코리아넷.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False)
    print(f"엑셀 파일 '{filename}'로 저장되었습니다.")

# 메인 함수
def main():
    all_data = []

    # URL 목록과 페이지 범위
    urls = [
        # {"url": "https://www.korean.net/portal/global/pg_news_local.do", "pages": 2, "category": "해외통신원 소식"},
        {"url": "https://www.korean.net/portal/global/pg_news_local.do", "pages": 280, "category": "해외통신원 소식"},
        {"url": "https://www.korean.net/portal/global/pg_news_group.do", "pages": 138, "category": "재외동포단체 소식"},
        {"url": "https://www.korean.net/portal/global/pg_news_hanin.do", "pages": 10, "category": "한인회 운영사례"}
    ]

    # 각 URL별로 데이터 수집
    for item in urls:
        base_url = item["url"]
        category = item["category"]
        max_pages = item["pages"]

        for page_no in range(max_pages):
            offset = page_no * 10
            print(f"{category} - 페이지 {page_no + 1}/{max_pages} 처리 중...")
            html = fetch_page_content(base_url, offset)
            page_data = parse_content(html, base_url, category)
            all_data.extend(page_data)

    # 엑셀 저장
    save_to_excel(all_data)

if __name__ == "__main__":
    main()
