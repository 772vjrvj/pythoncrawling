# clip_score_thairath_force.py
# -*- coding: utf-8 -*-

"""
목표
- thairath_renamed_seq_clean.csv 읽기
- new_image_file 값을 images_renamed_clean 폴더에서 찾아 이미지 로드
- CLIP으로 force 프롬프트 세트와의 유사도 점수 계산
- force_clip_score 컬럼 추가 후 CSV 저장

주의
- CLIP은 "판정"이 아니라 "유사도 점수"만 산출
- 점수는 보통 0~1 근처(또는 모델/정규화에 따라 조금 다름)
"""

import os
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
CSV_OUT = "thairath_renamed_seq_clean_force_scored.csv"

IMG_DIR = Path("../../images_renamed_clean")

# === force 프롬프트 세트(영어) ===
FORCE_PROMPTS = [
    "a photo of soldiers with rifles",
    "armed soldiers during a security operation",
    "military personnel in combat gear",
    "EOD bomb disposal unit",
    "explosive ordnance disposal team in protective suit",
    "bomb disposal robot and EOD officers",
    "police wearing bulletproof vests",
    "armed police officers in tactical gear",
    "riot police with protective equipment",
]

# 배치 크기(메모리/속도에 맞게 조절)
BATCH_SIZE = 32

# 모델 (가볍고 범용)
MODEL_NAME = "openai/clip-vit-base-patch32"


def _open_image_rgb(img_path: Path):
    """
    이미지 열기(PIL) - 깨진 파일/읽기 실패 대비
    """
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

    # =========================
    # load model
    # =========================
    dtype = torch.float16 if device == "cuda" else torch.float32
    model = CLIPModel.from_pretrained(
        MODEL_NAME,
        use_safetensors=True,
        torch_dtype=dtype
    ).to(device)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    model.eval()

    # 텍스트는 고정이므로 한 번만 토크나이즈해서 재사용
    text_inputs = processor(
        text=FORCE_PROMPTS,
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to(device)

    total = len(df)
    scores = ["" for _ in range(total)]
    status = ["" for _ in range(total)]  # 파일 없거나 unreadable 체크용 (선택)

    # =========================
    # batching
    # =========================
    idxs = list(range(total))
    for start in tqdm(range(0, total, BATCH_SIZE), desc="CLIP scoring"):
        batch_idxs = idxs[start:start + BATCH_SIZE]

        # 이미지 로드
        images = []
        valid_map = []  # (row_idx, image)
        for row_idx in batch_idxs:
            fname = str(df.at[row_idx, "new_image_file"]).strip()
            img_path = (IMG_DIR / fname).resolve()

            if not img_path.exists() or not img_path.is_file():
                scores[row_idx] = ""
                status[row_idx] = "FILE_NOT_FOUND"
                continue

            im = _open_image_rgb(img_path)
            if im is None:
                scores[row_idx] = ""
                status[row_idx] = "UNREADABLE"
                continue

            images.append(im)
            valid_map.append(row_idx)

        if not images:
            continue

        # 이미지 배치 전처리
        image_inputs = processor(
            images=images,
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            # 이미지/텍스트 임베딩
            img_feat = model.get_image_features(**image_inputs)     # (B, D)
            txt_feat = model.get_text_features(**text_inputs)       # (T, D)

            # L2 정규화 후 cosine similarity = dot product
            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
            txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)

            # (B, D) x (D, T) -> (B, T)
            sim = img_feat @ txt_feat.T

            # force 프롬프트 중 최대 유사도 점수 사용
            sim_max = sim.max(dim=1).values  # (B,)

            # CPU로 이동, float 변환
            sim_max = sim_max.detach().float().cpu().tolist()

        # 점수 기록
        for row_idx, sc in zip(valid_map, sim_max):
            # 보기 좋게 소수점 6자리로 저장(원하면 자리수 줄여도 됨)
            scores[row_idx] = f"{sc:.6f}"
            status[row_idx] = "OK"

    # =========================
    # save
    # =========================
    df["force_clip_score"] = scores
    df["force_clip_status"] = status  # 선택: 필요 없으면 지워도 됨

    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[DONE] output={out_path} rows={len(df)}")


if __name__ == "__main__":
    main()
