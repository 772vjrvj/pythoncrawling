# /src/workers/api_thumnail_make_set_load_worker.py
import os
import time
from urllib.parse import urlparse

from PIL import Image, ImageEnhance

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker


class ApiThumnailMakeSetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.driver = None
        self.file_driver = None
        self.excel_driver = None

        self.total_cnt = 0
        self.current_cnt = 0
        self.before_pro_value = 0

        self.api_client = APIClient(use_cache=False)

    def init(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        return True

    # =========================================================
    # helpers
    # =========================================================
    def _to_int(self, v, default=0):
        try:
            if v is None or v == "":
                return default
            return int(float(str(v).strip()))
        except Exception:
            return default

    def _to_str(self, v, default=""):
        if v is None:
            return default
        s = str(v).strip()
        return s if s else default

    def _safe_filename(self, name: str) -> str:
        name = (name or "").strip()
        if not name:
            return ""
        bad = r'<>:"/\|?*'
        for ch in bad:
            name = name.replace(ch, "_")
        name = name.replace("\n", " ").replace("\r", " ").strip()
        return name

    def _ensure_ext(self, filename: str, ext: str) -> str:
        filename = self._safe_filename(filename)
        ext = (ext or "jpg").lower().strip(".")
        base, cur = os.path.splitext(filename)
        if not filename:
            return ""
        if cur:
            return base + cur
        return f"{base}.{ext}"

    def _center_crop(self, img: Image.Image, tw: int, th: int) -> Image.Image:
        w, h = img.size
        left = (w - tw) // 2
        top = (h - th) // 2
        return img.crop((left, top, left + tw, top + th))

    def _make_edit_image(self, src_path, dst_path, tw, th, rotate_deg, scale_pct, ext):
        """
        ✅ 요구사항 버전: 덮는 형태 (cover + center crop)
        - 최종은 tw x th 고정
        - 먼저 cover로 꽉 채움
        - scale_pct(150 등)는 더 크게 만들어 overflow 유도
        - rotate 후에도 overflow 가능
        - 마지막은 center crop으로 tw x th로 자름
        """
        img = Image.open(src_path).convert("RGBA")

        # 0) cover로 tw x th를 꽉 채우는 크기로 resize
        w, h = img.size
        cover = max(tw / w, th / h)
        rw = max(1, int(w * cover))
        rh = max(1, int(h * cover))
        img = img.resize((rw, rh), Image.LANCZOS)

        # 1) scale_pct 적용 (150 => 1.5배)
        if scale_pct and scale_pct != 100:
            s = scale_pct / 100.0
            w, h = img.size
            img = img.resize(
                (max(1, int(w * s)), max(1, int(h * s))),
                Image.LANCZOS
            )

        # 2) 회전 (expand=True)
        if rotate_deg:
            img = img.rotate(-rotate_deg, expand=True)

        # 3) center crop
        w, h = img.size
        if w < tw or h < th:
            # 혹시라도 작아지면 다시 cover로 키움
            cover2 = max(tw / w, th / h)
            img = img.resize(
                (max(1, int(w * cover2)), max(1, int(h * cover2))),
                Image.LANCZOS
            )

        out_img = self._center_crop(img, tw, th)

        # 4) 저장
        ext_l = (ext or "jpg").lower().strip(".")
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        if ext_l in ("jpg", "jpeg"):
            out_img.convert("RGB").save(dst_path, format="JPEG", quality=95)
        elif ext_l == "png":
            out_img.save(dst_path, format="PNG")
        elif ext_l == "webp":
            out_img.convert("RGB").save(dst_path, format="WEBP", quality=90)
        else:
            dst_path = os.path.splitext(dst_path)[0] + ".jpg"
            out_img.convert("RGB").save(dst_path, format="JPEG", quality=95)

        return dst_path

    def _apply_watermark(self, base_path, wm_path, wm_w, wm_h, opacity_pct, anchor, padding, x_off, y_off):
        if not wm_path or not os.path.exists(wm_path):
            return base_path

        base = Image.open(base_path).convert("RGBA")
        wm = Image.open(wm_path).convert("RGBA")

        wm = wm.resize((max(1, wm_w), max(1, wm_h)), Image.LANCZOS)

        opacity = max(0, min(100, int(opacity_pct)))
        if opacity < 100:
            alpha = wm.split()[-1]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity / 100.0)
            wm.putalpha(alpha)

        W, H = base.size
        w, h = wm.size
        p = max(0, int(padding))
        xo = int(x_off)
        yo = int(y_off)

        anchor = (anchor or "br").lower().strip()
        if anchor == "tl":
            x = p + xo
            y = p + yo
        elif anchor == "tr":
            x = (W - w - p) + xo
            y = p + yo
        elif anchor == "bl":
            x = p + xo
            y = (H - h - p) + yo
        else:
            x = (W - w - p) + xo
            y = (H - h - p) + yo

        x = max(0, min(W - w, x))
        y = max(0, min(H - h, y))

        base.paste(wm, (x, y), wm)

        ext = os.path.splitext(base_path)[1].lower()
        if ext in (".jpg", ".jpeg", ".webp"):
            out = base.convert("RGB")
            if ext in (".jpg", ".jpeg"):
                out.save(base_path, format="JPEG", quality=95)
            else:
                out.save(base_path, format="WEBP", quality=90)
        else:
            base.save(base_path, format="PNG")

        return base_path

    def _resolve_wm_path(self, wm_file: str) -> str:
        wm_file = (wm_file or "").strip()
        if not wm_file:
            return ""
        if os.path.isabs(wm_file):
            return wm_file
        return os.path.join(os.getcwd(), wm_file)

    # =========================================================
    # main
    # =========================================================
    def main(self):
        try:
            self.log_signal_func("크롤링 시작")
            self.log_signal_func(f"엑셀 리스트: {self.excel_data_list}")
            self.log_signal_func(f"엑셀 세팅 항목: {self.setting}")
            self.log_signal_func(f"엑셀 컬럼 항목: {self.columns}")

            rows = self.excel_data_list or []
            if not rows:
                self.log_signal_func("❌ 엑셀 데이터 없음")
                return False

            self.total_cnt = len(rows)
            self.current_cnt = 0

            # 폴더 준비
            origin_dir = self.file_driver.create_folder("이미지 저장")
            edit_dir = self.file_driver.create_folder("이미지 수정")

            # setting
            tw = self._to_int(self.get_setting_value(self.setting, "thumb_width"), 1000)
            th = self._to_int(self.get_setting_value(self.setting, "thumb_height"), 1000)
            rotate_deg = self._to_int(self.get_setting_value(self.setting, "thumb_rotate_deg"), 0)
            scale_pct = self._to_int(self.get_setting_value(self.setting, "thumb_scale_pct"), 100)
            ext = self._to_str(self.get_setting_value(self.setting, "thumb_ext"), "jpg").lower().strip(".")
            delay_sec = self._to_int(self.get_setting_value(self.setting, "thumb_delay_sec"), 0)

            wm_enabled = bool(self.get_setting_value(self.setting, "wm_enabled"))
            wm_file = self._to_str(self.get_setting_value(self.setting, "wm_file"), "watermark.png")
            wm_width = self._to_int(self.get_setting_value(self.setting, "wm_width"), 35)
            wm_height = self._to_int(self.get_setting_value(self.setting, "wm_height"), 35)
            wm_opacity = self._to_int(self.get_setting_value(self.setting, "wm_opacity_pct"), 15)
            wm_anchor = self._to_str(self.get_setting_value(self.setting, "wm_anchor"), "br")
            wm_padding = self._to_int(self.get_setting_value(self.setting, "wm_padding"), 20)
            wm_x_offset = self._to_int(self.get_setting_value(self.setting, "wm_x_offset"), 0)
            wm_y_offset = self._to_int(self.get_setting_value(self.setting, "wm_y_offset"), 0)

            wm_path = self._resolve_wm_path(wm_file)
            if wm_enabled:
                if wm_path and os.path.exists(wm_path):
                    self.log_signal_func(f"워터마크 사용: {wm_path}")
                else:
                    self.log_signal_func(f"⚠️ 워터마크 ON 이지만 파일 없음: {wm_path} (워터마크 스킵)")

            # loop
            for idx, row in enumerate(rows, start=1):
                if not self.running:
                    self.log_signal_func("⛔ 사용자 중단")
                    break

                self.current_cnt += 1

                try:
                    # URL
                    url = (row.get("이미지 URL") or row.get("url") or "").strip()
                    if not url:
                        raise Exception("이미지 URL 없음")

                    # 결과 파일명
                    result_filename = (row.get("결과 파일명") or row.get("result_filename") or "").strip()
                    result_filename = self._safe_filename(result_filename)
                    if not result_filename:
                        result_filename = f"{idx}.{ext}"
                    else:
                        result_filename = self._ensure_ext(result_filename, ext)

                    # 수정 파일명
                    edit_filename = (row.get("수정 파일명") or row.get("edit_filename") or "").strip()
                    edit_filename = self._safe_filename(edit_filename)
                    if not edit_filename:
                        base, _ = os.path.splitext(result_filename)
                        edit_filename = f"{base}_edit.{ext}"
                    else:
                        edit_filename = self._ensure_ext(edit_filename, ext)

                    # 1) 원본 다운로드
                    origin_path = self.file_driver.save_image(origin_dir, result_filename, url)
                    if not origin_path:
                        raise Exception("원본 이미지 저장 실패")

                    # 2) 수정본 생성 (cover+crop)
                    edit_path = os.path.join(edit_dir, edit_filename)
                    edit_path = self._make_edit_image(
                        src_path=origin_path,
                        dst_path=edit_path,
                        tw=tw,
                        th=th,
                        rotate_deg=rotate_deg,
                        scale_pct=scale_pct,
                        ext=ext,
                    )

                    # 3) 워터마크 (수정본에 합성)
                    if wm_enabled and wm_path and os.path.exists(wm_path):
                        edit_path = self._apply_watermark(
                            base_path=edit_path,
                            wm_path=wm_path,
                            wm_w=wm_width,
                            wm_h=wm_height,
                            opacity_pct=wm_opacity,
                            anchor=wm_anchor,
                            padding=wm_padding,
                            x_off=wm_x_offset,
                            y_off=wm_y_offset,
                        )

                    # 결과 반영 (엑셀 헤더 기준)
                    row["이미지 URL"] = url
                    row["결과 파일명"] = result_filename
                    row["수정 파일명"] = edit_filename
                    row["결과 파일 경로"] = origin_path
                    row["수정 파일 경로"] = edit_path
                    row["상태"] = "성공"
                    row["메모"] = ""

                    self.log_signal_func(f"✅ 완료: {idx}/{self.total_cnt}  {result_filename}")

                except Exception as e:
                    row["상태"] = "실패"
                    row["메모"] = str(e)
                    self.log_signal_func(f"❌ 실패: {idx}/{self.total_cnt}  {e}")

                # progress
                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                if delay_sec > 0:
                    time.sleep(delay_sec)

            # =========================================================
            # ✅ 신규 엑셀 저장 (columns 체크된 것만)
            # =========================================================
            try:
                save_cols = self.columns or [
                    "이미지 URL",
                    "결과 파일명",
                    "수정 파일명",
                    "상태",
                    "메모",
                    "결과 파일 경로",
                    "수정 파일 경로",
                ]

                # 컬럼 누락 방지: rows에 키가 없으면 빈칸으로 넣어줌
                for r in rows:
                    for c in save_cols:
                        if c not in r:
                            r[c] = ""

                result_excel_path = self.file_driver.get_excel_filename("썸네일_결과")

                self.excel_driver.append_rows_text_excel(
                    filename=result_excel_path,
                    rows=rows,
                    columns=save_cols,
                    sheet_name="RESULT"
                )

                self.log_signal_func(f"📊 결과 엑셀 저장 완료: {result_excel_path}")

            except Exception as e:
                self.log_signal_func(f"❌ 결과 엑셀 저장 실패: {e}")

            return True

        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False

    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
