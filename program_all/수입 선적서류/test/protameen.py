# -*- coding: utf-8 -*-
# Protameen: NUMBER / INVOICE DATE / AMOUNT($) 추출 (텍스트 PDF)
import os, re, datetime

def read_text(pdf_path):
    try:
        from pypdf import PdfReader
    except:
        from PyPDF2 import PdfReader
    r = PdfReader(pdf_path)
    return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))

def _nearest_value(s, label, patt, max_span=220):
    u = s.upper()
    li = u.find(label)
    if li == -1: return None
    best, best_d = None, None
    for m in re.finditer(patt, s, re.I):
        d = abs((m.start()+m.end())//2 - li)
        if d <= max_span and (best is None or d < best_d):
            best, best_d = m, d
    return best

def parse_protameen(raw):
    if not raw: return None
    s = raw.replace("\u00A0", " ")
    s = re.sub(r"[ \t]+", " ", s)

    # 1) Date: INVOICE DATE와 가장 가까운 MM/DD/YYYY
    m_dt = _nearest_value(s, "INVOICE DATE", r"([01]?\d/[0-3]?\d/\d{4})")
    if not m_dt: return None
    mm, dd, yyyy = m_dt.group(1).split("/")
    iso = f"{int(yyyy):04d}-{int(mm):02d}-{int(dd):02d}"

    # 2) Invoice No.: NUMBER와 가장 가까운 4~10자리 숫자
    # 변경 (5자리 ZIP 배제 + 윈도우 확장)
    m_no = _nearest_value(s, "NUMBER", r"(?<!\d)(\d{6,10})(?!\d)", max_span=600)
    if not m_no: return None
    inv = m_no.group(1)

    # 3) Amount: AMOUNT 이후 영역에서 '... $unit ... $amount' 중 마지막 $금액
    ui = s.upper().find("AMOUNT")
    if ui == -1: return None
    win = s[ui: ui+400]  # AMOUNT 아래쪽 윈도우
    dollars = list(re.finditer(r"\$\s*([\d,]+\.\d{2})", win))
    if not dollars: return None
    amt = f"{float(dollars[-1].group(1).replace(',', '')):.2f}"

    return {"Invoice No.": inv, "Date": iso, "Amount": amt}

if __name__ == "__main__":
    base = os.path.join(os.getcwd(), "수입 선적서류", "Protameen")
    if not os.path.isdir(base):
        print("폴더 없음:", base); raise SystemExit(1)
    for name in sorted(os.listdir(base)):
        if name.lower().endswith(".pdf"):
            path = os.path.join(base, name)
            try:
                obj = parse_protameen(read_text(path))
                print(f"[{name}] ->", obj if obj else "필드 미검출")
            except Exception as e:
                print(f"[{name}] -> 에러:", str(e))
