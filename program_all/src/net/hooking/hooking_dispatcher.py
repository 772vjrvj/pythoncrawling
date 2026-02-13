# src/net/hooking/hooking_dispatcher.py
import os
from src.net.hooking.addon_registry import get_addon_path
import sys
import time
import socket
import subprocess
import threading


class HookingDispatcher:
    """
    HookingDispatcher (1차)
    - worker_key -> addon 파일 경로 매핑
    - mitm 인증서 자동 설치 (우선 CurrentUser, 실패 시 LocalMachine + UAC)
    - mitmdump 실행/종료 관리
    - stdout 로그를 MainWindow 로그로 중계
    """

    def __init__(self, log_fn):
        self.log_fn = log_fn

        self.proc = None
        self.read_thread = None
        self.read_thread_alive = False

        self.port = 8888
        self.out_dir = None
        self.base_dir = None

    # -------------------------------------------------
    # public
    # -------------------------------------------------
    def start(self, worker_key, out_dir, port):
        self.add_log("HookingDispatcher: start()")

        if self.proc is not None:
            self.add_log("HookingDispatcher: 이미 실행 중")
            return True

        self.port = port or 8888
        self.out_dir = out_dir or os.path.abspath("./out")
        self.base_dir = self._get_base_dir()

        self.add_log(" - worker_key  : %s" % str(worker_key))
        self.add_log(" - out_dir     : %s" % str(self.out_dir))
        self.add_log(" - port        : %s" % str(self.port))
        self.add_log(" - base_dir    : %s" % str(self.base_dir))

        mitmdump_path = os.path.join(self.base_dir, "runtime", "mitm", "mitmdump.exe")
        if not os.path.isfile(mitmdump_path):
            self.add_log("HookingDispatcher: mitmdump.exe 없음: %s" % mitmdump_path)
            return False

        addon_path = self._resolve_addon_path(worker_key)
        if not addon_path:
            self.add_log("HookingDispatcher: addon 매핑 실패")
            return False

        # out 폴더 준비
        self._prepare_dirs(self.out_dir)

        # 인증서 자동 설치
        if not self._ensure_cert_ready(mitmdump_path):
            self.add_log("HookingDispatcher: 인증서 준비 실패")
            return False

        # mitmdump 실행
        env = os.environ.copy()
        env["HOOK_OUT_DIR"] = os.path.abspath(self.out_dir)
        env["HOOK_INBOX_DIR"] = os.path.join(os.path.abspath(self.out_dir), "inbox")

        log_file = os.path.join(os.path.abspath(self.out_dir), "mitm.log")
        conf_dir = os.path.join(os.path.expanduser("~"), ".mitmproxy")

        cmd = [
            mitmdump_path,
            "-p", str(self.port),

            # === 신규 === mitm 설정
            "--set", "confdir=%s" % conf_dir,
            "--set", "termlog_verbosity=debug",
            "--set", 'termlog_file="%s"' % log_file,

            "-s", addon_path
        ]

        self.add_log("HookingDispatcher: mitm.log = %s" % log_file)
        self.add_log("HookingDispatcher: confdir  = %s" % conf_dir)


        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env
            )
        except Exception as e:
            self.add_log("HookingDispatcher: mitmdump 실행 실패: %s" % str(e))
            self.proc = None
            return False

        # stdout 중계 스레드
        self._start_read_thread()

        # 포트 오픈 확인
        if not self._wait_port("127.0.0.1", self.port, 6.0):
            self.add_log("HookingDispatcher: 포트 오픈 실패: %s" % str(self.port))
            self.stop()
            return False

        self.add_log("HookingDispatcher: 준비 완료")
        return True

    def stop(self):
        if self.proc is None:
            return

        self.add_log("HookingDispatcher: stop()")

        self.read_thread_alive = False

        try:
            self.proc.terminate()
        except Exception:
            pass

        for _ in range(30):
            try:
                if self.proc.poll() is not None:
                    break
            except Exception:
                break
            time.sleep(0.1)

        try:
            if self.proc and self.proc.poll() is None:
                self.proc.kill()
        except Exception:
            pass

        self.proc = None
        self.add_log("HookingDispatcher: 종료 완료")

    def _find_ca_cert_file(self, cert_dir):
        # mitmproxy가 만들어주는 ca cert 후보들
        candidates = [
            "mitmproxy-ca-cert.cer",
            "mitmproxy-ca-cert.pem",
            "mitmproxy-ca.cer",
            "mitmproxy-ca.pem",
        ]

        for name in candidates:
            p = os.path.join(cert_dir, name)
            if os.path.isfile(p):
                return p

        # 후보가 다르면 폴더 스캔으로 보수적으로 찾기
        try:
            for name in os.listdir(cert_dir):
                low = name.lower()
                if "mitmproxy-ca" in low and (low.endswith(".cer") or low.endswith(".pem") or low.endswith(".crt")):
                    p = os.path.join(cert_dir, name)
                    if os.path.isfile(p):
                        return p
        except Exception:
            pass

        return None


    # -------------------------------------------------
    # internal: addon mapping
    # -------------------------------------------------
    def _resolve_addon_path(self, hooking_text):

        try:
            addon_path = get_addon_path(hooking_text)
        except Exception as e:
            self.add_log("HookingDispatcher: addon 키 오류: %s" % str(e))
            return None

        if not os.path.isfile(addon_path):
            self.add_log("HookingDispatcher: addon 파일 없음: %s" % addon_path)
            return None

        return addon_path
    # -------------------------------------------------
    # internal: cert
    # -------------------------------------------------
    def _ensure_cert_ready(self, mitmdump_path):
        cert_dir = os.path.join(os.path.expanduser("~"), ".mitmproxy")
        self.add_log("HookingDispatcher: cert_dir = %s" % cert_dir)
        try:
            self.add_log("HookingDispatcher: cert_dir exists = %s" % str(os.path.isdir(cert_dir)))
            self.add_log("HookingDispatcher: cert_dir list = %s" % str(os.listdir(cert_dir))[:300])
        except Exception as e:
            self.add_log("HookingDispatcher: cert_dir list error = %s" % str(e))

        # 1) cert 파일 존재 확인(없으면 생성 시도)
        ca_path = self._find_ca_cert_file(cert_dir)

        if not ca_path:
            self.add_log("HookingDispatcher: ca cert 없음 -> 생성 시도")
            if not self._generate_cert_once(mitmdump_path):
                return False

            ca_path = self._find_ca_cert_file(cert_dir)

        if not ca_path:
            self.add_log("HookingDispatcher: ca cert 생성 실패(파일 없음): %s" % cert_dir)
            return False


        # 설치 시도
        self.add_log("HookingDispatcher: certutil (CurrentUser Root) 설치 시도")
        ok = self._install_cert_user_root(ca_path)
        if ok:
            self.add_log("HookingDispatcher: 인증서 설치 완료(CurrentUser)")
            return True

        self.add_log("HookingDispatcher: CurrentUser 설치 실패 -> LocalMachine 시도")
        self.add_log("HookingDispatcher: ca cert 확인: %s" % ca_path)

        # 3) LocalMachine
        self.add_log("HookingDispatcher: CurrentUser 설치 실패 -> LocalMachine 시도")

        if self._is_admin():
            ok2 = self._install_cert_machine_root(ca_path)
            if ok2:
                self.add_log("HookingDispatcher: 인증서 설치 완료(LocalMachine)")
                return True
            self.add_log("HookingDispatcher: LocalMachine 설치도 실패")
            return False

        self.add_log("HookingDispatcher: 관리자 권한 필요 -> UAC 요청")
        ok3 = self._install_cert_machine_root_uac(ca_path)
        if ok3:
            self.add_log("HookingDispatcher: 인증서 설치 완료(LocalMachine/UAC)")
            return True

        self.add_log("HookingDispatcher: UAC 설치 실패/거부됨")
        return False


    def _generate_cert_once(self, mitmdump_path):
        cmd = [mitmdump_path, "-p", "0"]
        p = None
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.add_log("HookingDispatcher: 인증서 생성용 mitmdump 실행 실패: %s" % str(e))
            return False

        # 기존 0.8초는 너무 짧을 수 있음
        time.sleep(2.0)

        try:
            p.terminate()
        except Exception:
            pass

        for _ in range(20):
            try:
                if p.poll() is not None:
                    break
            except Exception:
                break
            time.sleep(0.1)

        cert_dir = os.path.join(os.path.expanduser("~"), ".mitmproxy")
        return self._find_ca_cert_file(cert_dir) is not None


    def _install_cert_user_root(self, cer_path):
        cmd = ["certutil", "-user", "-addstore", "-f", "Root", cer_path]
        return self._run_cmd_ok(cmd)

    def _install_cert_machine_root(self, cer_path):
        cmd = ["certutil", "-addstore", "-f", "Root", cer_path]
        return self._run_cmd_ok(cmd)

    def _install_cert_machine_root_uac(self, cer_path):
        ps = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            'Start-Process -FilePath certutil -ArgumentList \'-addstore -f Root "%s"\' -Verb RunAs -Wait' % cer_path.replace('"', '\\"')
        ]
        return self._run_cmd_ok(ps)

    def _run_cmd_ok(self, cmd):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
        except Exception as e:
            self.add_log("HookingDispatcher: cmd 실행 예외: %s" % str(e))
            return False

        if r.returncode == 0:
            return True

        try:
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
            if out:
                self.add_log(" - stdout: %s" % out[:300])
            if err:
                self.add_log(" - stderr: %s" % err[:300])
        except Exception:
            pass

        return False

    def _is_admin(self):
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    # -------------------------------------------------
    # internal: process stdout -> log
    # -------------------------------------------------
    def _start_read_thread(self):
        if not self.proc or not self.proc.stdout:
            return

        self.read_thread_alive = True

        def _loop():
            try:
                while self.read_thread_alive:
                    line = self.proc.stdout.readline()
                    if not line:
                        break

                    line = line.rstrip("\r\n")

                    if not line:
                        continue

                    # ⭐ 필요한 로그만 통과
                    if (
                            "addon loaded" in line
                            or "proxy listening" in line
                            or "[SAVE]" in line
                            or "server shutdown" in line
                            or "Shutting down" in line
                    ):
                        self.add_log("[mitm] " + line)

            except Exception:
                pass

        t = threading.Thread(target=_loop, daemon=True)
        self.read_thread = t
        t.start()

    # -------------------------------------------------
    # internal: dirs / port
    # -------------------------------------------------
    def _prepare_dirs(self, out_dir):
        inbox = os.path.join(out_dir, "inbox")
        done = os.path.join(out_dir, "done")
        failed = os.path.join(out_dir, "failed")

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        if not os.path.isdir(inbox):
            os.makedirs(inbox)
        if not os.path.isdir(done):
            os.makedirs(done)
        if not os.path.isdir(failed):
            os.makedirs(failed)

    def _wait_port(self, host, port, timeout_sec):
        end = time.time() + float(timeout_sec)
        while time.time() < end:
            s = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                s.connect((host, int(port)))
                try:
                    s.close()
                except Exception:
                    pass
                return True
            except Exception:
                try:
                    if s:
                        s.close()
                except Exception:
                    pass
                time.sleep(0.1)
        return False

    def _get_base_dir(self):
        try:
            if getattr(sys, "frozen", False):
                return os.path.dirname(sys.executable)
        except Exception:
            pass
        return os.path.abspath(".")

    def add_log(self, msg):
        try:
            if self.log_fn:
                self.log_fn(msg)
        except Exception:
            pass
