import requests

def post_request_to_eat_site():
    # 요청 URL
    url = "https://ns.eat.co.kr/nm/ep/600/selectBidDtl.do"

    # 요청 헤더 설정 (쿠키는 제외)
    headers = {
        "Accept": "application/xml, text/xml, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache, no-store",
        "Connection": "keep-alive",
        "Content-Type": "text/xml; charset=UTF-8",
        "Pragma": "no-cache",
        "Referer": "https://ns.eat.co.kr/NeaT/eats/index.html",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    # XML 형식의 페이로드
    payload = """<?xml version="1.0" encoding="UTF-8"?>
    <Root xmlns="http://www.nexacroplatform.com/platform/dataset">
        <Parameters>
            <Parameter id="_ga">GA1.1.1730932468.1730046336</Parameter>
            <Parameter id="SCOUTER">z676al29lef7np</Parameter>
            <Parameter id="ccsession">20241028012536c612230c023920dce9</Parameter>
            <Parameter id="ccguid">20241028012536c612230c023920dce9</Parameter>
            <Parameter id="_ga_3DNP79B50L">GS1.1.1730046335.1.1.1730046970.60.0.0</Parameter>
            <Parameter id="_ga_1C6GSRP5Z8">GS1.1.1730046336.1.1.1730046971.0.0.0</Parameter>
        </Parameters>
        <Dataset id="ds_searchParam">
            <ColumnInfo>
                <Column id="ELCTRN_BID_ID" type="STRING" size="256" />
                <Column id="ACT_TYPE" type="STRING" size="256" />
                <Column id="SUCBID_RSN" type="STRING" size="256" />
            </ColumnInfo>
            <Rows>
                <Row>
                    <Col id="ELCTRN_BID_ID">5492743</Col>
                </Row>
            </Rows>
        </Dataset>
        <Dataset id="_ds_tranInfo">
            <ColumnInfo>
                <Column id="STM_ID" type="STRING" size="255" />
                <Column id="MENU_ID" type="STRING" size="255" />
                <Column id="MENU_NO" type="STRING" size="255" />
                <Column id="PRGRM_ID" type="STRING" size="255" />
                <Column id="PRGRM_URL" type="STRING" size="255" />
                <Column id="POPUP_YN" type="STRING" size="255" />
                <Column id="OPERSYSM_NM" type="STRING" size="255" />
                <Column id="WBSR_VER_VL" type="STRING" size="255" />
                <Column id="LG_MNG_YN" type="STRING" size="255" />
                <Column id="NEXA_CNPT" type="STRING" size="255" />
            </ColumnInfo>
            <Rows>
                <Row>
                    <Col id="STM_ID">NEAT</Col>
                    <Col id="MENU_ID">80029</Col>
                    <Col id="MENU_NO">8061000</Col>
                    <Col id="PRGRM_ID">EPTM600M02</Col>
                    <Col id="POPUP_YN">N</Col>
                    <Col id="OPERSYSM_NM">Windows 10 64bit</Col>
                    <Col id="WBSR_VER_VL">Chrome 130.0.0.0</Col>
                    <Col id="NEXA_CNPT"></Col>
                </Row>
            </Rows>
        </Dataset>
    </Root>
    """

    # POST 요청 보내기
    response = requests.post(url, headers=headers, data=payload)

    # 응답 결과 반환
    return response

# 메인 함수
def main():
    response = post_request_to_eat_site()

    # 응답 결과 출력
    print("Status Code:", response.status_code)
    print("Response Headers:", response.headers)
    print("Response Body:", response.text)

# 메인 함수 실행
if __name__ == "__main__":
    for _ in range(1000):
        main()

