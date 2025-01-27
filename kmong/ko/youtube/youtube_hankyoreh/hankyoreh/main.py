import requests
import json
import openpyxl


def fetch_comments(repSeq):

    limit = 1000
    offset = 1
    consumerSeq = 587
    livereSeq = 14223

    url = f'https://api-zero.livere.com/v1/comments/list?limit={limit}&offset={offset}&repSeq={repSeq}&consumerSeq={consumerSeq}&livereSeq={livereSeq}'
    response = requests.get(url)

    # 응답에서 JSON 부분만 추출하기 위해 불필요한 부분 제거
    response_text = response.text
    json_data = json.loads(response_text)

    # 'content' 필드 추출
    comments = []
    for parent in json_data["results"]["parents"]:
        content = parent.get("content", "")
        comments.append(content)

    # 중복 제거
    comments = list(set(comments))

    return comments


# 엑셀에 저장하는 함수
def save_to_excel(comment_list):
    # 엑셀 워크북과 워크시트 생성
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Comments"

    # 헤더 추가
    ws.append(["No", "Date", "Name", "Title", "URL", "Content"])

    # 각 객체의 데이터를 엑셀에 추가
    for comment in comment_list:
        ws.append([comment['no'], comment['date'], comment['name'], comment['title'], comment['url'], comment['content']])

    # 엑셀 파일 저장
    wb.save("comments.xlsx")



def main():

    dates = [
        "2023-06-19 11:45",
        "2023-06-19 17:00",
        "2023-06-19 17:55",
        "2023-06-19 18:43",
        "2023-06-23 20:33",
        "2023-06-25 8:00",
        "2023-06-26 14:51",
        "2023-06-26 19:30",
        "2023-07-06 21:05",
        "2023-07-10 19:07",
        "2023-07-12 21:28",
        "2023-07-13 16:19",
        "2023-07-14 16:11",
        "2023-07-14 18:53",
        "2023-07-17 6:00",
        "2023-07-17 18:53",
        "2023-07-18 10:49",
        "2023-07-18 14:47",
        "2023-07-18 18:43",
        "2023-07-20 17:28",
        "2023-07-21 15:25",
        "2023-07-24 6:00",
        "2023-07-28 19:00",
        "2023-08-18 11:42",
        "2023-08-20 11:02",
        "2023-08-20 19:29",
        "2023-08-21 14:37",
        "2023-08-23 22:09",
        "2023-08-24 17:43",
        "2023-08-31 21:05",
        "2023-09-10 18:49",
        "2023-09-16 21:07",
        "2023-09-19 8:00",
        "2023-09-19 15:35",
        "2023-09-19 18:02",
        "2023-09-20 17:40",
        "2023-09-20 19:07",
        "2023-09-20 19:39",
        "2023-09-20 20:39",
        "2023-09-21 5:00",
        "2023-09-21 18:50",
        "2023-09-22 5:01",
        "2023-09-22 11:21",
        "2023-09-22 19:25",
        "2023-09-23 14:00",
        "2023-09-24 18:21",
        "2023-09-25 18:49",
        "2023-09-26 5:00",
        "2023-09-26 17:45",
        "2023-09-27 13:47",
        "2023-09-28 9:00",
        "2023-10-07 5:00",
        "2023-10-22 18:20",
        "2023-10-26 18:03"
    ]

    names = [
        "엄지원",
        "이우연",
        "엄지원",
        "[사설]",
        "임재우",
        "성한용",
        "강희철",
        "엄지원",
        "임재우",
        "임재우",
        "엄지원, 강재구",
        "이우연, 강재구, 임재우",
        "임재우",
        "사설",
        "엄지원",
        "엄지원",
        "임재우",
        "엄지원",
        "엄지원",
        "엄지원",
        "엄지원, 강재구",
        "임재우",
        "엄지원",
        "임재우",
        "서영지",
        "엄지원",
        "서영지",
        "임재우, 강재구",
        "강재구, 선담은",
        "사설",
        "엄지원, 이우연, 손현수",
        "서영지",
        "임재우, 이지혜",
        "신민정",
        "사설",
        "성한용",
        "이우연",
        "손현수",
        "임재우",
        "엄지원, 강재구",
        "사설",
        "엄지원, 강재구",
        "엄지원",
        "사설",
        "하어영",
        "사설",
        "이주현",
        "엄지원",
        "전광준",
        "성한용",
        "박용현",
        "엄지원",
        "사설",
        "엄지원, 고한솔"
    ]

    titles = [
        "이재명 “불체포 권리 포기…제 발로 출석, 검찰 무도함 입증”",
        "체포동의안 부결 넉 달 만에…이재명 ‘불체포 특권’ 포기, 왜",
        "이재명, 예정 없던 불체포특권 포기…‘방탄 프레임’ 역공 승부수?",
        "“민주당 모든 걸 바꾸겠다”는 이재명 대표, 약속 실천해야",
        "민주당 혁신위 “당내 의원 전원 불체포특권 포기 서약을”",
        "‘불체포특권 포기’는 반정치 포퓰리즘…방탄 국회를 포기해야",
        "[유레카] 선언만으론 실효성 없는 ‘불체포특권’ 포기",
        "민주 지도부 “방탄용 임시국회 열지 않겠다”…혁신위 제안 수용",
        "“오합지졸, 콩가루”…민주 혁신위, 김영주·송영길 거론 강공",
        "김은경 혁신위원장 “소신 갖고 쇄신하겠다”…당 원로 “사즉생 각오로”",
        "민주 혁신위 “불체포특권 포기 안 하면 당 망한다”",
        "김은경 혁신위 첫 과제 ‘불체포특권 포기’, 의총서 추인 불발",
        "“불체포특권 먼저 포기하겠다”…비이재명계 31명 입장 발표",
        "[사설] ‘불체포특권’ 포기 거부한 민주당, 혁신위 왜 만들었나 돌아보라",
        "비명계, 불체포특권 포기 앞장…당 차원 결의 탄력받을까",
        "김은경 “자기 계파 살리기” 저격에 친이낙연계 “반드시 사과하라”",
        "김은경 “이재명·이낙연, 깨복쟁이 친구처럼 어깨동무해달라”",
        "민주당, 의총서 ‘불체포특권 포기’ 결의…불발 닷새 만에",
        "민주, 불체포 특권 포기 결의…‘정당한 영장’ 전제로 논란 불씨",
        "이재명 ‘사법리스크’ 2차전…8월 영장설에 뒤숭숭한 민주",
        "민주당 혁신위, 체포동의안 실명 투표 제안…‘제 식구 감싸기’ 방지",
        "민주당 ‘서울 지지율’ 추락 가속…“2030 무당층 이탈 많아져”",
        "이재명 구속영장 8월? 9월?…검찰과 민주당 계산법은",
        "정성호 “이재명 대표 구속된다더라도 사퇴하면 더 큰 혼란”",
        "김기현 “이재명, 영장심사를 백화점 쇼핑하듯… 특권의식”",
        "검찰 ‘9월 영장설’ 가시화…이재명 ‘불체포특권 난제’ 풀어낼까",
        "한동훈 “민주당, 불체포특권 포기하기 싫으면 그냥 하지 마라”",
        "“방탄 프레임 유도하나”…민주당-검찰, 이재명 소환일 신경전",
        "민주당 ‘이재명 영장’ 받을 결심?…8월 임시회 25일까지로 단축",
        "[사설] 제1 야당 대표 ‘무기한 단식’ 선언, 여야 정치 복구하라",
        "이재명 두 번째 구속영장 초읽기…체포안 처리에 ‘단식 변수’",
        "국힘, ‘내각 총사퇴’ 민주 요구에 “공당이길 포기한 것”",
        "부결 땐 방탄, 가결 땐 내분…민주 ‘이재명 체포동의안’ 다시 시험대",
        "“단식 핑계로 도망가지 말라”…국힘, 이재명 체포동의안 압박",
        "[사설] 민주당, ‘불체포 특권 포기’ 대국민 약속 지키길",
        "[성한용 칼럼] 국회의 판단을 존중해야 한다",
        "이재명, 국회 표결 하루 전 체포안 ‘부결’ 호소…단식 취지 ‘퇴색’",
        "국힘, 이재명 체포안 부결 요청에 “대국민 약속 헌신짝” 맹비난",
        "‘국회 비회기 기간’ 불체포특권 포기? 석 달 전 약속 ‘뒤집기 재해석’",
        "이재명 부결 지침 ‘중간지대’ 흔들까…체포안 오늘 표결",
        "[사설] 이재명 대표 영장심사 당당히 임하고, 당 분열 막아야",
        "민주당 내홍 격화…친명 “이탈표로 당 최대 위기” 비명 “사태 책임”",
        "이원욱 “박광온이 옴팡 뒤집어 써…최고위원 총사퇴해야”",
        "[사설] 민주당, ‘상응 조처’로는 당이 수습될 수 없다",
        "이재명 ‘단식 카드’ 왜 안 먹혔을까 [The 5]",
        "[사설] ‘24일 단식’ 끝낸 이재명 대표가 마주한 과제들",
        "이재명의 목표가 친명체제였을까?",
        "민주 ‘가결파’가 “체포안 부결시켜야” 입장문 준비했던 까닭은?",
        "이재명 노린 검찰 ‘기우제 수사’…“727일 조사, 376회 압수수색”",
        "‘검찰정치’ 이제 대가를 치를 시간…이재명 영장 기각 이후",
        "파탄 난 검찰의 ‘정치수사’…“한동훈 파면” 주장 분출 [논썰]",
        "통합이냐, 청산이냐…이재명 침묵의 의미는? [다음주의 질문]",
        "당무 복귀 이재명 대표, ‘통합’ 실천하라는 게 민심 [사설]",
        "이재명 “분열 필패, 단결 필승”…비명계 “좌표찍기 왜 놔두나”"
    ]

    urls = [
        "https://www.hani.co.kr/arti/politics/assembly/1096523.html",
        "https://www.hani.co.kr/arti/politics/assembly/1096593.html",
        "https://www.hani.co.kr/arti/politics/assembly/1096613.html",
        "https://www.hani.co.kr/arti/opinion/editorial/1096620.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1097283.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1097325.html",
        "https://www.hani.co.kr/arti/opinion/column/1097495.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1097597.html",
        "https://www.hani.co.kr/arti/politics/assembly/1099106.html",
        "https://www.hani.co.kr/arti/politics/assembly/1099531.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1099888.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1099989.html",
        "https://www.hani.co.kr/arti/politics/assembly/1100175.html",
        "https://www.hani.co.kr/arti/opinion/editorial/1100209.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1100390.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1100547.html",
        "https://www.hani.co.kr/arti/politics/assembly/1100607.html",
        "https://www.hani.co.kr/arti/politics/assembly/1100648.html",
        "https://www.hani.co.kr/arti/politics/assembly/1100729.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1101048.html",
        "https://www.hani.co.kr/arti/politics/assembly/1101190.html",
        "https://www.hani.co.kr/arti/politics/assembly/1101390.html",
        "https://www.hani.co.kr/arti/politics/assembly/1102179.html",
        "https://www.hani.co.kr/arti/politics/assembly/1104817.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1104958.html",
        "https://www.hani.co.kr/arti/politics/assembly/1105034.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1105116.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1105558.html",
        "https://www.hani.co.kr/arti/politics/assembly/1105687.html",
        "https://www.hani.co.kr/arti/opinion/editorial/1106663.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1107901.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1108818.html",
        "https://www.hani.co.kr/arti/politics/assembly/1109101.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1109171.html",
        "https://www.hani.co.kr/arti/opinion/editorial/1109221.html",
        "https://www.hani.co.kr/arti/opinion/column/1109368.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1109403.html",
        "https://www.hani.co.kr/arti/politics/assembly/1109416.html",
        "https://www.hani.co.kr/arti/politics/assembly/1109422.html",
        "https://www.hani.co.kr/arti/politics/assembly/1109429.html",
        "https://www.hani.co.kr/arti/opinion/editorial/1109579.html",
        "https://www.hani.co.kr/arti/politics/assembly/1109625.html",
        "https://www.hani.co.kr/arti/politics/assembly/1109665.html",
        "https://www.hani.co.kr/arti/opinion/editorial/1109739.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1109770.html",
        "https://www.hani.co.kr/arti/opinion/editorial/1109864.html",
        "https://www.hani.co.kr/arti/opinion/column/1110058.html",
        "https://www.hani.co.kr/arti/politics/assembly/1110073.html",
        "https://www.hani.co.kr/arti/society/society_general/1110219.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1110327.html",
        "https://www.hani.co.kr/arti/society/society_general/1110421.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1111184.html",
        "https://www.hani.co.kr/arti/opinion/editorial/1113118.html",
        "https://www.hani.co.kr/arti/politics/politics_general/1113808.html"
    ]

    repSeqs = [
                '6926199', '6926781', '6926822', '6926888', '6932781', '6933891', '6935977', '6935794', '6949221', '6953917',
                '6956922', '6958094', '6959658', '6960072', '6961847', '6962596', '6963261', '6963485', '6963733', '6966281',
                '6967589', '6970092', '6977383', '6999012', '7000563', '7000911', '7001653', '7004945', '7006207', '7014710',
                '7025945', '7033371', '7035981', '7036606', '7036753', '7038144', '7038065', '7038075', '7038172', '7038454',
                '7039638', '7040056', '7040389', '7040977', '7041626', '7042516', '7043535', '7043888', '7044809', '7045704',
                '7046392', '7053399', '7068466', '7073176'
            ]

    comment_list = []

    # 각 repSeq에 대해 댓글을 가져오고 데이터를 추가합니다
    for index, repSeq in enumerate(repSeqs):
        print(f'index : {index}')
        comments = fetch_comments(repSeq)
        for comment in comments:
            # 각 댓글에 대해 객체를 생성하여 리스트에 추가
            comment_data = {
                'no': index + 1,
                'date': dates[index],
                'name': names[index],
                'title': titles[index],
                'url': urls[index],
                'content': comment,
            }
            comment_list.append(comment_data)


    # 객체 리스트를 엑셀로 저장
    save_to_excel(comment_list)

if __name__ == "__main__":
    main()
