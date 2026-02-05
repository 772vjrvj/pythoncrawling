# -*- coding: utf-8 -*-
import asyncio
import glob
import json
import os
import re
from datetime import datetime

import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

# === 설정 ===
WIDGET_URL = r"""https://app.commentsplugin.com/widget-wix?pageId=masterPage&compId=comp-k5c7ety7&viewerCompId=comp-k5c7ety7&siteRevision=2793&viewMode=site&deviceType=desktop&locale=ko&tz=Asia%2FSeoul&regionalLanguage=ko&width=975&height=2950&instance=H-_OjENTC87qUzhsgzb016Ujwyy2A-bP_eyNKhQuXP8.eyJpbnN0YW5jZUlkIjoiNWI2NjJiOTUtZjBjMC00NDA0LTlhOGQtYmU1YzUxYzhjMTk0IiwiYXBwRGVmSWQiOiIxMzAxNjU4OS1hOWViLTQyNGEtOGE2OS00NmNiMDVjZTBiMmMiLCJzaWduRGF0ZSI6IjIwMjYtMDItMDVUMTI6MjY6MDUuNDg5WiIsInZlbmRvclByb2R1Y3RJZCI6IlByZW1pdW0xIiwiZGVtb01vZGUiOmZhbHNlLCJhaWQiOiIwOTNiYjU3NC1lODQ3LTQ5YmItYTJiMC04Zjk5YjNhMmQ4OGEiLCJzaXRlT3duZXJJZCI6ImJiMWQxMzI4LWMyNzgtNDBiYy05MTU4LTBkOTI2NzY2NmU1NSIsImJzIjoiRnZIb0tYLWltLXZ6RGRCQlBwX005ZHJJY0gxdl92dF83N2RxVHUyQ1N4MCIsInNjZCI6IjIwMjAtMDEtMTNUMDU6NTM6MTcuNDE3WiJ9&currency=KRW&currentCurrency=KRW&commonConfig=%7B%22brand%22%3A%22wix%22%2C%22host%22%3A%22VIEWER%22%2C%22bsi%22%3A%2207744318-5c3f-4054-aecd-2836e551f7c3%7C1%22%2C%22siteRevision%22%3A%222793%22%2C%22renderingFlow%22%3A%22NONE%22%2C%22language%22%3A%22ko%22%2C%22locale%22%3A%22ko-kr%22%2C%22BSI%22%3A%2207744318-5c3f-4054-aecd-2836e551f7c3%7C1%22%7D&currentRoute=.%2Fmembers&vsi=b41de390-f314-4ae7-8380-084954d7b157"""

OUT_DIR = "out_comments"
BASE_NAME = "commentsplugin_all"

MAX_CLICKS = 2000                 # 안전장치
FLUSH_EVERY_CLICKS = 20           # 20번 클릭마다 중간저장
INIT_WAIT_MS = 4000               # 최초 로딩 대기


# =========================
# Utils
# =========================
def norm_text(s: str) -> str:
    s = (s or "").replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def parse_total_count(text: str) -> int:
    m = re.search(r"댓글\s*([0-9,]+)\s*개", text or "")
    return int(m.group(1).replace(",", "")) if m else 0

def parse_ko_datetime(s: str):
    """
    '2024년 8월 27일 오후 10:13' -> datetime or None
    """
    if not s:
        return None
    s = s.strip()
    m = re.match(r"(\d+)년\s*(\d+)월\s*(\d+)일\s*(오전|오후)\s*(\d+):(\d+)", s)
    if not m:
        return None
    y, mo, d, ap, hh, mm = m.groups()
    hh = int(hh); mm = int(mm)
    if ap == "오후" and hh != 12:
        hh += 12
    if ap == "오전" and hh == 12:
        hh = 0
    return datetime(int(y), int(mo), int(d), hh, mm)

def ensure_dir(path: str):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def build_base_paths():
    ensure_dir(OUT_DIR)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(OUT_DIR, f"{BASE_NAME}_{ts}")
    return base

def dedupe(items):
    # 작성자 + created_at_raw + content 앞부분 기준 중복 제거
    uniq = {}
    for it in items:
        key = (
            it.get("author", ""),
            it.get("created_at_raw", ""),
            (it.get("content", "") or "")[:300],
        )
        uniq[key] = it
    return list(uniq.values())

def to_rows(items):
    rows = []
    for it in items:
        dt = parse_ko_datetime(it.get("created_at_raw", ""))
        attach_list = it.get("attachment_images") or []
        rows.append({
            "author": it.get("author", ""),
            "created_at": dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "",
            "created_at_raw": it.get("created_at_raw", ""),
            "score": it.get("score", ""),  # ✅ 없으면 빈값
            "profile_image_url": it.get("profile_image_url", ""),
            "attachment_images": "|".join([x for x in attach_list if x]),
            "content": it.get("content", ""),
        })
    return rows

def save_csv_xlsx(rows, base_path_no_ext: str):
    df = pd.DataFrame(
        rows,
        columns=["author", "created_at", "created_at_raw", "score",
                 "profile_image_url", "attachment_images", "content"]
    )

    csv_path = f"{base_path_no_ext}.csv"
    xlsx_path = f"{base_path_no_ext}.xlsx"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="comments")

    print("[SAVED]", csv_path)
    print("[SAVED]", xlsx_path)

def find_latest_saved_csv():
    files = sorted(glob.glob(os.path.join(OUT_DIR, f"{BASE_NAME}_*.csv")))
    if not files:
        return None
    return files[-1]

def load_rows_from_csv(csv_path: str):
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    return df.to_dict(orient="records")

def merge_rows(existing_rows, new_rows):
    uniq = {}
    for r in existing_rows:
        key = (r.get("author", ""), r.get("created_at_raw", ""), (r.get("content", "") or "")[:300])
        uniq[key] = r
    for r in new_rows:
        key = (r.get("author", ""), r.get("created_at_raw", ""), (r.get("content", "") or "")[:300])
        uniq[key] = r
    return list(uniq.values())


# =========================
# Page extract/click
# =========================
async def extract_total_text(page) -> str:
    try:
        h3 = page.locator("h3:has-text('댓글')")
        if await h3.count() > 0:
            return await h3.first.inner_text()
    except Exception:
        pass
    return ""

async def extract_comments(page):
    """
    li.comment-box 기준:
      - author
      - created_at_raw (.timestamp title)
      - content (comment-content/div.content 통째 innerText 우선)
      - score (없으면 "")
      - profile_image_url
      - attachment_images (복수)
    """
    js = r"""
    () => {
      const pickText = (el) => {
        if (!el) return "";
        return (el.innerText || el.textContent || "").trim();
      };

      const out = [];
      const boxes = Array.from(document.querySelectorAll("li.comment-box"));

      for (const li of boxes) {
        const authorEl = li.querySelector(".author");
        const tsEl = li.querySelector(".timestamp");

        const contentRoot =
          li.querySelector("comment-content") ||
          li.querySelector("div.content") ||
          li;

        const ratingSpan =
          li.querySelector("star-rating span.star-rating[aria-valuenow]") ||
          li.querySelector("span.star-rating[aria-valuenow]");

        const imgEl =
          li.querySelector("ca-user-photo img") ||
          li.querySelector(".profile-image img");

        const attachImgs = Array.from(li.querySelectorAll("img.comments-attachment-image"))
          .map(e => (e.getAttribute("src") || "").trim())
          .filter(Boolean);

        const author = authorEl ? authorEl.textContent.trim() : "";
        const created_at_raw = tsEl ? (tsEl.getAttribute("title") || "") : "";

        let content = pickText(contentRoot);
        if (!content || content.length < 2) {
          const alt = li.querySelector("div.content comment-content") ||
                      li.querySelector("div.content");
          content = pickText(alt);
        }

        let score = "";
        if (ratingSpan) {
          const v = ratingSpan.getAttribute("aria-valuenow");
          if (v != null && v !== "") score = String(v).trim();
        }

        const profile_image_url = imgEl ? (imgEl.getAttribute("src") || "") : "";

        out.push({
          author,
          created_at_raw,
          content,
          score,
          profile_image_url,
          attachment_images: attachImgs
        });
      }

      return out;
    }
    """
    items = await page.evaluate(js)

    for it in items:
        it["author"] = norm_text(it.get("author", ""))
        it["created_at_raw"] = norm_text(it.get("created_at_raw", ""))
        it["content"] = norm_text(it.get("content", ""))

        sc = it.get("score", "")
        it["score"] = "" if sc is None else str(sc).strip()

        it["profile_image_url"] = (it.get("profile_image_url") or "").strip()

        imgs = it.get("attachment_images") or []
        it["attachment_images"] = [x.strip() for x in imgs if x]

    return items

async def click_load_more_once(page, prev_count: int) -> bool:
    """
    ✅ 핵심: 클릭 성공이 아니라 '댓글 개수 증가'로 성공 판정
    """
    candidates = [
        "li.load-more .load-link",
        "li.load-more",
        "text=더 많은 댓글",
        "text=더보기",
        "button:has-text('더보기')",
        "a:has-text('더보기')",
    ]

    # 여러 후보를 돌면서 클릭 시도
    for sel in candidates:
        loc = page.locator(sel)
        if await loc.count() == 0:
            continue
        try:
            await loc.first.scroll_into_view_if_needed()
            await loc.first.click(timeout=1500)

            # ✅ 개수 증가 대기
            await page.wait_for_function(
                f"() => document.querySelectorAll('li.comment-box').length > {prev_count}",
                timeout=7000
            )
            return True
        except PWTimeoutError:
            # 증가 실패 → 다음 후보
            pass
        except Exception:
            pass

    # 클릭으로 증가 안 되면 스크롤 내려서 버튼 재렌더 유도
    try:
        await page.mouse.wheel(0, 2500)
        await page.wait_for_timeout(600)
    except Exception:
        pass

    # 스크롤 후 대표 셀렉터로 1회 추가 시도
    loc = page.locator("li.load-more .load-link")
    if await loc.count() > 0:
        try:
            await loc.first.scroll_into_view_if_needed()
            await loc.first.click(timeout=1500)
            await page.wait_for_function(
                f"() => document.querySelectorAll('li.comment-box').length > {prev_count}",
                timeout=7000
            )
            return True
        except Exception:
            return False

    return False


# =========================
# Main
# =========================
async def main():
    ensure_dir(OUT_DIR)

    # ✅ resume: 가장 최근 CSV가 있으면 merge
    resume_csv = find_latest_saved_csv()
    existing_rows = []
    if resume_csv:
        try:
            existing_rows = load_rows_from_csv(resume_csv)
            print("[RESUME] found existing csv:", resume_csv, "rows=", len(existing_rows))
        except Exception as e:
            print("[RESUME] failed to read csv:", resume_csv, "err=", str(e))
            existing_rows = []

    base = build_base_paths()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        await page.goto(WIDGET_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(INIT_WAIT_MS)

        total_text = await extract_total_text(page)
        total_cnt = parse_total_count(total_text)
        print("[TOTAL TEXT]", total_text)
        print("[TOTAL COUNT]", total_cnt)

        items = await extract_comments(page)
        print("[INIT LOADED]", len(items))

        # ✅ 검증: 초기 13개 마지막 1건 raw 출력
        if items:
            print("\n[INIT LAST ITEM RAW]")
            print(json.dumps(items[-1], ensure_ascii=False, indent=2))

        clicks = 0
        fail_streak = 0

        # 초기 저장
        tmp_items = dedupe(items)
        new_rows = to_rows(tmp_items)
        merged_rows = merge_rows(existing_rows, new_rows)
        save_csv_xlsx(merged_rows, f"{base}_partial_{clicks:04d}")

        while clicks < MAX_CLICKS:
            prev_count = await page.locator("li.comment-box").count()

            ok = await click_load_more_once(page, prev_count=prev_count)
            if not ok:
                fail_streak += 1
                print(f"[LOAD MORE FAIL] streak={fail_streak} loaded={prev_count}")

                # ✅ 연속 실패 5번이면 종료
                if fail_streak >= 5:
                    break

                continue

            # 성공
            fail_streak = 0
            clicks += 1

            items = await extract_comments(page)
            cur = len(items)
            print(f"[CLICK {clicks}] loaded={cur}")

            # 중간 저장
            if clicks % FLUSH_EVERY_CLICKS == 0:
                tmp_items = dedupe(items)
                new_rows = to_rows(tmp_items)
                merged_rows = merge_rows(existing_rows, new_rows)
                save_csv_xlsx(merged_rows, f"{base}_partial_{clicks:04d}")

            if total_cnt and cur >= total_cnt:
                break

        # 최종 저장
        final_items = dedupe(items)
        final_rows = to_rows(final_items)
        final_merged = merge_rows(existing_rows, final_rows)

        print("[FINAL UNIQUE THIS RUN]", len(final_rows))
        print("[FINAL MERGED TOTAL]", len(final_merged))

        save_csv_xlsx(final_merged, f"{base}_final")

        await page.wait_for_timeout(999999)

if __name__ == "__main__":
    asyncio.run(main())
