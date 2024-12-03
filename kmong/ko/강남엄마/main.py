import requests
import time
import random
import pandas as pd

def grade_to_str(grades):
    grade_mapping = {
        1: "미취학 0세",
        2: "미취학 1세",
        3: "미취학 2세",
        4: "미취학 3세",
        5: "미취학 4세",
        6: "미취학 5세",
        7: "미취학 6세",
        8: "초등학교 1학년",
        9: "초등학교 2학년",
        10: "초등학교 3학년",
        11: "초등학교 4학년",
        12: "초등학교 5학년",
        13: "초등학교 6학년",
        14: "중학교 1학년",
        15: "중학교 2학년",
        16: "중학교 3학년",
        17: "고등학교 1학년",
        18: "고등학교 2학년",
        19: "고등학교 3학년",
        20: "재수/N수"
    }

    if not grades:
        return ""

    grades.sort()
    ranges = {"미취학": [], "초등학교": [], "중학교": [], "고등학교": [], "재수/N수": []}

    for grade in grades:
        if grade in range(1, 8):
            ranges["미취학"].append(grade)
        elif grade in range(8, 14):
            ranges["초등학교"].append(grade)
        elif grade in range(14, 17):
            ranges["중학교"].append(grade)
        elif grade in range(17, 20):
            ranges["고등학교"].append(grade)
        elif grade == 20:
            ranges["재수/N수"].append(grade)

    result = []
    for key in ranges:
        if ranges[key]:
            start = ranges[key][0]
            end = ranges[key][-1]
            if start == end:
                result.append(grade_mapping[start])
            else:
                result.append(f"{grade_mapping[start]} ~ {grade_mapping[end]}")

    return ", ".join(result)

def subjects_to_str(subjects):
    subject_mapping = {
        1: "국어",
        2: "영어",
        3: "수학",
        4: "과학",
        5: "사회",
        6: "독서/토론/논술",
        7: "영재교육원/경시대회",
        8: "컨설팅",
        9: "SW교육/코딩교육",
        10: "유학/SAT/AP/토플",
        11: "제2외국어",
        12: "음악",
        13: "미술",
        14: "체육",
        15: "취업/자격증",
        16: "기타"
    }

    sorted_subjects = sorted(subjects)
    return ", ".join([subject_mapping[sub] for sub in sorted_subjects if sub in subject_mapping])

def fetch_academy_data(offset, limit):
    url = f"https://api.gangmom.kr/user/academies?offset={offset}&limit={limit}&type=infinite"
    response = requests.get(url)
    return response.json()

def main(total_records=1000, limit=200):
    data_list = []
    offsets = [i for i in range(0, total_records, limit)]

    for offset in offsets:
        data = fetch_academy_data(offset, limit)
        for academy in data['academies']:
            fullName = academy.get('fullName', '')
            logo_location = academy.get('logo', {}).get('location', '')
            roadAddress = academy.get('address', {}).get('roadAddress', '')
            jibunAddress = academy.get('address', {}).get('jibunAddress', '')
            detailAddress = academy.get('address', {}).get('detailAddress', '')
            callNumber = academy.get('callNumber', '')
            grade = grade_to_str(academy.get('grade', []))
            subject = subjects_to_str(academy.get('subject', []))
            url = academy.get('url', '')

            data = {
                '학원명': fullName,
                '사진': logo_location,
                '도로명 주소': roadAddress,
                '지번 주소': jibunAddress,
                '상세주소': detailAddress,
                '전화': callNumber,
                '수강대상(학년)': grade,
                '과목': subject,
                'url': url
            }

            print(f"data {data}")

            data_list.append(data)

        time.sleep(random.uniform(3, 6))

    df = pd.DataFrame(data_list)
    df.to_excel('academies.xlsx', index=False)

if __name__ == "__main__":
    main(total_records=1000, limit=200)
