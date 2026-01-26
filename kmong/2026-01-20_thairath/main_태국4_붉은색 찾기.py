# auto_red25_label.py
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import pandas as pd
from pathlib import Path

# =========================
# config
# =========================
CSV_IN  = "thairath_renamed_seq_clean.csv"
CSV_OUT = "thairath_renamed_seq_clean_red25.csv"

IMG_DIR = Path("images_renamed_clean")

# RED_THRESHOLD = 25.0  # %
RED_THRESHOLD = 20.0  # % # 2026-01-26 비율 높이기

# HSV 빨강 범위
H1_LOW, H1_HIGH = 0, 10
H2_LOW, H2_HIGH = 170, 180
S_MIN = 80
V_MIN = 50

MAX_WIDTH = 800  # 속도용 리사이즈


def calc_red_ratio_percent(img_bgr: np.ndarray) -> float:
    h, w = img_bgr.shape[:2]
    if w > MAX_WIDTH:
        scale = MAX_WIDTH / w
        img_bgr = cv2.resize(
            img_bgr,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA
        )

    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    lower1 = np.array([H1_LOW, S_MIN, V_MIN], dtype=np.uint8)
    upper1 = np.array([H1_HIGH, 255, 255], dtype=np.uint8)
    lower2 = np.array([H2_LOW, S_MIN, V_MIN], dtype=np.uint8)
    upper2 = np.array([H2_HIGH, 255, 255], dtype=np.uint8)

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)

    red_pixels = int(np.count_nonzero(mask))
    total_pixels = int(mask.shape[0] * mask.shape[1])

    if total_pixels == 0:
        return 0.0

    return (red_pixels / total_pixels) * 100.0


def main():
    base = Path.cwd()
    csv_path = base / CSV_IN

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    if not IMG_DIR.exists():
        raise FileNotFoundError(f"Image dir not found: {IMG_DIR}")

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    if "new_image_file" not in df.columns:
        raise ValueError("CSV에 new_image_file 컬럼이 없습니다.")

    total = len(df)
    red25_labels = []

    print(f"START red25 auto labeling | total={total}")
    print("-" * 60)

    for idx, fname in enumerate(df["new_image_file"], start=1):

        img_path = (IMG_DIR / fname).resolve()

        if not img_path.exists():
            red25_labels.append("RED_N")
            print(f"[{idx}/{total}] RED_N (file not found) -> {fname}")
            continue

        img = cv2.imdecode(
            np.fromfile(str(img_path), dtype=np.uint8),
            cv2.IMREAD_COLOR
        )

        if img is None:
            red25_labels.append("RED_N")
            print(f"[{idx}/{total}] RED_N (unreadable) -> {fname}")
            continue

        ratio = calc_red_ratio_percent(img)
        label = "RED_Y" if ratio >= RED_THRESHOLD else "RED_N"
        red25_labels.append(label)

        print(f"[{idx}/{total}] {label} ({ratio:.2f}%) -> {fname}")

    df["red25"] = red25_labels
    df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")

    print("-" * 60)
    print(f"DONE | output={CSV_OUT}")
    print("-" * 60)


if __name__ == "__main__":
    main()
