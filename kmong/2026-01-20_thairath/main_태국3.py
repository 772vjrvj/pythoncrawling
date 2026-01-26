# rename_and_copy_thairath_images_seq.py
# -*- coding: utf-8 -*-

"""
요구사항
1) 실행 경로의 thairath.csv 읽기
2) id 오름차순 정렬 (처리 순서 고정)
3) 새 폴더에 이미지를 "순번" 기준으로 복사 (TR_00000001, TR_00000002, ...)
4) 한 장 처리 끝날 때마다 로그: [1/6041] OK -> TR_00000001.jpg
5) CSV에 새 이름 매핑 컬럼 저장
6) red25	force	checkpoint	smoke	guns	memo 컬럼추가

주의
- 원본 파일명/경로 형식이 섞일 수 있어서(image_path가 파일 풀경로인 경우 등) 안전하게 src 경로를 구성
- src가 파일이 아니면(폴더 등) 스킵하여 Permission denied 방지
"""

import shutil
import pandas as pd
from pathlib import Path

# =========================
# config
# =========================
CSV_NAME = "thairath_clean.csv"

OUT_DIR_NAME = "../../images_renamed_clean"
OUT_CSV_NAME = "thairath_renamed_seq_clean.csv"

PREFIX = "TR"
PAD = 8

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def _safe_int(x):
    try:
        return int(str(x).strip())
    except Exception:
        return None


def _strip_quotes(s: str) -> str:
    s = (s or "").strip()
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        s = s[1:-1]
    return s.strip()


def build_src_path(base_dir: Path, image_path: str, image_file: str) -> Path:
    """
    CSV의 image_path / image_file 값이 섞여 있어도 안전하게 원본 파일 경로를 만든다.

    케이스:
    1) image_path 자체가 파일 풀패스(확장자 있음) -> 그대로 사용
    2) image_file 자체가 경로 포함(확장자 있음) -> 그걸 사용
    3) 기본: (폴더)image_path + (파일명)image_file
    """
    p_raw = _strip_quotes(image_path)
    f_raw = _strip_quotes(image_file)

    p = Path(p_raw) if p_raw else Path()
    f = Path(f_raw) if f_raw else Path()

    # 1) image_path가 파일 경로인 경우
    if p_raw and p.suffix.lower() in IMG_EXTS:
        return p if p.is_absolute() else (base_dir / p).resolve()

    # 2) image_file이 경로(슬래시 포함) + 확장자 있는 경우
    if f_raw and f.suffix.lower() in IMG_EXTS:
        if ("\\" in f_raw) or ("/" in f_raw) or f.is_absolute():
            return f if f.is_absolute() else (base_dir / f).resolve()

    # 3) image_path(폴더) + image_file(파일명)
    p_dir = (p if p.is_absolute() else (base_dir / p).resolve()) if p_raw else base_dir
    return (p_dir / f_raw).resolve()


def main():
    base_dir = Path.cwd()
    csv_path = base_dir / CSV_NAME
    out_dir = base_dir / OUT_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    required = ["id", "image_file", "image_path"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # 1) id 오름차순 정렬 (처리 순서 고정)
    df["_id_int"] = df["id"].apply(_safe_int)
    df = df.sort_values(by=["_id_int", "id"], ascending=True).reset_index(drop=True)

    total = len(df)

    # 결과 컬럼
    orig_full_paths = []
    new_seq_list = []
    new_files = []
    new_paths = []
    status = []

    for idx, row in df.iterrows():
        cur = idx + 1  # 순번(1..N)

        # 원본 id(기사 id)는 CSV에 그대로 남겨 추적 가능하게
        orig_id = str(row.get("id", "")).strip()

        image_file = str(row.get("image_file", "")).strip()
        image_path = str(row.get("image_path", "")).strip()

        # src 경로 구성 (혼합 케이스 대응)
        src = build_src_path(base_dir, image_path, image_file)
        orig_full_paths.append(str(src))

        # 확장자: src 기준(없으면 image_file 기준, 그것도 없으면 .jpg)
        ext = src.suffix or (Path(image_file).suffix if image_file else "") or ".jpg"
        new_name = f"{PREFIX}_{cur:0{PAD}d}{ext.lower()}"
        dst = (out_dir / new_name).resolve()

        new_seq_list.append(cur)
        new_files.append(new_name)
        new_paths.append(str(dst))

        # 파일 유효성 체크(폴더/없는 파일 방지)
        if (not src.exists()) or (not src.is_file()):
            status.append("FAIL: source not found or not a file")
            print(f"[{cur}/{total}] FAIL -> source not found or not a file | orig_id={orig_id} | src={src}")
            continue

        try:
            if dst.exists():
                status.append("OK: already exists")
                print(f"[{cur}/{total}] OK   -> already exists ({new_name})")
                continue

            shutil.copy2(src, dst)
            status.append("OK")
            print(f"[{cur}/{total}] OK   -> {new_name}")

        except Exception as e:
            msg = str(e) if e else "unknown error"
            status.append("FAIL: " + msg)
            print(f"[{cur}/{total}] FAIL -> {msg} | orig_id={orig_id} | src={src} | dst={dst}")

    # 결과 컬럼 추가
    df["orig_full_path"] = orig_full_paths
    df["new_seq"] = new_seq_list               # 1..N
    df["new_image_file"] = new_files           # TR_00000001.jpg ...
    df["new_image_path"] = new_paths           # 새 폴더 fullpath
    df["copy_status"] = status                 # OK/FAIL

    # 정리
    df = df.drop(columns=["_id_int"])

    out_csv = base_dir / OUT_CSV_NAME
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    ok = sum(1 for s in status if s.startswith("OK"))
    fail = total - ok

    print("-" * 60)
    print(f"DONE: total={total}, OK={ok}, FAIL={fail}")
    print(f"Output CSV: {out_csv}")
    print(f"Output images dir: {out_dir}")


if __name__ == "__main__":
    main()
