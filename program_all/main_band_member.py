import re
import requests
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List


URL = "https://api-kr.band.us/v2.0.0/get_members_of_band"


# 밴드명, md, akey, cookie, referer, PARAMS 만 수정하기
PARAMS = {
    "ts": "1770969310812",
    "band_no": "61514880",
}
BAND_NAME = "(주)유니온소프트"
HEADERS = {
    "Host": "api-kr.band.us",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "akey": "bbc59b0b5f7a1c6efe950f6236ccda35",
    "cache-control": "no-cache",
    "cookie": """BBC=88476de1-8bb5-4d7e-841c-a046bbf0a3a6; language=ko; di=web-AAAAABsRBYB2pOE7PztAZxRHyAgW6T0TBeh2X0vobKm-I_M-4QxfCwS9BpSl7W6M4l5E54; band_session=ZQIAAIZwIJrRV8Qg4-gnIbpnORLbJH19rhFw8-8KG5paf-3UX2M1WVZ7rWo8IhHJYTud0kR6OCXrjh-RDUaXv5zcfz4i4PJPJCuEtV62kBDQBy1j; as="50342e54:R+vfdrq62YFK5c8LKJbPFe9mhGlNkK8AXq9xjfuqtN8="; ai="4813b5c,19c60399154""",
    "device-time-zone-id": "Asia/Seoul",
    "device-time-zone-ms-offset": "32400000",
    "language": "ko",
    "md": "2G30slx+dQL26/LX1fv0QLZLZH5tQykiCMuG8b2fTnU=",
    "origin": "https://www.band.us",
    "pragma": "no-cache",
    "referer": "https://www.band.us/band/61514880/member",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0",
}


# =========================================================
# phone extract
# =========================================================

_SEP = r"[^\d]*"

_RE_MOBILE = re.compile(rf"(01[016789]){_SEP}(\d{{3,4}}){_SEP}(\d{{3,4}})")
_RE_070 = re.compile(rf"(070){_SEP}(\d{{3,4}}){_SEP}(\d{{4}})")
_RE_AREA = re.compile(rf"(0(?:2|[3-6]\d))" + _SEP + r"(\d{3,4})" + _SEP + r"(\d{4})")
_RE_SPECIAL = re.compile(rf"(1\d{{3}}){_SEP}(\d{{4}})")
_RE_LOCAL = re.compile(r"(?<!\d)(\d{3,4})" + _SEP + r"(\d{4})(?!\d)")


def _clean_text_for_scan(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u00A0", " ")
    s = re.sub(r"[()]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _fmt_mobile(a: str, b: str, c: str) -> str:
    if len(c) == 3:
        c = "0" + c
    return f"{a}-{b}-{c}"


def extract_phones(name: str, desc: str) -> List[str]:

    hay = _clean_text_for_scan(f"{name or ''} {desc or ''}")
    if not hay:
        return []

    found = []

    for m in _RE_MOBILE.finditer(hay):
        found.append(_fmt_mobile(m.group(1), m.group(2), m.group(3)))

    for m in _RE_070.finditer(hay):
        found.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")

    for m in _RE_AREA.finditer(hay):
        found.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")

    for m in _RE_SPECIAL.finditer(hay):
        found.append(f"{m.group(1)}-{m.group(2)}")

    for m in _RE_LOCAL.finditer(hay):
        if m.group(1).startswith("0"):
            continue
        found.append(f"{m.group(1)}-{m.group(2)}")

    # 중복 제거
    return list(dict.fromkeys(found))


def pick_phone(name: str, desc: str) -> str:
    phones = extract_phones(name, desc)
    return phones[0] if phones else ""


# =========================================================
# utils
# =========================================================

def ms_to_yyyy_mm_dd(ms: Any) -> str:
    try:
        return datetime.fromtimestamp(int(ms) / 1000).strftime("%Y-%m-%d")
    except:
        return ""


# =========================================================
# main
# =========================================================

def fetch_members() -> List[Dict[str, Any]]:
    resp = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return (data.get("result_data") or {}).get("members") or []


def build_rows(members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    for m in members:
        name = m.get("name", "") or ""
        desc = m.get("description", "") or ""

        rows.append({
            "밴드명": BAND_NAME,
            "유저번호": m.get("user_no", ""),
            "직책": m.get("role", ""),
            "등록일": ms_to_yyyy_mm_dd(m.get("created_at")),
            "이름": name,
            "설명": desc,
            "전화번호": pick_phone(name, desc),
        })

    return rows


def save_to_excel(rows: List[Dict[str, Any]], out_xlsx: str):

    df = pd.DataFrame(rows, columns=[
        "밴드명",
        "유저번호",
        "직책",
        "등록일",
        "이름",
        "설명",
        "전화번호"
    ])

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="members")

        ws = writer.sheets["members"]
        for col_idx, col_name in enumerate(df.columns, start=1):
            max_len = max([len(str(col_name))] + [len(str(v)) for v in df[col_name].fillna("").tolist()])
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = min(max_len + 2, 60)


if __name__ == "__main__":

    members = fetch_members()
    rows = build_rows(members)

    out_file = "band_members.xlsx"
    save_to_excel(rows, out_file)

    print("ok:", out_file, "rows:", len(rows))
