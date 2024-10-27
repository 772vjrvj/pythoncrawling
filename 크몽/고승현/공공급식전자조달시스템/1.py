import requests

def post_request_to_eat_site():
    # 요청 URL
    url = "https://ns.eat.co.kr/nm/ep/600/selectTmBidMBidPbancList.do"

    # 요청 헤더 설정 (쿠키 제외)
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
        <Dataset id="ds_searchParam">
            <ColumnInfo>
                <Column id="P_BID_NM" type="STRING" size="256" />
                <Column id="P_ELCTRN_BID_NO" type="STRING" size="256" />
                <Column id="P_BID_BGNG_DT" type="STRING" size="256" />
                <Column id="P_BID_END_DT" type="STRING" size="256" />
                <Column id="P_PRGRS_STAT_CD" type="STRING" size="256" />
                <Column id="P_INST_NM" type="STRING" size="256" />
                <Column id="P_CTPV_CD" type="STRING" size="256" />
                <Column id="P_SGG_CD" type="STRING" size="256" />
                <Column id="P_SRTNG_SEQN" type="STRING" size="256" />
                <Column id="P_DNTT_CNPT_CD" type="STRING" size="256" />
                <Column id="P_INST_GB_CD" type="STRING" size="256" />
                <Column id="EXCEL_GB_CD" type="STRING" size="256" />
                <Column id="JSP_YN" type="STRING" size="256" />
            </ColumnInfo>
            <Rows>
                <Row>
                    <Col id="P_BID_NM">공산</Col>
                    <Col id="P_BID_BGNG_DT">20241021</Col>
                    <Col id="P_BID_END_DT">20241028</Col>
                    <Col id="P_PRGRS_STAT_CD">007</Col>
                    <Col id="P_INST_NM">공업고등학교</Col>
                    <Col id="P_CTPV_CD" />
                    <Col id="P_SGG_CD" />
                </Row>
            </Rows>
        </Dataset>
        <Dataset id="_ds_pagingInfo">
            <ColumnInfo>
                <Column id="START_PAGE" type="STRING" size="255" />
                <Column id="PAGE_SIZE" type="STRING" size="255" />
            </ColumnInfo>
            <Rows>
                <Row>
                    <Col id="START_PAGE">1</Col>
                    <Col id="PAGE_SIZE">20</Col>
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
    for _ in range(1):
        main()
