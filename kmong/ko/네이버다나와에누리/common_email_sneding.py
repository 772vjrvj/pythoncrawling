import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

email_list = []

def create_email_table(email_list):

    table_rows = ""

    for row in email_list:
        table_rows += f"""
        <tr style="border: 1px solid #dddddd; text-align: left; padding: 12px;">
            <td style="border: 1px solid #dddddd; padding: 12px;">{row['excel_row']}</td>
            <td style="border: 1px solid #dddddd; padding: 12px;">{row['product_name']}</td>
            <td style="border: 1px solid #dddddd; padding: 12px;"><a href=\"{row['naver_url']}\" target=\"_blank\">{row['naver_url']}</a></td>
            <td style="border: 1px solid #dddddd; padding: 12px;">{row['product_key']}</td>
            <td style="border: 1px solid #dddddd; padding: 12px;">{row['memo']}</td>
            <td style="border: 1px solid #dddddd; padding: 12px;">{row['seller_key']}</td>
            <td style="border: 1px solid #dddddd; padding: 12px;">{row['net_profit_rate']}%</td>
            <td style="border: 1px solid #dddddd; padding: 12px;"><a href=\"{row['email_url']}\" target=\"_blank\">{row['email_url']}</a></td>
        </tr>
        """

    email_content = f"""
    <html>
    <body>
        <p>안녕하세요, 상품 정보입니다:)</p>
        <br>
        <br>
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 16px; font-family: Arial, sans-serif; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);">
            <tr style="border: 1px solid #dddddd; background-color: #f4f4f4; font-weight: bold;">
                <th style="border: 1px solid #dddddd; padding: 12px;">엑셀 번호</th>
                <th style="border: 1px solid #dddddd; padding: 12px;">상품명</th>
                <th style="border: 1px solid #dddddd; padding: 12px;">네이버 URL</th>
                <th style="border: 1px solid #dddddd; padding: 12px;">상품 키</th>
                <th style="border: 1px solid #dddddd; padding: 12px;">메모</th>
                <th style="border: 1px solid #dddddd; padding: 12px;">판매처</th>
                <th style="border: 1px solid #dddddd; padding: 12px;">마진율</th>
                <th style="border: 1px solid #dddddd; padding: 12px;">URL</th>
            </tr>
            {table_rows}
        </table>
    </body>
    </html>
    """
    return email_content


# 이메일 발송 함수
def send_email(email_data):
    global email_list
    for recip_email in email_data['수신자이메일']:
        sender_email = email_data['발신자이메일']
        sender_password = email_data['발신자비밀번호']
        recipient_email = recip_email
        subject = email_data['제목']

        body = create_email_table(email_list)

        send_naver_email(sender_email, sender_password, recipient_email, subject, body, attachment_path=None)
        time.sleep(1)


# 네이버 이메일 발송
def send_naver_email(sender_email, sender_password, recipient_email, subject, body, attachment_path=None):
    try:
        # SMTP 서버 설정 (네이버)
        smtp_server = "smtp.naver.com"
        smtp_port = 587

        # 이메일 메시지 생성
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject

        # 본문 추가
        message.attach(MIMEText(body, "html"))

        # 첨부 파일 추가 (옵션)
        if attachment_path:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment_path.split('/')[-1]}",
                )
                message.attach(part)

        # SMTP 서버에 연결
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # TLS 보안 활성화
        server.login(sender_email, sender_password)  # 로그인

        # 이메일 전송
        server.sendmail(sender_email, recipient_email, message.as_string())
        print("이메일이 성공적으로 전송되었습니다.")

        # 서버 종료
        server.quit()

    except Exception as e:
        print(f"이메일 전송 중 오류 발생: {e}")


# 메인 함수
def main(email_data):
    global email_list

    obj1 = {
        'excel_row': 'excel_row1',
        'product_name': 'product_name1',
        'naver_url': 'https://www.naver.com',
        'product_key': 'product_key1',
        'memo': 'memo1',
        'seller_key': 'seller_key1',
        'net_profit_rate': 'net_profit_rate1',
        'email_url': 'https://www.naver.com'
    }

    obj2 = {
        'excel_row': 'excel_row2',
        'product_name': 'product_name2',
        'naver_url': 'https://www.naver.com',
        'product_key': 'product_key2',
        'memo': 'memo2',
        'seller_key': 'seller_key2',
        'net_profit_rate': 'net_profit_rate2',
        'email_url': 'https://www.naver.com'
    }

    email_list.append(obj1)
    email_list.append(obj2)

    send_email(email_data)

if __name__ == "__main__":

    # 이메일 설정
    email_data = {
        '전송기준수': 1,     #(단위 개 매진률수 이상이 되면 메일 발송)
        '발신자이메일': '772vjrvj@naver.com',
        '발신자비밀번호': 'Ksh#8818510',
        '수신자이메일': ['772vjrvj@naver.com'],
        '제목': '특정 마진률 이상이면 메일 전송',
        '내용': '', # 엑셀행/ 상품명 / 네or다or에-N개-판매처 / 마진% / URL(네or다or에) 이 형식으로 바뀔것임 초기값은 공백
    }

    # 메인실행 함수
    main(email_data)

