from bs4 import BeautifulSoup
import json

def parse_html_file(filename):
    # HTML 파일 읽기
    with open(filename, "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content

def extract_part_edit_objects(html_content):
    # HTML 파싱
    soup = BeautifulSoup(html_content, 'html.parser')

    # 객체 배열 초기화
    results = []

    # 모든 <a> 태그를 탐색하여 'javascript:partEdit' 패턴 확인
    for tag in soup.find_all('a', href=True):
        href_value = tag['href']
        if "javascript:partEdit" in href_value:
            # 함수 호출에서 인수 추출
            parts = href_value.replace("javascript:partEdit(", "").replace(");", "").split(",")
            part_index = parts[0].strip()
            idx = parts[1].strip().strip("'")

            # 객체 생성 및 배열에 추가
            obj = {"part_index": int(part_index), "idx": int(idx)}
            results.append(obj)

    return results

def main():
    # HTML 파일 경로
    filename = "cafe24_category.html"

    # HTML 파일 파싱 및 데이터 추출
    html_content = parse_html_file(filename)
    results = extract_part_edit_objects(html_content)

    # 총 객체 수 및 결과 출력
    print(f"총 객체 수: {len(results)}")
    print(json.dumps(results, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()

# 카테고리 상세보기를 위한 번호

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
