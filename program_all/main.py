import requests

url = "https://fin.land.naver.com/front-api/v1/legalDivision/infoList"
params = {"legalDivisionNumbers[]": "1168010600"}
headers = {
    "Referer": "https://fin.land.naver.com/",
    "Accept": "application/json",  # JSON 응답이라 이렇게 두는 게 안전
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Sec-CH-UA": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cookie": '''NNB=Y56Y5KVEJVZWQ; ASID=da9384ec000001984b4b3eec00000023; NAC=ueSMDYBEzfSFB; _fwb=180Tmf4nkTz3sL0e1OB2Anz.1755538494927; landHomeFlashUseYn=Y; bnb_tooltip_shown_finance_v1=true; nstore_session=F/nYQe4QNs5p+QXQLhIhkOND; nstore_pagesession=j6P0OwqWmbPqRssM68C-391198; nhn.realestate.article.rlet_type_cd=A01; SHOW_FIN_BADGE=Y; _ga=GA1.1.343987944.1756381994; _gcl_au=1.1.1012244094.1756428552; _ga_9JHCQLWL5X=GS2.1.s1756428551$o1$g0$t1756428551$j60$l0$h0; _ga_Q7G1QTKPGB=GS2.1.s1756428552$o1$g0$t1756428552$j60$l0$h0; _fbp=fb.1.1756428552291.599892693593967085; _ga_NFRXYYY5S0=GS2.1.s1756428552$o1$g0$t1756428552$j60$l0$h0; _tt_enable_cookie=1; _ttp=01K3SMSJBYH469VBW6STQRCJQP_.tt.1; ttcsid=1756428552579::9HdKHVTyWSBjsoL_wXjx.1.1756428552579; ttcsid_CRLT6VRC77UC5E4HNKOG=1756428552578::McB6ZzkI46yLJKVeTgO1.1.1756428552813; nid_inf=1752193125; NID_AUT=g9cQvJ5C7I44xHqzsKNwVdE+jezI7UY0+UsLGsH3RKMxhofcFKoJ8KbsLyTRHFFM; nhn.realestate.article.trade_type_cd=B1; _ga_RCM29786SD=GS2.1.s1756541336$o5$g1$t1756541351$j45$l0$h0; realestate.beta.lastclick.cortar=1100000000; article_module_info={"BUILDING_INFO":true}; PROP_TEST_KEY=1757155903023.f591b8634a5d13fbedb99fcc9a49832cbabfa15447ad998821185b598e47d873; PROP_TEST_ID=7a433e0966a177a4150693606ab06b9e28dd692886972f835ae7176b7b92dfc6; NACT=1; SRT30=1757223157; BUC=aNXHGb1WLa36MC-krVlPHlHRwD3Bc7Z5ieI5BYCAp30=; NID_SES=AAABrOzNTPoQgw1ZDYUTfWoJ8X20WcFN75wn/rg4Kvw/2Ps8gdje841+TjJjOQu3nScJhqO1PY1Njb0CFUjWFzaG8PrxtVgvT8lnVr6LKBQuKosr6zszNEYR0cWPZSUQc92lRhwDZjUvGZVPg7fkWKTRqOoavmdEUyU/jjJP6jz3MFR39qUmmMeuoj09Rv8c3rcZbOEBJpt1/aQ+SAhn9XQxyl4/EVtHlwENtIhHC/BkoKC22LVYL4lN1p3O9kOrXJ9VPD8d4Cn6PsPpo5ZVlKH/442RpCxZtQbf6u/tnQnbvqdXle63oWVQloJyZJGXdIA6ZUd6tjl5KUB0yT8FJgou8jyyBxFKzOqQkZxHZKtH32YM38KpRbKjQBM5c9NlF1FAcOJC7Q9OIT+gO9gaE5wvcf6A903HVivPgzLTPqtSpsy90RkSkz+LhrUjhHyVEo3z3+bold1OlFnR1AauouVHA0e8xBn66CaruRNwVAexnBP8aG/QQM4kwylXgj6AaPO4UmK4tOH+kG15UiulbQWEo8HSSe7aeSVXvjMetJbrqIwpnnhAUUJyaDj/Yu5KHBaCwQ==''',
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}
res = requests.get(url, params=params, headers=headers, timeout=10)
res.raise_for_status()
print(res.json())
