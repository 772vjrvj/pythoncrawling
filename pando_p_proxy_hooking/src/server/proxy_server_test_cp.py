from mitmproxy import http
import logging
import sys
import os
import io

class ProxyLogger:
    def __init__(self):
        # 콘솔 한글 출력 지원
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace')

        # 로거 설정
        self.logger = logging.getLogger("proxy_logger")
        self.logger.setLevel(logging.INFO)

        # 콘솔 출력 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        self.logger.addHandler(console_handler)

        # 파일 핸들러 (UTF-8 저장)
        log_file_path = os.path.join(os.path.dirname(__file__), "proxy_utf8.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(file_handler)

        self.logger.info("🚀 프록시 서버 로딩 완료 (한글 출력 테스트)")

    def request(self, flow: http.HTTPFlow):
        msg = f"[요청] {flow.request.method} {flow.request.pretty_url}"
        self.logger.info(msg)

    def response(self, flow: http.HTTPFlow):
        msg = f"[응답] {flow.request.method} {flow.request.pretty_url} → {flow.response.status_code}"
        self.logger.info(msg)

addons = [ProxyLogger()]
