# file: send_ansim_cdr_mock.py
import os
import uuid
import random
from datetime import datetime, timedelta
import requests
from typing import Dict, Any, List

# ─────────────────────────────────────────────────────────────
# 환경설정 (필요에 맞게 수정)
# ─────────────────────────────────────────────────────────────
# ANSIM_ENDPOINT = os.getenv("ANSIM_ENDPOINT", "http://localhost:80/api/ansim/cdr")  # 배포 포트 맞게 변경
ANSIM_ENDPOINT = os.getenv("ANSIM_ENDPOINT", "https://healmecare.com/api/ansim/cdr")  # 배포 포트 맞게 변경
ANSIM_AUTH_KEY = os.getenv("ANSIM_AUTH_KEY", "Gr1yIZLwoC7lacQ1cr8JOhRB7")                     # 운영실 등록 키와 동일해야 함
VERIFY_TLS = os.getenv("VERIFY_TLS", "true").lower() == "true"                    # https 자가서명 테스트 시 false

# ─────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────
def fmt_ts(dt: datetime) -> str:
    """YYYYMMDDHHMMSS 포맷"""
    return dt.strftime("%Y%m%d%H%M%S")

def make_mock_payload(
        caller_no: str = "01011112222",
        called_no: str = "01033334444",
        vrno: str = "050123456789",
        call_result: str = None,         # None이면 랜덤
        release_reason: str = None       # None이면 랜덤
) -> Dict[str, Any]:
    """
    벤더 스펙의 snake_case JSON 생성
    - call_result: "00"(성공) or 실패코드(예: "11")
    - release_reason: "00"(정상), "1"(무응답), "2"(결번), "3"(호포기) 등
    """
    now = datetime.now()
    start = now - timedelta(seconds=random.randint(30, 300))
    duration = random.randint(10, 180)

    if call_result is None:
        call_result = random.choice(["00", "11"])  # 00: 성공, 11: 실패(샘플)
    if release_reason is None:
        release_reason = "00" if call_result == "00" else random.choice(["1", "2", "3"])

    end = start + timedelta(seconds=duration)

    callid = uuid.uuid4().hex[:16].upper()  # PK로 사용할 샘플 ID
    recfilename = None
    if call_result == "00":
        # 성공 시에만 녹취 파일명이 오는 케이스가 많아 샘플로 넣음
        recfilename = f"{fmt_ts(start)}_{caller_no}_{vrno}_{called_no}.mp3"

    payload = {
        "callid": callid,
        "caller_no": caller_no,
        "called_no": called_no,
        "vrno": vrno,
        "call_result": call_result,
        "release_reason": release_reason,
        "call_start": fmt_ts(start),
        "call_end": fmt_ts(end),
        "duration": str(duration),     # 문자열로 전송
        "recfilename": recfilename,    # 없으면 None 전달 가능
        "cpid": "0002"                 # 필요시 변경
        # create_dt는 서버에서 세팅하도록 비움(서버 서비스 로직에 따라 다름)
    }
    return payload

def post_cdr(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "Authorization": ANSIM_AUTH_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    resp = requests.post(ANSIM_ENDPOINT, json=payload, headers=headers, verify=VERIFY_TLS, timeout=5)
    # 200/401/500 등 상태코드와 본문 확인
    return {
        "status_code": resp.status_code,
        "response_json": safe_json(resp),
        "sent_payload": payload
    }

def safe_json(resp) -> Any:
    try:
        return resp.json()
    except Exception:
        return resp.text

# ─────────────────────────────────────────────────────────────
# 메인: 여러 건 전송 테스트
# ─────────────────────────────────────────────────────────────
def send_batch(n: int = 3) -> List[Dict[str, Any]]:
    results = []
    for _ in range(n):
        payload = make_mock_payload()
        result = post_cdr(payload)
        print(f"[POST] status={result['status_code']} callid={payload['callid']}")
        print("  response:", result["response_json"])
        results.append(result)
    return results

if __name__ == "__main__":
    print("ANSIM_ENDPOINT:", ANSIM_ENDPOINT)
    print("VERIFY_TLS:", VERIFY_TLS)
    print("---- sending mock CDRs ----")
    send_batch(3)
