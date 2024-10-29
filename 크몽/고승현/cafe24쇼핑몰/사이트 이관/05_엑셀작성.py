import os
import re
import pandas as pd

# 1. 카테고리 정보를 담고 있는 리스트
category_obj = [
    {
        "part_index": 1,
        "idx": 393,
        "name": "TODAYS REVIEW",
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

# 2. 새로운 객체 클래스 정의
class Product:
    def __init__(self):
        self.카테고리이름 = ""
        self.대표_상품명 = ""
        self.이차상품명_또는_옵션명 = ""
        self.필수_또는_모델_또는_옵션 = ""
        self.상품가격 = 0
        self.옵션가격 = 0
        self.옵션항목명 = ""
        self.옵션값 = ""
        self.썸네일_이미지 = ""
        self.상품안내 = ""
        self.카테고리_코드 = ""
        self.상품_코드 = ""
        self.상품주요특징 = ""
        self.상품이미지_2 = ""
        self.상품이미지_3 = ""
        self.상품노출 = "Y"


def replace_image_paths(html_content):
    """HTML 콘텐츠에서 이미지 경로를 변경하는 함수"""
    # 정규 표현식 패턴: /web/upload/NNEditor/YYYYMMDD/filename.jpg
    pattern = r'/web/upload/NNEditor/\d{8}/([a-zA-Z0-9_.-]+\.jpg)'

    # 변환 함수 정의
    def replace_path(match):
        filename = match.group(1)  # 추출한 파일 이름
        return f'/upload/goods/{filename}'  # 새로운 경로 생성

    # 이미지 경로 변경
    modified_content = re.sub(pattern, replace_path, html_content)
    return modified_content

def read_xlsx_files(folder_path):
    result = []
    for file_name in os.listdir(folder_path):
        print(file_name)
        if file_name.endswith('.xlsx'):
            file_path = os.path.join(folder_path, file_name)
            try:
                # XLSX 파일 읽기, openpyxl 엔진 사용
                df = pd.read_excel(file_path, engine='openpyxl')
            except Exception as e:
                print(f"Error reading {file_name}: {e}")
                continue  # 파일을 읽지 못하면 다음 파일로 넘어감

            for index, row in df.iterrows():
                product = Product()
                # 5-8. 각 필드 설정
                product.대표_상품명 = row["상품명"]
                product.이차상품명_또는_옵션명 = row["상품명"]  # 2차 상품명에 상품명 넣기
                product.필수_또는_모델_또는_옵션 = row["상품명"]  # 필요시 업데이트
                product.상품가격 = float(row["판매가"])  # 판매가
                product.옵션가격 = 0  # 옵션가격 (없을 경우 0)

                # 7. 옵션입력 처리
                option_input = row.get("옵션입력", "")
                # option_input이 float일 경우 str로 변환
                if isinstance(option_input, float):
                    option_input = str(option_input)

                # 문자열에서 "//"가 있는지 확인
                if "//" in option_input:
                    option_input = option_input.split("//")[0]  # 첫 번째 옵션만 사용

                match = re.match(r"(\w+)\{(.*?)\}", option_input)
                if match:
                    product.옵션항목명 = match.group(1)
                    product.옵션값 = match.group(2).replace("|", "/")

                # 8. 썸네일 이미지
                thumbnail_image_path = row.get("이미지등록(목록)", "")
                if thumbnail_image_path:
                    # 슬래시로 분리하고 마지막 요소를 선택
                    product.썸네일_이미지 = thumbnail_image_path.split('/')[-1]  # 슬래시 뒤의 값만 가져오기
                else:
                    product.썸네일_이미지 = ""  # 값이 없으면 빈 문자열

                # 9. 상품안내
                html_content = row.get("상품 상세설명", "")
                # 이미지 경로 변경 실행
                modified_html_content = replace_image_paths(html_content)
                product.상품안내 = modified_html_content

                cleaned_name = re.sub(r'[\d_-]', '', file_name.split('.')[0])  # 숫자, _ 및 - 제거
                cleaned_name = cleaned_name.replace(" ", "")  # 띄어쓰기 한 칸 제거
                product.카테고리이름 = cleaned_name

                for category in category_obj:
                    # category['name']을 트리밍하고 부모 이름을 추가한 후 비교
                    full_name = (category['parent_name'] + category['name'].strip()).replace("/", "").replace("-", "").upper()  # / 제거 후 대문자로 변환
                    if full_name.replace(" ", "") == cleaned_name.upper():  # cleaned_name도 대문자로 변환
                        product.카테고리_코드 = category['part1_code'] if category['part2_code'] == "" else category['part2_code']
                        break

                # 11. 기본 항목 설정
                product.상품코드 = ""
                product.상품주요특징 = ""
                product.상품이미지_2 = ""
                product.상품이미지_3 = ""

                result.append(product)
    return result
def save_to_excel(products, output_file):
    # 제품 데이터를 DataFrame으로 변환
    data = [{
        "카테고리 이름": product.카테고리이름,
        "카테고리 코드": product.카테고리_코드,
        "상품 코드": product.상품_코드,
        "대표 상품명": product.대표_상품명,
        "상품주요특징": product.상품주요특징,
        "상품노출": product.상품노출,
        "필수or모델or옵션": product.필수_또는_모델_또는_옵션,
        "2차상품명 or 옵션명": product.이차상품명_또는_옵션명,
        "상품가격": product.상품가격,
        "옵션항목명": product.옵션항목명,
        "옵션값": product.옵션값,
        "옵션가격": product.옵션가격,
        "썸네일 이미지": product.썸네일_이미지,
        "상품 이미지[2]": product.상품이미지_2,
        "상품 이미지[3]": product.상품이미지_3,
        "상품안내\n(HTML 사용 가능)": product.상품안내,
    } for product in products]

    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)

def main():
    folder_path = os.path.join(os.getcwd(), "모든_xlsx파일_241028")  # 현재 실행 경로에 "모든_xlsx파일" 폴더
    products = read_xlsx_files(folder_path)

    # 결과를 Excel 파일로 저장
    output_file = os.path.join(os.getcwd(), "제품정보_241029.xlsx")  # 저장할 엑셀 파일 경로
    save_to_excel(products, output_file)

    print(f"Total products: {len(products)}")
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()