import os
import re
import time
import threading
from collections import defaultdict
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt5.QtCore import QThread, pyqtSignal

from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker


class ApiNaverCafeCountOnlySetLoadWorker(BaseApiWorker):

    def __init__(self):
        super().__init__()
        self.selenium_driver = None
        self.file_driver = None
        self.excel_driver = None
        self.base_main_url = "https://www.onthespot.co.kr/"
        self.url_list: List[str] = []
        self.running = True
        self.site_name = "naver_cafe"
        self.excel_filename = ""
        self.result_list: List[Dict[str, Any]] = []
        self.before_pro_value = 0

        # 병렬 처리 설정
        self.max_workers = 5
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()

        # 진행률 1회만 내보내기 위한 플래그
        self._progress_emitted = False

    # 초기화
    def init(self):
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        return True

    # 입력에서 (url, file) 추출
    def _extract_inputs(self) -> List[Tuple[str, str]]:
        """
        excel_data_list에서 url, file(없으면 '__unknown__')을 뽑아 (url, file) 리스트로 반환
        - key는 대소문자 무시
        - url 공백/빈값 제외
        """
        pairs: List[Tuple[str, str]] = []
        for row in self.excel_data_list:
            # key lower 매핑
            lower_map = {k.lower(): k for k in row.keys()}
            url_key = lower_map.get("url")
            file_key = lower_map.get("file")  # UI에서 추가한 'file' 컬럼

            url_val = str(row[url_key]).strip() if (url_key and row.get(url_key)) else ""
            if not url_val:
                continue
            file_val = str(row[file_key]).strip() if (file_key and row.get(file_key)) else "__unknown__"
            pairs.append((url_val, file_val))
        return pairs

    # 메인
    def main(self):
        try:
            self.log_signal_func("크롤링 시작")

            url_file_pairs = self._extract_inputs()
            total = len(url_file_pairs)
            if total == 0:
                self.log_signal_func("처리할 URL이 없습니다.")
                return True

            # 병렬 실행 (재시도 없음 / 실패 시 바로 다음)
            self._executor = ThreadPoolExecutor(max_workers=min(self.max_workers, total))
            futures = {}
            for url, file_tag in url_file_pairs:
                if not self.running:
                    break
                fut = self._executor.submit(self._fetch_once, url, file_tag)
                futures[fut] = (url, file_tag)

            done_count = 0
            for fut in as_completed(futures):
                url, file_tag = futures[fut]
                if not self.running:
                    break

                try:
                    obj = fut.result()
                except Exception as e:
                    obj = {"url": url, "count": f"요청 실패: {e}", "file": file_tag}

                with self._lock:
                    self.result_list.append(obj)
                    done_count += 1
                    self.log_signal_func(f"전체 ({done_count}/{total}) : {url}")

            # === 파일명(file) 별로 저장 ===
            if self.result_list:
                # 기본 저장 경로를 얻어서 디렉터리만 재사용
                base_path = self.file_driver.get_excel_filename(self.site_name)
                out_dir = os.path.dirname(base_path) if base_path else os.getcwd()
                ts = time.strftime("%Y%m%d_%H%M%S")

                grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
                for obj in self.result_list:
                    file_tag = str(obj.get("file", "__unknown__"))
                    # 저장시에는 'file' 제외하고 url/count만 담기
                    grouped[file_tag].append({"url": obj.get("url", ""), "count": obj.get("count", "")})

                for file_tag, rows in grouped.items():
                    safe_file_tag = re.sub(r"[^\w\.-]+", "_", file_tag)  # 파일명 안전화
                    excel_filename = os.path.join(out_dir, f"{self.site_name}__{safe_file_tag}__{ts}.xlsx")
                    self.excel_driver.save_obj_list_to_excel(
                        excel_filename,
                        rows,
                        columns=["url", "count"],  # file 컬럼 저장 안 함
                        sheet_name="TX"
                    )
                    self.log_signal_func(f"저장 완료: {excel_filename}")
            return True

        except Exception as e:
            self.log_signal_func(f"❌ 전체 실행 중 예외 발생: {e}")
            return False

        finally:
            if self._executor:
                self._executor.shutdown(wait=False)
                self._executor = None

    def _fetch_once(self, url: str, file_tag: str) -> Dict[str, Any]:
        """
        한 URL에 대해 API 호출 1회만 수행 (실패 시 바로 메시지 반환).
        stop() 호출 시 즉시 중단.
        file_tag를 결과에 포함시켜 후처리에서 그룹핑 가능하도록 함.
        """
        if not self.running:
            return {"url": url, "count": "중단됨", "file": file_tag}

        api_client = APIClient(use_cache=False)

        # cafeId/articleId 추출
        m = re.search(r"cafe\.naver\.com/([^/]+)/(\d+)", url)
        if not m:
            return {"url": url, "count": "URL 형식 오류", "file": file_tag}
        cafe_id, article_id = m.group(1), m.group(2)

        api_url = f"https://article.cafe.naver.com/gw/v3/cafes/{cafe_id}/articles/{article_id}?useCafeId=false"
        headers = {
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
            "referer": f"https://m.cafe.naver.com/ca-fe/web/cafes/{cafe_id}/articles/{article_id}?useCafeId=false&tc",
        }

        try:
            json_data = api_client.get(api_url, headers=headers)
            count = json_data.get("result", {}).get("article", {}).get("readCount")
            if count is None:
                return {"url": url, "count": "글이 삭제되었습니다", "file": file_tag}
            return {"url": url, "count": count, "file": file_tag}
        except Exception as e:
            self.log_signal_func(f"❌ 조회중 에러: {e} | {url}")
            return {"url": url, "count": "글이 삭제되었습니다", "file": file_tag}

    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        if self.running:
            self.progress_end_signal.emit()

    # 프로그램 중단
    def stop(self):
        self.running = False
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
