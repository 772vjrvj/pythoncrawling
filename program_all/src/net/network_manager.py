# src/net/network_manager.py
import os
import sys


class NetworkManager:
    """
    NetworkManager (현재 단계)
    - MainWindow에서 proxy_text / hooking_text 텍스트만 세팅
    - start()에서 텍스트 유무만 보고 hooking 쪽으로 위임
    - 실제 인증서/mitm 실행은 hooking 쪽에서 처리
    """

    def __init__(self, log_fn):
        self.log_fn = log_fn

        self.proxy_text = None
        self.hooking_text = None

        self.out_dir = None
        self.port = 8888

        self.is_running = False
        self.hooking_runner = None

    # -----------------------------
    # setters
    # -----------------------------
    def set_proxy_text(self, text):
        self.proxy_text = text

    def set_hooking_text(self, text):
        self.hooking_text = text

    def set_out_dir(self, out_dir):
        self.out_dir = out_dir

    def set_port(self, port):
        try:
            self.port = int(port)
        except Exception:
            self.port = 8888

    def reset(self):
        self.proxy_text = None
        self.hooking_text = None
        self.out_dir = None
        self.port = 8888

    # -----------------------------
    # lifecycle
    # -----------------------------
    def start(self):
        if self.is_running:
            self.add_log("NetworkManager: 이미 실행 중")
            return True

        if not self.out_dir:
            self.out_dir = os.path.abspath("./out")

        self.add_log("NetworkManager: start()")
        self.add_log(" - proxy_text   : %s" % str(self.proxy_text))
        self.add_log(" - hooking_text : %s" % str(self.hooking_text))
        self.add_log(" - out_dir      : %s" % str(self.out_dir))
        self.add_log(" - port         : %s" % str(self.port))

        # === 신규 === hooking 텍스트가 있으면 hooking으로 위임
        if self.hooking_text:
            try:
                from src.net.hooking.hooking_dispatcher import HookingDispatcher
                self.hooking_runner = HookingDispatcher(self.add_log)
                ok = self.hooking_runner.start(
                    hooking_text=self.hooking_text,
                    out_dir=self.out_dir,
                    port=self.port
                )
                if not ok:
                    self.add_log("NetworkManager: hooking start 실패")
                    self.hooking_runner = None
                    return False
            except Exception as e:
                self.add_log("NetworkManager: hooking 호출 실패: %s" % str(e))
                self.hooking_runner = None
                return False

        # (proxy_text 단독 실행은 다음 단계에서 붙이면 됨)
        if (not self.hooking_text) and (not self.proxy_text):
            self.add_log("NetworkManager: 네트워크 기능 없음(스킵)")

        self.is_running = True
        return True

    def stop(self):
        if not self.is_running:
            return

        self.add_log("NetworkManager: stop()")

        # === 신규 === hooking 종료 위임
        try:
            if self.hooking_runner:
                self.hooking_runner.stop()
        except Exception:
            pass

        self.hooking_runner = None
        self.is_running = False

    def stop_all(self):
        self.stop()

    # -----------------------------
    # log
    # -----------------------------
    def add_log(self, msg):
        try:
            if self.log_fn:
                self.log_fn(msg)
        except Exception:
            pass
