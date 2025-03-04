import requests
import json
from typing import List, Dict
import time

def fetch_products(page: int) -> Dict:

    # API 요청을 위한 URL 및 기본 파라미터
    url = "https://www.kohls.com/catalog/womens-shirts-blouses-tops-clothing.jsp"

    # cookie = "362fd180cb7a77f64919ee892a4d9d35=0c76da8bd356d9cd59ff612f55c1535b; AKA_GEO=KR; AKA_RV2=5; AKA_RV=35; AKA_RV3=79; AKA_RV5=65; AKA_RV4=10; AKA_RV8=61; AKA_RV6=73; AKA_CNC2=True; AKA_CBCC=True; AKA_PDP2=True; AKA_STP=false; AKA_CDP2=True; AKA_ACM=True; AKA_PIQ=True; AKA_PMP_YP=; AKA_EXP=control1; akacd_www-kohls-com-mosaic-p2=2147483647~rv=21~id=c58c13b0c8709fee0949ba7432d8b5f3; bm_ss=ab8e18ef4e; PIM-SESSION-ID=Rb7CB6x9RxX8VBlc; ak_bmsc=5BE1EAF62D30B9E79ECABAD766D45929~000000000000000000000000000000~YAAQDNojF8Nh5leVAQAAMsiJWxpKHw+D243Qk+tTkYlrwbLmTuc0NGEjUEZtvDysCRY8AmCKlebH8RpQGdKYMrUtS6AKZhzLLfFfh2ExlI2iS3Xx04lhVDW0WTOvP+IYDdq2NX4CYv8gizmbufm6k/n4GRjn6d/c1+K2S1RRlE9rR+B7sZb6fxvhxzKYtHScSCWdtNV6/Razs2f2Dxo8cAKdOOKAXwMGrYcgWOkhE7rkhqw1R7z+qTWFmgT1EArZ4bcq2pGh1uQ/izxCZSe9CCpbMhQY00/rOmm2IiSQvHQJJ4e4t6a1DT1H7rSwzElpCbLZErgdQkkQceG/FtN8DfbWkfHRHfbxvU0t/1zLuM26cdB3a0as3C0XCAtM+0LBc9y9kXOAw1QuHuERXDRmXiFGgTmch1MghwDhuFTxz5gA4ghPRxfcHZiKFKJsxbTCidhc5vdAfIjVAA0KTg==; X-SESSIONID=62ffac22-e242-4053-9e43-3670788cf98a; SoftLoggedInCookie=; VisitorId=62ffac22-e242-4053-9e43-3670788cf98a; akaalb_aem_homepage=~op=aem_production:aem_production|~rv=26~m=aem_production:0|~os=554fb49c1bda6073578f281b62264a0e~id=42cf1e5e7dc75e413a7512200366bd0f; pdpUrl=; AKA_HP2Redesign=hp1; AKA_HPTest=65; AMCVS_F0EF5E09512D2CD20A490D4D%40AdobeOrg=1; rxVisitor=1740997513840DPQSOAP0TNGAF8T1R1B640MF1C5HFDFQ; __gsas=ID=b436c79f76cb509b:T=1740997513:RT=1740997513:S=ALNI_MaJkyjL-Ek1S19luxfOGmdCeDhtww; fp_client={%22id%22:%2234405907741740997515%22}; _mibhv=anon-1740997515533-7550037210_8212; _cs_c=0; _li_dcdm_c=.kohls.com; _lc2_fpi=0b10d8358f40--01jndrkpfbgz9p2781e1g5y5e2; _lc2_fpi_js=0b10d8358f40--01jndrkpfbgz9p2781e1g5y5e2; AKA_A2=A; affinity="71e5c29f2c12fb73"; store_location=; _dpm_ses.f2d1=*; at_check=true; AMCV_F0EF5E09512D2CD20A490D4D%40AdobeOrg=179643557%7CMCIDTS%7C20151%7CMCMID%7C05864698454350754950882754362888169186%7CMCAAMLH-1741602321%7C11%7CMCAAMB-1741602321%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1741004721s%7CNONE%7CMCSYNCSOP%7C411-20158%7CvVersion%7C5.5.0%7CMCCIDH%7C-514424871%7CMCSYNCS%7C1083-20158*1085-20158*1086-20158*1087-20158*1088-20158; _pin_unauth=dWlkPVlXUTFNRFl3TUdRdE5EZ3laaTAwTlRZM0xUbG1NVEl0TVRjMFkyRm1OV0V6TXpVeg; s_cc=true; IR_gbd=kohls.com; _evga_ce07={%22uuid%22:%22e203056b23a7d8bc%22}; _sfid_6ab3={%22anonymousId%22:%22e203056b23a7d8bc%22%2C%22consents%22:[]}; _tt_enable_cookie=1; _ttp=01JNDRKY8R88M397X2Z15TAWZX_.tt.1; _fbp=fb.1.1740997523825.30519979310429889; dtCookie=v_4_srv_7_sn_L47E3R5MGNF4QIOM9VM7TAK4MLVNS33D_app-3Acf6a6b14e494e621_1_ol_0_perc_100000_mul_1; _gcl_au=1.1.600558684.1740997524; _scid=KmpEVmAW0O2GgVYJM_fwJTx_ANPI3R9D; _gid=GA1.2.1988464754.1740997525; _ScCbts=%5B%5D; _sctr=1%7C1740927600000; kls_p=true; spa=1; tceGDF=false; _li_ss=CpABCgYI-QEQmhoKBQgKEJoaCgYI3QEQmhoKBQgJEJoaCgYIgQEQmhoKCQj_____BxCkGgoGCOMBEJoaCgYIpAEQmhoKBgizARCaGgoGCIkBEJoaCgYIpQEQmhoKBgiAAhCcGgoGCOEBEJoaCgYIogEQmhoKBgj_ARCaGgoGCNIBEJoaCgUIfhCaGgoGCIgBEJoa; _dpm_id.f2d1=fc11a745-7d9f-48e0-81ae-393e9f67d28f.1740997521.1.1740997836.1740997521.504fdb09-e36b-478d-95cd-464b1594ac1f; dtSa=-; gpv_pn=clothing%7Cshirts%20%26%20blouses%7Ctops%7Cwomens; IR_PI=d0a6ae05-f819-11ef-acf0-b3c0e68c0e05%7C1740997898706; _cs_cvars=%7B%221%22%3A%5B%22Page%20Name%22%2C%22clothing%7Cshirts%20%26%20blouses%7Ctops%7Cwomens%22%5D%2C%225%22%3A%5B%22PMP%20Page%20Name%22%2C%22women's%20tops%20and%20blouses%20for%20women%20at%20kohl's%20%7C%20kohl's%22%5D%7D; bm_sz=AD66300797E2561D21D141151354100F~YAAQb/EgF8kOA0mVAQAAeNuYWxqcRvPl670viaJM7f0rZVUigpPVkhSY0DnGMRBHfvRRAMSl/Qg63TpWgqSZoKNx9xILaKtvjq60VanjB/gNnGtmhNsowhZq/1IhW3MsDwfdlp31x27/YFqxHBPu348SwA2lNt/iY3Ajt3NmQPnVRyUyzgMYPwvBI/53pzPKIgpVR5TshW4oTrZS5/iCQgDmjo/2ZqiPJs3l2tqox70VAQc7lBLWBGPfIM1srijAzj+tRzyYRXUoq4QGrhGoq/jRYPmKp3+Qy7Go354HUKKnQ3Twemsxfyu8nCtRSDznUmV7RM2ZUemI1gF53F6TQeDBwDrr/aj4sjD/HOLQr4tr5HpYOHqpzlsu5S0W15hhHR9PJGFsDcSEtivOfelzC1Hc4T+/kpfqJmGXgriSiz0zrTJQ4VhZUjwfq6gYyJiC1dqfti6UUr0s37nklNBBty1641I7BZNAsWomMkRoxA==~3750209~4535344; bm_lso=08ABF70CC2A71586B4A98F709D702F9E0BA07ADA6AC12299C01EE3E3F283C8D8~YAAQnjggF1pPzkeVAQAA7ZeYWwKoxWA3GiRnTUvP7iTRndAxJQSp9vqlPtKO0RWevxz7Bw8XesWnWgQ666uNitoRX/+0mF0GhlEPfTPo8dYb8SjOdT83y9i6F+4GW9OtFWmHhSJidDMonAjcDAPRLhwH+Kvwrof9ez+8+okmPqKO99hddFjGCdzwcqFZChsnUaRfpBexpZKna/Ut56QD6W2lrzRr5JXa9oLcQznH0RsQg6nFLnDW6YbC51Si8eVg44sLqQnscorm1edAlFffLqPx83Ke5h0cd48n7PfXQcOWGnXIi3+7zNfjc0gyJiiMh6H+FoeYglklMILV6Bi2WPEUWDzXluTIeaOO/prGhYr4VXYpJ0RjyG0/RpRXyqH4gymChMTgziEpnb0GQDNnUi1/koBwquL84r3hB1ISteGoYZnZLvRvvjsui0O5vKqrDn7n8JFOLU27bSjG30vo^1740998503511; ae062a17b2ddc11f26ed2dc6752f3bd3=6282866faf464de71bfc4f2e032d788a; _rmt_an_idt=0; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Mar+03+2025+19%3A41%3A54+GMT%2B0900+(%ED%95%9C%EA%B5%AD+%ED%91%9C%EC%A4%80%EC%8B%9C)&version=202306.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d3719b0f-1577-4205-aaf7-6d185af01b70&interactionCount=0&landingPath=https%3A%2F%2Fwww.kohls.com%2Fcatalog%2Fwomens-shirts-blouses-tops-clothing.jsp%3FCN%3DGender%3AWomens+Product%3AShirts%2520%2526%2520Blouses+Category%3ATops+Department%3AClothing%26cc%3Dwms-TN3.0-S-shirtsblouses%26kls_sbp%3D05864698454350754950882754362888169186%26spa%3D1%26PPP%3D48%26WS%3D0%26S%3D1&groups=C005%3A1%2CC0001%3A1%2CC0003%3A1%2CC006%3A1%2CC0004%3A1%2CC0002%3A1; fp_session={%22i%22:%2246760242781740997515%22%2C%22d%22:9%2C%22r%22:%22https://www.google.com/%22}; mbox=session#a2aba4e89e9148a681e0a7cdba1187b6#1741000380|PC#a2aba4e89e9148a681e0a7cdba1187b6.32_0#1804243320; IR_5349=1740998520050%7C385561%7C1740998520050%7C%7C; _scid_r=OOpEVmAW0O2GgVYJM_fwJTx_ANPI3R9D_u8NaQ; _ga=GA1.1.67787307.1740997525; _uetsid=cb2725d0f81911ef837e753277861444; _uetvid=cb271120f81911ef9ba2799c1dcb860b; evarRefinementValues=%7B%22evar23%22%3A%22no%20refinement%22%2C%22evar24%22%3A%22no%20refinement%22%2C%22evar27%22%3A%22%22%2C%22evar28%22%3A%22Clothing%7CShirts%20%26%20Blouses%7CTops%7CWomens%22%2C%22pagename%22%3A%22Clothing%7CShirts%20%26%20Blouses%7CTops%7CWomens%22%2C%22prop40%22%3A%22Clothing%7CShirts%20%26%20Blouses%7CTops%7CWomens%3Eno%20refinement%22%7D; pmplocationhref=https%3A%2F%2Fwww.kohls.com%2Fcatalog%2Fwomens-shirts-blouses-tops-clothing.jsp%3FCN%3DGender%3AWomens%2BProduct%3AShirts%2520%2526%2520Blouses%2BCategory%3ATops%2BDepartment%3AClothing%26cc%3Dwms-TN3.0-S-shirtsblouses%26kls_sbp%3D05864698454350754950882754362888169186%26spa%3D1%26PPP%3D48%26WS%3D48%26S%3D1; akavpau_www=1740998916~id=4950ea5a8d902ba686e926daeaf7e346; AKA_HP2=control; bm_s=YAAQb/EgFwQXA0mVAQAAx6WaWwOjDZ2fH9GhtI2uvazE/Va13iGL5c4pcvbnSzl5NP5d6ITzS/k7x7qO5Cy/Sn75NJle+sQQ/0IYxW+PNQNTkzDC2oPzbbqLcWEINFOA+aNaNrlVYf2fKJqRBOvN5PZ+8U/fc5ettRyKk/jztyawtVpyBWnJfHvLZgp/9rjnmGgh3y0XV4UXO5Th3etcCu7sIsZphm2ePPH0k8sWfU9AMqpn4BmV/uf01My6lFLG64iMeiQL/xECKOVLO9peGnEe2vCvAd/u+2fv74+OY1b/+rzVu4XRZQcH/kui2Vj9csaMmUy6blflLXbYZxuSqqesS5Exagcdn/Iu6xUOurhoqNprbdYCu/eVrVVtzwLFQCzngjymwVnlTG2Z0hDWxwXSTDsazxSeSvAeSj1a9WbEX7oIYbSTRg8GnL9ipjSqzCTB1sAJSKfM/g==; bm_so=C817B785F1EAF8330B96719DDC0271BDFCF164EEA96313AC6CE21DABB5554842~YAAQb/EgFwUXA0mVAQAAyKWaWwJZ9Viy7dCuf7+TlU+e0ntFS0OzL8Zx0L6jl2cg/RhKk7sBrBCi3ZhPfhGnqgBeLju+ZkZywN7479tnTFtXiMGnqhpa7YnhNpCmFJoeNxGnASjibqsz5Apyy/M3HQA3gotfAv4UChiyvaVn0z8GQ0XltBJXTEBTJgp3fX+zzUTgvWHIhQETRPxJjjDRkpm4qscTcbed5Nkjmn3gfBRmScmI7g+LX4XzV60WBtTH4Yntq9yhSRdIDEThIJdMzpxij4QH2kL4gAQXCjeXcdm3iSiKaPkLoSKzgJ19cksImS9+vvMaVD5p47KIHK0qkb9HOwZlafdNT69EU48EyHJI5tuRR9wTh224N3/Y7zD75UsLJMsWbZGPGJCu1fq6FejVdXQhELLvrZJZhNFx4ZzrfPLK5f04yBuodEFQfiFJ6v3miSKBIXQrQnRSd8KC; _ga_ZLYRBY87M8=GS1.1.1740997546.1.1.1740998616.56.0.0; bm_sv=2EBFBFEAA52E88CD223F397F8254593F~YAAQb/EgFwoXA0mVAQAAWKiaWxqQ7eDAeIIBLnkR4LIkWZA5I9XApIoDZp9ptAjzUARQwvxKgYcf99qdxbmoFLSwFSbXh0HvfECRUvbPvIEJnRxu4xKBaKRhfTBE55p2FLhWz/avB082Gmd9V5WTdkrGbtHCj8w+12013EvFqjslZ2sl5CgfPetwATfUOuww4P8JvLczHRQ12JXBrQEQZAqB4kSdUgN+CgTA3VZ644xGdcXLio0dJ4dUGvjry/ln/w==~1; _cs_id=df5ecf8d-e471-aea9-8ffe-ca0707656b83.1740997515.1.1740998617.1740997515.1730825794.1775161515764.1.x; _cs_s=24.0.1.9.1741000474226; _abck=A4C6CD9ECBF988437288BE25239470B0~-1~YAAQT/EgFx+g+kiVAQAAdp6bWw3GBG5+yobSP/5GOH45UnT17a8M/0CJnD4662Z86bDfzPZRRP1AFm78q0BpKuMwmhNK4EoTl4XvHcOm21WK38foF34+3zWwmCzRLcMf9rM6lZ50gkZ+k+u56G+Jegv1ddPb8Db0pjdwZljgYRtHD4aV5xz4IHS/GOB4rcyrifeuGY7iMrYamUZoRE9iBlorRAYAJ+X095HKrXfzKIUKOuKE9sKCGiqe15PkYduEiGvl2B2u0NYB60gxQZVhGZCs+K2rnYSRv9omoXwv7GiraaW2IdubR4vWObftq8xkdozxYrX4WdwBvsU4GKmq3Wpou/EJ1KcDgdu5XRaAxLc5kxrFLcMsyiEjNaI/cZ/ckUvyWahdZVdoarj29rUkR4cHZAb9Qy17M/F4HZAH4ATG0XQFIak16gP4Aqpv9Mr7lOIVhp5n2egVik76H54hsu4mB1UXOPfaZBWaBw+mt5B6+t1xQCpvCr476qYjCBDvtAYO+oTnZ7Y01GKwtomLIaMKsWrvRJ+FeFdU+vAZeDHzlURb0FQ=~-1~-1~1741001111; RT="z=1&dm=kohls.com&si=c27f67b3-482b-4632-8f3e-28152d3187d9&ss=m7swyqs9&sl=9&tt=ove&bcn=%2F%2F684d0d42.akstat.io%2F&ld=lbnx&nu=207re2x3&cl=p4gh"; s_sq=kohlscomprod%3D%2526c.%2526a.%2526activitymap.%2526page%253Dclothing%25257Cshirts%252520%252526%252520blouses%25257Ctops%25257Cwomens%2526link%253DNext%252520Page%2526region%253Dpage-navigation-bottom%2526pageIDType%253D1%2526.activitymap%2526.a%2526.c; rxvt=1741000480372|1740997513841; dtPC=7$398513565_442h28vUOCNDJAPCIHFFLARIUETUCRHPLBTGIGC-0e0"

    cookie = ""

    headers = {
        "authority": "www.kohls.com",
        "method": "GET",
        "scheme": "https",
        "cookie": cookie,
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.kohls.com/catalog/womens-shirts-blouses-tops-clothing.jsp",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    # 요청 파라미터 템플릿
    payload = {
        "CN": "Gender:Womens Product:Shirts & Blouses Category:Tops Department:Clothing",
        "cc": "wms-TN3.0-S-shirtsblouses",
        "kls_sbp": "05864698454350754950882754362888169186",
        "spa": "1",
        "PPP": "48",
        "WS": 0,  # WS 값 변경
        "S": "1",
        "ajax": "true",
        "gNav": "false"
    }

    """
    특정 WS 값을 사용하여 요청을 보내고 데이터를 가져옴.
    :param ws_value: 변경할 WS 값 (0, 48, 96, ...)
    :return: JSON 데이터에서 'totalRecordsCount'와 'products' 리스트를 반환
    """
    payload["WS"] = page * 48

    response = requests.get(url, headers=headers, params=payload)

    if response.status_code == 200:
        data = response.json()
        return {
            "totalRecordsCount": data.get("totalRecordsCount", 0),
            "products": data.get("products", [])
        }
    else:
        print(f"Failed to fetch data for WS={page}. Status Code: {response.status_code}")
        return {"totalRecordsCount": 0, "products": []}


def main():
    """
    메인 실행 함수
    - WS 값을 0, 48, 96씩 증가시키면서 데이터 가져오기
    - totalRecordsCount 저장
    - products 리스트 수집
    """
    all_products: List[Dict] = []
    total_records = 0

    for ws in range(0, 47):  # 1부터 47까지 반복
        result = fetch_products(ws)
        if ws == 0:
            total_records = result["totalRecordsCount"]
        all_products.extend(result["products"])
        time.sleep(2)

    print(f"Total Records Count: {total_records}")
    print(f"Total Products Collected: {len(all_products)}")

    # 결과 출력 (일부만 표시)
    for product in all_products[:5]:  # 처음 5개만 출력
        print(json.dumps(product, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
