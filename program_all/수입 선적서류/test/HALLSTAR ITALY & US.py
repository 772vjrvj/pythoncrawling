# -*- coding: utf-8 -*-
import os, re, datetime
from pypdf import PdfReader


def read_text(pdf_path):
    r = PdfReader(pdf_path)
    return "\n".join([(p.extract_text() or "") for p in getattr(r, "pages", [])])

def parse_fields(raw):
    s = re.sub(r"[\u00A0\s]+", " ", raw)
    m = re.search(
        r"Invoice\s*No\.\s*/\s*Date\s*/\s*Internal\s*No\.\s*:\s*([^/]+?)\s*/\s*([0-3]?\d\.[01]?\d\.\d{4}).*?/\s*([A-Za-z0-9-]+)",
        s, re.I
    )
    if not m:
        m = re.search(r"Invoice\s*No\.?:\s*([^\s/]+).*?Date\s*:?s*([0-3]?\d\.[01]?\d\.\d{4})", s, re.I)
    if not m: return None

    inv_no = m.group(1).strip()
    date_str = m.group(2).strip()
    iso = datetime.datetime.strptime(date_str, "%d.%m.%Y").date().isoformat()

    am = re.search(r"Total\s*Amount\s*Due\s*([0-9][\d,]*\.\d{2})(?:\s*[A-Z]{3})?", s, re.I)
    if not am: return None
    amount = float(am.group(1).replace(",", ""))  # 52,724.59 -> 52724.59

    return {"Invoice No.": inv_no, "Date": iso, "Amount": amount}

def main():
    base = os.path.join(os.getcwd(), "수입 선적서류", "HALLSTAR ITALY & US")
    if not os.path.isdir(base):
        print("폴더를 찾을 수 없습니다:", base); return
    for name in sorted(os.listdir(base)):
        if name.lower().endswith(".pdf"):
            path = os.path.join(base, name)
            try:
                obj = parse_fields(read_text(path))
                print(f"[{name}] ->", obj if obj else "필드 미검출")
            except Exception as e:
                print(f"[{name}] -> 에러:", (e and getattr(e, "message", None)) or str(e))

if __name__ == "__main__":
    main()
