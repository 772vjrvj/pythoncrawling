import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import json

# 웹 드라이버 초기화 (크롬 드라이버 사용 예시, 드라이버 경로에 맞게 설정)
driver = webdriver.Chrome()

def wait_for_login():
    input("로그인이 완료되면 엔터를 눌러주세요.")

def fetch_category_data(categorys):
    results = []

    for category in categorys:
        # part_index에 따라 URL 결정
        if category['part_index'] == 1:
            base_url = "https://blang.shop/wb_admin/category/category_edit1.php"
        elif category['part_index'] == 2:
            base_url = "https://blang.shop/wb_admin/category/category_edit2.php"

        url = f"{base_url}?idx={category['idx']}&part_index={category['part_index']}"
        driver.get(url)

        try:
            time.sleep(1)
            # part_name 요소가 나타날 때까지 기다림
            part_name = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "part_name"))
            ).get_attribute("value")

            part1_code = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "part1_code"))
            ).get_attribute("value")

            # part2_code 요소 바로 찾기 (에러 처리 포함)
            try:
                part2_code = driver.find_element(By.NAME, "part2_code").get_attribute("value")
                part2_code = part2_code if part2_code else ""
            except NoSuchElementException:
                print(f"'part2_code' 요소가 존재하지 않습니다. (idx: {category['idx']})")
                part2_code = ""
            except Exception as e:
                print(f"'part2_code' 요소 검색 중 예상치 못한 오류 발생 (idx: {category['idx']}): {e}")
                part2_code = ""

            # parent_name 설정
            parent_name = ""
            if part2_code:  # part2_code가 있는 경우에만 부모 찾기
                for previous_obj in reversed(results):
                    if previous_obj["part1_code"] == part1_code and not previous_obj["part2_code"]:
                        parent_name = previous_obj["name"]
                        break

            # 객체 생성 및 결과에 추가
            obj = {
                "part_index": category['part_index'],
                "idx": category['idx'],
                "name": part_name,
                "part1_code": part1_code,
                "part2_code": part2_code,
                "parent_name": parent_name
            }
            print(obj)
            results.append(obj)

        except TimeoutException:
            print(f"요소를 찾는 데 타임아웃이 발생했습니다. (idx: {category['idx']})")
        except Exception as e:
            print(f"페이지 로딩 중 예상치 못한 오류 발생 (idx: {category['idx']}): {e}")

    return results

def main():
    driver.get("https://blang.shop/wb_admin/index.php")
    wait_for_login()  # 로그인 대기

    categorys = [
        {
            "part_index": 1,
            "idx": 393
        },
        {
            "part_index": 1,
            "idx": 391
        },
        {
            "part_index": 1,
            "idx": 410
        },
        {
            "part_index": 1,
            "idx": 389
        },
        {
            "part_index": 1,
            "idx": 442
        },
        {
            "part_index": 1,
            "idx": 32
        },
        {
            "part_index": 2,
            "idx": 120
        },
        {
            "part_index": 2,
            "idx": 163
        },
        {
            "part_index": 2,
            "idx": 336
        },
        {
            "part_index": 2,
            "idx": 396
        },
        {
            "part_index": 2,
            "idx": 397
        },
        {
            "part_index": 2,
            "idx": 398
        },
        {
            "part_index": 2,
            "idx": 399
        },
        {
            "part_index": 2,
            "idx": 400
        },
        {
            "part_index": 2,
            "idx": 401
        },
        {
            "part_index": 2,
            "idx": 402
        },
        {
            "part_index": 2,
            "idx": 403
        },
        {
            "part_index": 2,
            "idx": 404
        },
        {
            "part_index": 2,
            "idx": 405
        },
        {
            "part_index": 2,
            "idx": 406
        },
        {
            "part_index": 2,
            "idx": 407
        },
        {
            "part_index": 2,
            "idx": 408
        },
        {
            "part_index": 2,
            "idx": 409
        },
        {
            "part_index": 1,
            "idx": 328
        },
        {
            "part_index": 2,
            "idx": 331
        },
        {
            "part_index": 2,
            "idx": 329
        },
        {
            "part_index": 2,
            "idx": 330
        },
        {
            "part_index": 2,
            "idx": 411
        },
        {
            "part_index": 2,
            "idx": 412
        },
        {
            "part_index": 2,
            "idx": 413
        },
        {
            "part_index": 2,
            "idx": 414
        },
        {
            "part_index": 2,
            "idx": 415
        },
        {
            "part_index": 2,
            "idx": 416
        },
        {
            "part_index": 2,
            "idx": 417
        },
        {
            "part_index": 2,
            "idx": 418
        },
        {
            "part_index": 2,
            "idx": 419
        },
        {
            "part_index": 2,
            "idx": 420
        },
        {
            "part_index": 2,
            "idx": 421
        },
        {
            "part_index": 2,
            "idx": 422
        },
        {
            "part_index": 2,
            "idx": 423
        },
        {
            "part_index": 2,
            "idx": 424
        },
        {
            "part_index": 2,
            "idx": 425
        },
        {
            "part_index": 2,
            "idx": 426
        },
        {
            "part_index": 1,
            "idx": 34
        },
        {
            "part_index": 1,
            "idx": 235
        },
        {
            "part_index": 1,
            "idx": 33
        },
        {
            "part_index": 2,
            "idx": 151
        },
        {
            "part_index": 2,
            "idx": 152
        },
        {
            "part_index": 2,
            "idx": 168
        },
        {
            "part_index": 2,
            "idx": 427
        },
        {
            "part_index": 2,
            "idx": 428
        },
        {
            "part_index": 2,
            "idx": 429
        },
        {
            "part_index": 2,
            "idx": 430
        },
        {
            "part_index": 1,
            "idx": 204
        },
        {
            "part_index": 2,
            "idx": 206
        },
        {
            "part_index": 2,
            "idx": 333
        },
        {
            "part_index": 2,
            "idx": 334
        },
        {
            "part_index": 2,
            "idx": 335
        },
        {
            "part_index": 2,
            "idx": 431
        },
        {
            "part_index": 2,
            "idx": 432
        },
        {
            "part_index": 2,
            "idx": 433
        },
        {
            "part_index": 1,
            "idx": 382
        },
        {
            "part_index": 2,
            "idx": 383
        },
        {
            "part_index": 2,
            "idx": 384
        },
        {
            "part_index": 2,
            "idx": 434
        },
        {
            "part_index": 1,
            "idx": 385
        },
        {
            "part_index": 1,
            "idx": 386
        },
        {
            "part_index": 2,
            "idx": 387
        },
        {
            "part_index": 2,
            "idx": 388
        },
        {
            "part_index": 1,
            "idx": 203
        },
        {
            "part_index": 1,
            "idx": 437
        }
    ]

    results = fetch_category_data(categorys)
    print(f"총 객체 수: {len(results)}")
    print(json.dumps(results, indent=4, ensure_ascii=False))

    driver.quit()

if __name__ == "__main__":
    main()


category_obj = [
    {
        "part_index": 1,
        "idx": 393,
        "name": "TODAY REVIEW",
        "part1_code": "1728286931",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 391,
        "name": "이번주신상",
        "part1_code": "1728280612",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 410,
        "name": "GIFT BOX",
        "part1_code": "1728305221",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 389,
        "name": "미러급SA",
        "part1_code": "1728121673",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 442,
        "name": "바로배송",
        "part1_code": "1728559852",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 32,
        "name": "BAG",
        "part1_code": "1422929956",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 2,
        "idx": 120,
        "name": "CHA",
        "part1_code": "1422929956",
        "part2_code": "1505723217",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 163,
        "name": "LV",
        "part1_code": "1422929956",
        "part2_code": "1543288636",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 336,
        "name": "DIO",
        "part1_code": "1422929956",
        "part2_code": "1612325329",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 396,
        "name": "GU",
        "part1_code": "1422929956",
        "part2_code": "1728301104",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 397,
        "name": "PRA",
        "part1_code": "1422929956",
        "part2_code": "1728305074",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 398,
        "name": "YSL",
        "part1_code": "1422929956",
        "part2_code": "1728305100",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 399,
        "name": "CN",
        "part1_code": "1422929956",
        "part2_code": "1728305108",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 400,
        "name": "HER",
        "part1_code": "1422929956",
        "part2_code": "1728305117",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 401,
        "name": "BB",
        "part1_code": "1422929956",
        "part2_code": "1728305131",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 402,
        "name": "FEN",
        "part1_code": "1422929956",
        "part2_code": "1728305145",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 403,
        "name": "BALEN",
        "part1_code": "1422929956",
        "part2_code": "1728305146",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 404,
        "name": "BV",
        "part1_code": "1422929956",
        "part2_code": "1728305159",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 405,
        "name": "VT",
        "part1_code": "1422929956",
        "part2_code": "1728305168",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 406,
        "name": "CHL",
        "part1_code": "1422929956",
        "part2_code": "1728305176",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 407,
        "name": "GOY",
        "part1_code": "1422929956",
        "part2_code": "1728305185",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 408,
        "name": "LOE",
        "part1_code": "1422929956",
        "part2_code": "1728305194",
        "parent_name": "BAG"
    },
    {
        "part_index": 2,
        "idx": 409,
        "name": "ETC",
        "part1_code": "1422929956",
        "part2_code": "1728305201",
        "parent_name": "BAG"
    },
    {
        "part_index": 1,
        "idx": 328,
        "name": "SHOE",
        "part1_code": "1603683335",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 2,
        "idx": 331,
        "name": "CHA",
        "part1_code": "1603683335",
        "part2_code": "1603683415",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 329,
        "name": "LV",
        "part1_code": "1603683335",
        "part2_code": "1603683376",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 330,
        "name": "DIO",
        "part1_code": "1603683335",
        "part2_code": "1603683398",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 411,
        "name": "GU",
        "part1_code": "1603683335",
        "part2_code": "1728305417",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 412,
        "name": "PRA",
        "part1_code": "1603683335",
        "part2_code": "1728305427",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 413,
        "name": "YSL",
        "part1_code": "1603683335",
        "part2_code": "1728305435",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 414,
        "name": "CN",
        "part1_code": "1603683335",
        "part2_code": "1728305442",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 415,
        "name": "HER",
        "part1_code": "1603683335",
        "part2_code": "1728305450",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 416,
        "name": "BB",
        "part1_code": "1603683335",
        "part2_code": "1728305495",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 417,
        "name": "FEN",
        "part1_code": "1603683335",
        "part2_code": "1728305503",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 418,
        "name": "BALEN",
        "part1_code": "1603683335",
        "part2_code": "1728305510",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 419,
        "name": "BV",
        "part1_code": "1603683335",
        "part2_code": "1728305520",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 420,
        "name": "MQ",
        "part1_code": "1603683335",
        "part2_code": "1728305527",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 421,
        "name": "VT",
        "part1_code": "1603683335",
        "part2_code": "1728305533",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 422,
        "name": "CHL",
        "part1_code": "1603683335",
        "part2_code": "1728305540",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 423,
        "name": "RV",
        "part1_code": "1603683335",
        "part2_code": "1728305548",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 424,
        "name": "JC",
        "part1_code": "1603683335",
        "part2_code": "1728305554",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 425,
        "name": "LORO",
        "part1_code": "1603683335",
        "part2_code": "1728305564",
        "parent_name": "SHOE"
    },
    {
        "part_index": 2,
        "idx": 426,
        "name": "ETC",
        "part1_code": "1603683335",
        "part2_code": "1728305572",
        "parent_name": "SHOE"
    },
    {
        "part_index": 1,
        "idx": 34,
        "name": "WALLET",
        "part1_code": "1422930483",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 235,
        "name": "SPORT",
        "part1_code": "1565598696",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 33,
        "name": "FORMAN",
        "part1_code": "1422930473",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 2,
        "idx": 151,
        "name": "LV",
        "part1_code": "1422930473",
        "part2_code": "1538122065",
        "parent_name": "FORMAN"
    },
    {
        "part_index": 2,
        "idx": 152,
        "name": "GU",
        "part1_code": "1422930473",
        "part2_code": "1538122126",
        "parent_name": "FORMAN"
    },
    {
        "part_index": 2,
        "idx": 168,
        "name": "DIO",
        "part1_code": "1422930473",
        "part2_code": "1543288846",
        "parent_name": "FORMAN"
    },
    {
        "part_index": 2,
        "idx": 427,
        "name": "PRA",
        "part1_code": "1422930473",
        "part2_code": "1728305592",
        "parent_name": "FORMAN"
    },
    {
        "part_index": 2,
        "idx": 428,
        "name": "HER",
        "part1_code": "1422930473",
        "part2_code": "1728305601",
        "parent_name": "FORMAN"
    },
    {
        "part_index": 2,
        "idx": 429,
        "name": "BALEN",
        "part1_code": "1422930473",
        "part2_code": "1728305609",
        "parent_name": "FORMAN"
    },
    {
        "part_index": 2,
        "idx": 430,
        "name": "ETC",
        "part1_code": "1422930473",
        "part2_code": "1728305616",
        "parent_name": "FORMAN"
    },
    {
        "part_index": 1,
        "idx": 204,
        "name": "CLOTH",
        "part1_code": "1554563027",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 2,
        "idx": 206,
        "name": "OUTER",
        "part1_code": "1554563027",
        "part2_code": "1554563132",
        "parent_name": "CLOTH"
    },
    {
        "part_index": 2,
        "idx": 333,
        "name": "T-SHIRT",
        "part1_code": "1554563027",
        "part2_code": "1609148558",
        "parent_name": "CLOTH"
    },
    {
        "part_index": 2,
        "idx": 334,
        "name": "BOTTOM",
        "part1_code": "1554563027",
        "part2_code": "1609148566",
        "parent_name": "CLOTH"
    },
    {
        "part_index": 2,
        "idx": 335,
        "name": "SKIRT",
        "part1_code": "1554563027",
        "part2_code": "1609148654",
        "parent_name": "CLOTH"
    },
    {
        "part_index": 2,
        "idx": 431,
        "name": "DRESS",
        "part1_code": "1554563027",
        "part2_code": "1728305626",
        "parent_name": "CLOTH"
    },
    {
        "part_index": 2,
        "idx": 432,
        "name": "Unisex 남녀공용",
        "part1_code": "1554563027",
        "part2_code": "1728305635",
        "parent_name": "CLOTH"
    },
    {
        "part_index": 2,
        "idx": 433,
        "name": "FOR MAN",
        "part1_code": "1554563027",
        "part2_code": "1728305644",
        "parent_name": "CLOTH"
    },
    {
        "part_index": 1,
        "idx": 382,
        "name": "ACC",
        "part1_code": "1728121360",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 2,
        "idx": 383,
        "name": "모자/벨트/헤어밴드",
        "part1_code": "1728121360",
        "part2_code": "1728121372",
        "parent_name": "ACC"
    },
    {
        "part_index": 2,
        "idx": 384,
        "name": "귀걸이/목걸이/반지/시계",
        "part1_code": "1728121360",
        "part2_code": "1728121394",
        "parent_name": "ACC"
    },
    {
        "part_index": 2,
        "idx": 434,
        "name": "트윌리/스카프/머플러",
        "part1_code": "1728121360",
        "part2_code": "1728305700",
        "parent_name": "ACC"
    },
    {
        "part_index": 1,
        "idx": 385,
        "name": "홈인테리어",
        "part1_code": "1728121423",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 386,
        "name": "NO BRAND",
        "part1_code": "1728121435",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 2,
        "idx": 387,
        "name": "OUTER",
        "part1_code": "1728121435",
        "part2_code": "1728121465",
        "parent_name": "NO BRAND"
    },
    {
        "part_index": 2,
        "idx": 388,
        "name": "T-SHIRT",
        "part1_code": "1728121435",
        "part2_code": "1728121477",
        "parent_name": "NO BRAND"
    },
    {
        "part_index": 1,
        "idx": 203,
        "name": "개인결제",
        "part1_code": "1548154666",
        "part2_code": "",
        "parent_name": ""
    },
    {
        "part_index": 1,
        "idx": 437,
        "name": "메인섹션2",
        "part1_code": "1728306246",
        "part2_code": "",
        "parent_name": ""
    }
]