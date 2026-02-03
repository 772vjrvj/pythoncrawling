# -*- coding: utf-8 -*-
import json
import time
import random
import httpx

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker


class Api457deepDetailSetLoadWorker(BaseApiWorker):
    def __init__(self):
        super().__init__()

        self.site_name = "457deep"

        self.csv_filename = None
        self.flush_size = 18
        self.buffer = []
        self.finalized = False

        self.excel_driver = None
        self.file_driver = None
        self.api_client = None

        self.total_saved = 0

        # progress
        self.current_cnt = 0
        self.total_cnt = 0
        self.before_pro_value = 0.0

    # 프로그램 중단
    def stop(self):
        self.log_signal_func("⛔ 중지 요청됨 (저장 후 종료합니다.)")
        self.running = False

    def init(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.api_client = APIClient(use_cache=False, log_func=self.log_signal_func)
        return True

    def main(self):
        self.log_signal_func("시작합니다.")

        self.finalized = False
        self.buffer = []
        self.total_saved = 0

        self.current_cnt = 0
        self.total_cnt = 0
        self.before_pro_value = 0.0

        if not self.columns:
            self.log_signal_func("columns가 비어있습니다.")
            return False

        # --- total_cnt 계산(체크된 item 개수) ---
        rows = self.setting_detail or []
        for r in rows:
            if r.get("row_type") == "item" and r.get("checked", True):
                self.total_cnt += 1

        if self.total_cnt <= 0:
            self.total_cnt = 1

        self.log_signal_func(f"작업 대상(자식 item) 수: {self.total_cnt}")

        # CSV 초기화
        self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
        self.excel_driver.init_csv(self.csv_filename, self.columns)
        self.log_signal_func(f"CSV 생성: {self.csv_filename}")

        try:
            sections = self.get_sections()
            if not sections:
                self.log_signal_func("setting_detail에 section이 없습니다.")
                return True

            with httpx.Client(http2=True, timeout=30) as client:
                for sec in sections:
                    if not self.running:
                        self.log_signal_func("⛔ 중지 감지 (섹션) → 저장 후 종료")
                        return True

                    sec_id = sec.get("id")
                    sec_title = (sec.get("title") or sec_id or "").replace("\n", "").strip()
                    self.log_signal_func(f"[섹션] {sec_title}")

                    items = self.get_items(sec_id)
                    if not items:
                        self.log_signal_func(f"  - 아이템 없음: {sec_id}")
                        continue

                    for it in items:
                        if not self.running:
                            self.log_signal_func("⛔ 중지 감지 (카테고리) → 저장 후 종료")
                            return True

                        if not it.get("checked", True):
                            continue

                        name = (it.get("value") or it.get("code") or "").replace("\n", "").strip()
                        list_url = it.get("list_url") or ""
                        if not list_url:
                            self.log_signal_func(f"  - list_url 없음: {name}")
                            # ✅ 그래도 1개 item 처리로 보고 progress는 올릴지 말지 애매한데
                            # 보통은 "실제로 처리된 item" 기준이 더 직관적이라 여기서는 증가 안 함.
                            continue

                        context = f"{sec_title} > {name}".strip()

                        # === 카테고리 시작 로그 ===
                        self.log_signal_func(f"[{context}] ✅ 카테고리 시작")
                        self.log_signal_func(f"[{context}] url: {list_url}")

                        # 1) 목록에서 id 전체 수집
                        ids = self.collect_all_ids(client, list_url, context)
                        self.log_signal_func(f"[{context}] id 수집 완료: {len(ids)}개")

                        # 2) 상세 수집
                        cat_saved = 0
                        total_ids = len(ids)

                        for idx, pid in enumerate(ids, start=1):
                            if not self.running:
                                self.log_signal_func(f"[{context}] ⛔ 중지 감지 (상세) → 저장 후 종료")
                                return True

                            # === 상세 진행 로그 ===
                            if idx == 1 or (idx % 100 == 0) or (idx == total_ids):
                                self.log_signal_func(f"[{context}] 📥 상세 {idx}/{total_ids}")

                            post, detail_url = self.fetch_post(client, list_url, pid, context)
                            if not post:
                                continue

                            row = self.map_row(post, detail_url)
                            self.buffer.append(row)
                            cat_saved += 1

                            if len(self.buffer) >= self.flush_size:
                                self.flush_buffer(context)

                            time.sleep(random.uniform(0.15, 0.35))

                        # 카테고리 완료 로그
                        self.log_signal_func(
                            f"[{context}] ✅ 카테고리 완료 / saved={cat_saved} / total_saved={self.total_saved}"
                        )

                        # === progress: 자식 item 1개 끝날 때마다 ===
                        self.current_cnt += 1
                        pro_value = (self.current_cnt / self.total_cnt) * 1000000
                        self.progress_signal.emit(self.before_pro_value, pro_value)
                        self.before_pro_value = pro_value
                        self.log_signal_func(f"[진행] {self.current_cnt}/{self.total_cnt} (pro={int(pro_value)})")

            return True

        finally:
            # 중지/예외/정상 모두 저장 보장
            self.finalize_export()

    def destroy(self):
        # 마지막 progress + 종료
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 작업 종료")
        self.progress_end_signal.emit()

    # =========================================================
    # setting_detail helpers
    # =========================================================
    def get_sections(self):
        out = []
        rows = self.setting_detail or []
        for r in rows:
            if r.get("row_type") == "section":
                out.append(r)
        return out

    def get_items(self, parent_id):
        out = []
        rows = self.setting_detail or []
        for r in rows:
            if r.get("row_type") == "item" and r.get("parent_id") == parent_id:
                out.append(r)
        return out

    # =========================================================
    # export
    # =========================================================
    def flush_buffer(self, context=""):
        if not self.csv_filename:
            return
        if not self.buffer:
            return

        n = len(self.buffer)
        self.excel_driver.append_to_csv(self.csv_filename, self.buffer, self.columns)
        self.total_saved += n

        if context:
            self.log_signal_func(f"[{context}] 💾 CSV 저장 +{n} (누적 {self.total_saved})")
        else:
            self.log_signal_func(f"💾 CSV 저장 +{n} (누적 {self.total_saved})")

    def finalize_export(self):
        if self.finalized:
            return

        try:
            if self.buffer:
                self.log_signal_func(f"🧾 잔여 데이터 flush: {len(self.buffer)}건")
                self.flush_buffer("FINAL")

            if self.csv_filename:
                self.log_signal_func("📦 CSV → XLSX 변환 시작")
                self.excel_driver.convert_csv_to_excel_and_delete(self.csv_filename)
                self.log_signal_func("✅ CSV → XLSX 변환 완료 (CSV 삭제)")

            self.finalized = True

        except Exception as e:
            self.log_signal_func(f"❌ finalize 오류: {e}")

    # =========================================================
    # list -> ids
    # =========================================================
    def collect_all_ids(self, client, list_url, context):
        out = []
        seen = set()

        page = 1
        total = 0

        while True:
            if not self.running:
                self.log_signal_func(f"[{context}] ⛔ 중지 감지 (목록)")
                break

            posts = self.fetch_posts(client, list_url, page, context)

            # 페이지 로그: 어디/무엇/몇페이지/몇건/누적
            self.log_signal_func(f"[{context}] 📄 목록 page={page} posts={len(posts)} total_ids={total}")

            if not posts:
                self.log_signal_func(f"[{context}] ✔ 마지막 페이지 (page={page})")
                break

            new_cnt = 0
            for p in posts:
                pid = p.get("id") or ""
                if not pid:
                    continue
                if pid in seen:
                    continue

                seen.add(pid)
                out.append(pid)
                new_cnt += 1

            total += new_cnt
            self.log_signal_func(f"[{context}] ➕ 신규 {new_cnt} / 누적 {total}")

            if new_cnt == 0:
                self.log_signal_func(f"[{context}] ✔ 신규 없음 → 종료 (page={page})")
                break

            page += 1
            time.sleep(random.uniform(0.15, 0.35))

        self.log_signal_func(f"[{context}] ✅ 목록 수집 완료 total={total}")
        return out

    def fetch_posts(self, client, list_url, page, context):
        url = list_url + ("&page=" if "?" in list_url else "?page=") + str(page)
        headers = self.make_headers(list_url)

        try:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            return self.extract_posts(r.text)
        except Exception as e:
            self.log_signal_func(f"[{context}] ❌ 목록 실패 page={page}: {e}")
            return []

    def extract_posts(self, text):
        i = text.find('"posts":')
        if i < 0:
            return []
        i = text.find('[', i)
        if i < 0:
            return []

        depth = 0
        for j in range(i, len(text)):
            ch = text[j]
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[i:j + 1])
                    except Exception:
                        return []
        return []

    # =========================================================
    # detail fetch
    # =========================================================
    def fetch_post(self, client, list_url, post_id, context):
        detail_url = list_url.rstrip("/") + "/detail/" + post_id
        url = detail_url + "?_rsc=1"
        headers = self.make_headers(list_url)

        try:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            post = self.extract_obj(r.text, "post")
            return post, detail_url
        except Exception as e:
            self.log_signal_func(f"[{context}] ❌ 상세 실패 id={post_id}: {e}")
            return None, detail_url

    def extract_obj(self, text, key):
        k = text.find(f'"{key}":')
        if k < 0:
            return None
        i = text.find('{', k)
        if i < 0:
            return None

        d = 0
        for j in range(i, len(text)):
            ch = text[j]
            if ch == '{':
                d += 1
            elif ch == '}':
                d -= 1
                if d == 0:
                    try:
                        return json.loads(text[i:j + 1])
                    except Exception:
                        return None
        return None

    def make_headers(self, list_url):
        path = "/"
        try:
            s = list_url.split("://", 1)[1]
            idx = s.find("/")
            if idx >= 0:
                path = "/" + s[idx + 1:]
        except Exception:
            path = "/"

        return {
            "rsc": "1",
            "next-url": path,
            "referer": list_url,
            "user-agent": "Mozilla/5.0"
        }

    # =========================================================
    # mapping (self.columns는 'value'(한글 헤더) 리스트)
    # =========================================================
    def map_row(self, post, detail_url):
        row = {}
        for col_name in self.columns:
            row[col_name] = ""

        # ✅ URL 컬럼(추가됨): 상세보기 전체 URL
        if "URL" in row:
            row["URL"] = detail_url

        if "아이디" in row:
            row["아이디"] = post.get("id", "")
        if "등록일" in row:
            row["등록일"] = post.get("createdAt", "")
        if "수정일" in row:
            row["수정일"] = post.get("updatedAt", "")
        if "유저아이디" in row:
            row["유저아이디"] = post.get("userId", "")

        if "제목" in row:
            row["제목"] = post.get("title", "")
        if "내용" in row:
            row["내용"] = post.get("content", "")

        if "순서" in row:
            row["순서"] = post.get("sequence", "")
        if "좋아요" in row:
            row["좋아요"] = post.get("likeCount", "")
        if "댓글수" in row:
            row["댓글수"] = post.get("commentCount", "")
        if "조회수" in row:
            row["조회수"] = post.get("viewCount", "")

        if "유저명" in row:
            name = ""
            try:
                user = post.get("user") or {}
                profile = user.get("profile") or {}
                name = profile.get("name") or ""
            except Exception:
                name = ""
            row["유저명"] = name

        if "카테고리" in row:
            ct = ""
            try:
                cat = post.get("category") or {}
                ct = cat.get("title") or post.get("imwebCategoryTitle") or ""
            except Exception:
                ct = ""
            row["카테고리"] = ct

        return row
