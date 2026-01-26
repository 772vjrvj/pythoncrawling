# clip_score_thairath_guns.py
# -*- coding: utf-8 -*-

"""
목표
- thairath_renamed_seq_clean.csv 읽기
- new_image_file 값을 images_renamed_clean 폴더에서 찾아 이미지 로드
- CLIP으로 "총기 증거물 전시/수거(다수 총기 나열)" 프롬프트와의 유사도 점수 계산
- guns_clip_score 컬럼 추가 후 CSV 저장

주의
- CLIP은 "판정"이 아니라 "유사도 점수"만 산출
- 이 스크립트는 "총기 사용/제조 방법"이 아니라, "증거물 정리/전시 장면"만 점수화
"""

from pathlib import Path

import pandas as pd
from PIL import Image
from tqdm import tqdm

import torch
from transformers import CLIPProcessor, CLIPModel


# =========================
# config
# =========================
CSV_IN  = "thairath_renamed_seq_clean.csv"
CSV_OUT = "thairath_renamed_seq_clean_guns_scored.csv"

IMG_DIR = Path("../../images_renamed_clean")

# =========================================================
# === 다수 총기 "증거물 전시/수거" 프롬프트
# - 핵심: 여러 총기가 테이블/바닥 위에 나열, evidence display, seized firearms
# - 단독 총기/사격/전투 장면이 아니라 "증거물 정리" 뉘앙스
# =========================================================
GUNS_PROMPTS = [
    # evidence display / seizure core
    "seized firearms displayed as evidence on a table",
    "multiple guns laid out on a table as police evidence",
    "confiscated guns lined up on the floor",
    "weapons seizure evidence display with many firearms",
    "police evidence table with multiple firearms",

    # arranged / cataloged
    "firearms arranged in rows for evidence documentation",
    "guns and ammunition displayed as confiscated evidence",
    "assault rifles and handguns laid out as seized evidence",
    "a collection of confiscated firearms arranged on the ground",
    "evidence整理 scene with many seized guns",  # mixed language ok

    # press / briefing style
    "law enforcement press conference showing seized guns on a table",
    "police presenting confiscated firearms as evidence",
    "investigators photographing guns laid out as evidence",

    # variations
    "pile of seized weapons on the floor in a police station",
    "table full of confiscated handguns and rifles",
    "evidence display of many firearms and magazines",
]

BATCH_SIZE = 32
MODEL_NAME = "openai/clip-vit-base-patch32"


def _open_image_rgb(img_path: Path):
    try:
        with Image.open(img_path) as im:
            return im.convert("RGB")
    except Exception:
        return None


def main():
    csv_path = Path.cwd() / CSV_IN
    out_path = Path.cwd() / CSV_OUT

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    if not IMG_DIR.exists():
        raise FileNotFoundError(f"Image dir not found: {IMG_DIR}")

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    if "new_image_file" not in df.columns:
        raise ValueError("CSV에 new_image_file 컬럼이 없습니다.")

    # =========================
    # device
    # =========================
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] device={device}")

    dtype = torch.float16 if device == "cuda" else torch.float32
    model = CLIPModel.from_pretrained(
        MODEL_NAME,
        use_safetensors=True,
        torch_dtype=dtype
    ).to(device)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    model.eval()

    # 텍스트 프롬프트 고정
    text_inputs = processor(
        text=GUNS_PROMPTS,
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to(device)

    total = len(df)
    scores = ["" for _ in range(total)]
    status = ["" for _ in range(total)]

    idxs = list(range(total))
    for start in tqdm(range(0, total, BATCH_SIZE), desc="CLIP guns scoring"):
        batch_idxs = idxs[start:start + BATCH_SIZE]

        images = []
        valid_map = []

        for row_idx in batch_idxs:
            fname = str(df.at[row_idx, "new_image_file"]).strip()
            img_path = (IMG_DIR / fname).resolve()

            if not img_path.exists():
                status[row_idx] = "FILE_NOT_FOUND"
                continue

            im = _open_image_rgb(img_path)
            if im is None:
                status[row_idx] = "UNREADABLE"
                continue

            images.append(im)
            valid_map.append(row_idx)

        if not images:
            continue

        image_inputs = processor(images=images, return_tensors="pt").to(device)

        with torch.no_grad():
            img_feat = model.get_image_features(**image_inputs)   # (B, D)
            txt_feat = model.get_text_features(**text_inputs)     # (T, D)

            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
            txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)

            sim = img_feat @ txt_feat.T
            sim_max = sim.max(dim=1).values
            sim_max = sim_max.detach().float().cpu().tolist()

        for row_idx, sc in zip(valid_map, sim_max):
            scores[row_idx] = f"{sc:.6f}"
            status[row_idx] = "OK"

    # =========================
    # save
    # =========================
    df["guns_clip_score"] = scores
    df["guns_clip_status"] = status

    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[DONE] output={out_path} rows={len(df)}")


if __name__ == "__main__":
    main()
