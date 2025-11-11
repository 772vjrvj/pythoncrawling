# launcher_qt.py
# -*- coding: utf-8 -*-
"""
PandoP 런처(자기 위치 기준 win-unpacked\PandoP.exe 실행 및 감시)
- 기본 동작: 런처(exe 혹은 script)가 있는 폴더를 기준으로 win-unpacked\PandoP.exe 를 실행/감시
- frozen(PyInstaller) / script 둘 다 동작
- 사용법:
    python launcher_qt.py --interval 5
    또는 (원할 경우) python launcher_qt.py --target "C:\... \win-unpacked\PandoP.exe" --interval 5
"""

import sys
import time
import logging
import subprocess
import socket
import argparse
from pathlib import Path

try:
    import psutil
except ImportError:
    print("psutil이 필요합니다. 설치: pip install psutil")
    sys.exit(1)


# -----------------------
# 기본값(필요시 수정)
# -----------------------
DEFAULT_CHECK_INTERVAL = 60
DEFAULT_SINGLE_PORT = 34211
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 30  # 초


# -----------------------
# 로거 설정
# -----------------------
def setup_logger(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "launcher.log"

    logger = logging.getLogger("pandop_launcher")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    return logger


# -----------------------
# 경로 결정 유틸
# -----------------------
def get_base_dir() -> Path:
    """
    런처의 '현재 위치(배포된 exe의 폴더 또는 .py 파일의 폴더)'를 반환.
    - PyInstaller로 빌드한 exe일 때는 sys.executable의 부모
    - 스크립트로 실행할 때는 __file__의 부모
    """
    if getattr(sys, "frozen", False):
        # PyInstaller로 빌드된 경우
        return Path(sys.executable).resolve().parent
    else:
        # 스크립트로 실행한 경우
        return Path(__file__).resolve().parent


# -----------------------
# 프로세스 검사 및 시작
# -----------------------
def is_running_by_path(target_path: Path) -> bool:
    try:
        target_real = str(target_path.resolve())
    except Exception:
        target_real = str(target_path)
    for proc in psutil.process_iter(['pid', 'exe', 'cmdline']):
        try:
            exe = proc.info.get('exe') or ""
            if exe:
                if str(Path(exe).resolve()) == target_real:
                    return True
            else:
                cmd = proc.info.get('cmdline') or []
                if cmd and Path(cmd[0]).exists():
                    if str(Path(cmd[0]).resolve()) == target_real:
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def start_target(target_path: Path, logger) -> subprocess.Popen:
    if not target_path.exists():
        raise FileNotFoundError(f"Target not found: {target_path}")
    cwd = str(target_path.parent)
    # 윈도우에서 콘솔 창을 안 띄우고 싶으면 creationflags 옵션 추가 가능
    p = subprocess.Popen([str(target_path)], cwd=cwd)
    logger.info(f"Start requested: {target_path} (pid={p.pid})")
    return p


def ensure_single_instance(port: int, logger) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('127.0.0.1', port))
        s.listen(1)
        logger.info(f"Single-instance lock acquired on port {port}")
        return s
    except OSError:
        logger.error("Launcher already running (single-instance lock failed). Exiting.")
        s.close()
        sys.exit(0)


# -----------------------
# 메인 루프
# -----------------------
def main():
    ap = argparse.ArgumentParser(description="PandoP Launcher (watcher) - base on launcher location")
    ap.add_argument('--target', '-t', required=False,
                    help='(선택) full path to PandoP.exe. 없으면 런처 위치 기준 win-unpacked\\PandoP.exe 사용')
    ap.add_argument('--interval', '-i', type=int, default=DEFAULT_CHECK_INTERVAL,
                    help='체크 주기(초). 테스트용으로 5 사용 가능')
    ap.add_argument('--logdir', default=None, help='로그 디렉토리(선택). 기본: 런처 위치/launcher_logs')
    ap.add_argument('--port', type=int, default=DEFAULT_SINGLE_PORT, help='single-instance 포트')
    ap.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES, help='연속 재시도 허용 횟수')
    args = ap.parse_args()

    # 대상 경로 결정: 인수가 있으면 그거, 없으면 런처 위치 기준 win-unpacked\PandoP.exe
    if args.target:
        target_path = Path(args.target).resolve()
    else:
        base = get_base_dir()
        target_path = base / "win-unpacked" / "PandoP.exe"

    if not target_path.exists():
        print(f"[ERROR] 대상 PandoP.exe를 찾을 수 없습니다: {target_path}")
        print(" - 런처를 PandoP가 설치된 상위 폴더(또는 exe와 같은 폴더)에 두거나")
        print(" - --target 인수로 경로를 직접 지정하세요.")
        sys.exit(1)

    log_dir = Path(args.logdir) if args.logdir else target_path.parent / "launcher_logs"
    logger = setup_logger(log_dir)

    logger.info("Launcher starting...")
    logger.info(f"Target resolved: {target_path}")
    lock_sock = ensure_single_instance(args.port, logger)

    retry_count = 0
    try:
        while True:
            try:
                if is_running_by_path(target_path):
                    logger.debug("Target already running.")
                    retry_count = 0
                else:
                    logger.info("Target not running. Attempting to start...")
                    try:
                        start_target(target_path, logger)
                        time.sleep(2)
                        if is_running_by_path(target_path):
                            logger.info("Target started successfully.")
                            retry_count = 0
                        else:
                            retry_count += 1
                            logger.warning(f"Start attempted but target not found. retry_count={retry_count}")
                    except Exception as e:
                        retry_count += 1
                        logger.exception(f"Failed to start target (attempt {retry_count}): {e}")

                    if retry_count >= args.max_retries:
                        logger.error(f"Exceeded max retries ({args.max_retries}). Backing off for {DEFAULT_RETRY_BACKOFF}s")
                        time.sleep(DEFAULT_RETRY_BACKOFF)
                        retry_count = 0

                time.sleep(max(1, args.interval))
            except KeyboardInterrupt:
                logger.info("Launcher interrupted by user.")
                break
            except Exception as e:
                logger.exception(f"Unexpected error in loop: {e}")
                time.sleep(5)
    finally:
        try:
            lock_sock.close()
        except Exception:
            pass
        logger.info("Launcher exiting.")


if __name__ == "__main__":
    main()
