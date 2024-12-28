import json
import logging
import os
from datetime import datetime
from urllib.request import urlretrieve
from tqdm import tqdm

import pandas as pd

def setup_logging(log_level=logging.INFO):
    """
    로깅을 설정하는 함수

    :param log_level: 로그 레벨 (기본값 INFO)
    """
    # 로그 포맷 정의
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 로깅 설정 (콘솔에만 로그 출력)
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler()  # 콘솔에만 로그 출력
        ]
    )


# 이미지 다운로드 함수
def download_images(attach_urls, attach_names, writer_id, page):
    # 최상위 폴더 'reviews_image'가 없다면 생성
    root_folder = 'reviews_image'
    if not os.path.exists(root_folder):
        os.makedirs(root_folder)

    # 'page_{page}' 폴더가 없다면 생성
    page_folder = os.path.join(root_folder, f'page_{page}')
    if not os.path.exists(page_folder):
        os.makedirs(page_folder)

    # writer_id에서 '*' 문자를 '★'로 변경
    safe_writer_id = writer_id.replace('*', '★')

    # safe_writer_id에 해당하는 폴더가 없다면 생성
    writer_folder = os.path.join(page_folder, safe_writer_id)
    if not os.path.exists(writer_folder):
        os.makedirs(writer_folder)

    image_files = []

    for i, (url, name) in enumerate(zip(attach_urls[:9], attach_names[:9])):  # 최대 9개까지 다운로드
        image_path = os.path.join(writer_folder, name)  # attach_name을 파일 이름으로 사용

        # 파일 이름 중복 체크 및 처리
        base_name, extension = os.path.splitext(name)
        counter = 1

        # 중복 파일이 있는지 확인하고, 있으면 숫자를 추가
        while os.path.exists(image_path):
            # 새로운 이름을 만들어서 이미지 경로를 업데이트
            image_path = os.path.join(writer_folder, f"{base_name}_{counter}{extension}")
            counter += 1

        # 이미지 다운로드
        urlretrieve(url, image_path)
        image_files.append(image_path)

    return image_files


def parse_datetime(date_str):
    try:
        # createDate가 빈 문자열이 아니고, 형식이 맞을 경우 datetime으로 변환
        if date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f+00:00").strftime("%Y-%m-%d %H:%M:%S")
        else:
            return ''  # 빈 문자열일 경우 빈 문자열 반환
    except ValueError:
        # ValueError 발생 시 잘못된 날짜 형식인 경우
        logging.error(f"Invalid date format: {date_str}")
        return ''  # 오류 발생 시 빈 문자열 반환


# 리뷰 데이터를 처리하고 Excel로 출력하는 함수
def process_reviews():
    result_data = []

    # json_data 폴더 경로
    folder_path = 'json_data'

    # for i in range(1, 49):
    for i in tqdm(range(1, 49), desc="파일 처리 중", unit="file"):  # tqdm을 사용하여 진행 표시


        logging.info(f'\n')
        logging.info(f'시작 {i} ==========')

        file_path = os.path.join(folder_path, f'json_data_{i}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as json_file:
                # JSON 데이터 읽기
                reviews = json.load(json_file)

                if reviews and 'contents' in reviews:

                    # for index, review in enumerate(reviews['contents'], start=1):
                    for index, review in enumerate(tqdm(reviews['contents'], desc=f"파일 {i} 리뷰 처리 중", leave=False), start=1):

                        review_data = {
                            '내용': review.get('reviewContent', ''),
                            '작성자': review.get('writerId', ''),
                            '작성시각': parse_datetime(review.get('createDate', '')),
                            '평점': review.get('reviewScore', ''),
                            '첨부파일': '',
                            '옵션': review.get('productOptionContent', ''),
                            '현재 순서': index,
                            '현재 페이지': reviews.get('page', ''),
                            '전체 페이지 수': reviews.get('totalPages', ''),
                            '전체 글 수': reviews.get('totalElements', '')
                        }
                        # reviewAttaches 처리
                        attach_urls = []
                        attach_names = []
                        if 'reviewAttaches' in review:
                            for attach in review['reviewAttaches']:
                                attach_url = attach.get('attachUrl')  # attachUrl이 없으면 None이 반환
                                attach_name = os.path.basename(attach_url)

                                if attach_url and attach_name:  # attachUrl과 attachName이 모두 있을 경우에만 추가
                                    attach_urls.append(attach_url)
                                    attach_names.append(attach_name)

                            if attach_urls and attach_names:
                                # 최대 9개까지 이미지 다운로드 및 이름 저장
                                image_files = download_images(attach_urls, attach_names, review_data['작성자'], reviews.get('page', ''))
                                logging.info(f'image_files : {image_files}')
                                review_data['첨부파일'] = ",".join(attach_names[:9])  # 최대 9개까지 결합

                        logging.info(f'현재 순서 : {index}, index: {i}, page: {reviews.get("page", "")}, review_data : {review_data}')

                        result_data.append(review_data)

                logging.info(f'끝 {i} ==========')


    # 결과를 DataFrame으로 변환 후 Excel로 저장
    df = pd.DataFrame(result_data)
    df.to_excel("reviews_result.xlsx", index=False)


# 메인 함수 실행
if __name__ == "__main__":

    # 설정 함수 호출
    setup_logging(log_level=logging.INFO)
    process_reviews()
